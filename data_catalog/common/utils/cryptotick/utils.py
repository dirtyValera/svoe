from typing import List, Tuple

from data_catalog.common.data_models.models import InputItemBatch, InputItem
from data_catalog.common.utils.sql.models import DataCatalog
from utils.s3.s3_utils import list_files_and_sizes_kb

CRYPTOTICK_RAW_BUCKET_NAME = 'svoe-cryptotick-data'


def cryptotick_input_items(batch_size: int) -> List[InputItemBatch]:
    # raw_files = list_files_and_sizes_kb(CRYPTOTICK_RAW_BUCKET_NAME)
    raw_files = [('limitbook_full/20230201/BINANCE_SPOT_BTC_USDT.csv.gz', 252 * 1024)]
    grouped_by_data_type = {}
    for raw_path, size_kb in raw_files:
        item = _parse_s3_key(raw_path, size_kb)
        data_type = item[DataCatalog.data_type.name]
        if data_type in grouped_by_data_type:
            if len(grouped_by_data_type[data_type][-1]) == batch_size:
                grouped_by_data_type[data_type].append([])
            grouped_by_data_type[data_type][-1].append(item)
        else:
            grouped_by_data_type[data_type] = [[item]]
    res = []
    batch_id = 0
    for data_type in grouped_by_data_type:
        for batch in grouped_by_data_type[data_type]:
            res.append(({'batch_id': batch_id}, batch))
            batch_id += 1
    return res


def _parse_s3_key(path: str, size_kb) -> InputItem:
    # example quotes/20230201/BINANCE_SPOT_BTC_USDT.csv.gz
    s = path.split('/')
    if s[0] == 'limitbook_full':
        data_type = 'l2_book' # TODO l2_inc
    elif s[0] == 'quotes':
        data_type = 'ticker'
    elif s[0] == 'trades':
        data_type = 'trades'
    else:
        raise ValueError(f'Unknown data_type {s[0]}')

    raw_date = s[1] # YYYYMMDD
    # make DD-MM-YYYY
    date = f'{raw_date[6:8]}-{raw_date[4:6]}-{raw_date[0:4]}'
    file = s[2] # BINANCE_SPOT_BTC_USDT.csv.gz
    f = file.split('_')
    exchange = f[0]
    if f[1] == 'SPOT':
        instrument_type = 'spot'
    else:
        raise ValueError(f'Unknown instrument_type {f[1]}')
    base = f[2]
    quote = f[3].split('.')[0]

    # TODO call cryptofeed lib to construct symbol here?
    symbol = f'{base}-{quote}'

    path = f's3://{CRYPTOTICK_RAW_BUCKET_NAME}/' + path
    return {
        DataCatalog.path.name: path,
        DataCatalog.data_type.name: data_type,
        DataCatalog.exchange.name: exchange,
        DataCatalog.symbol.name: symbol,
        DataCatalog.base.name: base,
        DataCatalog.quote.name: quote,
        DataCatalog.source.name: 'cryptotick',
        DataCatalog.date.name: date,
        DataCatalog.size_kb.name: size_kb,
        DataCatalog.instrument_type.name: instrument_type
    }



