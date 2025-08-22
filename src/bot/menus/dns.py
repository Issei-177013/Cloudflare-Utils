from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.bot.i18n import t

def dns_menu(lang="en"):
    keyboard = [
        [InlineKeyboardButton(t("list_records", lang), callback_data="dns_list")],
        [InlineKeyboardButton(t("add_record", lang), callback_data="dns_add")],
        [InlineKeyboardButton(t("edit_record", lang), callback_data="dns_edit")],
        [InlineKeyboardButton(t("delete_record", lang), callback_data="dns_delete")],
        [InlineKeyboardButton(t("back", lang), callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)