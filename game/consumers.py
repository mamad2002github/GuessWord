# GUESS/game/consumers.py
import random
import re

from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.utils import timezone
from asgiref.sync import sync_to_async
from .models import Game, GameState, GameHistory, User, Word
from .serializers import GameSerializer, GameStateSerializer
from django.db import transaction

get_game_object = sync_to_async(Game.objects.get)
get_game_state_object = sync_to_async(GameState.objects.get)
get_word_text = sync_to_async(lambda word_obj: word_obj.text.upper())
save_game = sync_to_async(lambda obj: obj.save())
save_state = sync_to_async(lambda obj: obj.save())
save_user = sync_to_async(lambda obj: obj.save())
create_game_history = sync_to_async(GameHistory.objects.create)
get_user_by_id = sync_to_async(User.objects.get)


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'game_{self.game_id}'
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        try:
            game = await get_game_object(game_id=self.game_id)
            if game.status == 'finished':
                await self.send_error_message("این بازی قبلاً تمام شده است.")
                await self.close()
                return

            if game.status == 'pending' or self.user == game.player1 or self.user == game.player2:
                await self.channel_layer.group_add(self.game_group_name, self.channel_name)
                await self.accept()
                state = await get_game_state_object(game=game)
                await self.send_game_update(game, state, "game_joined_or_reconnected")
            else:
                await self.send_error_message("شما اجازه دسترسی به این بازی را ندارید.")
                await self.close()
        except Game.DoesNotExist:
            await self.send_error_message("بازی یافت نشد.")
            await self.close()
        except GameState.DoesNotExist:
            await self.send_error_message("وضعیت بازی یافت نشد.")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        try:
            game = await get_game_object(game_id=self.game_id)
            state = await get_game_state_object(game=game)

            if game.status == 'finished':
                await self.send_error_message("بازی تمام شده است.")
                return

            if action not in ['join_game'] and self.user not in [game.player1, game.player2]:
                await self.send_error_message("شما اجازه انجام این عمل را ندارید.")
                return

            if action == 'join_game':
                await self.handle_join_game(game, state, data)
            elif action == 'guess_letter':
                await self.handle_guess_letter(game, state, data)
            elif action == 'guess_word':
                await self.handle_guess_word(game, state, data)
            elif action == 'request_hint':
                await self.handle_request_hint(game, state, data)
            elif action == 'reveal_letter':
                await self.handle_reveal_letter(game, state, data)
            elif action == 'pause_game':
                await self.handle_pause_game(game, state, data)
            elif action == 'resume_game':
                await self.handle_resume_game(game, state, data)
            elif action == 'check_timeout':  # این اکشن برای مدیریت توسط سرور یا کلاینت است
                await self.handle_check_timeout(game, state)
            else:
                await self.send_error_message(f"اکشن '{action}' نامعتبر است.")

        except Game.DoesNotExist:
            await self.send_error_message('بازی یافت نشد.')
        except GameState.DoesNotExist:
            await self.send_error_message('وضعیت بازی یافت نشد.')
        except Word.DoesNotExist:  # اگر کلمه به نحوی از state حذف شده باشد
            await self.send_error_message('کلمه بازی یافت نشد.')
        except User.DoesNotExist:  # اگر کاربری در state به نحوی نامعتبر باشد
            await self.send_error_message('کاربر یافت نشد.')
        except Exception as e:
            print(f"Error in GameConsumer: {type(e).__name__} - {e}")
            await self.send_error_message('خطایی در سرور رخ داد.')

    async def handle_join_game(self, game, state, data):
        if game.status == 'pending' and self.user != game.player1 and not game.player2:
            player2_id_str = str(self.user.id)
            async with transaction.atomic():
                game.player2 = self.user
                game.status = 'active'

                state.current_player = random.choice([game.player1, game.player2])
                state.last_turn_time = timezone.now()

                # مقداردهی اولیه سازگار با سایر بخش‌ها
                if not isinstance(state.revealed_letters, dict): state.revealed_letters = {}
                state.revealed_letters[player2_id_str] = []  # لیست اندیس‌ها

                if not isinstance(state.hints_used, dict): state.hints_used = {}
                state.hints_used[player2_id_str] = []  # برای عدالت، بازیکن دوم هم با لیست خالی شروع می‌کند

                await save_game(game)
                await save_state(state)

            await self.send_game_update_to_group(game, state, "player_joined")
        elif game.player2 == self.user or game.player1 == self.user:
            await self.send_game_update(game, state, "reconnected_to_game")
        else:
            await self.send_error_message("نمی‌توانید به این بازی بپیوندید.")

    async def handle_guess_letter(self, game, state, data):
        if state.current_player != self.user:
            await self.send_error_message("الان نوبت شما نیست.")
            return

        letter = data.get('letter', '').upper()
        position_str = data.get('position')

        if not letter or position_str is None:
            await self.send_error_message("حرف یا موقعیت ارسال نشده است.")
            return
        try:
            position = int(position_str)
        except ValueError:
            await self.send_error_message("موقعیت باید عدد صحیح باشد.")
            return

        word_obj = state.word
        word_text = await get_word_text(word_obj)

        if not (0 <= position < len(word_text)):
            await self.send_error_message("موقعیت نامعتبر است.")
            return
        if not re.match(r'^[A-Zآ-ی]$', letter):  # پشتیبانی از حروف فارسی اگر کلمات فارسی هستند
            await self.send_error_message("حرف نامعتبر است. (فقط حروف الفبا)")
            return

        async with transaction.atomic():
            if not isinstance(state.guessed_letters, list): state.guessed_letters = []

            is_correct = (letter == word_text[position])
            # جلوگیری از حدس تکراری برای یک خانه (اختیاری اما مفید)
            for guess_info in state.guessed_letters:
                if guess_info['position'] == position and guess_info['player_id'] == self.user.id:
                    # میتوانید اجازه دهید دوباره حدس بزند یا خطا دهید
                    # await self.send_error_message("شما قبلاً این خانه را حدس زده‌اید.")
                    # return
                    pass  # فعلا اجازه تکرار میدهیم، امتیاز هم طبق روال کم یا زیاد میشود

            state.guessed_letters.append(
                {'letter': letter, 'position': position, 'correct': is_correct, 'player_id': self.user.id})

            score_change = 20 if is_correct else -20
            if self.user == game.player1:
                state.player1_score += score_change
            else:
                state.player2_score += score_change

            if is_correct:
                self.user.coins += 1
                await save_user(self.user)

            state.current_player = game.player2 if self.user == game.player1 else game.player1
            state.last_turn_time = timezone.now()
            await save_state(state)

        # بررسی اتمام بازی
        # حروف صحیح حدس زده شده (بدون تکرار موقعیت)
        correctly_guessed_indices = {g['position'] for g in state.guessed_letters if g['correct']}
        if len(correctly_guessed_indices) == len(word_text):
            await self.end_game(game, state, reason="all_letters_guessed")
        else:
            await self.send_game_update_to_group(game, state, "letter_guessed")

    async def handle_guess_word(self, game, state, data):
        if state.current_player != self.user:
            await self.send_error_message("الان نوبت شما نیست.")
            return

        guessed_word = data.get('word', '').upper()
        actual_word_obj = state.word
        actual_word_text = await get_word_text(actual_word_obj)

        winner = None
        # loser = None # این متغیر استفاده نشده بود

        if guessed_word == actual_word_text:
            winner = self.user
            # loser = game.player1 if self.user == game.player2 else game.player2
            # اعمال امتیاز برای حدس کلمه صحیح
            if self.user == game.player1:
                state.player1_score += 100  # امتیاز برای حدس کلمه صحیح
            else:
                state.player2_score += 100
        else:  # حدس کلمه غلط بود
            winner = game.player1 if self.user == game.player2 else game.player2  # بازیکن دیگر برنده می‌شود
            # loser = self.user
            # اعمال امتیاز منفی برای حدس کلمه غلط (اختیاری)
            # یا اعمال امتیاز مثبت برای بازیکنی که از اشتباه حریف سود برده
            if self.user == game.player1:  # بازیکن ۱ اشتباه حدس زد
                state.player2_score += 50  # امتیاز به بازیکن ۲
                # state.player1_score -= 50 # جریمه بازیکن ۱
            else:  # بازیکن ۲ اشتباه حدس زد
                state.player1_score += 50  # امتیاز به بازیکن ۱
                # state.player2_score -= 50 # جریمه بازیکن ۲

        await self.end_game(game, state, reason="word_guessed", game_winner=winner)

    async def handle_request_hint(self, game, state, data):
        player_id_str = str(self.user.id)
        if self.user.coins < 1:  # هزینه راهنمایی
            await self.send_error_message("سکه کافی برای راهنمایی ندارید.")
            return

        if not isinstance(state.hints_used, dict): state.hints_used = {}
        player_hints_used_numbers = state.hints_used.get(player_id_str, [])

        next_hint_number = len(player_hints_used_numbers) + 1

        if next_hint_number > 3:  # با فرض داشتن hint1, hint2, hint3 در مدل Word
            await self.send_error_message("شما از تمام راهنمایی‌ها استفاده کرده‌اید.")
            return

        word_obj = state.word
        hint_to_provide = None
        if next_hint_number == 1:
            hint_to_provide = word_obj.hint1
        elif next_hint_number == 2:
            hint_to_provide = word_obj.hint2
        elif next_hint_number == 3:
            hint_to_provide = word_obj.hint3

        if hint_to_provide:
            async with transaction.atomic():
                self.user.coins -= 1  # کسر هزینه راهنمایی
                await save_user(self.user)

                player_hints_used_numbers.append(next_hint_number)
                state.hints_used[player_id_str] = player_hints_used_numbers
                # گرفتن راهنمایی نباید نوبت را عوض کند یا زمان را ریست کند
                await save_state(state)

            await self.send_personal_message(
                {'type': 'hint_provided', 'hint': hint_to_provide, 'coins': self.user.coins})
            # ارسال آپدیت به گروه برای نمایش تغییر سکه
            await self.send_game_update_to_group(game, state, "hint_taken_update")
        else:
            await self.send_error_message("راهنمایی بیشتری موجود نیست یا خطایی رخ داده.")

    async def handle_reveal_letter(self, game, state, data):
        player_id_str = str(self.user.id)
        if self.user.coins < 1:  # هزینه نمایش حرف
            await self.send_error_message("سکه کافی برای نمایش حرف ندارید.")
            return

        word_obj = state.word
        word_text = await get_word_text(word_obj)

        if not isinstance(state.revealed_letters, dict): state.revealed_letters = {}
        player_revealed_indices = state.revealed_letters.get(player_id_str, [])

        # حروف قبلاً به درستی حدس زده شده توسط هر دو بازیکن (اندیس‌ها)
        correctly_guessed_indices = {g['position'] for g in state.guessed_letters if g['correct']}

        # اندیس‌های قابل نمایش: آنهایی که نه قبلاً به این بازیکن نمایش داده شده‌اند و نه به طور عمومی حدس زده شده‌اند
        unrevealed_target_indices = [
            i for i in range(len(word_text))
            if i not in player_revealed_indices and i not in correctly_guessed_indices
        ]

        if not unrevealed_target_indices:
            await self.send_error_message("حرف دیگری برای نمایش وجود ندارد.")
            return

        position_to_reveal = random.choice(unrevealed_target_indices)
        letter_to_reveal = word_text[position_to_reveal]

        async with transaction.atomic():
            self.user.coins -= 1  # کسر هزینه
            await save_user(self.user)

            player_revealed_indices.append(position_to_reveal)
            state.revealed_letters[player_id_str] = player_revealed_indices
            # نمایش حرف نباید نوبت را عوض کند یا زمان را ریست کند
            await save_state(state)

        await self.send_personal_message({
            'type': 'letter_revealed',
            'letter': letter_to_reveal,
            'position': position_to_reveal,
            'coins': self.user.coins
        })
        # ارسال آپدیت به گروه برای نمایش تغییر سکه و احتمالاً وضعیت جدید حروف آشکار شده (اگر کلاینت آن را نمایش دهد)
        await self.send_game_update_to_group(game, state, "letter_revealed_update")

    async def handle_pause_game(self, game, state, data):
        if not game.player2:  # بازی تک نفره در انتظار را نمیتوان متوقف کرد
            await self.send_error_message("بازی هنوز بازیکن دوم ندارد و نمی‌توان متوقف کرد.")
            return
        if game.status == 'active':
            async with transaction.atomic():
                game.status = 'paused'
                state.paused_at = timezone.now()
                # زمان باقیمانده بازیکن فعلی از نوبتش باید ذخیره شود اگر تایمر نوبت وجود دارد
                if state.current_player and state.last_turn_time:
                    time_elapsed_on_turn = (timezone.now() - state.last_turn_time).total_seconds()
                    # این بخش نیاز به یک فیلد جدید در GameState دارد مثلاً: remaining_turn_time
                    # state.remaining_turn_time_on_pause = TURN_TIMEOUT_SECONDS - time_elapsed_on_turn
                await save_game(game)
                await save_state(state)
            await self.send_game_update_to_group(game, state, "game_paused")
        else:
            await self.send_error_message(f"بازی در وضعیت {game.status} است و نمی‌توان متوقف کرد.")

    async def handle_resume_game(self, game, state, data):
        if game.status == 'paused':
            async with transaction.atomic():
                game.status = 'active'
                if state.paused_at:
                    pause_duration = timezone.now() - state.paused_at
                    if state.last_turn_time:  # اگر بازی قبلا شروع شده و last_turn_time دارد
                        state.last_turn_time += pause_duration  # به زمان آخرین نوبت، مدت توقف را اضافه کن
                    else:  # اگر بازی بلافاصله پس از ایجاد و قبل از اولین حرکت متوقف شده باشد
                        state.last_turn_time = timezone.now()
                else:  # اگر paused_at به نحوی None بود، زمان را به حال حاضر تنظیم کن
                    state.last_turn_time = timezone.now()

                state.paused_at = None
                # اگر remaining_turn_time_on_pause ذخیره شده بود، اینجا باید تایمر نوبت را بر اساس آن تنظیم کرد
                await save_game(game)
                await save_state(state)
            await self.send_game_update_to_group(game, state, "game_resumed")
        else:
            await self.send_error_message(f"بازی در وضعیت {game.status} است و نمی‌توان ادامه داد.")

    async def handle_check_timeout(self, game, state):
        if game.status != 'active':
            return

        now = timezone.now()
        turn_timeout_seconds = 30  # زمان مجاز برای هر نوبت، این مقدار باید قابل تنظیم باشد
        player_timed_out_this_check = False

        # 1. بررسی تایم‌اوت نوبت بازیکن فعلی
        if state.current_player and state.last_turn_time:
            time_since_last_turn = (now - state.last_turn_time).total_seconds()
            if time_since_last_turn > turn_timeout_seconds:
                async with transaction.atomic():
                    # جریمه بازیکن فعلی برای تایم اوت نوبت (اختیاری)
                    # if state.current_player == game.player1:
                    #     state.player1_score -= 5 # جریمه کوچک
                    # else:
                    #     state.player2_score -= 5

                    # تغییر نوبت
                    state.current_player = game.player2 if state.current_player == game.player1 else game.player1
                    state.last_turn_time = now
                    await save_state(state)
                    player_timed_out_this_check = True

        # 2. آپدیت زمان کلی باقیمانده بازیکنان (اگر این منطق فعال است)
        # این بخش باید با دقت پیاده‌سازی شود. اگر هر بازیکن یک زمان کلی برای تمام حرکاتش دارد.
        # در مدل فعلی، player1_time و player2_time در GameState وجود دارد.
        # این زمان باید در هر تغییر نوبت یا به صورت دوره‌ای کم شود.
        # اگر player_timed_out_this_check সত্য হয়, زمان بازیکن قبلی از last_turn_time تا now محاسبه و کم میشود.
        # اگر player_timed_out_this_check نادرست باشد، زمان بازیکن فعلی از last_turn_time تا now محاسبه و کم میشود.
        # این بخش برای سادگی فعلا دقیق پیاده‌سازی نشده و به `end_game` بر اساس اتمام زمان کلی موکول شده.

        # 3. بررسی اتمام بازی به دلیل اتمام زمان کلی یکی از بازیکنان
        # فرض میکنیم playerX_time در هر تغییر نوبت یا با یک مکانیزم دیگر آپدیت میشود
        if state.player1_time is not None and state.player1_time <= 0:
            await self.end_game(game, state, reason="player_time_up", game_winner=game.player2)
            return
        if state.player2_time is not None and state.player2_time <= 0:
            await self.end_game(game, state, reason="player_time_up", game_winner=game.player1)
            return

        if player_timed_out_this_check:
            await self.send_game_update_to_group(game, state, "turn_timeout_occurred")

    async def end_game(self, game, state, reason="unknown", game_winner=None):
        if game.status == 'finished':
            return

        async with transaction.atomic():
            original_winner_before_score_adjustment = game_winner

            game.status = 'finished'

            # تعیین برنده بر اساس امتیازها اگر از قبل (مثلا با حدس کلمه) مشخص نشده
            if not game_winner:
                if state.player1_score > state.player2_score:
                    game_winner = game.player1
                elif state.player2_score > state.player1_score:
                    game_winner = game.player2
                # اگر امتیازها مساوی بود، game_winner None می‌ماند (تساوی)

            # اگر دلیل، اتمام زمان یک بازیکن بود و هنوز برنده با امتیاز مشخص نشده یا نیاز به تایید دارد
            if reason == "player_time_up":
                # game_winner قبلا در handle_check_timeout یا جای دیگر بر اساس اتمام زمان مشخص شده
                if state.player1_time is not None and state.player1_time <= 0 and (
                        state.player2_time is None or state.player2_time > 0):
                    game_winner = game.player2
                    if original_winner_before_score_adjustment != game.player2:  # اگر حدس کلمه توسط P1 باعث برد P1 شده بود ولی زمانش تمام شد
                        state.player2_score += state.player2_time // 10 if state.player2_time else 0  # امتیاز زمان به P2
                elif state.player2_time is not None and state.player2_time <= 0 and (
                        state.player1_time is None or state.player1_time > 0):
                    game_winner = game.player1
                    if original_winner_before_score_adjustment != game.player1:
                        state.player1_score += state.player1_time // 10 if state.player1_time else 0  # امتیاز زمان به P1

            game.winner = game_winner

            # اعطای XP و ثبت تاریخچه
            result_player1 = 'draw'
            result_player2 = 'draw'

            if game.winner:
                winner_obj_db = await get_user_by_id(id=game.winner.id)  # برای اطمینان از آبجکت به‌روز
                winner_obj_db.xp += 50  # XP ثابت برای برد
                await save_user(winner_obj_db)
                if game.winner == game.player1:
                    result_player1 = 'won'
                    result_player2 = 'lost'
                else:
                    result_player1 = 'lost'
                    result_player2 = 'won'

            # اطمینان از وجود بازیکنان قبل از ایجاد تاریخچه
            if game.player1:
                await create_game_history(game=game, player=game.player1, opponent=game.player2, level=game.level,
                                          result=result_player1, final_score=state.player1_score)
            if game.player2:  # player2 ممکن است None باشد اگر بازی هرگز شروع نشده باشد
                await create_game_history(game=game, player=game.player2, opponent=game.player1, level=game.level,
                                          result=result_player2, final_score=state.player2_score)

            await save_game(game)
            await save_state(state)  # ذخیره آخرین امتیازها

        await self.send_game_update_to_group(game, state, "game_ended", additional_data={'reason': reason,
                                                                                         'winner_id': game.winner.id if game.winner else None})

    # Helper methods
    async def send_game_update_to_group(self, game, state, event_type, additional_data=None):
        game_data = GameSerializer(game).data
        state_data = GameStateSerializer(state).data
        message = {
            'type': 'game_update',  # این type برای فراخوانی متد game_update در همین کلاس است
            'payload': {
                'event': event_type,
                'game': game_data,
                'state': state_data,
            }
        }
        if additional_data:
            message['payload'].update(additional_data)
        await self.channel_layer.group_send(self.game_group_name, message)

    async def send_game_update(self, game, state, event_type, additional_data=None):
        game_data = GameSerializer(game).data
        state_data = GameStateSerializer(state).data
        payload = {
            'event': event_type,
            'game': game_data,
            'state': state_data,
        }
        if additional_data:
            payload.update(additional_data)
        await self.send(text_data=json.dumps(payload))

    async def send_error_message(self, error_text):
        await self.send(text_data=json.dumps({'type': 'error', 'message': error_text}))  # اضافه کردن type

    async def send_personal_message(self, data_dict):
        # اطمینان از وجود type برای تفکیک در کلاینت
        if 'type' not in data_dict:
            data_dict['type'] = 'personal_update'  # یک نوع پیشفرض
        await self.send(text_data=json.dumps(data_dict))

    async def game_update(self, event):
        await self.send(text_data=json.dumps(event['payload']))