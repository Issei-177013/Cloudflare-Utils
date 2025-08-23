"""
Telegram Bot Main Entry Point.
"""
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler, TypeHandler, ContextTypes

from src.bot.menus.main import main_menu
from src.bot.handlers import button_handler
from src.core.app import Application as CoreApplication
from src.core.config import config_manager
from src.bot.i18n import t
from src.core.logger import logger

async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    A pre-flight check to ensure the user is allowed to interact with the bot.
    This handler runs in group -1, so it runs before all other handlers.
    """
    if not update.effective_user:
        return

    config = config_manager.get_config()
    allowed_ids = config.get("bot", {}).get("allowed_user_ids", [])
    user_id = update.effective_user.id

    if allowed_ids and user_id not in allowed_ids:
        logger.warning(f"Unauthorized access attempt by user ID: {user_id}")
        lang = config_manager.get_bot_lang()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=t("unauthorized_access", lang)
        )
        # Stop this update from being processed further.
        context.application.stop_handling_update()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message with the main menu."""
    lang = config_manager.get_bot_lang()
    await update.message.reply_text(t("welcome_message", lang), reply_markup=main_menu(lang))

def main():
    """Starts the bot."""
    logger.info("Attempting to start Telegram bot...")
    config = config_manager.get_config()
    bot_config = config.get("bot", {})

    if not bot_config.get("enabled"):
        logger.info("Bot is disabled in the configuration. Exiting.")
        return

    token = bot_config.get("token")
    
    if not token:
        logger.error("Bot token is not set in the configuration. Exiting.")
        return

    application = ApplicationBuilder().token(token).build()
    
    # Attach the application facade to the bot's context
    application.app = CoreApplication()

    # Add the access check handler in a low-numbered group to run it first.
    application.add_handler(TypeHandler(Update, check_access), group=-1)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("Starting bot polling...")
    application.run_polling()

if __name__ == '__main__':
    main()