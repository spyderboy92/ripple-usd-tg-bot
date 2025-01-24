from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
import os
from tg import states
from handlers import WalletHandlers


class WalletBot:
    """Telegram bot for wallet management."""

    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.wallet_handlers = WalletHandlers()

    def run(self):
        """Runs the bot."""
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.wallet_handlers.start)],
            states={
                states.START: [
                    CallbackQueryHandler(self.wallet_handlers.button_handler),
                ],
                states.SEND_ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   self.wallet_handlers.handle_send_address)
                ],
                states.SEND_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   self.wallet_handlers.handle_send_amount)
                ],
                states.SEND_CONFIRMATION: [
                    CallbackQueryHandler(
                        self.wallet_handlers.handle_confirmation),
                ],
                states.CREATE_WALLET: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   self.wallet_handlers.handle_create_wallet)
                ],
            },
            fallbacks=[CommandHandler('start', self.wallet_handlers.start)],
        )
        self.application.add_handler(conv_handler)
        self.application.run_polling()


if __name__ == '__main__':
    bot = WalletBot(os.getenv('BOT_API_KEY'))
    bot.run()
