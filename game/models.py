import uuid
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    xp = models.PositiveIntegerField(default=0)
    coins = models.PositiveIntegerField(default=0)

    @property
    def level(self):
        if self.xp < 400:
            return 1
        elif self.xp < 800:
            return 2
        elif self.xp < 1500:
            return 3
        elif self.xp < 2500:
            return 4
        else:
            return 5

    def __str__(self):
        return self.username

class Word(models.Model):
    LEVEL_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    text = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    hint1 = models.CharField(max_length=100)
    hint2 = models.CharField(max_length=100)
    hint3 = models.CharField(max_length=100)

    def __str__(self):
        return self.text

class Game(models.Model):
    STATUS_GAME = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('finished', 'Finished'),
    )
    LEVEL_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_player1')
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_player2', null=True, blank=True)
    game_id = models.UUIDField(unique=True, editable=False)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_GAME, default='pending')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_games')

    def __str__(self):
        return f"Game {self.game_id} ({self.level})"

class GameHistory(models.Model):
    RESULT_GAME = (
        ('win', 'Win'),
        ('lose', 'Lose'),
        ('draw', 'Draw'),
    )
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='game_history')
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_player')
    opponent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opponent_game')
    level = models.CharField(max_length=10, choices=Game.LEVEL_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=10, choices=RESULT_GAME, default='draw')

    def __str__(self):
        return f"{self.player.username} vs {self.opponent.username} ({self.result})"

class GameState(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='game_state')
    current_player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='current_player', null=True, blank=True)
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='game_word')
    guessed_letters = models.JSONField(default=dict)
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    player1_time = models.IntegerField()
    player2_time = models.IntegerField()
    revealed_letters = models.JSONField(default=dict)
    hints_used = models.JSONField(default=dict)
    last_turn_time = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"State for Game {self.game.game_id}"