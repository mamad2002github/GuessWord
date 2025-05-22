from rest_framework import serializers
from .models import User, Game, GameState, GameHistory, Word
import re

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        # چک کردن وجود کاربر
        if not User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'کاربری با این نام وجود ندارد.'})

        # ولیدیشن طول username و password
        if len(username) < 4:
            raise serializers.ValidationError({'username': 'نام کاربری باید حداقل ۴ حرف باشد.'})
        if len(password) < 6:
            raise serializers.ValidationError({'password': 'رمز عبور باید حداقل ۶ حرف باشد.'})

        return data

class UserSerializer(serializers.ModelSerializer):
    level = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'xp', 'coins', 'level']
        extra_kwargs = {
            'username': {'read_only': True},  # برای جلوگیری از تغییر username
        }

    def validate_xp(self, value):
        if value < 0:
            raise serializers.ValidationError('XP نمی‌تواند منفی باشد.')
        return value

    def validate_coins(self, value):
        if value < 0:
            raise serializers.ValidationError('سکه نمی‌تواند منفی باشد.')
        return value

    def validate_first_name(self, value):
        if value and not re.match(r'^[a-zA-Zآ-ی\s]+$', value):
            raise serializers.ValidationError('نام فقط می‌تواند شامل حروف باشد.')
        return value

    def validate_last_name(self, value):
        if value and not re.match(r'^[a-zA-Zآ-ی\s]+$', value):
            raise serializers.ValidationError('نام خانوادگی فقط می‌تواند شامل حروف باشد.')
        return value

class SignupSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate(self, data):
        # چک کردن برابری رمزها
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'رمزها باید برابر باشند.'})

        # ولیدیشن طول password
        if len(data['password']) < 6:
            raise serializers.ValidationError({'password': 'رمز عبور باید حداقل ۶ حرف باشد.'})

        return data

    def validate_username(self, value):
        # چک کردن یکتایی username
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('این نام کاربری قبلاً استفاده شده است.')
        # چک کردن طول و فرمت username
        if len(value) < 4:
            raise serializers.ValidationError('نام کاربری باید حداقل ۴ حرف باشد.')
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', value):
            raise serializers.ValidationError('نام کاربری باید با حرف شروع شود و فقط شامل حروف و اعداد باشد.')
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            xp=0,
            coins=0
        )
        return user

class GameSerializer(serializers.ModelSerializer):
    player1 = serializers.SerializerMethodField()
    player2 = serializers.SerializerMethodField()
    winner = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['game_id', 'player1', 'player2', 'level', 'status', 'winner', 'created_at']
        extra_kwargs = {
            'game_id': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def get_player1(self, obj):
        return obj.player1.username if obj.player1 else None

    def get_player2(self, obj):
        return obj.player2.username if obj.player2 else None

    def get_winner(self, obj):
        return obj.winner.username if obj.winner else None

    def validate_level(self, value):
        valid_levels = ['easy', 'medium', 'hard']
        if value not in valid_levels:
            raise serializers.ValidationError('سطح باید یکی از این موارد باشد: easy, medium, hard')
        return value

    def validate_status(self, value):
        valid_statuses = ['pending', 'active', 'paused', 'finished']
        if value not in valid_statuses:
            raise serializers.ValidationError('وضعیت باید یکی از این موارد باشد: pending, active, paused, finished')
        return value

    def validate(self, data):
        # اطمینان از اینکه player1 کاربر فعلی است
        request = self.context.get('request')
        if request and 'player1' in data and data['player1'] != request.user:
            raise serializers.ValidationError({'player1': 'بازیکن اول باید کاربر فعلی باشد.'})
        return data

class GameStateSerializer(serializers.ModelSerializer):
    word = serializers.SerializerMethodField()
    current_player = serializers.SerializerMethodField()

    class Meta:
        model = GameState
        fields = [
            'game', 'word', 'guessed_letters', 'revealed_letters', 'hints_used',
            'player1_score', 'player2_score', 'player1_time', 'player2_time',
            'current_player', 'paused_at', 'last_turn_time'
        ]
        extra_kwargs = {
            'game': {'read_only': True},
        }

    def get_word(self, obj):
        word = obj.word.text
        result = ['_'] * len(word)
        # نمایش حروف درست حدس‌زده‌شده
        for letter, info in obj.guessed_letters.items():
            if info['correct']:
                result[info['position']] = letter
        # نمایش حروف نمایش‌داده‌شده
        for letter, info in obj.revealed_letters.items():
            result[info['position']] = letter
        return ' '.join(result)  # مثلاً "_ A _ E" برای "cake"

    def get_current_player(self, obj):
        return obj.current_player.username if obj.current_player else None

    def validate_hints_used(self, value):
        for user_id, hints in value.items():
            if not all(hint in [1, 2, 3] for hint in hints):
                raise serializers.ValidationError('نکات باید ۱، ۲ یا ۳ باشند.')
        return value

    def validate_guessed_letters(self, value):
        for letter, info in value.items():
            if not re.match(r'^[A-Z]$', letter):
                raise serializers.ValidationError('حروف حدس‌زده‌شده باید تک‌حرف A-Z باشند.')
            if 'correct' not in info or 'position' not in info:
                raise serializers.ValidationError('اطلاعات حدس باید شامل correct و position باشد.')
        return value

    def validate_player1_score(self, value):
        if value < 0:
            raise serializers.ValidationError('امتیاز بازیکن اول نمی‌تواند منفی باشد.')
        return value

    def validate_player2_score(self, value):
        if value < 0:
            raise serializers.ValidationError('امتیاز بازیکن دوم نمی‌تواند منفی باشد.')
        return value

class GameHistorySerializer(serializers.ModelSerializer):
    player = serializers.SerializerMethodField()
    opponent = serializers.SerializerMethodField()

    class Meta:
        model = GameHistory
        fields = ['game', 'player', 'opponent', 'level', 'result', 'date']
        extra_kwargs = {
            'game': {'read_only': True},
            'date': {'read_only': True},
        }

    def get_player(self, obj):
        return obj.player.username

    def get_opponent(self, obj):
        return obj.opponent.username if obj.opponent else None

    def validate_result(self, value):
        valid_results = ['win', 'lose', 'draw']
        if value not in valid_results:
            raise serializers.ValidationError('نتیجه باید win، lose یا draw باشد.')
        return value

    def validate_level(self, value):
        valid_levels = ['easy', 'medium', 'hard']
        if value not in valid_levels:
            raise serializers.ValidationError('سطح باید یکی از این موارد باشد: easy, medium, hard')
        return value

    def validate(self, data):
        if 'player' in data and 'opponent' in data and data['opponent'] and data['player'] == data['opponent']:
            raise serializers.ValidationError('بازیکن و حریف نمی‌توانند یکسان باشند.')
        return data

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret['date']:
            ret['date'] = instance.date.strftime('%d-%m-%Y')
        return ret