from bot.models import CustomUser
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from asgiref.sync import sync_to_async
from aiogram.fsm.context import FSMContext


@sync_to_async
def sync_save_user_language(user_id, user_lang):
    user, created = CustomUser.objects.get_or_create(
        telegram_id=user_id,
        defaults={'user_lang': user_lang}
    )

    if not created and user.user_lang != user_lang:
        user.user_lang = user_lang
        user.save()


async def save_user_language(user_id, user_lang):
    await sync_save_user_language(user_id, user_lang)


@sync_to_async
def save_user_info_to_db(state: FSMContext, telegram_id: int, username: str):
    state_data = state.proxy()
    CustomUser.objects.update_or_create(
        telegram_id=telegram_id,
        defaults={
            "full_name": state_data.get("full_name"),
            "phone_number": state_data.get("contact"),
            "tg_username": f"https://t.me/{username}",
        }
    )


async def get_courses(user_lang):
    return await sync_to_async(Course.objects.filter)(user_lang=user_lang)


async def get_main_menu(user_lang):
    courses = await get_courses(user_lang)
    inline_kb = InlineKeyboardMarkup()
    for course in courses:
        inline_kb.add(InlineKeyboardButton(text=course.title, callback_data=str(course.id)))
    return inline_kb
