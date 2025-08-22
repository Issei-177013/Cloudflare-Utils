from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.bot.i18n import t

def settings_menu(lang="en"):
    keyboard = [
        [InlineKeyboardButton(t("toggle_console_logging", lang), callback_data="settings_toggle_console_logging")],
        [InlineKeyboardButton(t("toggle_slow_mode", lang), callback_data="settings_toggle_slow_mode")],
        [InlineKeyboardButton(t("back", lang), callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)