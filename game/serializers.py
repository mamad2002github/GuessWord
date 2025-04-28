from rest_framework import serializers
from .models import *

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model= Profile
        fields = '__all__'
class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model= Game
        fields = '__all__'
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model= User
        fields = '__all__'
class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model= Word
        fields = '__all__'
class GameHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model= GameHistory
        fields = '__all__'
