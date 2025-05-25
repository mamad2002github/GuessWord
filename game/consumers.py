import random
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.utils import timezone
from .models import Game, GameState, GameHistory
from .serializers import GameSerializer, GameStateSerializer
from django.db import transaction
import asyncio
from django.db.models import Q

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'game_{self.game_id}'
        await self.channel_layer.group_add(self.game_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        try:
            game = Game.objects.get(game_id=self.game_id)
            state = GameState.objects.get(game=game)

            if action == 'check_timeout':
                # چک کردن تایم‌اوت نوبت (۳۰ ثانیه)
                if state.current_player == self.scope['user'] and state.last_turn_time:
                    time_elapsed = (timezone.now() - state.last_turn_time).total_seconds()
                    if time_elapsed > 30:  # 30 seconds timeout per turn
                        with transaction.atomic():
                            state.current_player = game.player2 if state.current_player == game.player1 else game.player1
                            state.last_turn_time = timezone.now()
                            state.save()
                            serializer = GameStateSerializer(state)
                            await self.channel_layer.group_send(
                                self.game_group_name,
                                {
                                    'type': 'game_update',
                                    'message': {'state': serializer.data}
                                }
                            )

                # چک کردن زمان کلی بازیکن‌ها
                if state.player1_time <= 0 or state.player2_time <= 0:
                    await self.end_game(game, state)
                    return  # جلوگیری از ادامه محاسبات

                # آپدیت زمان بازیکن فعلی
                if state.current_player == self.scope['user'] and state.player1_time > 0 and state.player2_time > 0:
                    with transaction.atomic():
                        time_elapsed = (timezone.now() - state.last_turn_time).total_seconds()
                        if state.current_player == game.player1 and state.player1_time > 0:
                            state.player1_time = max(0, state.player1_time - int(time_elapsed))
                        elif state.current_player == game.player2 and state.player2_time > 0:
                            state.player2_time = max(0, state.player2_time - int(time_elapsed))
                        state.last_turn_time = timezone.now()
                        state.save()
                        serializer = GameStateSerializer(state)
                        await self.channel_layer.group_send(
                            self.game_group_name,
                            {
                                'type': 'game_update',
                                'message': {'state': serializer.data}
                            }
                        )

            elif action == 'join_game':
                if game.status == 'pending' and self.scope['user'] != game.player1:
                    with transaction.atomic():
                        game.player2 = self.scope['user']
                        game.status = 'active'
                        state.current_player = random.choice([game.player1, game.player2])
                        state.last_turn_time = timezone.now()
                        state.revealed_letters['player2'] = []
                        state.hints_used['player2'] = [1]
                        game.save()
                        state.save()
                        game_serializer = GameSerializer(game)
                        state_serializer = GameStateSerializer(state)
                        await self.channel_layer.group_send(
                            self.game_group_name,
                            {
                                'type': 'game_update',
                                'message': {
                                    'game': game_serializer.data,
                                    'state': state_serializer.data
                                }
                            }
                        )

        except Game.DoesNotExist:
            await self.send(text_data=json.dumps({'error': 'بازی یافت نشد'}))

    async def game_update(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def end_game(self, game, state):
        with transaction.atomic():
            game.status = 'finished'
            if state.player1_time <= 0:
                extra_score = state.player2_time // 10
                state.player2_score += extra_score
            elif state.player2_time <= 0:
                extra_score = state.player1_time // 10
                state.player1_score += extra_score

            if state.player1_score > state.player2_score:
                game.winner = game.player1
                game.player1.xp += 50
                game.player1.save()
                GameHistory.objects.create(game=game, player=game.player1, opponent=game.player2, level=game.level,
                                           result='won')
                GameHistory.objects.create(game=game, player=game.player2, opponent=game.player1, level=game.level,
                                           result='lost')
            elif state.player2_score > state.player1_score:
                game.winner = game.player2
                game.player2.xp += 50
                game.player2.save()
                GameHistory.objects.create(game=game, player=game.player2, opponent=game.player1, level=game.level,
                                           result='won')
                GameHistory.objects.create(game=game, player=game.player1, opponent=game.player2, level=game.level,
                                           result='lost')
            else:
                GameHistory.objects.create(game=game, player=game.player1, opponent=game.player2, level=game.level,
                                           result='draw')
                GameHistory.objects.create(game=game, player=game.player2, opponent=game.player1, level=game.level,
                                           result='draw')
            game.save()
            game_serializer = GameSerializer(game)
            state_serializer = GameStateSerializer(state)
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_update',
                    'message': {
                        'status': 'finished',
                        'game': game_serializer.data,
                        'state': state_serializer.data
                    }
                }
            )