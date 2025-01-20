import qrcode
from io import BytesIO
from xrpl.wallet import generate_faucet_wallet
from xrpl.clients import JsonRpcClient



class XrpWallet:
    """Handles wallet operations."""

    testnet_url = "https://s.devnet.rippletest.net:51234/"
    #mainnet_url = "https://s1.ripple.com"

    def __init__(self, user_id):
        self.user_id = user_id
        self.balance = 100  # Default balance for testing
        self.wallet_address = None

    async def create_wallet(self, wallet_name: str) -> str:
        """Creates a wallet with a given name."""
        try:
            client = JsonRpcClient(self.testnet_url)  # mainnet change needed
            # Await the coroutine directly
            wallet = await generate_faucet_wallet(client)
            print("Wallet Address:", wallet.classic_address)
            print("Wallet Seed:", wallet.seed)
            self.wallet_address = wallet.classic_address  # Use the classic address from the generated wallet
            return f"Wallet created with address: {self.wallet_address}"
        except Exception as e:
            return f"Error creating wallet: {str(e)}"

    def check_balance(self) -> float:
        """Returns the wallet balance."""
        return self.balance

    def send(self, amount: float, address: str) -> bool:
        """Sends funds to the specified address."""
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False

    def generate_qr_code(self) -> BytesIO:
        """Generates a QR code for the wallet address."""
        qr_image = qrcode.make(self.wallet_address)
        qr_io = BytesIO()
        qr_image.save(qr_io)
        qr_io.seek(0)
        return qr_io