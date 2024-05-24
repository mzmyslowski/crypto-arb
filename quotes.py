import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import time

import pandas as pd

class AsyncQuoter:
    RESERVES_CHANGING_TOPICS = {
        'sync': "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1",
        'swap': "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
        'mint': "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f",
        'burn': "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496"
    }
    
    def __init__(self, w3, decimals, rate_limit, filter_block_identifier, pair_abi_path='abis/IUniswapV2Pair.json', pair_contract_block_identifier='latest') -> None:
        self.w3 = w3
        self.decimals = decimals
        self.rate_limit = rate_limit
        self.filter_block_identifier = filter_block_identifier
        self.reserves_changing_filter = self.w3.eth.filter({
            'fromBlock': self.filter_block_identifier,
            'topics': ['0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1']
        })
        self.pair_abi = json.load(open(pair_abi_path))['abi']
        self.pair_contract_block_identifier = pair_contract_block_identifier

    def fetch_all_reserves(self, pools):
        loop = asyncio.get_event_loop()
        prices = loop.run_until_complete(self.fetch_all_reserves_async(pools))
        return prices
    
    async def fetch_all_reserves_async(self, pools):
        results = []
        for i in range(0, len(pools), self.rate_limit):
            start = asyncio.get_event_loop().time()
            batch = pools[i:i + self.rate_limit]
            tasks = [asyncio.create_task(self._fetch_reserve(*pool[:-1])) for pool in batch]
            results += await asyncio.gather(*tasks)
            execution_time = asyncio.get_event_loop().time() - start
            print(i, execution_time)
            await asyncio.sleep(max(1.1 * (1 - execution_time), 0))
        return results
    
    async def _fetch_reserve(self, pool_address, token0_address, token1_address):
        contract = self.w3.eth.contract(address=pool_address, abi=self.pair_abi)
        reserves = await asyncio.get_event_loop().run_in_executor(None, lambda: contract.functions.getReserves().call(block_identifier=self.pair_contract_block_identifier))
        price_token1_in_token0 = self.get_price_token1_in_token0(
            reserve0=reserves[0], 
            reserve1=reserves[1], 
            token0_address=token0_address, 
            token1_address=token1_address
        )
        return (reserves[0], reserves[1], price_token1_in_token0, self.filter_block_identifier)
    
    def catch_up_with_reserves(self, pools):
        reserves_changing_logs = self.reserves_changing_filter.get_all_entries()
        return self._update_reserves(pools=pools, reserves_changing_logs=reserves_changing_logs)

    def update_reserves(self, pools):
        reserves_changing_logs = self.reserves_changing_filter.get_new_entries()
        return self._update_reserves(pools=pools, reserves_changing_logs=reserves_changing_logs)
    
    def _update_reserves(self, pools, reserves_changing_logs):
        if len(reserves_changing_logs) == 0:
            return 0
        else:
            pools_ = set(pools['Pool'])
            reserves = {}
            latest_identifiers = {}
            for log in reserves_changing_logs:
                if log['address'] not in pools_:
                    continue
                pending_update = latest_identifiers.get(log['address'], {})
                if (
                    log['blockNumber'] > pending_update.get('blockNumber', -1) or 
                    (
                        log['blockNumber'] == pending_update.get('blockNumber', -1) and
                        log['transactionIndex'] > pending_update.get('transactionIndex', -1)
                    )
                    ):
                    token0, token1 = pools[pools['Pool'] == log['address']][['Token 0', 'Token 1']].values[0]
                    reserve0, reserve1 = self.get_reserves_from_log(log)
                    qoute = self.get_price_token1_in_token0(reserve0=reserve0, reserve1=reserve1, token0_address=token0, token1_address=token1)
                    reserves[log['address']] = ((token0, token1, reserve0, reserve1, qoute, log['blockNumber']))
                    latest_identifiers[log['address']] = {
                        'blockNumber': log['blockNumber'],
                        'transactionIndex': log['transactionIndex']
                    }
            reserves_df = pd.DataFrame.from_dict(reserves, orient='index', columns=['Token 0', 'Token 1',' Reserve 0', 'Reserve 1', 'Quote', 'blockNumber'])
            pools.set_index('Pool', inplace=True)
            pools.update(reserves_df)
            pools.reset_index(inplace=True)
            return len(reserves)
        
    
    def get_reserves_from_log(self, log):
        pair_contract = self.w3.eth.contract(abi=self.pair_abi)
        event = pair_contract.events.Sync().process_log(log)
        return (event['args']['reserve0'], event['args']['reserve1'])
    
    def get_price_token1_in_token0(self, reserve0, reserve1, token0_address, token1_address):
        if reserve0 == 0 or reserve1 == 0:
            return 0
        else:
            return (reserve0 / (10 ** int(self.decimals[token0_address]))) / (reserve1 / (10 ** int(self.decimals[token1_address])))


class ConcurrentQuoter:
    PAIR_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "getReserves",
            "outputs": [
                {"internalType": "uint112", "name": "reserve0", "type": "uint112"},
                {"internalType": "uint112", "name": "reserve1", "type": "uint112"},
                {"internalType": "uint32", "name": "blockTimestampLast", "type": "uint32"},
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
    ]
    
    def __init__(self, w3, decimals, rate_limit, max_workers) -> None:
        self.w3 = w3
        self.decimals = decimals
        self.rate_limit = rate_limit
        self.max_workers = max_workers
    
    def fetch_all_reserves(self, pools):
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for i in range(0, len(pools), self.rate_limit):
                start_time = time.time()
                batch = pools[i:i + self.rate_limit]
                batch_results = list(executor.map(lambda x: self.fetch_reserve(*x), batch))
                results.extend(batch_results)
                processing_time = time.time() - start_time
                print(i, processing_time)
                if processing_time < 1:
                    time.sleep(1.1 * (1 - processing_time))
        return results
    
    def fetch_reserve(self, pool_address, token0_address, token1_address):
        pair_contract = self.w3.eth.contract(address=pool_address, abi=self.PAIR_ABI)
        (reserve0, reserve1, price_token1_in_token0) = (None, None, None)
        try:
            reserves = pair_contract.functions.getReserves().call()
            reserve0, reserve1, _ = reserves
            price_token1_in_token0 = (reserve0 / (10 ** int(self.decimals[token0_address]))) / (reserve1 / (10 ** int(self.decimals[token1_address])))
        except Exception as e:
            print(f"Error with pool {pool_address}: {e}")
        return (reserve0, reserve1, price_token1_in_token0)
