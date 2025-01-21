import asyncio
import xrpl
import requests
from io import BytesIO
import qrcode
from xrpl.wallet import generate_faucet_wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountLines, AccountInfo



class XrpWallet:
    """Handles wallet operations."""

    testnet_url = "https://s.devnet.rippletest.net:51234/"  # Testnet URL

    def __init__(self, user_id):
        self.user_id = user_id
        self.wallet_address = None
        self.wallet_seed = None

    async def create_wallet(self, wallet_name: str) -> str:
        """
        Creates a new XRP wallet.

        Args:
            wallet_name (str): Name for the wallet.

        Returns:
            str: Message with wallet details or error.
        """
        try:
            client = JsonRpcClient(self.testnet_url)
            # Call synchronous generate_faucet_wallet using asyncio.to_thread
            wallet = await asyncio.to_thread(generate_faucet_wallet, client)
            self.wallet_address = wallet.classic_address
            self.wallet_seed = wallet.seed

            # Add test balance by requesting XRP from the faucet
            add_balance_message = await self.add_test_balance(self.wallet_address)

            return (
                f"Wallet '{wallet_name}' created successfully!\n"
                f"Address: {self.wallet_address}\n"
                f"Seed: {self.wallet_seed}"
            )
        except Exception as e:
            return f"Error creating wallet: {str(e)}"

    async def add_test_balance(self, wallet_address: str) -> str:
        """
        Adds test balance to the wallet by requesting XRP from the faucet.

        Args:
            wallet_address (str): Address of the wallet to fund.

        Returns:
            str: Message indicating success or failure.
        """
        try:
            faucet_url = "https://faucet.altnet.rippletest.net/accounts"  # Testnet faucet URL
            # Send a request to the faucet with the wallet address
            response = await asyncio.to_thread(requests.post, faucet_url, json={"address": wallet_address})

            if response.status_code == 200:
                return f"Successfully added XRP to wallet {wallet_address}."
            else:
                return f"Failed to add XRP to wallet. Status code: {response.status_code}, Message: {response.text}"
        except Exception as e:
            return f"Error adding test balance: {str(e)}"

    # def check_balance(self) -> float:
    #     """
    #     Mocked balance check for the wallet.
    #
    #     Returns:
    #         float: The wallet balance.
    #     """
    #     return self.balance
    #
    # def check_balance2(self, account_address, currency="RLUSD"):
    #     """Check balance for a given currency (e.g., RL USD)"""
    #     # Initialize XRPL client (using testnet in this case)
    #     # client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
    #     client = xrpl.clients.JsonRpcClient(self.testnet_url)
    #     # Fetch account lines (this includes the balances for custom currencies)
    #     account_lines = AccountLines(account=account_address)
    #     response = client.request(account_lines)
    #
    #     # Check if the response contains any lines (currencies)
    #     if hasattr(response, 'result') and 'lines' in response.result:
    #         lines = response.result['lines']
    #         for line in lines:
    #             # Check if the line corresponds to RL USD (or the specified currency)
    #             currency_code = self.hex_to_ascii(line["currency"])
    #             if currency_code == currency:
    #                 balance = line["balance"]
    #                 return float(balance)  # Return balance as a float (in RL USD)
    #     else:
    #         print("No currency lines found for this account.")
    #         return 0.0  # No balance found for the specified currency

    def check_balance(self, account_address):
        """Check the balance of XRP in an account (without using AccountLines for custom currencies)"""
        client = xrpl.clients.JsonRpcClient(self.testnet_url)

        # Request account info (this will give the balance of XRP)
        account_info = AccountInfo(account=account_address, ledger_index="validated")
        response = client.request(account_info)

        # Check if the response contains account data
        if hasattr(response, 'result') and 'account_data' in response.result:
            account_data = response.result['account_data']

            # Check if the balance field is in account_data
            if 'Balance' in account_data:
                balance_drops = int(account_data['Balance'])  # Balance is in drops (1 XRP = 1,000,000 drops)
                balance_xrp = balance_drops / 1_000_000  # Convert drops to XRP
                return balance_xrp
            else:
                print("Balance not found in account data.")
                return 0.0  # No balance found for XRP
        else:
            print(f"Error or unexpected response: {response}")
            return 0.0  # No account data or unexpected response

    def send_xrp(self, seed, amount, destination):
        sending_wallet = xrpl.wallet.Wallet.from_seed(seed)
        client = xrpl.clients.JsonRpcClient(self.testnet_url)
        payment = xrpl.models.transactions.Payment(
            account=sending_wallet.address,
            amount=xrpl.utils.xrp_to_drops(int(amount)),
            destination=destination,
        )
        try:
            response = xrpl.transaction.submit_and_wait(payment, client, sending_wallet)
        except xrpl.transaction.XRPLReliableSubmissionException as e:
            response = f"Submit failed: {e}"

        return response

    def generate_qr_code(self) -> BytesIO:
        """
        Generates a QR code for the wallet address.

        Returns:
            BytesIO: In-memory QR code image.
        """
        if not self.wallet_address:
            raise ValueError("Wallet address is not set. Create a wallet first.")
        qr_image = qrcode.make(self.wallet_address)
        qr_io = BytesIO()
        qr_image.save(qr_io)
        qr_io.seek(0)
        return qr_io

    def save_qr_code(self, file_path: str) -> None:
        """
        Saves the QR code for the wallet address to a file.

        Args:
            file_path (str): File path to save the QR code.
        """
        if not self.wallet_address:
            raise ValueError("Wallet address is not set. Create a wallet first.")
        qr_image = qrcode.make(self.wallet_address)
        qr_image.save(file_path)
        print(f"QR code saved to {file_path}")

    @staticmethod
    def hex_to_ascii(hex_str):
        """Convert a hexadecimal string to an ASCII string."""
        byte_array = bytes.fromhex(hex_str)
        return byte_array.decode('utf-8').rstrip('\x00')
