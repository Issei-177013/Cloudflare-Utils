from telegram import Update
from telegram.ext import ContextTypes
from src.bot.menus.main import main_menu
from src.bot.menus.accounts import accounts_menu

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu_main":
        await query.edit_message_text("Choose an option:", reply_markup=main_menu())
    elif query.data == "menu_accounts":
        await query.edit_message_text("Accounts Menu:", reply_markup=accounts_menu())
    elif query.data == "accounts_list":
        success, data = context.application.app.get_accounts()
        if not success:
            await query.edit_message_text(f"Error: {data}", reply_markup=accounts_menu())
            return
        if not data:
            await query.edit_message_text("No accounts configured.", reply_markup=accounts_menu())
            return
        message = "Accounts:\n" + "\n".join([f"- {acc['name']}" for acc in data])
        await query.edit_message_text(message, reply_markup=accounts_menu())
    elif query.data == "menu_dns":
        await query.edit_message_text("DNS Menu:", reply_markup=dns_menu())
    elif query.data == "menu_zones":
        await query.edit_message_text("Zones Menu:", reply_markup=zones_menu())
    elif query.data == "menu_firewall":
        await query.edit_message_text("Firewall Menu:", reply_markup=firewall_menu())
    elif query.data == "menu_settings":
        await query.edit_message_text("Settings Menu:", reply_markup=settings_menu())
    # TODO: Implement other menu handlers and actions