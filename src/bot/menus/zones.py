from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.bot.i18n import t

def zones_menu(lang="en"):
    keyboard = [
        [InlineKeyboardButton(t("list_zones", lang), callback_data="zones_list")],
        [InlineKeyboardButton(t("add_zone", lang), callback_data="zones_add")],
        [InlineKeyboardButton(t("delete_zone", lang), callback_data="zones_delete")],
        [InlineKeyboardButton(t("back", lang), callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)