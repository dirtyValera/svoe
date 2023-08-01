import uuid
from typing import Dict, List, Optional, Any

from ray.air import Checkpoint
from ray.train.rl import RLPredictor
from ray.train.sklearn import SklearnPredictor
from ray.train.torch import TorchPredictor
from ray.train.xgboost import XGBoostPredictor

from simulation.models.instrument import Instrument
from simulation.models.order import Order, OrderSide, OrderType, OrderStatus
from simulation.models.portfolio import Portfolio
from utils.time.utils import convert_str_to_seconds


class BaseStrategy:

    def __init__(self, portfolio: Portfolio, predictor_config: Dict):
        self.portfolio = portfolio
        self.prediction_latency = predictor_config['prediction_latency']
        self.predictor = self._predictor(predictor_config)
        self.latest_prediction = None
        self.latest_prediction_ts = None

    def _predictor(self, predictor_config: Dict):
        model_type = predictor_config['model_type']
        checkpoint_uri = predictor_config['checkpoint_uri']
        checkpoint = Checkpoint.from_uri(checkpoint_uri)
        # TODO enum this
        if model_type == 'xgboost':
            predictor = XGBoostPredictor.from_checkpoint(checkpoint)
        elif model_type == 'torch':
            predictor = TorchPredictor.from_checkpoint(checkpoint)
        elif model_type == 'sklearn':
            predictor = SklearnPredictor.from_checkpoint(checkpoint)
        elif model_type == 'rl':
            predictor = RLPredictor.from_checkpoint(checkpoint)
        else:
            raise ValueError(f'Unknown model type: {model_type}')

        return predictor

    def _event_to_predictor_request(self, event: Any) -> Any:
        return None # TODO

    def on_data(self, data_event: Dict) -> Optional[List[Order]]:
        ts = data_event['timestamp']
        if self.latest_prediction_ts is None or \
                ts - self.latest_prediction_ts > convert_str_to_seconds(self.prediction_latency):
            req = self._event_to_predictor_request(data_event)
            self.latest_prediction = self.predictor.predict(req)
            self.latest_prediction_ts = ts
        return self.on_data_udf(data_event)

    def on_data_udf(self, data_event: Dict) -> Optional[List[Order]]:
        raise NotImplementedError

    def make_order(self, side: OrderSide, type: OrderType, instrument: Instrument, qty: float, price: float) -> Order:
        order_id = str(uuid.uuid4())
        # lock quantities
        base_instr, quote_instr = instrument.to_asset_instruments()
        base_wallet = self.portfolio.get_wallet(base_instr)
        quote_wallet = self.portfolio.get_wallet(quote_instr)
        # qty is base_qty
        if side == OrderSide.BUY:
            # we lock quote
            qoute_qty = price * qty
            quote_wallet.lock_from_balance(order_id=order_id, qty=qoute_qty)
        else:
            base_wallet.lock_from_balance(order_id=order_id, qty=qty)

        return Order(
            order_id=order_id,
            type=type,
            side=side,
            instrument=instrument,
            price=price,
            quantity=qty,
            status=OrderStatus.OPEN
        )
