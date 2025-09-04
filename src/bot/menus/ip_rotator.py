from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.bot.i18n import t

def ip_rotator_menu(lang="en"):
    keyboard = [
        [InlineKeyboardButton(t("back", lang), callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)