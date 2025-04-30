from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password, ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers
import random
from .models import Profile, Game, Word, GameHistory
from .serializers import UserSerializer, ProfileSerializer, GameSerializer, GameHistorySerializer

# Create your views here.

class UserRegisterView(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        errors = {}
        username = request.data['username']
        password = request.data['password']
        email = request.data['email']
        password2 = request.data['password2']
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        if not username:
            errors['username'] = ['Username is required']
        if not email:
            errors['email'] = ['Email is required']
        if User.objects.filter(email=email).exists():
            errors['email'] = ['Email already exists']
        if not password:
            errors['password'] = ['Password is required']
        if not password2:
            errors['password2'] = ['Password is required']

        if password and password2 and password != password2:
            errors.setdefault('password', []).append("Passwords do not match.")

        if password:
            try:
                validate_password(password)
            except DjangoValidationError as e:
                errors.setdefault('password', []).append(str(e))
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username,first_name=first_name,last_name=last_name, email=email)
                user.set_password(password)
                user.save()

                if not hasattr(user, 'profile'):
                    Profile.objects.create(user=user)

        except Exception as e:
            return Response({"error": f"An error occurred during registration: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        output_serializer = self.get_serializer(user)
        data = {
            'id': output_serializer.data['id'],
            'username': output_serializer.data['username'],
            'email': output_serializer.data['email'],
            'first_name': output_serializer.data['first_name'],
            'last_name': output_serializer.data['last_name'],
        }
        return Response(data, status=status.HTTP_201_CREATED)


class UserProfileViewSet(generics.RetrieveAPIView):
    queryset =Profile.objects.select_related('user').all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
class UserGameHistoryView(generics.ListAPIView):
    serializer_class = GameHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user=self.request.user
        return GameHistorySerializer.objects.filter(user=user).select_related('game','game__player_1',
                                                                              "game__player_2",'user').order_by('-completion_date')

class LeaderBoardView(generics.ListAPIView):
    queryset = Profile.objects.select_related("user").order_by("-total_score")[:10]
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]


class GameViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Game.objects.all().select_related(
            'player_1',  # FK to User
            'player_2',  # FK to User (nullable)
            'word',  # FK to Word
            'current_turn',  # FK to User (nullable)
            'winner',  # FK to User (nullable)
            'player_1__profile',  # Profile of player 1 for score updates
            'player_2__profile'  # Profile of player 2 for score updates
        )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(status="waiting",player_2__isnull=True)
        response_data = []
        for game in queryset:
            player1_username = game.player_1.username if game.player_1 else None
            response_data.append({
                "id": game.id,
                "player_1_username": player1_username,
                "difficulty": game.difficulty,
                # Example of getting display value if needed
                "difficulty_display": game.get_difficulty_display(),
                "status": game.status,
            })
        return Response(response_data)
    def create(self, request, *args, **kwargs):
        difficulty = request.data['difficulty']
        if not difficulty or difficulty not in [choice[0] for choice in Word.DIFFICULTY_CHOICES]:
            return Response({"difficulty": difficulty}, status=status.HTTP_400_BAD_REQUEST)
        user = self.request.user
        possible_words = Word.objects.filter(difficulty=difficulty)
        if not possible_words.exists():
            return Response(
                {"difficulty": [f"No words found for difficulty '{difficulty}'."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        word = random.choice(possible_words)
        try:
            game = Game.objects.create(
                word=word,
                difficulty=difficulty,
                player_1=user,
                status="waiting",
            )
            # Note: game.initialize_game() is called later when player 2 joins
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer=GameSerializer(game,context={'request': request})
        # Use the helper method to filter output for a detail-like view
        filtered_data = self._filter_game_output_data(serializer.data, detail_view=True, game_obj=game)
        return Response(filtered_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        game = Game.objects.get(pk=kwargs['pk'])

        if request.user==game.player_1 or request.user==game.player_2:
            serializer = GameSerializer(game, context={'request': request})
            filtered_data = self._filter_game_output_data(serializer.data, detail_view=True, game_obj=game)
            return Response(filtered_data, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "You are not allowed to see this game!"},)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def join(self, request, *args, **kwargs):
        game = Game.objects.get(pk=kwargs['pk'])

        if game.status != "waiting" and game.player_2 is not None:
            return Response({'detail':'this game is not ready to joined'},)
        if request.user==game.player_1:
            return Response({'detail':'you can not join to own game'})

        if Game.objects.filter(status__in=['waiting', 'active'], player_1=request.user).exclude(pk=game.pk).exists() or \
                Game.objects.filter(status__in=['waiting', 'active'], player_2=request.user).exclude(pk=game.pk).exists():
            return Response({"detail": "You are already in an active game."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            game.player_2 = request.user
            game.status = "active"
            game.initialize_game()
            game.save()
        except Exception as e:
            return Response({"error": f"Could not join game: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = GameSerializer(game, context={'request': request})
        filtered_data = self._filter_game_output_data(serializer.data, detail_view=True, game_obj=game)
        return Response(filtered_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def guess(self,request,pk):
        letter_data = request.data.get('guessed_letters')
        game = get_object_or_404(self.get_queryset(), pk=pk)
        user = request.user

        if not letter_data  :
            return Response({"detail": "Letter Not Provide."},status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(letter_data, str) or len(letter_data) != 1 or not letter_data.isalpha():
            return Response({"letter": ["Please provide a single alphabetical character."]},
                            status=status.HTTP_400_BAD_REQUEST)
        letter = letter_data.lower()

        if game.status != 'active':
            return Response({"detail": "Game is not active."},status=status.HTTP_400_BAD_REQUEST)
        if user != game.current_turn:
            return Response({"detail":"not your turn."},status=status.HTTP_400_BAD_REQUEST)

        if game.get_remaining_time() <= 0:
            self._end_game_due_to_timeout(game)  # End the game
            serializer = GameSerializer(game, context={'request': request})  # Get updated state
            filtered_data = self._filter_game_output_data(serializer.data, detail_view=True, game_obj=game)
            return Response(
                {"detail": "Time is up!", "game_state": filtered_data},
                status=status.HTTP_400_BAD_REQUEST  # Bad request because action cannot be performed
            )
        if letter in game.guessed_letters:
            return Response({"detail": f"Letter{letter} already guessed."},status=status.HTTP_400_BAD_REQUEST)
        try:
            word_text = game.word.text.lower()  # Normalize word to lowercase
            correct_guess = letter in word_text
            # Points based on project description (adjust if needed)
            points_correct = 20
            points_incorrect = -20  # Or -10 if preferred
            score_change = points_correct if correct_guess else points_incorrect

            game.guessed_letters += letter  # Add to guessed letters regardless of correctness

            all_letters_guessed = False
            if correct_guess:
                # Update display word only on correct guess
                new_display = "".join([c if c in game.guessed_letters else "_" for c in word_text])
                game.current_display_word = new_display
                # Check if all letters are now revealed
                all_letters_guessed = "_" not in new_display
            # else: display_word remains unchanged

            # Update player score
            if user == game.player_1:
                game.player1_score += score_change
            elif user == game.player_2:  # Ensure player_2 exists
                game.player2_score += score_change

            # Switch turn (only if game is not over yet)
            game_ended = False
            winner = None
            if correct_guess and all_letters_guessed:
                # Current user wins by completing the word
                winner = user
                self._end_game(game, winner=winner, is_draw=False)
                game_ended = True
            else:
                # Switch turn to the other player
                if game.player_2:  # Ensure there is a player 2
                    game.current_turn = game.player_2 if user == game.player_1 else game.player_1
                # If no player 2 (shouldn't happen in 'active' state, but safe check)
                # or if game ended, current_turn might be set to None in _end_game
            game.last_active_time = timezone.now()
            game.save()  # Save all changes to the game state

        except Exception as e:
            return Response({"error": f"An error occurred during guess processing: {e}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        serializer = GameSerializer(game, context={'request': request})
        game_state_data = self._filter_game_output_data(serializer.data, detail_view=True, game_obj=game)

        response_detail = "Guess processed."
        if game_ended:
            win_message = "You guessed the word and won!" if winner == user else f"{winner.username} guessed the word and won!"
            response_detail = f"Game Over! {win_message}"
        elif correct_guess:
            response_detail = f"Correct guess: '{letter}'!"
        else:
            response_detail = f"Incorrect guess: '{letter}'."

        response_data = {
            "detail": response_detail,
            "correct": correct_guess,
            "game_state": game_state_data
        }
        return Response(response_data, status=status.HTTP_200_OK)

        # Add these helper methods inside the GameViewSet class (indented)
# Add these helper methods inside the GameViewSet class (indented)
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def pause(self,request,pk=None):
        game = get_object_or_404(self.get_queryset(), pk=pk)
        user = request.user
        if game.status!='active':
            return Response({"detail":"Game is not active."},status=status.HTTP_400_BAD_REQUEST)
        if user!=game.player_1 and user!=game.player_2:
            return Response({"detail":"Not your turn."},status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        elapsed_since_last_active = (now - game.last_active_time).total_seconds()
        game.time_elapsed_before_pause += elapsed_since_last_active
        game.status = 'paused'

        game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data, status=status.HTTP_200_OK)
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def resume(self,request,pk=None):
        game = get_object_or_404(self.get_queryset(), pk=pk)
        user = request.user
        if game.status !="paused":
            return Response({"detail":"Game is not paused"},status=status.HTTP_400_BAD_REQUEST)
        if game.player_1!=user or game.player_2!=user:
            return Response({"detail":"Not your turn."},status=status.HTTP_400_BAD_REQUEST)
        game.status='active'
        game.last_active_time = timezone.now()
        game.save()

        serializer = self.get_serializer(game)
        return Response(serializer.data)



    def _filter_game_output_data(self, data, detail_view=False, game_obj=None):
        """
        Helper method to filter the output of the generic GameSerializer
        based on the context (list vs detail).
        Removes sensitive or unnecessary fields.
        """
        # Always remove fields used only for input or internal linking/sensitive data
        fields_to_remove = ['letter', 'difficulty', 'word']

        if not detail_view:
            # Fields to remove for list view (show only minimal info)
            fields_to_remove.extend([
                'player_1', 'player_2', # Full player objects removed
                'word_details', 'guessed_letters', 'current_turn', 'current_turn_username',
                'player1_score', 'player2_score', 'start_time',
                'time_limit_seconds', 'remaining_time', 'winner', 'winner_username', 'is_draw'
            ])
            # Note: We already manually constructed list view data,
            # but this shows how filtering *could* be done if using serializer for list.
        else:
            # Fields to remove/adjust for detail view
            if not data.get('player_1'): fields_to_remove.append('player_1')
            if not data.get('player_2'): fields_to_remove.append('player_2')
            if not data.get('winner'): fields_to_remove.append('winner')
            if not data.get('current_turn'): fields_to_remove.append('current_turn')

            # Optionally, simplify player/winner/turn representation to just usernames
            # We'll add simple username fields and remove the full objects
            if game_obj and game_obj.player_1: data['player_1_username'] = game_obj.player_1.username
            if game_obj and game_obj.player_2: data['player_2_username'] = game_obj.player_2.username
            # (winner_username and current_turn_username are already sourced in the serializer)

            # Remove the potentially large nested user objects if just username is sufficient
            fields_to_remove.extend(['player_1', 'player_2', 'winner', 'current_turn'])


        # Perform the removal
        for field in fields_to_remove:
            data.pop(field, None) # Use pop with default None to avoid KeyError

        # Add any other conditional filtering based on game state if needed
        # Example: if game status is finished, maybe set remaining_time to 0 or null

        return data

    def _end_game(self, game, winner, is_draw):
        """
        Handles the logic for ending a game: updating status,
        creating history records, and updating player profiles.
        Uses transaction.atomic for consistency.
        """
        # Prevent ending a game multiple times
        if game.status == 'finished':
            return

        try:
            with transaction.atomic():
                # Update game status
                game.status = 'finished'
                game.winner = winner
                game.is_draw = is_draw
                game.current_turn = None # No more turns
                # Consider adding an end_time field to the Game model
                # game.end_time = timezone.now()
                game.save()

                # Create history records and update total scores
                players_data = [(game.player_1, game.player1_score), (game.player_2, game.player2_score)]
                for player, score in players_data:
                    if player: # Ensure player exists (for player_2)
                        # Determine result for this player
                        if is_draw:
                            result = 'draw'
                        elif player == winner:
                            result = 'win'
                        else:
                            result = 'loss'

                        # Create GameHistory entry
                        GameHistory.objects.create(
                            user=player,
                            game=game,
                            score_in_game=score,
                            result=result,
                            difficulty=game.difficulty, # Store game difficulty
                            completion_date=timezone.now()
                        )

                        # Update player's total score in their profile
                        # Use get_or_create for safety, though profile should exist
                        profile, created = Profile.objects.get_or_create(user=player)
                        # Ensure total_score doesn't go below zero if score is negative? (optional rule)
                        profile.total_score = max(0, profile.total_score + score)
                        profile.save()
        except Exception as e:
            # Log the error appropriately in a real application
            print(f"Error ending game {game.id}: {e}")
            # Consider how to handle partial failures if the transaction fails

    def _end_game_due_to_timeout(self, game):
        """
        Ends the game specifically because time ran out.
        Determines winner based on scores at timeout.
        """
         # Prevent ending a game multiple times
        if game.status == 'finished':
            return

        winner = None
        is_draw = False
        # Determine winner based on score comparison
        # Ensure player_2 exists before comparing scores if game might somehow timeout before p2 joins
        if game.player_2:
            if game.player1_score > game.player2_score:
                winner = game.player_1
            elif game.player2_score > game.player1_score:
                winner = game.player_2
            else:
                is_draw = True # Scores are equal
        else:
            # If timeout happens in 'waiting' state (unlikely but possible)
            # Or handle single player mode differently here if implemented
             winner = None # Or maybe player 1 wins by default? Define rules.
             is_draw = False # Or True?

        self._end_game(game, winner=winner, is_draw=is_draw)