from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Game, Word, GameHistory
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=False, label="Confirm Password")
    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'password2', 'is_staff', 'is_active', 'date_joined']
        read_only_fields = ['id', 'is_staff', 'is_active', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True},
            'password2': {'write_only': True},
        }

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'total_score']
        read_only_fields = ['id', 'user']


class GameSerializer(serializers.ModelSerializer):
    player_1 = UserSerializer(read_only=True, required=False)
    player_2 = UserSerializer(read_only=True, required=False, allow_null=True)
    word_details = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    remaining_time = serializers.SerializerMethodField(read_only=True)
    current_turn_username = serializers.CharField(source='current_turn.username', read_only=True, allow_null=True)
    winner_username = serializers.CharField(source='winner.username', read_only=True, allow_null=True)
    difficulty = serializers.ChoiceField(choices=Word.DIFFICULTY_CHOICES, required=False, write_only=True)
    letter = serializers.CharField(max_length=1, required=False, write_only=True)

    class Meta:
        model = Game
        fields = [
            'id', 'player_1', 'player_2', 'word', 'difficulty', 'difficulty_display',
            'current_display_word', 'guessed_letters', 'current_turn', 'current_turn_username',
            'player1_score', 'player2_score', 'start_time', 'time_limit_seconds', 'remaining_time',
            'status', 'status_display', 'winner', 'winner_username', 'is_draw',
            'word_details',
            'letter',
        ]
        read_only_fields = ['id', 'word', 'start_time', 'status', 'winner', 'is_draw',
                          'current_display_word', 'guessed_letters', 'current_turn',
                          'player1_score', 'player2_score']
        extra_kwargs = {
             'word': {'write_only': False}
        }


    def get_word_details(self, obj):
        if obj.word:
            return {'id': obj.word.id, 'difficulty': obj.word.difficulty}
        return None

    def get_remaining_time(self, obj):
        return obj.get_remaining_time()


class GameHistorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    game_id = serializers.IntegerField(source='game.id', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    result_display = serializers.CharField(source='get_result_display', read_only=True)
    opponent_username = serializers.SerializerMethodField()

    class Meta:
        model = GameHistory
        fields = ['id', 'user', 'game_id', 'score_in_game', 'result', 'result_display',
                  'completion_date', 'difficulty', 'difficulty_display', 'opponent_username']
        read_only_fields = ['id', 'user', 'game_id', 'completion_date']

    def get_opponent_username(self, obj):
        game = obj.game
        user = obj.user
        if game.player_1_id == user.id and game.player_2:
            return game.player_2.username
        elif game.player_2_id == user.id:
            return game.player_1.username
        return "No Opponent / N/A"