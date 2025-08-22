"""
Telegram Bot Main Entry Point.
"""
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from src.bot.menus.main import main_menu
from src.bot.handlers import button_handler
from src.core.app import Application
from src.core.config import config_manager
from src.bot.i18n import t

async def start(update, context):
    """Sends a welcome message with the main menu."""
    lang = config_manager.get_bot_lang()
    await update.message.reply_text(t("welcome_message", lang), reply_markup=main_menu(lang))

def main():
    """Starts the bot."""
    config = config_manager.get_config()
    token = config.get("bot", {}).get("token", "YOUR_TELEGRAM_BOT_TOKEN")
    
    if token == "YOUR_TELEGRAM_BOT_TOKEN":
        print("Bot token is a placeholder. Please update it in your configs.json")
        return

    application = ApplicationBuilder().token(token).build()
    
    # Attach the application facade to the bot's context
    application.app = Application()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Starting bot polling...")
    application.run_polling()

if __name__ == '__main__':
    main()