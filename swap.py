from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
import os
import requests

load_dotenv(override=True)

# Configuration
WEB3_URL = os.environ['WEB3_LOCAL_NODE']
WALLET_ADDRESS = os.environ['MY_ADDRESS_LOCAL']
WALLET_PRIVATE_KEY = os.environ['PRIVATE_KEY_LOCAL']
ROUTER_ADDRESS = os.environ['SUSHISWAP_ROUTER02']
PATH = ['0x46e98FFE40E408bA6412bEb670507e083C8B95ff', '0x3f5294DF68F871241c4B18fcF78ebD8Ac18aB654', '0x1C9922314ED1415c95b9FD453c3818fd41867d0B', '0x46e98FFE40E408bA6412bEb670507e083C8B95ff']
AMOUNT_IN = int(10**18) 

# Setup Web3
w3 = Web3(Web3.HTTPProvider(WEB3_URL))

# Ensure connected to Ethereum network
if w3.is_connected():
    print("Connected to Ethereum network")
else:
    print("Failed to connect to Ethereum network")
    exit(1)

def get_contract_abi(contract_address):
    url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={os.environ['ETHERSCAN_API_KEY']}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            return data['result']
        else:
            return f"Error fetching ABI: {data['message']}"
    else:
        return "Failed to fetch data from Etherscan"

# Load Uniswap V3 Router contract
router_abi = get_contract_abi(ROUTER_ADDRESS)
uniswap_router = w3.eth.contract(address=ROUTER_ADDRESS, abi=router_abi)
token_abi = get_contract_abi(PATH[0])
token_contract = w3.eth.contract(address=PATH[0], abi=token_abi)
balance = token_contract.functions.balanceOf(WALLET_ADDRESS).call()
AMOUNT_IN = balance
print(balance)
amount_out_min = 0

swap_tx = uniswap_router.functions.swapExactTokensForTokens(
    AMOUNT_IN,
    amount_out_min,
    PATH,  # Path: DAFFY -> BUGS
    WALLET_ADDRESS,
    int(w3.eth.get_block('latest')['timestamp']) + 10 * 60  # Deadline
).build_transaction({
    'from': WALLET_ADDRESS,
    'gas': 1000000,  # Adjust based on the required gas
    'nonce': w3.eth.get_transaction_count(WALLET_ADDRESS)  # Increment nonce after approval
})


# Sign the transaction
signed_tx = w3.eth.account.sign_transaction(swap_tx, WALLET_PRIVATE_KEY)

# Send the transaction
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

# Wait for the transaction receipt
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"Transaction successful with hash: {tx_receipt.transactionHash.hex()}")
print(token_contract.functions.balanceOf(WALLET_ADDRESS).call())