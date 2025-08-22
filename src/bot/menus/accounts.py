from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.bot.i18n import t

def accounts_menu(lang="en"):
    keyboard = [
        [InlineKeyboardButton(t("list_accounts", lang), callback_data="accounts_list")],
        [InlineKeyboardButton(t("add_account", lang), callback_data="accounts_add")],
        [InlineKeyboardButton(t("delete_account", lang), callback_data="accounts_delete")],
        [InlineKeyboardButton(t("back", lang), callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)