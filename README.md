# Arbitrage Trading Bot

This repository contains a Python-based arbitrage trading bot that interacts with Uniswap v2 based decentralized exchanges (DEXs) to identify and exploit arbitrage opportunities.

## Features

- **Blockchain Interaction**: Connects to the Ethereum blockchain using Web3.
- **Pool Initialization**: Fetches and stores initial reserves for liquidity pools.
- **Real-Time Updates**: Continuously updates pool reserves and identifies arbitrage opportunities.
- **Arbitrage Execution**: Calculates optimal trade amounts and executes arbitrage trades.

## Requirements

- Python 3.8+
- An Ethereum node provider (e.g., Infura)
- Environment variables for configuration

## Installation

1. **Clone the repository**:
   ```sh
   git clone git@github.com:mzmyslowski/crypto-arb.git
   cd crypto-arb
   ```

2. **Install dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root and add the following variables:
   ```env
   WEB3_PROVIDER_URL=<your_ethereum_node_provider_url>
   UNISWAP_ROUTER02=<uniswap_router_address>
   SUSHISWAP_ROUTER02=<sushiswap_router_address>
   WETH=<weth_token_address>
   UNISWAP_ROUTER_ABI_PATH=<path_to_uniswap_router_abi_json>
   POOLS_PATH=<path_to_pools_csv>
   DECIMALS_PATH=<path_to_decimals_json>
   POOLS_RESERVES_PATH=<path_to_pools_reserves_csv>
   LOGS_PATH=<path_to_logs_directory>
   ```

4. **Prepare required files**:
   Ensure you have the necessary JSON and CSV files specified in your environment variables.

## Usage

1. **Initialize Pool Reserves**:
   To initialize pool reserves, run the script with the `init_pools` parameter set to `True`:
   ```sh
   python main.py True
   ```

2. **Start Arbitrage Bot**:
   To start the bot without initializing pool reserves:
   ```sh
   python main.py False
   ```

## Code Overview

- **Imports and Configuration**: The script imports necessary libraries, loads environment variables, and sets up constants.
- **Main Function**:
  - Connects to the Ethereum blockchain.
  - Loads router ABI and contract instances for Uniswap and Sushiswap.
  - Initializes or updates pool reserves.
  - Continuously monitors and updates reserves, and identifies arbitrage opportunities.
- **Arbitrage Execution**:
  - Builds a graph from the pool data.
  - Identifies negative cycles indicating potential arbitrage.
  - Calculates optimal input amounts and expected outputs.
  - Executes trades and logs results.

## Logging

The bot logs arbitrage opportunities and trade details into a specified directory, with each log file named by the timestamp of its creation.

## Contributing

Contributions are welcome! Please create a pull request or submit an issue for any improvements or bug fixes.

## License

This project is licensed under the MIT License. 

## Contact

For any inquiries or issues, please contact [schizoburger@gmail.com](mailto:schizoburger@gmail.com).

---

*Happy Trading!*

---

Note: Ensure you have appropriate permissions and security measures in place when deploying and using the bot on a live network.
