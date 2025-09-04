from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.bot.i18n import t

def settings_menu(lang="en"):
    keyboard = [
        [InlineKeyboardButton(t("language", lang), callback_data="settings_language")],
        [InlineKeyboardButton(t("configure_timezone", lang), callback_data="settings_timezone")],
        [InlineKeyboardButton(t("manage_user_ids", lang), callback_data="settings_user_ids")],
        [InlineKeyboardButton(t("back", lang), callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)