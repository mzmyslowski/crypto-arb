import requests

class ABI:
    def get_contract_abi(contract_address, etherscan_api_key):
        url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={etherscan_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == '1':
                return data['result']
            else:
                return f"Error fetching ABI: {data['message']}"
        else:
            return "Failed to fetch data from Etherscan"