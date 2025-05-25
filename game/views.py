import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from . import models
from .models import User, Word, Game, GameState, GameHistory
from .serializers import LoginSerializer, SignupSerializer, UserSerializer, GameSerializer, GameStateSerializer, \
    GameHistorySerializer
import random
from datetime import timedelta


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            return Response({'error': 'نام کاربری یا رمز عبور اشتباه است'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class GameHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        histories = GameHistory.objects.filter(player=request.user)
        serializer = GameHistorySerializer(histories, many=True)
        return Response(serializer.data)


class NewGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['player1'] = request.user.id
        serializer = GameSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            with transaction.atomic():
                game = serializer.save(player1=request.user)
                time_limit = {'easy': 300, 'medium': 240, 'hard': 180}[game.level]
                word = Word.objects.filter(level=game.level).order_by('?').first()
                state_data = {
                    'game': game.id,
                    'current_player': request.user.id,
                    'word': word.id,
                    'player1_time': time_limit,
                    'player2_time': time_limit,
                    'revealed_letters': {str(request.user.id): [], 'player2': []},
                    'hints_used': {str(request.user.id): [1], 'player2': [1]}
                }
                state_serializer = GameStateSerializer(data=state_data)
                if state_serializer.is_valid():
                    state_serializer.save()
                    return Response({'game_id': game.game_id, 'status': 'pending'}, status=status.HTTP_201_CREATED)
                return Response(state_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JoinGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(game_id=game_id, status='pending')
            if game.player1 == request.user:
                return Response({'error': 'نمی‌توانید به بازی خودتان بپیوندید'}, status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic():
                game.player2 = request.user
                game.status = 'active'
                game.save()
                state = GameState.objects.get(game=game)
                state.current_player = random.choice([game.player1, game.player2])
                state.last_turn_time = timezone.now()
                state.revealed_letters['player2'] = []
                state.hints_used['player2'] = [1]
                state.save()
                serializer = GameSerializer(game)
                return Response(serializer.data)
        except Game.DoesNotExist:
            return Response({'error': 'بازی یافت نشد یا در انتظار نیست'}, status=status.HTTP_404_NOT_FOUND)


class GameStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, game_id):
        try:
            game = Game.objects.get(game_id=game_id)
            if request.user not in [game.player1, game.player2]:
                return Response({'error': 'عدم دسترسی'}, status=status.HTTP_403_FORBIDDEN)
            state = GameState.objects.get(game=game)
            serializer = GameStateSerializer(state)
            return Response(serializer.data)
        except Game.DoesNotExist:
            return Response({'error': 'بازی یافت نشد'}, status=status.HTTP_404_NOT_FOUND)


class GuessView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(game_id=game_id, status='active')
            if request.user not in [game.player1, game.player2]:
                return Response({'error': 'شما اجازه دسترسی به این بازی را ندارید.'}, status=status.HTTP_403_FORBIDDEN)
            state = GameState.objects.get(game=game)
            if state.current_player != request.user:
                return Response({'error': 'الان نوبت شما نیست.'}, status=status.HTTP_400_BAD_REQUEST)

            letter = request.data.get('letter', '').upper()
            position = request.data.get('position')
            if not letter or position is None:
                return Response({'error': 'لطفاً یک حرف و موقعیت آن را وارد کنید.'}, status=status.HTTP_400_BAD_REQUEST)

            word = state.word.text.upper()
            if not re.match(r'^[A-Z]$', letter):
                return Response({'error': 'حرف باید یک کاراکتر از A تا Z باشد.'}, status=status.HTTP_400_BAD_REQUEST)
            if position < 0 or position >= len(word):
                return Response({'error': 'موقعیت واردشده معتبر نیست.'}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # اطمینان از اینکه guessed_letters یک لیست است
                if not isinstance(state.guessed_letters, list):
                    state.guessed_letters = []

                # ثبت حدس جدید
                guess = {'letter': letter, 'correct': letter == word[position], 'position': position}
                state.guessed_letters.append(guess)

                if guess['correct']:
                    if request.user == game.player1:
                        state.player1_score += 20
                        request.user.coins += 1
                    else:
                        state.player2_score += 20
                        request.user.coins += 1
                    request.user.save()
                else:
                    if request.user == game.player1:
                        state.player1_score -= 20
                    else:
                        state.player2_score -= 20

                state.current_player = game.player2 if request.user == game.player1 else game.player1
                state.last_turn_time = timezone.now()
                state.save()

                # چک کردن اتمام بازی
                correct_positions = set(g['position'] for g in state.guessed_letters if g['correct'])
                if len(correct_positions) == len(word):
                    return self.end_game(game, state)

                serializer = GameStateSerializer(state)
                return Response(serializer.data)
        except Game.DoesNotExist:
            return Response({'error': 'این بازی وجود ندارد.'}, status=status.HTTP_404_NOT_FOUND)

    def end_game(self, game, state):
        game.status = 'finished'
        with transaction.atomic():
            if state.player1_score > state.player2_score:
                game.winner = game.player1
                game.player1.xp += 50
                game.player1.save()
                GameHistory.objects.create(game=game, player=game.player1, opponent=game.player2, level=game.level, result='won')
                GameHistory.objects.create(game=game, player=game.player2, opponent=game.player1, level=game.level, result='lost')
            elif state.player2_score > state.player1_score:
                game.winner = game.player2
                game.player2.xp += 50
                game.player2.save()
                GameHistory.objects.create(game=game, player=game.player2, opponent=game.player1, level=game.level, result='won')
                GameHistory.objects.create(game=game, player=game.player1, opponent=game.player2, level=game.level, result='lost')
            else:
                GameHistory.objects.create(game=game, player=game.player1, opponent=game.player2, level=game.level, result='draw')
                GameHistory.objects.create(game=game, player=game.player2, opponent=game.player1, level=game.level, result='draw')
            game.save()
        serializer = GameSerializer(game)
        return Response({'status': 'game ended', 'game': serializer.data})

class HintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(game_id=game_id, status='active')
            if request.user not in [game.player1, game.player2]:
                return Response({'error': 'شما اجازه دسترسی به این بازی را ندارید.'}, status=status.HTTP_403_FORBIDDEN)
            if request.user.coins < 1:
                return Response({'error': 'شما سکه کافی برای گرفتن نکته ندارید.'}, status=status.HTTP_400_BAD_REQUEST)

            state = GameState.objects.get(game=game)
            user_hints = state.hints_used.get(str(request.user.id), [1])
            if len(user_hints) >= 3:
                return Response({'error': 'شما نمی‌توانید نکته دیگری بگیرید.'}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                next_hint = max(user_hints) + 1
                user_hints.append(next_hint)
                state.hints_used[str(request.user.id)] = user_hints
                request.user.coins -= 1
                request.user.save()
                state.last_turn_time = timezone.now()  # آپدیت زمان نوبت
                state.save()
                hint_text = getattr(state.word, f'hint{next_hint}')
                return Response({'hint': hint_text})
        except Game.DoesNotExist:
            return Response({'error': 'این بازی وجود ندارد.'}, status=status.HTTP_404_NOT_FOUND)

class RevealLetterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(game_id=game_id, status='active')
            if request.user not in [game.player1, game.player2]:
                return Response({'error': 'شما اجازه دسترسی به این بازی را ندارید.'}, status=status.HTTP_403_FORBIDDEN)
            if request.user.coins < 1:
                return Response({'error': 'شما سکه کافی برای نمایش حرف ندارید.'}, status=status.HTTP_400_BAD_REQUEST)

            state = GameState.objects.get(game=game)
            word = state.word.text.upper()
            unrevealed = [i for i in range(len(word)) if
                          word[i] not in state.revealed_letters.get(str(request.user.id), [])]
            if not unrevealed:
                return Response({'error': 'هیچ حرفی برای نمایش باقی نمانده است.'}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                position = random.choice(unrevealed)
                letter = word[position]
                user_revealed = state.revealed_letters.get(str(request.user.id), [])
                user_revealed.append(letter)
                state.revealed_letters[str(request.user.id)] = user_revealed
                request.user.coins -= 1
                request.user.save()
                state.last_turn_time = timezone.now()  # آپدیت زمان نوبت
                state.save()
                return Response({'letter': letter, 'position': position})
        except Game.DoesNotExist:
            return Response({'error': 'این بازی وجود ندارد.'}, status=status.HTTP_404_NOT_FOUND)

class PauseGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(game_id=game_id, status='active')
            if request.user not in [game.player1, game.player2]:
                return Response({'error': 'شما اجازه دسترسی به این بازی را ندارید'}, status=status.HTTP_403_FORBIDDEN)
            if not game.player2:
                return Response({'error': 'بازی هنوز بازیکن دوم ندارد و نمی‌توان آن را متوقف کرد'}, status=status.HTTP_400_BAD_REQUEST)
            state = GameState.objects.get(game=game)
            with transaction.atomic():
                game.status = 'paused'
                state.paused_at = timezone.now()
                game.save()
                state.save()
                serializer = GameSerializer(game)
                return Response({'status': 'paused', 'game': serializer.data})
        except Game.DoesNotExist:
            return Response({'error': 'بازی یافت نشد'}, status=status.HTTP_404_NOT_FOUND)


class ResumeGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(game_id=game_id, status='paused')
            if request.user not in [game.player1, game.player2]:
                return Response({'error': 'شما اجازه دسترسی به این بازی را ندارید'}, status=status.HTTP_403_FORBIDDEN)
            if not game.player2:
                with transaction.atomic():
                    game.status = 'pending'  # برگرداندن به حالت pending
                    game.save()
                    return Response({'status': 'returned_to_pending', 'message': 'بازی به حالت انتظار برگشت چون بازیکن دوم وجود ندارد'})
            if (timezone.now() - game.created_at).days > 7:
                return Response({'error': 'بازی منقضی شده است'}, status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic():
                game.status = 'active'
                state = GameState.objects.get(game=game)
                state.paused_at = None
                state.last_turn_time = timezone.now()
                game.save()
                state.save()
                serializer = GameSerializer(game)
                return Response({'status': 'resumed', 'game': serializer.data})
        except Game.DoesNotExist:
            return Response({'error': 'بازی یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

class GuessWordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(game_id=game_id, status='active')
            if request.user not in [game.player1, game.player2]:
                return Response({'error': 'عدم دسترسی'}, status=status.HTTP_403_FORBIDDEN)
            state = GameState.objects.get(game=game)
            if state.current_player != request.user:
                return Response({'error': 'نوبت شما نیست'}, status=status.HTTP_400_BAD_REQUEST)

            guess = request.data.get('guess', '').upper()
            word = state.word.text.upper()
            with transaction.atomic():
                if guess == word:
                    game.winner = request.user
                    request.user.xp += 50
                    request.user.save()
                    GameHistory.objects.create(game=game, player=game.player1, opponent=game.player2, level=game.level,
                                               result='won' if game.player1 == request.user else 'lost')
                    GameHistory.objects.create(game=game, player=game.player2, opponent=game.player1, level=game.level,
                                               result='won' if game.player2 == request.user else 'lost')
                else:
                    game.winner = game.player2 if request.user == game.player1 else game.player1
                    game.winner.xp += 50
                    game.winner.save()
                    GameHistory.objects.create(game=game, player=game.player1, opponent=game.player2, level=game.level,
                                               result='won' if game.player1 == game.winner else 'lost')
                    GameHistory.objects.create(game=game, player=game.player2, opponent=game.player1, level=game.level,
                                               result='won' if game.player2 == game.winner else 'lost')
                game.status = 'finished'
                game.save()
                serializer = GameSerializer(game)
                return Response({'status': 'game ended', 'game': serializer.data})
        except Game.DoesNotExist:
            return Response({'error': 'بازی یافت نشد'}, status=status.HTTP_404_NOT_FOUND)


class PendingGamesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        games = Game.objects.filter(status='pending').exclude(player1=request.user)
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)


class PausedGamesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        games = Game.objects.filter(status='paused', player2__isnull=False).filter(
            models.Q(player1=request.user) | models.Q(player2=request.user))
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)