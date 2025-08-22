from telegram import Update
from telegram.ext import ContextTypes
from src.bot.menus.main import main_menu
from src.bot.menus.accounts import accounts_menu
from src.bot.menus.dns import dns_menu
from src.bot.menus.zones import zones_menu
from src.bot.menus.firewall import firewall_menu
from src.bot.menus.settings import settings_menu
from src.bot.menus.language import language_menu
from src.bot.i18n import t
from src.core.config import config_manager

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = config_manager.get_bot_lang()

    if query.data == "menu_main":
        await query.edit_message_text(t("main_menu", lang), reply_markup=main_menu(lang))
    elif query.data == "menu_accounts":
        await query.edit_message_text(t("accounts_menu_title", lang), reply_markup=accounts_menu(lang))
    elif query.data == "accounts_list":
        success, data = context.application.app.get_accounts()
        if not success:
            await query.edit_message_text(f'{t("error_prefix", lang)}{data}', reply_markup=accounts_menu(lang))
            return
        if not data:
            await query.edit_message_text(t("no_accounts_configured", lang), reply_markup=accounts_menu(lang))
            return
        message = f'{t("accounts_list_title", lang)}\n' + "\n".join([f"- {acc['name']}" for acc in data])
        await query.edit_message_text(message, reply_markup=accounts_menu(lang))
    elif query.data == "menu_dns":
        await query.edit_message_text(t("dns_menu_title", lang), reply_markup=dns_menu(lang))
    elif query.data == "menu_zones":
        await query.edit_message_text(t("zones_menu_title", lang), reply_markup=zones_menu(lang))
    elif query.data == "menu_firewall":
        await query.edit_message_text(t("firewall_menu_title", lang), reply_markup=firewall_menu(lang))
    elif query.data == "menu_settings":
        await query.edit_message_text(t("settings_menu_title", lang), reply_markup=settings_menu(lang))
    elif query.data == "menu_language":
        await query.edit_message_text(t("language_menu_title", lang), reply_markup=language_menu(lang))
    elif query.data == "set_lang_en":
        config_manager.set_bot_lang("en")
        lang = "en"
        await query.edit_message_text(t("language_menu_title", lang), reply_markup=language_menu(lang))
    elif query.data == "set_lang_fa":
        config_manager.set_bot_lang("fa")
        lang = "fa"
        await query.edit_message_text(t("language_menu_title", lang), reply_markup=language_menu(lang))
    # TODO: Implement other menu handlers and actions