from rest_framework import serializers
from .models import User, Game, GameState, GameHistory, Word
import re

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'error': 'کاربری با این نام کاربری پیدا نشد.'})
        if len(username) < 4:
            raise serializers.ValidationError({'error': 'نام کاربری باید حداقل ۴ کاراکتر باشد.'})
        if len(password) < 6:
            raise serializers.ValidationError({'error': 'رمز عبور باید حداقل ۶ کاراکتر باشد.'})
        return data

class UserSerializer(serializers.ModelSerializer):
    level = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'xp', 'coins', 'level']
        extra_kwargs = {
            'username': {'read_only': True},
        }

    def validate_xp(self, value):
        if value < 0:
            raise serializers.ValidationError({'error': 'مقدار XP نمی‌تواند منفی باشد.'})
        return value

    def validate_coins(self, value):
        if value < 0:
            raise serializers.ValidationError({'error': 'تعداد سکه‌ها نمی‌تواند منفی باشد.'})
        return value

    def validate_first_name(self, value):
        if value and not re.match(r'^[a-zA-Zآ-ی\s]+$', value):
            raise serializers.ValidationError({'error': 'نام فقط باید شامل حروف فارسی یا انگلیسی باشد.'})
        return value

    def validate_last_name(self, value):
        if value and not re.match(r'^[a-zA-Zآ-ی\s]+$', value):
            raise serializers.ValidationError({'error': 'نام خانوادگی فقط باید شامل حروف فارسی یا انگلیسی باشد.'})
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
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'error': 'رمز عبور و تأیید آن باید یکسان باشند.'})
        if len(data['password']) < 6:
            raise serializers.ValidationError({'error': 'رمز عبور باید حداقل ۶ کاراکتر باشد.'})
        return data

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError({'error': 'این نام کاربری قبلاً استفاده شده است.'})
        if len(value) < 4:
            raise serializers.ValidationError({'error': 'نام کاربری باید حداقل ۴ کاراکتر باشد.'})
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', value):
            raise serializers.ValidationError({'error': 'نام کاربری باید با حرف شروع شود و فقط شامل حروف و اعداد باشد.'})
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
            raise serializers.ValidationError({'error': 'سطح بازی باید یکی از موارد ساده، متوسط یا سخت باشد.'})
        return value

    def validate_status(self, value):
        valid_statuses = ['pending', 'active', 'paused', 'finished']
        if value not in valid_statuses:
            raise serializers.ValidationError({'error': 'وضعیت بازی باید یکی از موارد در انتظار، فعال، متوقف یا پایان‌یافته باشد.'})
        return value

    def validate(self, data):
        request = self.context.get('request')
        if request and 'player1' in data and data['player1'] != request.user:
            raise serializers.ValidationError({'error': 'بازیکن اول باید خود شما باشید.'})
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
        for guess in obj.guessed_letters:
            if guess['correct']:
                result[guess['position']] = guess['letter']
        # نمایش حروف نمایش‌داده‌شده
        for letter, info in obj.revealed_letters.items():
            result[info['position']] = letter
        return ' '.join(result)  # مثلاً "_ A _ E" برای "CAKE"

    def get_current_player(self, obj):
        return obj.current_player.username if obj.current_player else None

    def validate_hints_used(self, value):
        for user_id, hints in value.items():
            if not all(hint in [1, 2, 3] for hint in hints):
                raise serializers.ValidationError({'error': 'شماره نکات باید ۱، ۲ یا ۳ باشد.'})
        return value

    def validate_guessed_letters(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError({'error': 'حروف حدس‌زده‌شده باید به‌صورت لیست باشند.'})
        for guess in value:
            if not re.match(r'^[A-Z]$', guess['letter']):
                raise serializers.ValidationError({'error': 'حروف حدس‌زده‌شده باید یک حرف از A تا Z باشند.'})
            if 'correct' not in guess or 'position' not in guess:
                raise serializers.ValidationError({'error': 'اطلاعات حدس باید شامل وضعیت و موقعیت باشد.'})
        return value

    def validate_player1_score(self, value):
        if value < 0:
            raise serializers.ValidationError({'error': 'امتیاز بازیکن اول نمی‌تواند منفی باشد.'})
        return value

    def validate_player2_score(self, value):
        if value < 0:
            raise serializers.ValidationError({'error': 'امتیاز بازیکن دوم نمی‌تواند منفی باشد.'})
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
        valid_results = ['won', 'lost', 'draw']  # هماهنگ با views.py
        if value not in valid_results:
            raise serializers.ValidationError({'error': 'نتیجه بازی باید یکی از موارد برنده، بازنده یا تساوی باشد.'})
        return value

    def validate_level(self, value):
        valid_levels = ['easy', 'medium', 'hard']
        if value not in valid_levels:
            raise serializers.ValidationError({'error': 'سطح بازی باید یکی از موارد ساده، متوسط یا سخت باشد.'})
        return value

    def validate(self, data):
        if 'player' in data and 'opponent' in data and data['opponent'] and data['player'] == data['opponent']:
            raise serializers.ValidationError({'error': 'بازیکن و حریف نمی‌توانند یک نفر باشند.'})
        return data

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret['date']:
            ret['date'] = instance.date.strftime('%d-%m-%Y')
        return ret