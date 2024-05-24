import numpy as np

class UniswapV2Sizing:
    FEE = 0.003
    def get_optimal_input(self, path, graph) -> float:
        e0 = graph[path[0][0]][path[0][1]][path[0][2]]['reserve0']
        e1 = graph[path[0][0]][path[0][1]][path[0][2]]['reserve1']
        for i in range(1, len(path)):
            r1_prime = graph[path[i][0]][path[i][1]][path[i][2]]['reserve0']
            r2 = graph[path[i][0]][path[i][1]][path[i][2]]['reserve1']
            e0, e1 = self._get_reserves_for_virtual_pool(e0, e1, r1_prime, r2, self.FEE)
        optimal_amount_in = int((np.sqrt(e0 * e1 * (1 - self.FEE)) - e0) / (1 - self.FEE))
        return optimal_amount_in, e0, e1
    
    def _get_reserves_for_virtual_pool(self, r0, r1, r1_prime, r2, fee):
        """
        Returns reserves e0, e1 of A and C respectively for the virtual pool A->C constructed
        from the 2 pools A->B and B->C with the reserves of each token 
        in the first one given by r0, r1 and r1_prime, r2 
        in the second one.
        """
        fee = 1 - fee
        e0 = (r0 * r1_prime) / (r1_prime + r1 * fee)
        e1 = (fee * r1 * r2) / (r1_prime + r1 * fee)
        return e0, e1
    
    def get_approximated_amount_out(self, amount_in, e0, e1):
        # Implementation from https://github.com/Uniswap/v2-periphery/blob/0335e8f7e1bd1e8d8329fd300aea2ef2f36dd19f/contracts/libraries/UniswapV2Library.sol#L43C14-L43C26
        amount_in_with_fee = amount_in * 997
        numerator = amount_in_with_fee * e1
        denominator = e0 * 1000 + amount_in_with_fee
        return numerator / denominator
    
    def get_real_amount_out(self, amount_in, path, graph, uniswap_router, sushiswap_router):
        last_exchange = graph[path[0][0]][path[0][1]][path[0][2]]['exchange']
        temp_path = [path[0][0], path[0][1]]
        amount_in_ = amount_in
        for i in range(1, len(path)):
            exchange = graph[path[i][0]][path[i][1]][path[i][2]]['exchange']
            if last_exchange == exchange:
                temp_path.append(path[i][1])
            else:
                if last_exchange == 'uniswapV2':
                    router = uniswap_router
                else:
                    router = sushiswap_router
                amount_in_ = router.functions.getAmountsOut(
                                amount_in_,
                                temp_path
                            ).call()[-1] 
                last_exchange = exchange
                temp_path = [path[i][0], path[i][1]]
        if last_exchange == 'uniswapV2':
            router = uniswap_router
        else:
            router = sushiswap_router       
        amount_in_ = router.functions.getAmountsOut(
                        amount_in_,
                        temp_path
                    ).call()[-1] 
        return amount_in_