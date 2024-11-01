from aiogram import Dispatcher, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (Message, CallbackQuery,
                           InlineKeyboardMarkup, InlineKeyboardButton)

from bot.validators import phone_number_validator

from bot.db import save_user_info_to_db, save_user_language, get_main_menu

from bot.models import Course, CustomUser

from bot.keyboards import get_languages

from bot.states import UserRegistrationState

from bot.utils import default_languages, introduction_template
from django.conf import settings
from aiogram.client.default import DefaultBotProperties
from asgiref.sync import sync_to_async

from aiogram.enums import ParseMode

dp = Dispatcher()
bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@dp.message(CommandStart())
async def welcome(message: Message):
    user_id = message.from_user.id

    user = await CustomUser.objects.filter(telegram_id=user_id).afirst()

    if user and user.user_lang:
        await message.answer(
            caption=introduction_template[user.user_lang],
            reply_markup=await get_main_menu(user.user_lang)
        )
    else:
        msg = default_languages['welcome_message']
        await message.answer(msg, reply_markup=get_languages())


@dp.callback_query(lambda call: call.data.startswith("lang"))
async def get_query_languages(call: CallbackQuery):
    user_id = call.from_user.id
    user_lang = call.data.split("_")[1]

    await save_user_language(user_id, user_lang)

    await bot.answer_callback_query(call.id)
    await call.message.answer("Quyidagi kurslardan birini tanlang:", reply_markup=await get_main_menu(user_lang))


@dp.callback_query(lambda c: c.data.startswith("course_"))
async def course_detail(callback_query: CallbackQuery):
    course_id = int(callback_query.data.split("_")[1])
    course = Course.objects.get(id=course_id)

    caption_text = (
        f"<b>{course.title}</b>\n\n"
        f"{course.description}\n\n"
        f"Narx: {course.price} so'm\n"
        f"Davomiyligi: {course.course_duration}"
    )

    await callback_query.message.answer_photo(
        photo=settings.MEDIA_URL + course.image.url,
        caption=caption_text,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Yozilish", callback_data=f"enroll_{course.id}")
        )
    )
    await bot.answer_callback_query(callback_query.id)


@dp.callback_query(F.data.startswith("enroll_"))
async def enroll_in_course(callback_query: CallbackQuery, state: FSMContext):
    course_id = int(callback_query.data.split("_")[1])
    await state.update_data(course_id=course_id)  # Kurs IDni saqlaymiz

    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Iltimos, ismingizni kiriting.")
    await state.set_state(UserRegistrationState.full_name)  # Holatni "full_name" ga o'zgartiramiz


@dp.message(UserRegistrationState.full_name)
async def get_full_name(message: Message, state: FSMContext):
    full_name = message.text
    await state.update_data(full_name=full_name)  # Ismni holatga saqlaymiz

    await message.answer("Endi telefon raqamingizni quyidagi shaklda kiriting: +998 (XX) XXX XX XX")
    await state.set_state(UserRegistrationState.contact_info)  # Holatni "contact_info" ga o'zgartiramiz


@dp.message(UserRegistrationState.contact_info)
async def get_contact_info(message: Message, state: FSMContext):
    contact = message.text

    if not phone_number_validator.match(contact):
        await message.answer("Telefon raqamingiz noto'g'ri formatda. Iltimos, +998 (XX) XXX XX XX shaklida kiriting.")
        return  # Noto'g'ri formatda bo'lsa, qayta so'raymiz

    await state.update_data(contact=contact)  # To'g'ri formatda saqlaymiz

    # Tasdiqlovchi xabar va holatni tozalash
    await message.answer("Rahmat! Siz bilan operatorlarimiz tez orada bog'lanadi.")
    await save_user_info_to_db(state, message.from_user.id, message.from_user.username)  # Ma'lumotni bazaga saqlaymiz
    await state.clear()  # Holatni tozalaymiz
