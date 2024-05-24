from collections import defaultdict
import math
import networkx as nx
import numpy as np
from typing import List, Dict, Tuple

class Graph:
    def build_graph(self, pools) -> nx.MultiDiGraph:
        self.g = nx.MultiDiGraph()
        for _, row in pools.iterrows():
            if row['Quote']:
                # reserve0 and reserve1 should be called 
                # reserveIn and reserveOut respectively
                # to not confuse them with the 
                # ordering of the parameters in the pool.
                self.g.add_edge(
                    row['Token 1'],
                    row['Token 0'],
                    key=row['Pool'],  
                    weight=-np.log(float(row['Quote'])),
                    reserve0=int(row['Reserve 1']),
                    reserve1=int(row['Reserve 0']),
                    exchange=row['Exchange']
                )
                self.g.add_edge(
                    row['Token 0'],
                    row['Token 1'],
                    key=row['Pool'],  
                    weight=np.log(float(row['Quote'])),
                    reserve0=int(row['Reserve 0']),
                    reserve1=int(row['Reserve 1']),
                    exchange=row['Exchange']
                )
        return self.g

    def get_negative_cycles(self, source) -> List[List[Tuple]]:
        n = len(self.g.nodes())
        distance = defaultdict(lambda: math.inf)
        predecessor = {}  
        distance[source] = 0

        for _ in range(n - 1):
            for u, v, key in self.g.edges(keys=True):
                weight = self.g[u][v][key]['weight']
                if distance[u] + weight < distance[v]:
                    distance[v] = distance[u] + weight
                    predecessor[v] = (u, key)

        all_cycles = []
        seen = set()
        for u, v, key in self.g.edges(keys=True):
            weight = self.g[u][v][key]['weight']
            if distance[u] + weight < distance[v]:
                if v in seen or not predecessor.get(v):
                    continue
                cycle = []
                x = v
                while True:
                    seen.add(x)
                    pred, edge_key = predecessor[x]
                    cycle.append((pred, x, edge_key))  
                    x = pred                    
                    if x == v or next((True for el in cycle if x == el[1]), False):  
                        break 
                start_idx = next((i for i, el in enumerate(cycle) if x == el[1]), None)
                
                cycle = cycle[start_idx:]
                cycle.reverse()  
                if cycle not in all_cycles:
                    all_cycles.append(cycle)
        return all_cycles

    def calculate_arb(self, cycle: List[Tuple]) -> float:
        total = 0
        for u, v, key in cycle:
            total += self.g[u][v][key]["weight"]
        arb = np.exp(-total) - 1
        return arb

    def is_arb(self) -> bool:
        return nx.negative_edge_cycle(self.g)
