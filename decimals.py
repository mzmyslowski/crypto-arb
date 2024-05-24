class Decimals:
    TOKEN_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
    ]

    def __init__(self, w3) -> None:
        self.w3 = w3

    def get_decimal(self, token_address):
        token_contract = self.w3.eth.contract(address=token_address, abi=self.TOKEN_ABI)
        token_decimals = token_contract.functions.decimals().call()
        return token_decimals