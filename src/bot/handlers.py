from telegram import Update # type: ignore
from telegram.constants import ChatType, ParseMode # type: ignore
from telegram.ext import ContextTypes # type: ignore
from src.core.logger import logger
from src.bot.menus.main import main_menu
from src.bot.menus.accounts import (
    accounts_menu, get_account_details_menu,
    get_edit_rename_menu, get_edit_token_menu, get_delete_confirmation_menu,
    get_add_account_label_menu, get_add_account_token_menu
)
from src.bot.menus.dns import dns_menu
from src.bot.menus.zones import (
    account_selection_menu_for_zones,
    zones_list_menu,
    get_zone_details_menu
)
from src.bot.menus.firewall import firewall_menu
from src.bot.menus.settings import settings_menu
from src.bot.menus.language import language_menu
from src.bot.i18n import t
from src.bot.utils import format_token_guidance_html
from src.core.config import config_manager
from src.core.accounts import add_account, get_accounts, edit_account, delete_account
from src.core.zones import list_zones_for_account, get_zone_details_for_account
from src.core.cloudflare_api import CloudflareAPI
from src.core.exceptions import AuthenticationError, APIError

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

    elif command == "VIEW_ACCOUNT":
        await query.answer()
        try:
            account_name, page_str = data.split(':', 1)
            page = int(page_str)
            
            details = config_manager.find_account(account_name)
            if not details:
                raise Exception(f"Account '{account_name}' not found.")

            text, reply_markup, parse_mode = get_account_details_menu(details, page, lang)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as e:
            await query.answer(text=f"{t('error_prefix', lang)} {e}", show_alert=True)

    elif command == "EDIT_ACCOUNT":
        account_name, page_str = data.split(':', 1)
        context.user_data['wizard_step'] = 'awaiting_new_name'
        context.user_data['account_to_edit'] = account_name
        context.user_data['page'] = int(page_str)
        context.user_data['wizard_message'] = query.message
        
        text, reply_markup = get_edit_rename_menu(account_name, int(page_str), lang)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif command == "EDIT_SKIP_RENAME":
        account_name, page_str = data.split(':', 1)
        context.user_data['wizard_step'] = 'awaiting_new_token'
        
        text, reply_markup = get_edit_token_menu(account_name, int(page_str), lang)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif command == "EDIT_CANCEL":
        await query.answer()
        account_name, page_str = data.split(':', 1)
        context.user_data.clear()

        page = int(page_str)
        accounts = get_accounts()
        reply_markup = accounts_menu(accounts, page=page, lang=lang)
        await query.edit_message_text(
            t("accounts_list_title", lang),
            reply_markup=reply_markup
        )

    elif command == "EDIT_BACK_TO_RENAME":
        account_name, page_str = data.split(':', 1)
        context.user_data['wizard_step'] = 'awaiting_new_name'
        
        text, reply_markup = get_edit_rename_menu(account_name, int(page_str), lang)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif command == "EDIT_SKIP_TOKEN":
        await query.answer()
        account_name, page_str = data.split(':', 1)
        context.user_data.clear()

        page = int(page_str)
        accounts = get_accounts()
        reply_markup = accounts_menu(accounts, page=page, lang=lang)
        await query.edit_message_text(
            t("accounts_list_title", lang),
            reply_markup=reply_markup
        )
        
    elif command == "DELETE_ACCOUNT":
        await query.answer()
        account_name, page_str = data.split(':', 1)
        page = int(page_str)
        
        text, reply_markup = get_delete_confirmation_menu(account_name, page, lang)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif command == "CONFIRM_DELETE":
        await query.answer(t("deleting", lang))
        account_name, page_str = data.split(':', 1)
        page = int(page_str)

        try:
            delete_account(account_name)
            await query.answer(t("deleted_successfully", lang), show_alert=False)
            
            # Refresh and adjust pagination
            accounts = get_accounts()
            items_per_page = 10
            total_pages = (len(accounts) + items_per_page - 1) // items_per_page
            
            if page > total_pages and total_pages > 0:
                page = total_pages

            reply_markup = accounts_menu(accounts, page=page, lang=lang)
            await query.edit_message_text(t("accounts_list_title", lang), reply_markup=reply_markup)
        except Exception as e:
            await query.answer(f"{t('error_prefix', lang)} {e}", show_alert=True)

    elif command == "ADD_ACCOUNT":
        await query.answer()
        context.user_data['wizard_step'] = 'awaiting_account_label'
        context.user_data['wizard_context'] = {}
        context.user_data['wizard_message'] = query.message
        
        text, reply_markup = get_add_account_label_menu(lang)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif command == "ADD_ACCOUNT_SKIP_LABEL":
        await query.answer()
        
        accounts = get_accounts()
        existing_names = {acc['name'] for acc in accounts}
        
        i = 1
        while f"account-{i}" in existing_names:
            i += 1
        
        new_label = f"account-{i}"
        
        context.user_data['wizard_step'] = 'awaiting_account_token'
        context.user_data['wizard_context']['label'] = new_label
        
        text, reply_markup, parse_mode = get_add_account_token_menu(lang)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)

    elif command == "ADD_ACCOUNT_CANCEL":
        await query.answer()
        context.user_data.clear()
        
        accounts = get_accounts()
        reply_markup = accounts_menu(accounts, page=1, lang=lang)
        await query.edit_message_text(t("accounts_list_title", lang), reply_markup=reply_markup)

    elif command == "ADD_ACCOUNT_BACK_TO_LABEL":
        await query.answer()
        context.user_data['wizard_step'] = 'awaiting_account_label'
        
        text, reply_markup = get_add_account_label_menu(lang)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif command == "menu_dns":
        await query.answer()
        await query.edit_message_text(t("dns_menu_title", lang), reply_markup=dns_menu(lang))

    elif command in ("menu_zones", "ZONES_ACCOUNTS_PAGE"):
        await query.answer()
        page = int(data) if data else 1
        try:
            accounts = get_accounts()
            reply_markup = account_selection_menu_for_zones(accounts, page=page, lang=lang)
            await query.edit_message_text(t("choose_account_for_zones", lang), reply_markup=reply_markup)
        except Exception as e:
            await query.answer(text=t("error_prefix", lang) + str(e), show_alert=True)

    elif command == "ZONES_PICK_ACCOUNT":
        await query.answer(text=t("loading", lang))
        account_name, account_page_str = data.split(':', 1)
        account_page = int(account_page_str)
        try:
            zones = list_zones_for_account(account_name)
            text = t('zones_list_title', lang).format(account_name=account_name)
            if not zones:
                text += f"\n\n{t('no_zones_yet', lang)}"
            
            # The first page of zones is always 1
            reply_markup = zones_list_menu(zones, account_name, page=1, lang=lang)
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error picking account for zones: {e}", exc_info=True)
            await query.answer(text=f"{t('error_prefix', lang)} {e}", show_alert=True)
            # On error, show the account list again with an error message
            accounts = get_accounts()
            reply_markup = account_selection_menu_for_zones(accounts, page=account_page, lang=lang)
            error_text = f"❌ {e}\n\n{t('choose_account_for_zones', lang)}"
            await query.edit_message_text(error_text, reply_markup=reply_markup)

    elif command == "ZONES_PAGE":
        await query.answer(text=t("loading", lang))
        account_name, page_str = data.split(':', 1)
        page = int(page_str)
        try:
            zones = list_zones_for_account(account_name)
            text = t('zones_list_title', lang).format(account_name=account_name)
            if not zones:
                text += f"\n\n{t('no_zones_yet', lang)}"
            
            reply_markup = zones_list_menu(zones, account_name, page=page, lang=lang)
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error paginating zones: {e}", exc_info=True)
            await query.answer(text=f"{t('error_prefix', lang)} {e}", show_alert=True)
            # On error, we can't do much but show the alert, as we don't have the account page context

    elif command == "VIEW_ZONE":
        await query.answer()
        try:
            account_name, zone_id, page_str = data.split(':', 2)
            page = int(page_str)
            
            details = get_zone_details_for_account(account_name, zone_id)
            if not details:
                raise Exception(f"Zone '{zone_id}' not found.")

            text, reply_markup, parse_mode = get_zone_details_menu(details, account_name, page, lang)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Error viewing zone details: {e}", exc_info=True)
            await query.answer(text=f"{t('error_prefix', lang)} {e}", show_alert=True)

    elif command in ("ZONE_SETTINGS", "EDIT_ZONE", "DELETE_ZONE", "ADD_ZONE"):
        await query.answer(text=t("coming_soon", lang), show_alert=True)

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

