from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.bot.i18n import t

def firewall_menu(lang="en"):
    keyboard = [
        [InlineKeyboardButton(t("list_rules", lang), callback_data="firewall_list")],
        [InlineKeyboardButton(t("add_rule", lang), callback_data="firewall_add")],
        [InlineKeyboardButton(t("delete_rule", lang), callback_data="firewall_delete")],
        [InlineKeyboardButton(t("back", lang), callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)