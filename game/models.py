from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    total_score = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username+"-"+str(self.total_score)


class Word(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    text = models.CharField(max_length=50)
    difficulty = models.CharField(max_length=50,choices=DIFFICULTY_CHOICES)

    def __str__(self):
        return self.text
STATUS_CHOICES = [
    ('waiting', 'Waiting'),
    ('active', 'Active'),
    ('paused', 'Paused'),
    ('finished', 'Finished'),]
class Game(models.Model):
    word = models.ForeignKey(Word,on_delete=models.CASCADE)
    difficulty = models.CharField(max_length=10,choices=Word.DIFFICULTY_CHOICES)
    player_1 = models.ForeignKey(User,on_delete=models.CASCADE)
    player_2 = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    time_limit = models.PositiveIntegerField(default=0)
    start_game = models.DateTimeField(auto_now_add=True)
    end_game = models.DateTimeField(null=True,blank=True)
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    status = models.CharField(max_length=50,choices=STATUS_CHOICES)

RESULT_CHOICES = [
    ('win', 'برد'),
    ('loss', 'باخت'),
    ('draw', 'مساوی'),
]
class GameHistory(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,)
    game = models.ForeignKey(Game,on_delete=models.CASCADE,)
    final_score = models.IntegerField()
    result = models.CharField(max_length=5,choices=RESULT_CHOICES,)
    completion_date = models.DateTimeField(default=timezone.now,)
    difficulty = models.CharField(max_length=10,choices=Word.DIFFICULTY_CHOICES,)

    def __str__(self):
        return f"تاریخچه: {self.user.username} - بازی {self.game_id} ({self.get_result_display()})"