async def handle_add_account_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE, step: str, lang: str):
    new_text = update.message.text
    wizard_message = context.user_data.get('wizard_message')

    if not wizard_message:
        await update.message.delete()
        return

    if step == 'awaiting_account_label':
        label = new_text.strip()
        
        if not (1 <= len(label) <= 30):
            await update.message.reply_text(t("add_account_invalid_label_length", lang), quote=True)
            return
        
        if config_manager.find_account(label):
            await update.message.reply_text(t("add_account_duplicate_label", lang).format(label=label), quote=True)
            return
            
        context.user_data['wizard_context']['label'] = label
        context.user_data['wizard_step'] = 'awaiting_account_token'
        
        await update.message.delete()
        text, reply_markup, parse_mode = get_add_account_token_menu(lang)
        await wizard_message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)

    elif step == 'awaiting_account_token':
        token = new_text.strip()
        label = context.user_data['wizard_context']['label']
        
        await wizard_message.edit_text(t("validating_token", lang))
        await update.message.delete()
        
        try:
            add_account(label, token)
            context.user_data.clear()
            
            accounts = get_accounts()
            reply_markup = accounts_menu(accounts, page=1, lang=lang)
            await wizard_message.edit_text(
                f"{t('account_added_successfully', lang)}\n\n{t('accounts_list_title', lang)}",
                reply_markup=reply_markup
            )
            
        except (AuthenticationError, APIError) as e:
            text, reply_markup, parse_mode = get_add_account_token_menu(lang)
            error_message = f"❌ {t('invalid_token_error', lang)}\n\n<i>{e}</i>"
            await wizard_message.edit_text(
                f"{error_message}\n\n{text}",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            text, reply_markup, parse_mode = get_add_account_token_menu(lang)
            await wizard_message.edit_text(
                f"❌ {t('error_prefix', lang)} {e}\n\n{text}",
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )

async def handle_edit_account_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE, step: str, lang: str):
    new_text = update.message.text
    wizard_message = context.user_data.get('wizard_message')

    if not wizard_message:
        await update.message.delete()
        return
        
    account_to_edit = context.user_data['account_to_edit']
    page = context.user_data['page']

    if step == 'awaiting_new_name':
        if len(new_text) > 30 or config_manager.find_account(new_text):
            await update.message.reply_text(t("invalid_name", lang), quote=True)
            return

        await update.message.delete()
        edit_account(account_to_edit, new_name=new_text)
        
        context.user_data['wizard_step'] = 'awaiting_new_token'
        context.user_data['account_to_edit'] = new_text
        
        text, reply_markup = get_edit_token_menu(new_text, page, lang)
        await wizard_message.edit_text(
            f"✅ {t('name_updated', lang)}\n\n{text}",
            reply_markup=reply_markup
        )

    elif step == 'awaiting_new_token':
        try:
            cf_api = CloudflareAPI(new_text)
            cf_api.verify_token()
        except Exception:
            await update.message.reply_text(t("invalid_token", lang), quote=True)
            return

        await update.message.delete()
        edit_account(account_to_edit, new_token=new_text)
        context.user_data.clear()

        details = config_manager.find_account(account_to_edit)
        text, reply_markup, parse_mode = get_account_details_menu(details, page, lang)
        await wizard_message.edit_text(
            f"✅ {t('token_updated', lang)}\n\n{text}",
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

async def handle_wizard_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data or 'wizard_step' not in context.user_data:
        return

    lang = config_manager.get_bot_lang()
    step = context.user_data['wizard_step']

    if step.startswith('awaiting_account_'):
        await handle_add_account_wizard(update, context, step, lang)
    elif step.startswith('awaiting_new_'):
        await handle_edit_account_wizard(update, context, step, lang)