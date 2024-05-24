from datetime import datetime
import json
from typing import Dict

class ArbLogs:
    def __init__(self, logs_path) -> None:
        self.logs_path = logs_path
        self._database = None

    @property
    def database(self):
        if self._database is None:
            self._database = open(self.logs_path, mode='a')
        return self._database
    
    def add_arb_log(self, block_num, path, pools, exchanges, reserves, amount_in, approx_amount_out, real_amount_out) -> Dict:
        log = {
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Block number': block_num,
            'Pools': pools,
            'Exchanges': exchanges,
            'Path': path,
            'Reserves': reserves,
            'Amount in': amount_in,
            'Approx amount out': approx_amount_out,
            'Real amount out': real_amount_out
        }
        self.add_log(log=log)
        return log

    def add_log(self, log) -> None:
        json.dump(log, self.database, indent=4)
