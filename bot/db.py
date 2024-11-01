from bot.models import CustomUser, Course
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async
from aiogram.fsm.context import FSMContext
from django.db import IntegrityError


@sync_to_async
def sync_save_user_language(user_id, user_lang):
    try:
        user, created = CustomUser.objects.get_or_create(
            telegram_id=user_id,
            defaults={'user_lang': user_lang}
        )

        if not created:  # Agar foydalanuvchi mavjud bo'lsa
            if user.user_lang != user_lang:  # Agar til o'zgargan bo'lsa
                user.user_lang = user_lang
                user.save()  # Bu yerda xatolik yuz berishi mumkin

    except IntegrityError as e:
        print(f"IntegrityError: {e}")  # Xatolik haqida ma'lumot chiqarish


async def save_user_language(user_id, user_lang):
    await sync_save_user_language(user_id, user_lang)


@sync_to_async
def save_user_info_to_db(user_data):
    try:
        new_user, created = CustomUser.objects.update_or_create(
            telegram_id=user_data['telegram_id'],
            defaults={
                "full_name": user_data['full_name'],
                "phone_number": user_data['phone_number'],
                "tg_username": user_data['tg_username'],
                "username": user_data['username']
            }
        )
        return new_user
    except IntegrityError:
        raise Exception("User already exists")


async def get_courses(user_lang):
    field_name = f"title_{user_lang}"
    return await sync_to_async(list)(Course.objects.filter(**{field_name + '__isnull': False}))


async def get_main_menu(user_lang):
    courses = await get_courses(user_lang)

    if not courses:
        print("Kurslar topilmadi!")
        return None

    inline_keyboard = []
    for course in courses:
        course_title = getattr(course, f"title_{user_lang}")
        inline_keyboard.append([InlineKeyboardButton(text=course_title, callback_data=f"course_{course.id}")])

    inline_kb = InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=2)

    return inline_kb


@sync_to_async
def save_user_course_enrollment(user_id, course_id):
    user = CustomUser.objects.filter(telegram_id=user_id).first()
    if user:
        user.course_id = course_id
        user.save()
    else:
        raise ValueError("Foydalanuvchi topilmadi yoki kursga qo'shib bo'lmadi.")
