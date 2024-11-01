import aiohttp
import re
from aiogram import Dispatcher, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (Message, CallbackQuery,
                           InlineKeyboardMarkup, InlineKeyboardButton)

from urllib.parse import urljoin

from bot.db import save_user_info_to_db, save_user_language, get_main_menu,save_user_course_enrollment

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
        main_menu_markup = await get_main_menu(user.user_lang)
        await message.answer(
            text=introduction_template[user.user_lang],
            reply_markup=main_menu_markup
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
    main_menu_markup = await get_main_menu(user_lang)
    await call.message.answer("Quyidagi kurslardan birini tanlang \n\n Выберите один из курсов ниже",
                              reply_markup=main_menu_markup)


@dp.callback_query(lambda c: c.data.startswith("course_"))
async def course_detail(callback_query: CallbackQuery):
    course_id = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id

    try:
        user = await sync_to_async(CustomUser.objects.get)(telegram_id=user_id)
        user_language = user.user_lang
    except CustomUser.DoesNotExist:
        user_language = 'uz'

    try:
        course = await sync_to_async(Course.objects.get)(id=course_id)
    except Course.DoesNotExist:
        await callback_query.message.answer("Kurs topilmadi.")
        return

    if user_language == 'ru':
        caption_text = (
            f"<b>{course.title_ru}</b>\n\n"
            f"{course.description_ru}\n\n"
            f"Цена: {course.price} сум\n"
            f"Длительность: {course.course_duration}"
        )
        button_text = "Записаться на курс"
    else:
        caption_text = (
            f"<b>{course.title}</b>\n\n"
            f"{course.description}\n\n"
            f"Narx: {course.price} so'm\n"
            f"Davomiyligi: {course.course_duration}"
        )
        button_text = "Kursga yozilish"

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=button_text, callback_data=f"enroll_{course.id}")]])
    try:
        await callback_query.message.answer(
            text=caption_text,
            reply_markup=inline_kb
        )
    except Exception as e:
        print(f"Error sending message: {e}")
        await callback_query.message.answer("Xatolik yuz berdi")

    await bot.answer_callback_query(callback_query.id)


@dp.callback_query(F.data.startswith("enroll_"))
async def enroll_in_course(callback_query: CallbackQuery, state: FSMContext):
    course_id = int(callback_query.data.split("_")[1])
    await state.update_data(course_id=course_id)
    user_id = callback_query.from_user.id


    await bot.answer_callback_query(callback_query.id)

    try:
        user = await sync_to_async(CustomUser.objects.get)(telegram_id=user_id)
        user_language = user.user_lang
    except CustomUser.DoesNotExist:
        user_language = 'uz'

    if user_language == 'ru':
        ask_text = "Пожалуйста, введите свое имя."
    else:
        ask_text = "Iltimos, ismingizni kiriting."

    await save_user_course_enrollment(user_id, course_id)

    await callback_query.message.answer(ask_text)
    await state.set_state(UserRegistrationState.full_name)


@dp.message(UserRegistrationState.full_name)
async def get_full_name(message: Message, state: FSMContext):
    full_name = message.text
    await state.update_data(full_name=full_name)
    user_id = message.from_user.id


    try:
        user = await sync_to_async(CustomUser.objects.get)(telegram_id=user_id)
        user_language = user.user_lang
    except CustomUser.DoesNotExist:
        user_language = 'uz'

    if user_language == 'ru':
        ask_text = (
            "Теперь введите свой номер телефона в форму ниже: \n\n"
            "+998 (XX) XXX XX XX"
        )
    else:
        ask_text = (
            "Endi telefon raqamingizni quyidagi shaklda kiriting: \n\n"
            "+998 (XX) XXX XX XX"
        )

    await message.answer(ask_text)
    await state.set_state(UserRegistrationState.contact_info)


phone_number_validator = re.compile(r'^\+998 \(\d{2}\) \d{3} \d{2} \d{2}$')


@dp.message(UserRegistrationState.contact_info)
async def get_contact_info(message: Message, state: FSMContext):
    user_id = message.from_user.id

    contact = message.text
    state_data = await state.get_data()

    try:
        user = await sync_to_async(CustomUser.objects.get)(telegram_id=user_id)
        user_language = user.user_lang
    except CustomUser.DoesNotExist:
        user_language = 'uz'

    if not phone_number_validator.search(contact):
        if user_language == 'ru':
            await message.answer("Ваш номер телефона указан в неправильном формате. Пожалуйста, \n\n"
                                 "+998 (XX) XXX XX XX введите в форме.")
        else:  # O'zbek tili
            await message.answer("Telefon raqamingiz noto'g'ri formatda. Iltimos, \n\n"
                                 "+998 (XX) XXX XX XX shaklida kiriting.")
        return

    await state.update_data(contact_info=contact)
    contact_info = (await state.get_data()).get('contact_info')

    user_data = {
        "full_name": state_data['full_name'],
        "username": message.from_user.username,
        "tg_username": f"https://t.me/{message.from_user.username}",
        "telegram_id": user_id,
        "phone_number": contact_info
    }

    if user_language == 'ru':
        await message.answer("Спасибо! Наши операторы свяжутся с вами в ближайшее время.")
    else:
        await message.answer("Rahmat! Siz bilan operatorlarimiz tez orada bog'lanadi.")

    await save_user_info_to_db(user_data)
    await state.clear()
