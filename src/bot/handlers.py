from telegram import Update # type: ignore
from telegram.constants import ChatType, ParseMode # type: ignore
from telegram.ext import ContextTypes # type: ignore
from src.bot.menus.main import main_menu
from src.bot.menus.accounts import accounts_menu, get_account_details_menu, get_edit_rename_menu, get_edit_token_menu, get_delete_confirmation_menu
from src.bot.menus.dns import dns_menu
from src.bot.menus.zones import zones_menu
from src.bot.menus.firewall import firewall_menu
from src.bot.menus.settings import settings_menu
from src.bot.menus.language import language_menu
from src.bot.i18n import t
from src.core.config import config_manager
from src.core.accounts import get_accounts, edit_account, delete_account
from src.core.cloudflare_api import CloudflareAPI

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

async def handle_wizard_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles text input during a wizard process.
    """
    if not context.user_data or 'wizard_step' not in context.user_data:
        # Ignore if not in wizard process.
        return

    lang = config_manager.get_bot_lang()
    step = context.user_data['wizard_step']
    account_to_edit = context.user_data['account_to_edit']
    page = context.user_data['page']
    new_text = update.message.text

    if step == 'awaiting_new_name':
        # --- Step 1: Handle new name ---
        if len(new_text) > 20 or config_manager.find_account(new_text):
            await update.message.reply_text(t("invalid_name", lang))
            return

        edit_account(account_to_edit, new_name=new_text)
        await update.message.reply_text(t("name_updated", lang))
        
        # Update state for next step
        context.user_data['wizard_step'] = 'awaiting_new_token'
        context.user_data['account_to_edit'] = new_text # Using new account name
        
        # Proceed to token step
        text, reply_markup = get_edit_token_menu(new_text, page, lang)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)

    elif step == 'awaiting_new_token':
        # --- Step 2: Handle new token ---
        try:
            cf_api = CloudflareAPI(new_text)
            cf_api.verify_token()
        except Exception:
            await update.message.reply_text(t("invalid_token", lang))
            return

        edit_account(account_to_edit, new_token=new_text)
        await update.message.reply_text(t("token_updated", lang))

        # End of wizard, show updated details
        context.user_data.clear()
        details = config_manager.find_account(account_to_edit)
        text, reply_markup = get_account_details_menu(details, page, lang)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=text, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )