import calculator as C
from featurizer.features.data.l2_book_delats.l2_book_deltas import L2BookDeltasData
from featurizer.features.definitions.l2_book_snapshot.l2_book_snapshot_feature_definition import \
    L2BookSnapshotFeatureDefinition
from featurizer.features.definitions.mid_price.mid_price_feature_definition import MidPriceFeatureDefinition
from featurizer.features.definitions.feature_definition import NamedFeature, FeatureDefinition
from featurizer.features.blocks.blocks import BlockMeta, BlockRange, Block, BlockRangeMeta
import portion as P
import unittest
import dask
import pandas as pd
from typing import Dict, Type, Tuple
from featurizer.features.loader.l2_snapshot_utils import get_info
from featurizer.features.loader.df_utils import load_files


class TestFeatureCalculator(unittest.TestCase):

    def test_get_ranges_overlaps(self):
        grouped_range = {}
        ranges_a = P.IntervalDict()
        ranges_a[P.closed(1, 4)] = [self.meta(1, 2), self.meta(2.1, 5)]
        ranges_a[P.closed(4.1, 8)] = [self.meta(5, 5.5), self.meta(6, 7)]
        ranges_a[P.closed(9, 15)] = [self.meta(9, 15)]
        grouped_range[self.mock_named_feature('feature_a')] = ranges_a

        ranges_b = P.IntervalDict()
        ranges_b[P.closed(2, 5)] = [self.meta(2, 3), self.meta(3.1, 6)]
        ranges_b[P.closed(6, 7)] = [self.meta(6, 7)]
        ranges_b[P.closed(9, 20)] = [self.meta(9, 15), self.meta(15.1, 18), self.meta(18.1, 22)]
        grouped_range[self.mock_named_feature('feature_b')] = ranges_b

        expected = P.IntervalDict()
        expected[P.closed(2, 4)] = {
            self.mock_named_feature('feature_a'): [{'start_ts': 1, 'end_ts': 2}, {'start_ts': 2.1, 'end_ts': 5}],
            self.mock_named_feature('feature_b'): [{'start_ts': 2, 'end_ts': 3}, {'start_ts': 3.1, 'end_ts': 6}]
        }
        expected[P.closed(4.1, 5)] = {
            self.mock_named_feature('feature_a'): [{'start_ts': 5, 'end_ts': 5.5}, {'start_ts': 6, 'end_ts': 7}],
            self.mock_named_feature('feature_b'): [{'start_ts': 2, 'end_ts': 3}, {'start_ts': 3.1, 'end_ts': 6}]
        }
        expected[P.closed(6, 7)] = {
            self.mock_named_feature('feature_a'): [{'start_ts': 5, 'end_ts': 5.5}, {'start_ts': 6, 'end_ts': 7}],
            self.mock_named_feature('feature_b'): [{'start_ts': 6, 'end_ts': 7}]
        }
        expected[P.closed(9, 15)] = {
            self.mock_named_feature('feature_a'): [{'start_ts': 9, 'end_ts': 15}],
            self.mock_named_feature('feature_b'): [{'start_ts': 9, 'end_ts': 15}, {'start_ts': 15.1, 'end_ts': 18},
                          {'start_ts': 18.1, 'end_ts': 22}]
        }

        overlaps = C.get_ranges_overlaps(grouped_range)
        self.assertEqual(overlaps, expected)

    def mock_named_feature(self, feature_name: str):
        return feature_name, Type[FeatureDefinition]

    def meta(self, start_ts, end_ts, extra=None):
        # TODO make mock function
        res = {'start_ts': start_ts, 'end_ts': end_ts}
        if extra:
            res.update(extra)
        return res

    # TODO customize dask graph visualization
    # https://stackoverflow.com/questions/58394758/adding-labels-to-a-dask-graph
    # https://stackoverflow.com/questions/67680325/annotations-for-custom-graphs-in-dask
    def test_build_task_graph_l2_snaps(self):
        feature_ranges = self.mock_l2_book_deltas_data_ranges_meta(30 * 1000, 10)
        named_feature = L2BookSnapshotFeatureDefinition.named()
        graph = C.build_task_graph(named_feature, feature_ranges)
        print(graph)
        dask.visualize(*graph)

    def test_build_task_graph_mid_price(self):
        feature_ranges = self.mock_l2_book_deltas_data_ranges_meta(30 * 1000, 10)
        named_feature = MidPriceFeatureDefinition.named()
        graph = C.build_task_graph(named_feature, feature_ranges)
        print(graph)
        dask.visualize(*graph)

    def mock_l2_book_deltas_data_ranges_meta(
            self, block_len_ms, num_blocks, between_blocks_ms=100, cur_ts=0
    ) -> Dict[NamedFeature, BlockRangeMeta]:
        res = {}
        named_data = L2BookDeltasData.named()
        ranges = []
        for i in range(0, num_blocks):
            meta = self.meta(cur_ts, cur_ts + block_len_ms)
            if i % 2 == 0:
                # TODO sync keys with L2BookSnapshotFeatureDefinition.group_dep_ranges
                meta['snapshot_ts'] = cur_ts + 10 * 1000
            ranges.append(meta)
            cur_ts += block_len_ms
            cur_ts += between_blocks_ms
        res[named_data] = ranges
        return res

    def mock_l2_book_delta_data_and_meta(self) -> Tuple[Dict[NamedFeature, BlockRange], Dict[NamedFeature, BlockRangeMeta]]:
        consec_athena_files_BINANCE_FUTURES_BTC_USD_PERP = [
            's3://svoe.test.1/data_lake/data_feed_market_data/l2_book/exchange=BINANCE_FUTURES/instrument_type=perpetual/instrument_extra={}/symbol=BTC-USDT-PERP/base=BTC/quote=USDT/date=2022-10-03/compaction=raw/version=local/BINANCE_FUTURES*l2_book*BTC-USDT-PERP*1664778796.722228*1664778826.607931*2e74bf76915c4b168248b18d059773b1.gz.parquet',
            's3://svoe.test.1/data_lake/data_feed_market_data/l2_book/exchange=BINANCE_FUTURES/instrument_type=perpetual/instrument_extra={}/symbol=BTC-USDT-PERP/base=BTC/quote=USDT/date=2022-10-03/compaction=raw/version=local/BINANCE_FUTURES*l2_book*BTC-USDT-PERP*1664778826.710401*1664778856.692907*4ffb70c161f4429d81663ca70d070ccc.gz.parquet',
            's3://svoe.test.1/data_lake/data_feed_market_data/l2_book/exchange=BINANCE_FUTURES/instrument_type=perpetual/instrument_extra={}/symbol=BTC-USDT-PERP/base=BTC/quote=USDT/date=2022-10-03/compaction=raw/version=local/BINANCE_FUTURES*l2_book*BTC-USDT-PERP*1664778856.819425*1664778887.340147*9b0e6bf57fc34074a662e3db00aebfae.gz.parquet',
            's3://svoe.test.1/data_lake/data_feed_market_data/l2_book/exchange=BINANCE_FUTURES/instrument_type=perpetual/instrument_extra={}/symbol=BTC-USDT-PERP/base=BTC/quote=USDT/date=2022-10-03/compaction=raw/version=local/BINANCE_FUTURES*l2_book*BTC-USDT-PERP*1664778887.442283*1664778919.106682*49d157f8d4134b409ba0126b008250b3.gz.parquet',
            's3://svoe.test.1/data_lake/data_feed_market_data/l2_book/exchange=BINANCE_FUTURES/instrument_type=perpetual/instrument_extra={}/symbol=BTC-USDT-PERP/base=BTC/quote=USDT/date=2022-10-03/compaction=raw/version=local/BINANCE_FUTURES*l2_book*BTC-USDT-PERP*1664778919.204879*1664778949.1246562*c04cc54b0c094afd922c53ccf6344651.gz.parquet',
            's3://svoe.test.1/data_lake/data_feed_market_data/l2_book/exchange=BINANCE_FUTURES/instrument_type=perpetual/instrument_extra={}/symbol=BTC-USDT-PERP/base=BTC/quote=USDT/date=2022-10-03/compaction=raw/version=local/BINANCE_FUTURES*l2_book*BTC-USDT-PERP*1664778949.313781*1664778979.103868*f3605c1202f64eb3bca1960eb5b9b241.gz.parquet',
            's3://svoe.test.1/data_lake/data_feed_market_data/l2_book/exchange=BINANCE_FUTURES/instrument_type=perpetual/instrument_extra={}/symbol=BTC-USDT-PERP/base=BTC/quote=USDT/date=2022-10-03/compaction=raw/version=local/BINANCE_FUTURES*l2_book*BTC-USDT-PERP*1664778979.1611981*1664779009.082793*71c48c0b589d4c0b9ee2961dde59d9a1.gz.parquet'
        ]

        block_range = load_files(consec_athena_files_BINANCE_FUTURES_BTC_USD_PERP)
        infos = [get_info(block) for block in block_range]
        block_range_meta = []
        for i in range(len(consec_athena_files_BINANCE_FUTURES_BTC_USD_PERP)):
            block_meta = {
                'path': consec_athena_files_BINANCE_FUTURES_BTC_USD_PERP[i]
            }
            if 'snapshot_ts' in infos[i]:
                block_meta['snapshot_ts'] = infos[i]['snapshot_ts']
            block_range_meta.append(block_meta)

        named_data = L2BookDeltasData.named()
        return {named_data: block_range}, {named_data: block_range_meta}

    def test_featurization_e2e(self):
        # mock consecuitive l2 delta blocks
        block_range, block_range_meta = self.mock_l2_book_delta_data_and_meta()

        # calculate in offline/distributed way
        named_feature = L2BookSnapshotFeatureDefinition.named()
        task_graph = C.build_task_graph(named_feature, block_range_meta)
        res_blocks = dask.compute(task_graph)
        offline_res = pd.concat(res_blocks)

        # calculate online
        stream_graph = C.build_stream_graph(named_feature)
        stream = stream_graph[named_feature]
        sources = {input_data_name: stream_graph[input_data_name] for input_data_name in block_range_meta.keys()}
        merged_events = C.merge_feature_blocks(block_range)
        online_res = C.run_stream(merged_events, sources, stream)

        assert offline_res == online_res


if __name__ == '__main__':
    # unittest.main()
    t = TestFeatureCalculator()
    t.test_build_task_graph_mid_price()
