"""
Telegram Bot Main Entry Point.
"""
from telegram import Update # type: ignore
from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler, TypeHandler, MessageHandler, filters, ContextTypes # type: ignore

from src.bot.menus.main import main_menu
from src.bot.menus.language import language_menu
from src.bot.handlers import button_handler, handle_wizard_input
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
    bot_settings = config.get("settings", {}).get("bot", {})
    allowed_ids = bot_settings.get("allowed_user_ids", [])
    user_id = update.effective_user.id

    if allowed_ids and user_id not in allowed_ids:
        logger.warning(f"Unauthorized access attempt by user ID: {user_id}")
        lang = config_manager.get_bot_lang(user_id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=t("unauthorized_access", lang)
        )
        # Stop this update from being processed further.
        context.application.stop_handling_update()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message with the main menu or language selection."""
    user_id = update.effective_user.id
    lang_config = config_manager.get_config().get("settings", {}).get("bot", {}).get("lang", {})
    
    # If user does not have a language set, show language menu
    if str(user_id) not in lang_config.get("users", {}):
        await update.message.reply_text("Please select your language:", reply_markup=language_menu())
    else:
        lang = config_manager.get_bot_lang(user_id)
        await update.message.reply_text(t("welcome_message", lang), reply_markup=main_menu(lang))

def main():
    """Starts the bot."""
    logger.info("Attempting to start Telegram bot...")
    config = config_manager.get_config()
    bot_settings = config.get("settings", {}).get("bot", {})

    if not bot_settings.get("enabled"):
        logger.info("Bot is disabled in the configuration. Exiting.")
        return

    token = bot_settings.get("token")
    
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wizard_input))
    
    logger.info("Starting bot polling...")
    application.run_polling()

if __name__ == '__main__':
    main()