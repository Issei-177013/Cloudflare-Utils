from telegram import InlineKeyboardButton, InlineKeyboardMarkup # type: ignore
from telegram.constants import ParseMode # type: ignore
from src.bot.i18n import t
from src.bot.utils import lri, pdi, escape_html

def accounts_menu(accounts, page=1, lang="en"):
    """
    Generates a paginated keyboard for the list of accounts.
    """
    keyboard = []
    items_per_page = 10
    
    # Truncate label helper
    def truncate(label, length=15):
        return (label[:length] + '…') if len(label) > length else label

    if not accounts:
        # Empty state: only "Add Account" and "Back"
        keyboard.append([InlineKeyboardButton(t("add_account", lang), callback_data="ADD_ACCOUNT")])
    else:
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        
        for acc in accounts[start_index:end_index]:
            account_name = acc.get("name", "N/A")
            row = [
                InlineKeyboardButton(f"👤 {truncate(account_name)}", callback_data=f"VIEW_ACCOUNT:{account_name}:{page}"),
                InlineKeyboardButton(t("edit_account", lang), callback_data=f"EDIT_ACCOUNT:{account_name}:{page}"),
                InlineKeyboardButton(t("delete_account", lang), callback_data=f"DELETE_ACCOUNT:{account_name}:{page}")
            ]
            keyboard.append(row)
        
        # Always add "Add Account" at the end of the list of accounts
        keyboard.append([InlineKeyboardButton(t("add_account", lang), callback_data="ADD_ACCOUNT")])

        # Pagination controls
        total_pages = (len(accounts) + items_per_page - 1) // items_per_page
        if total_pages > 1:
            pagination_row = []
            if page > 1:
                pagination_row.append(InlineKeyboardButton(t("prev_page", lang), callback_data=f"ACCOUNTS_PAGE:{page-1}"))
            
            pagination_row.append(InlineKeyboardButton(t("page_indicator", lang).format(page=page, total_pages=total_pages), callback_data="noop"))

            if page < total_pages:
                pagination_row.append(InlineKeyboardButton(t("next_page", lang), callback_data=f"ACCOUNTS_PAGE:{page+1}"))
            
            keyboard.append(pagination_row)

    # Global "Back" button
    keyboard.append([InlineKeyboardButton(t("back", lang), callback_data="menu_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_account_details_menu(account_details, page, lang="en"):
    """
    Generates a message and keyboard for the account details view.
    """
    name = account_details.get('name', 'N/A')
    token = account_details.get('api_token', 'N/A')

    parse_mode = ParseMode.HTML
    name_lri = f'{lri}<code>{escape_html(name)}</code>{pdi}'
    token_html = f'{lri}<span class="tg-spoiler">{escape_html(token)}</span>{pdi}'

    text = (
        f"<b>{t('account_details_title', lang)}</b>\n\n"
        f"<b>{t('account_name', lang)}:</b> {name_lri}\n"
        f"<b>{t('token', lang)}:</b> {token_html}"
    )

    keyboard = [
        [InlineKeyboardButton(t("back", lang), callback_data=f"ACCOUNTS_PAGE:{page}")]
    ]

    return text, InlineKeyboardMarkup(keyboard), parse_mode

def get_edit_rename_menu(account_name, page, lang="en"):
    """
    Generates the UI for the first step of the edit wizard (rename).
    """
    text = t("edit_rename_prompt", lang).format(account_name=account_name)
    keyboard = [
        [
            InlineKeyboardButton(t("skip", lang), callback_data=f"EDIT_SKIP_RENAME:{account_name}:{page}"),
            InlineKeyboardButton(t("cancel", lang), callback_data=f"EDIT_CANCEL:{account_name}:{page}")
        ]
    ]
    return text, InlineKeyboardMarkup(keyboard)

def get_delete_confirmation_menu(account_name, page, lang="en"):
    """
    Generates a confirmation screen for deleting an account.
    """
    text = t("delete_confirmation", lang).format(account_name=account_name)
    keyboard = [
        [
            InlineKeyboardButton(t("confirm_delete", lang), callback_data=f"CONFIRM_DELETE:{account_name}:{page}"),
            InlineKeyboardButton(t("cancel", lang), callback_data=f"ACCOUNTS_PAGE:{page}")
        ]
    ]
    return text, InlineKeyboardMarkup(keyboard)

def get_edit_token_menu(account_name, page, lang="en"):
    """
    Generates the UI for the second step of the edit wizard (update token).
    """
    text = t("edit_token_prompt", lang)
    keyboard = [
        [
            InlineKeyboardButton(t("skip", lang), callback_data=f"EDIT_SKIP_TOKEN:{account_name}:{page}"),
            InlineKeyboardButton(t("back", lang), callback_data=f"EDIT_BACK_TO_RENAME:{account_name}:{page}")
        ]
    ]
    return text, InlineKeyboardMarkup(keyboard)