from django.urls import path
from .views import (
    LoginView, SignupView, ProfileView, GameHistoryView, NewGameView, JoinGameView,
    GameStateView, GuessView, HintView, RevealLetterView, PauseGameView, ResumeGameView,
    GuessWordView, PendingGamesView, PausedGamesView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('game-history/', GameHistoryView.as_view(), name='game_history'),
    path('new-game/', NewGameView.as_view(), name='new_game'),
    path('join-game/<uuid:game_id>/', JoinGameView.as_view(), name='join_game'),
    path('game/<uuid:game_id>/state/', GameStateView.as_view(), name='game_state'),
    path('game/<uuid:game_id>/guess/', GuessView.as_view(), name='guess'),
    path('game/<uuid:game_id>/hint/', HintView.as_view(), name='hint'),
    path('game/<uuid:game_id>/reveal-letter/', RevealLetterView.as_view(), name='reveal_letter'),
    path('game/<uuid:game_id>/pause/', PauseGameView.as_view(), name='pause_game'),
    path('game/<uuid:game_id>/resume/', ResumeGameView.as_view(), name='resume_game'),
    path('game/<uuid:game_id>/guess-word/', GuessWordView.as_view(), name='guess_word'),
    path('pending-games/', PendingGamesView.as_view(), name='pending_games'),
    path('paused-games/', PausedGamesView.as_view(), name='paused_games'),
]