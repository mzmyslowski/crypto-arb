import pandas as pd
from graph import Graph

def test_graph_building():
    data = {
        'Token 0': ['A', 'B', 'C'],
        'Token 1': ['B', 'C', 'A'],
        'Quote': [1.2, 0.8, 1.1],
        'Pool': ['Pool1', 'Pool2', 'Pool3'],
        'Reserve 0': [100, 200, 300],
        'Reserve 1': [120, 160, 330],
        'Exchange': ['Ex1', 'Ex2', 'Ex3']
    }
    df = pd.DataFrame(data)
    graph = Graph()
    g = graph.build_graph(df)

    assert len(g.nodes()) == 3, "Graph should have 3 nodes"
    assert len(g.edges()) == 6, "Graph should have 6 edges considering bidirectionality"
    assert g.has_edge('A', 'B'), "Graph should contain an edge from A to B"
    assert g.has_edge('B', 'A'), "Graph should contain an edge from B to A"

def test_three_pools_one_exchange_arb():
    data = {
        'Token 0': ['A', 'B', 'C'],
        'Token 1': ['B', 'C', 'A'],
        'Quote': [1.1, 1.1, 0.9], 
        'Pool': ['Pool1', 'Pool2', 'Pool3'],
        'Reserve 0': [100, 200, 300],
        'Reserve 1': [110, 220, 270],
        'Exchange': ['Ex1', 'Ex1', 'Ex1']
    }
    df = pd.DataFrame(data)
    graph = Graph()
    g = graph.build_graph(df)
    cycles = graph.get_negative_cycles('A')

    #0.9 * 1.1 * 1.1 = 1.089
    expected_cycle = [('A', 'C', 'Pool3'), ('C', 'B', 'Pool2'), ('B', 'A', 'Pool1')]
    assert cycles[0] == expected_cycle, "Detected cycle does not match the expected cycle"

def test_two_pools_arb_with_many_tokens():
    data = {
        'Token 0': ['A', 'B', 'B', 'C', 'C', 'D'],
        'Token 1': ['B', 'C', 'A', 'D', 'B', 'A'],
        'Quote': [1.2, 1.2, 0.9, 1.2, 0.9, 0.75], 
        'Pool': ['Pool1', 'Pool2', 'Pool3', 'Pool4', 'Pool5', 'Pool6'],
        'Reserve 0': [100, 200, 200, 300, 300, 400],
        'Reserve 1': [120, 240, 180, 360, 270, 300],
        'Exchange': ['Ex1', 'Ex2', 'Ex3', 'Ex4', 'Ex5', 'Ex6']
    }
    df = pd.DataFrame(data)
    graph = Graph()
    g = graph.build_graph(df)
    cycles = graph.get_negative_cycles('A')

    # 0.9 * 1.2 = 1.08
    expected_cycles = [[('A', 'B', 'Pool3'), ('B', 'A', 'Pool1')]]

    # Convert cycles to sets for comparison to ignore order
    assert cycles == expected_cycles, "Detected cycles do not match the expected cycles"

def two_two_pools_two_exchanges_arb():
    data = {
        'Token 0': ['A', 'B'],
        'Token 1': ['B', 'A'],
        'Quote': [1.2, 0.9], 
        'Pool': ['Pool1', 'Pool2'],
        'Reserve 0': [100, 200],
        'Reserve 1': [120, 180],
        'Exchange': ['Ex1', 'Ex2']
    }
    df = pd.DataFrame(data)
    graph = Graph()
    g = graph.build_graph(df)
    cycles = graph.get_negative_cycles('A')

    # 0.9 * 1.2 = 1.08
    expected_cycles = [[('A', 'B', 'Pool2'), ('B', 'A', 'Pool1')]]

    # Convert cycles to sets for comparison to ignore order

    assert cycles == expected_cycles, "Detected cycles do not match the expected cycles"

def test_two_pools_arb_w_same_token0_and_token1():
    # This is an arbitrage from the tx 0x8a70d6db0aa24622ff751484e641c364358c0ab7d6b1bc67b7886e98dd810e57
    data = {
        'Token 0': ['0x91Af0fBB28ABA7E31403Cb457106Ce79397FD4E6', '0x91Af0fBB28ABA7E31403Cb457106Ce79397FD4E6'],
        'Token 1': ['0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'],
        'Quote': [21421.536494150692, 21318.65227427863], 
        'Pool': ['0x9E48FaDf799E0513d2EF4631478ea186741fA617', '0x505a152C24B03A666E903aA6159e5F9433094893'],
        'Reserve 0': [38056942739665874911653, 48546840265250650917],
        'Reserve 1': [1776573904960440161, 2277200248902383],
        'Exchange': ['sushiswapV2', 'uniswapv2']
    }
    df = pd.DataFrame(data)
    graph = Graph()
    g = graph.build_graph(df)
    cycles = graph.get_negative_cycles('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')

    # Due to shortcomings of the current implementation of Bellman-Ford algorithm,
    # only the arbitrage AERGO -> ETH -> AERGO (Uniswap -> SushiSwap -> Uniswap)
    # is returned but the tx 0x8a70d6db0aa24622ff751484e641c364358c0ab7d6b1bc67b7886e98dd810e57
    # contained the arbitrage ETH -> AERGO -> ETH (SushiSwap -> Uniswap -> SushiSwap).
    expected_cycles = [
            [
                ('0x91Af0fBB28ABA7E31403Cb457106Ce79397FD4E6', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '0x505a152C24B03A666E903aA6159e5F9433094893'),
                ('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '0x91Af0fBB28ABA7E31403Cb457106Ce79397FD4E6', '0x9E48FaDf799E0513d2EF4631478ea186741fA617')
            ]
         ]

    arb = graph.calculate_arb(cycles[0])

    assert cycles == expected_cycles, "Detected cycles do not match the expected cycles"
    assert round(arb, 10) == round(1 / 21318.65227427863 * 21421.536494150692 - 1, 10), "Profit percentage of detected cycle do no match the expected profit"

def test_no_arb_without_fees():
    data = {
        'Token 0': ['A', 'B', 'C'],
        'Token 1': ['B', 'C', 'A'],
        'Quote': [1.0, 1.0, 1.0], 
        'Pool': ['Pool1', 'Pool2', 'Pool3'],
        'Reserve 0': [100, 200, 300],
        'Reserve 1': [100, 200, 300],
        'Exchange': ['Ex1', 'Ex2', 'Ex3']
    }
    df = pd.DataFrame(data)
    graph = Graph()
    g = graph.build_graph(df)
    cycles = graph.get_negative_cycles('A')

    assert len(cycles) == 0, "There should be no negative cycles"

def test_arbitrage_calculation():
    data = {
        'Token 0': ['A', 'B', 'C', 'A'],
        'Token 1': ['B', 'C', 'A', 'B'],
        'Quote': [1.1, 1.1, 0.9, 1.1],
        'Pool': ['Pool1', 'Pool2', 'Pool3', 'Pool4'],
        'Reserve 0': [100, 200, 300, 400],
        'Reserve 1': [110, 220, 270, 440],
        'Exchange': ['Ex1', 'Ex2', 'Ex3', 'Ex4']
    }
    df = pd.DataFrame(data)
    graph = Graph()
    g = graph.build_graph(df)
    cycles = graph.get_negative_cycles('A')

    # Assuming there's a known negative cycle for testing
    if cycles:
        arb = graph.calculate_arb(cycles[0])
        assert arb > 0, "Arbitrage calculation should return a positive value indicating profit"