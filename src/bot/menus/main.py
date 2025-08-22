from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.bot.i18n import t

def main_menu(lang="en"):
    keyboard = [
        [InlineKeyboardButton(t("accounts", lang), callback_data="menu_accounts")],
        [InlineKeyboardButton(t("dns", lang), callback_data="menu_dns")],
        [InlineKeyboardButton(t("zones", lang), callback_data="menu_zones")],
        [InlineKeyboardButton(t("firewall", lang), callback_data="menu_firewall")],
        [InlineKeyboardButton(t("settings", lang), callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(keyboard)