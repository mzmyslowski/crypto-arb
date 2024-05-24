from datetime import datetime
import json
import os
import time

from dotenv import load_dotenv
import pandas as pd
from web3 import Web3
from web3.exceptions import ContractLogicError

from arb_logs import ArbLogs
from graph import Graph
from sizing import UniswapV2Sizing
from quotes import AsyncQuoter

load_dotenv(override=True)

WEB3_URL = os.environ['WEB3_PROVIDER_URL']

SUSHISWAP_V2_FEE = 0.003
RATE_LIMIT = 10

UNISWAP_ROUTER_ADDRESS = os.environ['UNISWAP_ROUTER02']
SUSHISWAP_ROUTER_ADDRESS = os.environ['SUSHISWAP_ROUTER02']
WETH_ADDRESS = os.environ['WETH']

UNISWAP_ROUTER_ABI_PATH = os.environ['UNISWAP_ROUTER_ABI_PATH']
POOLS_PATH = os.environ['POOLS_PATH']
DECIMALS_PATH = os.environ['DECIMALS_PATH']
POOLS_RESERVES_PATH = os.environ['POOLS_RESERVES_PATH']
LOGS_PATH = os.environ['LOGS_PATH']

def main(init_pools):
    w3 = Web3(Web3.HTTPProvider(WEB3_URL))

    router_abi = json.load(open(UNISWAP_ROUTER_ABI_PATH))['abi']
    uniswap_router = w3.eth.contract(address=UNISWAP_ROUTER_ADDRESS, abi=router_abi)
    sushiswap_router = w3.eth.contract(address=SUSHISWAP_ROUTER_ADDRESS, abi=router_abi)

    with open(DECIMALS_PATH, 'r') as f:
        decimals = json.load(f)

    if init_pools:
        block_num = w3.eth.get_block('latest')['number']
        print(block_num)
        quoter = AsyncQuoter(
            w3=w3, 
            decimals=decimals, 
            rate_limit=RATE_LIMIT, 
            filter_block_identifier=block_num
        )   
        pools = pd.read_csv(POOLS_PATH)
        prices = quoter.fetch_all_reserves(pools.values)
        pools[['Reserve 0', 'Reserve 1', 'Quote', 'blockNumber']] = prices
        pools.to_csv(POOLS_RESERVES_PATH, index=False)
    else:
        pools = pd.read_csv(POOLS_RESERVES_PATH)
        block_num = int(max(pools['blockNumber']))
        print(block_num)
        quoter = AsyncQuoter(
            w3=w3, 
            decimals=decimals, 
            rate_limit=RATE_LIMIT, 
            filter_block_identifier=block_num
        )
        n_pools_updated = quoter.catch_up_with_reserves(pools=pools)
        print(f'Caught up with {n_pools_updated} pools.')
        pools.to_csv(POOLS_RESERVES_PATH, index=False)
    
    logs = ArbLogs(logs_path=os.path.join(LOGS_PATH, datetime.now().strftime("log_%Y-%m-%d_%H-%M-%S")))

    is_first_iteration = True
    
    while True:
        n_pools_updated = quoter.update_reserves(pools=pools)
        if is_first_iteration or n_pools_updated > 0:
            if is_first_iteration:
                is_first_iteration = False
            start = time.time()
            block_num = int(pools['blockNumber'].max())
            pools.to_csv(POOLS_RESERVES_PATH, index=False)
            print(block_num)
            print(f'Updated {n_pools_updated} pools.')
            
            graph = Graph()
            g = graph.build_graph(pools=pools)
            if graph.is_arb():
                print('Arb exists')
                sizing = UniswapV2Sizing()
                cycles = graph.get_negative_cycles(source=WETH_ADDRESS)
                for cycle in cycles:
                    optimal_amount_in, e0, e1 = sizing.get_optimal_input(path=cycle, graph=g)
                    if optimal_amount_in > 0:
                        approx_amount_out = sizing.get_approximated_amount_out(amount_in=optimal_amount_in, e0=e0, e1=e1)
                        amount_out = 0
                        decimal = int(decimals[cycle[0][0]])
                        try: 
                            amount_out = sizing.get_real_amount_out(
                                amount_in=optimal_amount_in,
                                path=cycle,
                                graph=g,
                                uniswap_router=uniswap_router,
                                sushiswap_router=sushiswap_router
                            )
                        except ContractLogicError as e:
                            print(e)
                        logs.add_arb_log(
                            block_num=block_num,
                            path=cycle,
                            pools=[x[2] for x in cycle],
                            exchanges=[g[x[0]][x[1]][x[2]]['exchange'] for x in cycle],
                            reserves=[(g[x[0]][x[1]][x[2]]['reserve0'], g[x[0]][x[1]][x[2]]['reserve1']) for x in cycle],
                            amount_in=optimal_amount_in / (10 ** decimal),
                            approx_amount_out=approx_amount_out / (10 ** decimal),
                            real_amount_out=amount_out / (10 ** decimal)
                        )
                        print(
                            'Cycle', cycle, '\n',
                            'Amount in:', optimal_amount_in / (10 ** decimal), '\n',
                            'Approx amount out', approx_amount_out / (10 ** decimal), '\n',
                            'Amount out', amount_out / (10 ** decimal), '\n',
                        )
                print(f'Execution time: {(time.time() - start)}s')
            else:
                time.sleep(1)
    

if __name__ == "__main__":
    main(init_pools=False)