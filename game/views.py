import re
from sqlite3 import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
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
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
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
        print("DEBUG: Entering NewGameView post method...")
        level = request.data.get('level')
        print(f"DEBUG: Received level from request.data: {level}")

        defined_levels = [choice[0] for choice in Game.LEVEL_CHOICES]
        if not level or level not in defined_levels:
            print(f"DEBUG: Invalid level received: {level}. Valid levels are: {defined_levels}")
            raise serializers.ValidationError(
                {'level': [f'فیلد "level" ضروری است و باید یکی از مقادیر {defined_levels} باشد.']}
            )
        print(f"DEBUG: Level validation passed: {level}")

        try:
            with transaction.atomic():
                game = Game.objects.create(player1=request.user, level=level, status='pending')
                print(f"DEBUG: Game object created: game.id={game.id}, game.game_id (UUID)={game.game_id}")

                time_limit_dict = {'easy': 300, 'medium': 240, 'hard': 180}
                time_limit = time_limit_dict[game.level]

                print(f"DEBUG: Attempting to select Word with level={game.level} (without is_active filter)")
                word = Word.objects.filter(level=game.level).order_by('?').first()

                print(f"DEBUG: Selected Word: {word}, Word ID: {word.id if word else 'None'}")
                if not word:
                    print(f"DEBUG: No word found for level {game.level}")
                    raise serializers.ValidationError(
                        {'level': [f'کلمه‌ای برای سطح "{game.level}" یافت نشد.']}
                    )

                player1_id_str = str(request.user.id)
                print(
                    f"DEBUG: Attempting to create GameState with game.id={game.id}, word.id={word.id}, user.id={request.user.id}")

                GameState.objects.create(
                    game=game,
                    word=word,
                    current_player=request.user,
                    player1_time=time_limit,
                    player2_time=time_limit,
                    revealed_letters={player1_id_str: []},
                    hints_used={player1_id_str: []}
                )
                print(f"DEBUG: GameState created successfully for game.id={game.id}")

                return Response({'game_id': game.game_id, 'status': game.status}, status=status.HTTP_201_CREATED)

        except serializers.ValidationError as e_val:
            print(f"DEBUG: ValidationError in NewGameView for user {request.user.username}: {e_val.detail}")
            return Response(e_val.detail, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as ie_gs:
            print(f"DEBUG: IntegrityError during Game/GameState creation: {str(ie_gs)}")
            print(
                f"DEBUG: Values at potential GameState creation: game.pk={getattr(game, 'pk', 'N/A')}, word.pk={getattr(word, 'pk', 'N/A')}, current_player.pk={request.user.pk}")
            return Response({'error': 'خطای پایگاه داده هنگام ایجاد بازی رخ داد.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e_main:
            print(
                f"DEBUG: Unexpected error in NewGameView for user {request.user.username}: {type(e_main).__name__} - {str(e_main)}")
            return Response({'error': 'خطای داخلی سرور هنگام پردازش درخواست شما رخ داد.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class JoinGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(game_id=game_id, status='pending')
            if game.player1 == request.user:
                return Response({'error': 'نمی‌توانید به بازی خودتان بپیوندید'}, status=status.HTTP_400_BAD_REQUEST)

            player2_id_str = str(request.user.id)
            with transaction.atomic():
                game.player2 = request.user
                game.status = 'active'
                game.save()

                state = GameState.objects.get(game=game)
                state.current_player = random.choice([game.player1, game.player2])
                state.last_turn_time = timezone.now()


                if not isinstance(state.revealed_letters, dict):
                    state.revealed_letters = {}
                state.revealed_letters[player2_id_str] = []

                if not isinstance(state.hints_used, dict):
                    state.hints_used = {}
                state.hints_used[player2_id_str] = [1]

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
                return Response({'error': 'شما اجازه دسترسی به این بازی را ندارید.'},
                                status=status.HTTP_403_FORBIDDEN)
            state = GameState.objects.get(game=game)
            if state.current_player != request.user:
                return Response({'error': 'الان نوبت شما نیست.'}, status=status.HTTP_400_BAD_REQUEST)

            letter = request.data.get('letter', '').upper()
            position = request.data.get('position')
            if not letter or position is None:
                return Response({'error': 'لطفاً یک حرف و موقعیت آن را وارد کنید.'},
                                status=status.HTTP_400_BAD_REQUEST)

            word_obj = state.word
            word_text = word_obj.text.upper()
            if not re.match(r'^[A-Z]$', letter):
                return Response({'error': 'حرف باید یک کاراکتر از A تا Z باشد.'}, status=status.HTTP_400_BAD_REQUEST)  #

            try:
                position = int(position)
            except ValueError:
                return Response({'error': 'موقعیت باید یک عدد صحیح باشد.'}, status=status.HTTP_400_BAD_REQUEST)

            if not (0 <= position < len(word_text)):
                return Response({'error': 'موقعیت واردشده معتبر نیست.'}, status=status.HTTP_400_BAD_REQUEST)  #

            with transaction.atomic():
                if not isinstance(state.guessed_letters, list):
                    state.guessed_letters = []

                guess = {'letter': letter, 'correct': letter == word_text[position], 'position': position}
                state.guessed_letters.append(guess)

                current_player_score_field = 'player1_score' if request.user == game.player1 else 'player2_score'

                if guess['correct']:
                    setattr(state, current_player_score_field, getattr(state, current_player_score_field) + 20)
                    request.user.coins += 1
                    request.user.save()
                else:
                    setattr(state, current_player_score_field, getattr(state, current_player_score_field) - 20)

                state.current_player = game.player2 if request.user == game.player1 else game.player1
                state.last_turn_time = timezone.now()
                state.save()
                correct_positions = {g['position'] for g in state.guessed_letters if g['correct']}
                if len(correct_positions) == len(word_text):
                    return self.end_game(game, state)

                serializer = GameStateSerializer(state)
                return Response(serializer.data)
        except Game.DoesNotExist:
            return Response({'error': 'این بازی وجود ندارد.'}, status=status.HTTP_404_NOT_FOUND)
        except GameState.DoesNotExist:
            return Response({'error': 'وضعیت بازی یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)
        except Word.DoesNotExist:
            return Response({'error': 'کلمه بازی یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

    def end_game(self, game, state):  #
        game.status = 'finished'
        with transaction.atomic():
            player1_final_score = state.player1_score
            player2_final_score = state.player2_score
            winner_determined = False
            if player1_final_score > player2_final_score:
                game.winner = game.player1
                game.player1.xp += 50
                game.player1.save()
                GameHistory.objects.create(game=game, player=game.player1, opponent=game.player2, level=game.level,result='won')
                GameHistory.objects.create(game=game, player=game.player2, opponent=game.player1, level=game.level,result='lost')
                winner_determined = True
            elif player2_final_score > player1_final_score:
                game.winner = game.player2
                game.player2.xp += 50
                game.player2.save()
                GameHistory.objects.create(game=game, player=game.player2, opponent=game.player1, level=game.level,result='won')
                GameHistory.objects.create(game=game, player=game.player1, opponent=game.player2, level=game.level,result='lost')
                winner_determined = True

            if not winner_determined:
                GameHistory.objects.create(game=game, player=game.player1, opponent=game.player2, level=game.level,result='draw')
                GameHistory.objects.create(game=game, player=game.player2, opponent=game.player1, level=game.level,result='draw')
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
                state.last_turn_time = timezone.now()
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
                state.last_turn_time = timezone.now()
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