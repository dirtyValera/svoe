from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple


@dataclass
class TimestampedBase:
    timestamp: float
    receipt_timestamp: float


# common data source events
@dataclass
class L2BookDelta(TimestampedBase):
    delta: bool  # indicates whether this is delta or full snapshot
    orders: List[Tuple[str, float, float]]  # side, price, size


@dataclass
class Trade(TimestampedBase):
    side: str  # 'sell' or 'buy'
    amount: float
    price: float
    id: Optional[str]
    type: Optional[str]