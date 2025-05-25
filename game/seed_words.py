import os
import sys
import django

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GUESS.settings')  # 'yourproject' رو با اسم پروژه‌ات عوض کن
django.setup()

from django.db import transaction
from game.models import Word

@transaction.atomic
def seed_words():
    words = [
        # سطح ساده (easy) - 4-5 حرفی
        {'text': 'cake', 'level': 'easy', 'hint1': 'یه دسر شیرین', 'hint2': 'توی جشن‌ها سرو می‌شه', 'hint3': 'معمولاً خامه داره'},
        {'text': 'book', 'level': 'easy', 'hint1': 'می‌خونیش', 'hint2': 'صفحه داره', 'hint3': 'توی کتابخونه پیدا می‌شه'},
        {'text': 'tree', 'level': 'easy', 'hint1': 'بلند رشد می‌کنه', 'hint2': 'برگ داره', 'hint3': 'سایه می‌ده'},
        {'text': 'fish', 'level': 'easy', 'hint1': 'توی آب زندگی می‌کنه', 'hint2': 'شنا می‌کنه', 'hint3': 'باله داره'},
        {'text': 'star', 'level': 'easy', 'hint1': 'شب می‌درخشه', 'hint2': 'توی آسمونه', 'hint3': 'چشمک می‌زنه'},
        {'text': 'bird', 'level': 'easy', 'hint1': 'بال داره', 'hint2': 'پرواز می‌کنه', 'hint3': 'آواز می‌خونه'},
        {'text': 'moon', 'level': 'easy', 'hint1': 'شب دیده می‌شه', 'hint2': 'دور زمین می‌چرخه', 'hint3': 'دهانه داره'},
        {'text': 'ship', 'level': 'easy', 'hint1': 'روی آب حرکت می‌کنه', 'hint2': 'بار حمل می‌کنه', 'hint3': 'کاپیتان داره'},
        {'text': 'ring', 'level': 'easy', 'hint1': 'توی انگشت می‌ندازی', 'hint2': 'گرد و حلقه‌ست', 'hint3': 'معمولاً براقه'},
        {'text': 'desk', 'level': 'easy', 'hint1': 'برای درس خوندن', 'hint2': 'کشو داره', 'hint3': 'توی کلاسه'},
        # سطح متوسط (medium) - 6 حرفی
        {'text': 'puzzle', 'level': 'medium', 'hint1': 'یه بازی فکری', 'hint2': 'قطعه‌قطعه‌ست', 'hint3': 'باید حلش کنی'},
        {'text': 'guitar', 'level': 'medium', 'hint1': 'یه ساز موسیقی', 'hint2': 'سیم داره', 'hint3': 'با انگشت نواخته می‌شه'},
        {'text': 'window', 'level': 'medium', 'hint1': 'نور می‌ده', 'hint2': 'شیشه‌ایه', 'hint3': 'می‌تونی بازش کنی'},
        {'text': 'bridge', 'level': 'medium', 'hint1': 'از رودخونه رد می‌شه', 'hint2': 'دو طرف رو وصل می‌کنه', 'hint3': 'ماشین روش می‌ره'},
        {'text': 'camera', 'level': 'medium', 'hint1': 'عکس می‌گیره', 'hint2': 'لنز داره', 'hint3': 'خاطره ثبت می‌کنه'},
        {'text': 'forest', 'level': 'medium', 'hint1': 'پر از درخته', 'hint2': 'حیات وحش داره', 'hint3': 'سبز و پرپشته'},
        {'text': 'market', 'level': 'medium', 'hint1': 'محل خرید', 'hint2': 'غذا می‌فروشن', 'hint3': 'معمولاً شلوغه'},
        {'text': 'rocket', 'level': 'medium', 'hint1': 'به فضا می‌ره', 'hint2': 'بالا پرتاب می‌شه', 'hint3': 'فضانوردا استفاده می‌کنن'},
        {'text': 'pencil', 'level': 'medium', 'hint1': 'برای نوشتن', 'hint2': 'پاک‌کن داره', 'hint3': 'چوبیه'},
        {'text': 'singer', 'level': 'medium', 'hint1': 'آهنگ اجرا می‌کنه', 'hint2': 'با صداش', 'hint3': 'روی صحنه‌ست'},
        # سطح پیشرفته (hard) - 8+ حرفی
        {'text': 'strawberry', 'level': 'hard', 'hint1': 'یه میوه قرمز', 'hint2': 'دونه‌های ریز داره', 'hint3': 'شیرین و آبداره'},
        {'text': 'television', 'level': 'hard', 'hint1': 'برنامه نشون می‌ده', 'hint2': 'صفحه داره', 'hint3': 'توی پذیراییه'},
        {'text': 'butterfly', 'level': 'hard', 'hint1': 'بال‌های رنگارنگ داره', 'hint2': 'با نرمی پرواز می‌کنه', 'hint3': 'از پیله میاد'},
        {'text': 'pineapple', 'level': 'hard', 'hint1': 'میوه گرمسیریه', 'hint2': 'بیرونش تیغ‌تیغه', 'hint3': 'زرد و شیرینه'},
        {'text': 'microscope', 'level': 'hard', 'hint1': 'توی علم استفاده می‌شه', 'hint2': 'چیزای ریز رو بزرگ می‌کنه', 'hint3': 'برای چیزای کوچیکه'},
        {'text': 'helicopter', 'level': 'hard', 'hint1': 'با پره پرواز می‌کنه', 'hint2': 'توی هوا معلقه', 'hint3': 'برای نجات استفاده می‌شه'},
        {'text': 'newspaper', 'level': 'hard', 'hint1': 'اخبار روز', 'hint2': 'روی کاغذ چاپ می‌شه', 'hint3': 'تیتر داره'},
        {'text': 'telescope', 'level': 'hard', 'hint1': 'ستاره‌ها رو می‌بینی', 'hint2': 'توی نجوم استفاده می‌شه', 'hint3': 'لنز داره'},
        {'text': 'volleyball', 'level': 'hard', 'hint1': 'یه ورزش تیمی', 'hint2': 'با تور بازی می‌شه', 'hint3': 'با دست می‌زنن'},
        {'text': 'flashlight', 'level': 'hard', 'hint1': 'نور می‌ده', 'hint2': 'توی تاریکی استفاده می‌شه', 'hint3': 'باتری داره'},
    ]

    for word_data in words:
        Word.objects.get_or_create(
            text=word_data['text'],
            level=word_data['level'],
            defaults={
                'hint1': word_data['hint1'],
                'hint2': word_data['hint2'],
                'hint3': word_data['hint3']
            }
        )

if __name__ == "__main__":
    seed_words()