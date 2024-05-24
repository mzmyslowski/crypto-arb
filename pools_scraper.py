import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd

with open('sushi.html', 'r') as f:
    bs = BeautifulSoup(f, 'html.parser')
pools = bs.find_all('a', {'class': 'flex items-center text-sm font-medium p-4 align-middle [&:has([role=checkbox])]:pr-0'})
pools = set([link.get('href') for link in pools])
pools_addresses = []
for pool in tqdm(pools):
    resp = requests.get(pool)
    if not resp.ok:
        break
    bs = BeautifulSoup(resp.content, 'html.parser')
    addresses = bs.find_all('a', class_='cursor-pointer text-blue hover:underline')
    pools_addresses.append([link.get('href').split('/')[-1] for link in addresses])
df = pd.DataFrame(pools_addresses, columns=['Pool', 'Token 0', 'Token 1'])
df.to_csv('sushiswap_pools.csv', index=False)
