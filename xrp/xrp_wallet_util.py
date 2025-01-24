import asyncio
import xrpl
import requests
from io import BytesIO
import qrcode
from xrpl.wallet import generate_faucet_wallet
from xrpl.clients import JsonRpcClient
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models.requests import AccountLines, AccountInfo


class XrpWalletUtil:
    """Handles wallet operations."""

    testnet_url = "https://s.devnet.rippletest.net:51234/"  # Testnet URL

    async def create_wallet(self) -> dict:
        try:
            client = JsonRpcClient(self.testnet_url)
            # Call synchronous generate_faucet_wallet using asyncio.to_thread
            wallet = await asyncio.to_thread(generate_faucet_wallet, client)
            wallet_address = wallet.classic_address
            wallet_seed = wallet.seed

            # Add test balance by requesting XRP from the faucet
            add_balance_message = await self.add_test_balance(wallet_address)
            # add_balance_message = await self.add_test_balance(self.wallet_address)
            # add_rlusd_message = await self.add_rlusd_trust_line(wallet_address, wallet_seed)

            wallet_details = {
                "wallet_address": wallet.classic_address,
                "wallet_seed": wallet.seed,
            }

            return wallet_details
        except Exception as e:
            print("Error creating wallet: {str(e)}")

    async def add_test_balance(self, wallet_address: str) -> str:
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

    async def add_rlusd_trust_line(self, wallet_address: str, wallet_seed: str):
        client = xrpl.clients.JsonRpcClient(self.testnet_url)

        rlusd_issuer = "https://faucet.altnet.rippletest.net/accounts"  # TODO: Ask discord dev

        trust_set_tx = xrpl.models.transactions.TrustSet(
            account=wallet_address,
            limit_amount=xrpl.models.amounts.IssuedCurrencyAmount(
                currency="RLUSD",
                issuer=rlusd_issuer,
                value="1000"  # Trust limit
            )
        )

        wallet = xrpl.wallet.Wallet(address=wallet_address, seed=wallet_seed)

        try:
            response = xrpl.transaction.submit_and_wait(
                trust_set_tx, client, wallet)
            return f"RLUSD trust line created: {response}"
        except Exception as e:
            return f"Trust line creation failed: {str(e)}"

    async def send_xrp(self, seed, amount, destination):
        sending_wallet = xrpl.wallet.Wallet.from_seed(seed)
        # client = xrpl.clients.JsonRpcClient(self.testnet_url)
        client = xrpl.asyncio.clients.AsyncJsonRpcClient(self.testnet_url)
        payment = xrpl.models.transactions.Payment(
            account=sending_wallet.address,
            amount=xrpl.utils.xrp_to_drops(int(amount)),
            destination=destination,
        )
        try:
            response = await xrpl.asyncio.transaction.submit_and_wait(payment, client, sending_wallet)
        except xrpl.transaction.XRPLReliableSubmissionException as e:
            response = f"Submit failed: {e}"

        return response

    async def check_balance(self, account_address):
        """Check the balance of XRP in an account (without using AccountLines for custom currencies)
        TODO: check how to add RLUSD """
        # client = xrpl.clients.JsonRpcClient(self.testnet_url)
        client = xrpl.asyncio.clients.AsyncJsonRpcClient(self.testnet_url)

        # Request account info (this will give the balance of XRP)
        account_info = AccountInfo(
            account=account_address, ledger_index="validated")
        response = await client.request(account_info)

        # Check if the response contains account data
        if hasattr(response, 'result') and 'account_data' in response.result:
            account_data = response.result['account_data']

            # Check if the balance field is in account_data
            if 'Balance' in account_data:
                # Balance is in drops (1 XRP = 1,000,000 drops)
                balance_drops = int(account_data['Balance'])
                balance_xrp = balance_drops / 1_000_000  # Convert drops to XRP
                return balance_xrp
            else:
                print("Balance not found in account data.")
                return 0.0  # No balance found for XRP
        else:
            print(f"Error or unexpected response: {response}")
            return 0.0  # No account data or unexpected response

    def generate_qr_code(self, wallet_address) -> BytesIO:
        """
        Generates a QR code for the wallet address.

        Returns:
            BytesIO: In-memory QR code image.
        """
        if not wallet_address:
            raise ValueError(
                "Wallet address is not set. Create a wallet first.")
        qr_image = qrcode.make(wallet_address)
        qr_io = BytesIO()
        qr_image.save(qr_io)
        qr_io.seek(0)
        return qr_io

    @staticmethod
    def hex_to_ascii(hex_str):
        """Convert a hexadecimal string to an ASCII string."""
        byte_array = bytes.fromhex(hex_str)
        return byte_array.decode('utf-8').rstrip('\x00')
