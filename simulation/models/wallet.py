from typing import Dict

from simulation.models.instrument import Instrument


# TODO add Ledger class to keep track of all executed Trade instances
class Wallet:
    instrument: Instrument
    balance: float
    locked: Dict[str, float] = {}