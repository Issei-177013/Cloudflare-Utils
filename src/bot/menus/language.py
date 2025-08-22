from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.bot.i18n import t

def language_menu(lang="en"):
    keyboard = [
        [InlineKeyboardButton("English", callback_data="set_lang_en")],
        [InlineKeyboardButton("فارسی", callback_data="set_lang_fa")],
        [InlineKeyboardButton(t("back", lang), callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(keyboard)