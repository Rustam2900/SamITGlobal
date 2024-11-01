from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_languages(flag="lang"):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="uz ", callback_data=f"{flag}_uz"),
         InlineKeyboardButton(text='ru ', callback_data=f"{flag}_ru")], ])
    return keyboard
