from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from tg import states
from xrp.wallet import Wallet
from xrp.xrp_wallet_util import XrpWalletUtil


class WalletHandlers:
    """Handles the Telegram bot's commands and messages."""

    def __init__(self):
        self.wallets = {}  # in-memory storage, TODO: Move to DB
        self.transaction_data = {}
        self.wallet_util = XrpWalletUtil()

    async def start(self, update: Update, context) -> int:
        """Displays the main menu with inline buttons."""
        keyboard = [
            [InlineKeyboardButton("Send", callback_data='send')],
            [InlineKeyboardButton("Receive", callback_data='receive')],
            [InlineKeyboardButton("Check Balance", callback_data='check_balance')],
            [InlineKeyboardButton("Create Wallet", callback_data='create_wallet')],
            [InlineKeyboardButton("Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Welcome to Ripple USD bot!!Choose an option:", reply_markup=reply_markup)
        return states.START

    async def button_handler(self, update: Update, context) -> int:
        """Runs when state reaches states.START"""
        query = update.callback_query
        await query.answer()

        if query.data == 'send':
            return await self.send_funds(update, context)
        elif query.data == 'receive':
            return await self.receive_funds(update, context)
        elif query.data == 'check_balance':
            return await self.check_balance(update, context)
        elif query.data == 'create_wallet':
            return await self.create_wallet(update, context)
        elif query.data == 'help':
            return await self.help_command(update, context)

    async def send_funds(self, update: Update, context) -> int:
        """Initiates the send funds flow."""
        wallet = self.get_user_wallet(update.callback_query.from_user.id)
        if not wallet.wallet_address:
            await update.callback_query.message.reply_text("No wallet created. Please create one first.")
            return await self.start(update.callback_query.message, context)
        await update.callback_query.message.reply_text("Enter the address to send to:")
        return states.SEND_ADDRESS

    async def handle_send_address(self, update: Update, context) -> int:
        """Handles receiving the recipient's address."""
        context.user_data['address'] = update.message.text
        self.transaction_data["address"] = context.user_data['address']
        await update.message.reply_text("Enter the amount to send:")
        return states.SEND_AMOUNT

    async def handle_send_amount(self, update: Update, context):
        """Handle the amount input."""
        amount = update.message.text
        self.transaction_data["amount"] = amount

        # Send confirmation message with InlineKeyboard
        keyboard = [
            [
                InlineKeyboardButton("Confirm", callback_data="confirm"),
                InlineKeyboardButton("Cancel", callback_data="cancel"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Confirm the transaction:\nAddress: {self.transaction_data['address']}\n"
            f"Amount: {self.transaction_data['amount']}\n",
            reply_markup=reply_markup
        )
        return states.SEND_CONFIRMATION

    async def handle_confirmation(self, update: Update, context) -> int:
        """Handle confirmation or cancellation."""
        query = update.callback_query
        await query.answer()

        if query.data == "confirm":
            # Process the transaction
            wallet = self.get_user_wallet(update.callback_query.from_user.id)
            self.wallet_util.send_xrp(wallet.wallet_seed, self.transaction_data["amount"], self.transaction_data["address"])
            await query.edit_message_text("Transaction confirmed! Sending funds...")
            # Add logic to send funds here
        else:
            await query.edit_message_text("Entered: " + query.data + "Transaction canceled.")

        return states.START

    async def receive_funds(self, update: Update, context) -> int:
        """Displays the user's wallet address and QR code."""
        user_id = update.callback_query.from_user.id
        wallet = self.get_user_wallet(user_id)
        if wallet is None:
            await update.callback_query.message.reply_text("No wallet created. Please create one first.")
            return await self.start(update.callback_query.message, context)
        qr_code = self.wallet_util.generate_qr_code(wallet.wallet_address)
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=qr_code,
            caption=f"WALLET ADDRESS: {wallet.wallet_address}",
        )
        return await self.start(update.callback_query.message, context)

    async def check_balance(self, update: Update, context) -> int:
        """Checks and displays the user's wallet balance."""
        wallet = self.get_user_wallet(update.callback_query.from_user.id)
        if wallet is None:
            await update.callback_query.message.reply_text("No wallet created.")
        else:
            balance = await self.wallet_util.check_balance(wallet.wallet_address)
            await update.callback_query.message.reply_text(f"Your balance is {balance}.")
        return await self.start(update.callback_query.message if update.callback_query else update.message, context)

    async def create_wallet(self, update: Update, context) -> int:
        """Starts the wallet creation process."""
        user_id = update.callback_query.from_user.id
        wallet = self.get_user_wallet(user_id)
        # If wallet already exists, no need to create
        if wallet != None:
            await update.callback_query.message.reply_text("Wallet has been already created.")
            return states.START
        else:
            await update.callback_query.message.reply_text("Enter your wallet name:")
            return states.CREATE_WALLET

    async def handle_create_wallet(self, update: Update, context) -> int:
        """Creates a wallet with the specified name."""
        user_id = update.message.from_user.id
        wallet_name = update.message.text
        wallet = self.get_user_wallet(user_id)
        if wallet != None:
            await update.message.reply_text("Wallet has been already created.")
            return await self.start(update.message, context)

        response = await self.wallet_util.create_wallet()  # Await the coroutine
        wallet_address = response["wallet_address"]
        wallet_seed = response["wallet_seed"]
        new_wallet = Wallet(user_id, wallet_address, wallet_seed, wallet_name)
        self.wallets[user_id] = new_wallet
        await update.message.reply_text("Wallet has been created. Address: "+ wallet_address)
        return await self.start(update.message, context)

    async def help_command(self, update: Update, context) -> int:
        """Displays help information."""
        help_text = (
            "Available commands:\n"
            "- Send: Send funds to another address\n"
            "- Receive: View your wallet address and QR code\n"
            "- Check Balance: View your wallet balance\n"
            "- Create Wallet: Create a new wallet\n"
            "- Help: Show this help message"
        )
        await update.callback_query.message.reply_text(help_text)
        return await self.start(update.callback_query.message, context)

    def get_user_wallet(self, user_id: int) -> XrpWalletUtil:
        """Retrieves or creates a wallet for the user."""
        # if user_id not in self.wallets:
        #     self.wallets[user_id] = XrpWalletUtil(user_id)
        return self.wallets.get(user_id)