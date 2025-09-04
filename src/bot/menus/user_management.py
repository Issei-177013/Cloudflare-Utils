from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.bot.i18n import t
from src.core.config import config_manager

def user_management_menu(current_user_id, lang="en"):
    """
    Generates a keyboard for the user management menu.
    """
    config = config_manager.get_config()
    allowed_ids = config.get("settings", {}).get("bot", {}).get("allowed_user_ids", [])

    keyboard = []
    for user_id in allowed_ids:
        text = str(user_id)
        if user_id == current_user_id:
            text += " (You)"
            row = [InlineKeyboardButton(text, callback_data="noop")]
        else:
            row = [
                InlineKeyboardButton(text, callback_data="noop"),
                InlineKeyboardButton(t("delete", lang), callback_data=f"delete_user:{user_id}")
            ]
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(t("add_user_id", lang), callback_data="add_user_id")])
    keyboard.append([InlineKeyboardButton(t("back", lang), callback_data="menu_settings")])

    return InlineKeyboardMarkup(keyboard)