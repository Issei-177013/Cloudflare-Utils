from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from src.bot.utils import lri, pdi, escape_html
from src.bot.i18n import t

def account_selection_menu_for_zones(accounts, page=1, lang="en"):
    """
    Generates a paginated keyboard for selecting an account to view its zones.
    """
    keyboard = []
    items_per_page = 10
    
    if not accounts:
        keyboard.append([InlineKeyboardButton(t("back", lang), callback_data="menu_main")])
    else:
        # Sort accounts: default first, then alphabetically
        accounts.sort(key=lambda x: (not x.get('default', False), x.get('name', '').lower()), reverse=True)
        accounts.sort(key=lambda x: x.get('name', '').lower())
        default_account = next((acc for acc in accounts if acc.get('default')), None)
        if default_account:
            accounts.remove(default_account)
            accounts.insert(0, default_account)

        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        
        for acc in accounts[start_index:end_index]:
            account_name = acc.get("name", "N/A")
            is_default = acc.get("default", False)
            button_text = f"👤 {account_name}"
            if is_default:
                button_text += " ⭐"
            
            row = [
                InlineKeyboardButton(button_text, callback_data=f"ZONES_PICK_ACCOUNT:{account_name}:{page}")
            ]
            keyboard.append(row)
        
        # Pagination controls
        total_pages = (len(accounts) + items_per_page - 1) // items_per_page
        if total_pages > 1:
            pagination_row = []
            if page > 1:
                pagination_row.append(InlineKeyboardButton(t("prev_page", lang), callback_data=f"ZONES_ACCOUNTS_PAGE:{page-1}"))
            
            pagination_row.append(InlineKeyboardButton(t("page_indicator", lang).format(page=page, total_pages=total_pages), callback_data="noop"))

            if page < total_pages:
                pagination_row.append(InlineKeyboardButton(t("next_page", lang), callback_data=f"ZONES_ACCOUNTS_PAGE:{page+1}"))
            
            keyboard.append(pagination_row)

    # Global "Back" button
    keyboard.append([InlineKeyboardButton(t("back", lang), callback_data="menu_main")])
    
    return InlineKeyboardMarkup(keyboard)

def zones_list_menu(zones, account_name, page=1, lang="en"):
    """
    Generates a paginated keyboard for the list of zones.
    """
    keyboard = []
    items_per_page = 10

    if not zones:
        # Empty state: only "Add Zone" and "Back"
        keyboard.append([InlineKeyboardButton(t("add_zone", lang), callback_data=f"ADD_ZONE:{account_name}:{page}")])
    else:
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        
        for zone in zones[start_index:end_index]:
            zone_name = zone.name
            zone_id = zone.id
            
            row = [
                InlineKeyboardButton(f"{zone_name}", callback_data=f"VIEW_ZONE:{account_name}:{zone_id}:{page}"),
                InlineKeyboardButton(t("zone_settings", lang), callback_data=f"ZONE_SETTINGS:{account_name}:{zone_id}:{page}"),
                InlineKeyboardButton(t("zone_edit", lang), callback_data=f"EDIT_ZONE:{account_name}:{zone_id}:{page}"),
                InlineKeyboardButton(t("zone_delete", lang), callback_data=f"DELETE_ZONE:{account_name}:{zone_id}:{page}")
            ]
            keyboard.append(row)
        
        # Always add "Add Zone" at the end of the list
        keyboard.append([InlineKeyboardButton(t("add_zone", lang), callback_data=f"ADD_ZONE:{account_name}:{page}")])

        # Pagination controls
        total_pages = (len(zones) + items_per_page - 1) // items_per_page
        if total_pages > 1:
            pagination_row = []
            if page > 1:
                pagination_row.append(InlineKeyboardButton(t("prev_page", lang), callback_data=f"ZONES_PAGE:{account_name}:{page-1}"))
            
            pagination_row.append(InlineKeyboardButton(t("page_indicator", lang).format(page=page, total_pages=total_pages), callback_data="noop"))

            if page < total_pages:
                pagination_row.append(InlineKeyboardButton(t("next_page", lang), callback_data=f"ZONES_PAGE:{account_name}:{page+1}"))
            
            keyboard.append(pagination_row)

    # "Back" button to return to account selection
    keyboard.append([InlineKeyboardButton(t("back", lang), callback_data="menu_zones")])
    
    return InlineKeyboardMarkup(keyboard)

def get_zone_details_menu(zone_details, account_name, page, lang="en"):
    """
    Generates a message and keyboard for the zone details view.
    """
    name = zone_details.name or 'N/A'
    zone_id = zone_details.id or 'N/A'
    status = zone_details.status or 'N/A'
    plan_name = zone_details.plan.name if hasattr(zone_details, 'plan') and zone_details.plan else 'N/A'
    nameservers = ", ".join(zone_details.name_servers) if hasattr(zone_details, 'name_servers') else 'N/A'
    created_on = zone_details.created_on.isoformat() if hasattr(zone_details, 'created_on') else 'N/A'
    modified_on = zone_details.modified_on.isoformat() if hasattr(zone_details, 'modified_on') else 'N/A'

    text = (
        f"{t('zone_details_title', lang)}\n\n"
        f"<b>{t('zone_name', lang)}:</b> {lri}<code>{escape_html(name)}</code>{pdi}\n"
        f"<b>{t('zone_id', lang)}:</b> {lri}<code>{escape_html(zone_id)}</code>{pdi}\n"
        f"<b>{t('zone_status', lang)}:</b> {status}\n"
        f"<b>{t('zone_plan', lang)}:</b> {plan_name}\n"
        f"<b>{t('zone_nameservers', lang)}:</b> {lri}<code>{escape_html(nameservers)}</code>{pdi}\n"
        f"<b>{t('zone_created_on', lang)}:</b> {created_on}\n"
        f"<b>{t('zone_modified_on', lang)}:</b> {modified_on}"
    )

    keyboard = [
        [InlineKeyboardButton(t("back", lang), callback_data=f"ZONES_PAGE:{account_name}:{page}")]
    ]
    
    return text, InlineKeyboardMarkup(keyboard), ParseMode.HTML