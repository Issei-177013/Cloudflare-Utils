from telegram import Update
from telegram.constants import ChatType
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
from src.core.accounts import get_accounts

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = config_manager.get_bot_lang()

    if update.effective_chat.type != ChatType.PRIVATE:
        await query.answer(text=t("private_chat_only", lang), show_alert=True)
        await query.edit_message_text(t("private_chat_only", lang))
        return

    parts = query.data.split(':', 1)
    command = parts[0]
    data = parts[1] if len(parts) > 1 else None

    if command == "menu_main":
        await query.answer()
        await query.edit_message_text(t("main_menu", lang), reply_markup=main_menu(lang))

    elif command in ("menu_accounts", "ACCOUNTS_PAGE"):
        await query.answer(text=t("loading", lang), show_alert=False)
        page = int(data) if data else 1
        try:
            accounts = get_accounts()
            reply_markup = accounts_menu(accounts, page=page, lang=lang)
            await query.edit_message_text(t("accounts_list_title", lang), reply_markup=reply_markup)
        except Exception as e:
            await query.answer(text=t("error_prefix", lang), show_alert=True)
            await query.edit_message_text(f"{t('error_prefix', lang)}{e}")

    elif command in ["VIEW_ACCOUNT", "EDIT_ACCOUNT", "DELETE_ACCOUNT", "ADD_ACCOUNT"]:
        await query.answer(text=t("coming_soon", lang), show_alert=False)

    elif command == "menu_dns":
        await query.answer()
        await query.edit_message_text(t("dns_menu_title", lang), reply_markup=dns_menu(lang))

    elif query.data == "menu_zones":
        await query.answer()
        await query.edit_message_text(t("zones_menu_title", lang), reply_markup=zones_menu(lang))

    elif query.data == "menu_firewall":
        await query.answer()
        await query.edit_message_text(t("firewall_menu_title", lang), reply_markup=firewall_menu(lang))

    elif query.data == "menu_settings":
        await query.answer()
        await query.edit_message_text(t("settings_menu_title", lang), reply_markup=settings_menu(lang))

    elif query.data == "menu_language":
        await query.answer()
        await query.edit_message_text(t("language_menu_title", lang), reply_markup=language_menu(lang))

    elif query.data == "set_lang_en":
        await query.answer(text=t("loading", lang), show_alert=False)
        config_manager.set_bot_lang("en")
        await query.edit_message_text(t("language_menu_title", "en"), reply_markup=language_menu("en"))

    elif query.data == "set_lang_fa":
        await query.answer(text=t("loading", lang), show_alert=False)
        config_manager.set_bot_lang("fa")
        await query.edit_message_text(t("language_menu_title", "fa"), reply_markup=language_menu("fa"))
    # TODO: Implement other menu handlers and actions