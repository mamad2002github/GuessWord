from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
# Create your models here.

class Profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - Score: {self.total_score}"


class Word(models.Model):

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    text = models.CharField(max_length=50, unique=True,)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES,)

    def __str__(self):
        return f"{self.text} ({self.get_difficulty_display()})"


class Game(models.Model):

    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('finished', 'Finished'),
    ]

    word = models.ForeignKey(Word, on_delete=models.PROTECT, related_name='games',)
    player_1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games_as_player1',)
    player_2 = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='games_as_player2', )
    current_display_word = models.CharField(max_length=50, default="", blank=True, )
    guessed_letters = models.CharField(max_length=50, default="", blank=True,)
    current_turn = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='games_turn', )
    player1_score = models.IntegerField(default=0,)
    player2_score = models.IntegerField(default=0, )
    time_limit_seconds = models.PositiveIntegerField(default=600, )
    start_time = models.DateTimeField(auto_now_add=True, )
    last_active_time = models.DateTimeField(default=timezone.now,)
    time_elapsed_before_pause = models.PositiveIntegerField(default=0,)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting',)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='games_won', )
    is_draw = models.BooleanField(default=False,)

    def initialize_game(self):
        self.current_display_word = "_" * len(self.word.text)
        if self.word.difficulty == 'easy':
            self.time_limit_seconds = 10 * 60
        elif self.word.difficulty == 'medium':
            self.time_limit_seconds = 7 * 60
        else: # hard
            self.time_limit_seconds = 5 * 60
        self.guessed_letters = ""

        self.current_turn = self.player_1
        self.start_time = timezone.now()
        self.last_active_time = self.start_time
        self.status = 'active' if self.player_2 else 'waiting'
        self.save()

    def get_remaining_time(self):
        if self.status != 'active':
            return self.time_limit_seconds - self.time_elapsed_before_pause

        now = timezone.now()
        current_elapsed = (now - self.last_active_time).total_seconds()
        total_elapsed = self.time_elapsed_before_pause + current_elapsed
        remaining = self.time_limit_seconds - total_elapsed
        return max(0, int(remaining))

    def __str__(self):
        player2_username = self.player_2.username if self.player_2 else "Waiting..."
        return f"Game {self.id}: {self.player_1.username} vs {player2_username} ({self.get_status_display()})"


class GameHistory(models.Model):

    RESULT_CHOICES = [
        ('win', 'Win'),
        ('loss', 'Loss'),
        ('draw', 'Draw'),
        ('incomplete', 'Incomplete'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_history',)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='history_entries', )
    score_in_game = models.IntegerField()
    result = models.CharField(max_length=10, choices=RESULT_CHOICES,)
    completion_date = models.DateTimeField(default=timezone.now,)

    def __str__(self):
        return f"History: {self.user.username} - Game {self.game.id} - Result: {self.get_result_display()}"

    class Meta:
        verbose_name_plural = "Game Histories"
        ordering = ['-completion_date']


# --- سیگنال‌ها (اختیاری اما مفید) ---
# می‌توانید سیگنال‌هایی بنویسید که:
# 1. هنگام ایجاد کاربر، پروفایل او را بسازد.
# 2. هنگام پایان یافتن بازی (status='finished')، دو رکورد GameHistory (یکی برای هر بازیکن) ایجاد کند
#    و امتیاز کلی (total_score) پروفایل بازیکنان را آپدیت کند.

# مثال سیگنال برای ساخت پروفایل (در signals.py یا انتهای models.py)


    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()