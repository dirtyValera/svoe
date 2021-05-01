from configs.data_feed.base_config_builder import BaseConfigBuilder

from pathlib import Path
from typing import Any
import yaml

MEDIUM = 'kafka'

# https://stackoverflow.com/questions/52996028/accessing-local-kafka-from-within-services-deployed-in-local-docker-for-mac-inc
KAFKA_IP = '127.0.0.1' # ip='host.docker.internal', # for Docker on Mac use host.docker.internal:19092
KAFKA_PORT = 9092 # port=19092

# TODO figure out production paths
CRYPTOSTORE_CONFIG_PATH = str(Path(__file__).parent / 'cryptostore_config.yaml')
AWS_CREDENTIALS_PATH = str(Path(__file__).parent / 'aws_credentials.yaml')


# Cryptostore specific configs
class CryptostoreConfigBuilder(BaseConfigBuilder):

    # TODO Figure out path for debug config
    # DEBUG ONLY
    def cryptostore_single_config(self) -> str:
        ex_to_pairs = {}
        for exchange in self.exchanges_config.keys():
            ex_to_pairs[exchange] = self.exchanges_config[exchange][0]
        config = self._build_cryptostore_config(ex_to_pairs)
        return self._dump_yaml_config(config, CRYPTOSTORE_CONFIG_PATH)

    def _build_cryptostore_config(self, ex_to_pairs: dict[str, list[str]]) -> dict:
        aws_credentials = self._read_aws_credentials()
        config = {
            'cache' : MEDIUM,
            'kafka' : {
                'ip' : KAFKA_IP,
                'port' : 9092,
                'start_flush' : True,
            },
            'storage' : ['parquet'],
            'storage_retries' : 5,
            'storage_retry_wait' : 30,
            'parquet' : {
                'del_file' : True,
                'append_counter' : 0,
                'file_format' : ['exchange', 'symbol', 'data_type', 'timestamp'],
                'compression' : {
                    'codec' : 'BROTLI',
                    'level' : 6,
                },
                'prefix_date' : True,
                'S3' : {
                    'key_id' : aws_credentials[0],
                    'secret' : aws_credentials[1],
                    'bucket' : aws_credentials[2],
                    'prefix' : 'parquet',
                },
                # path=TEMP_FILES_PATH,
            },
            'storage_interval' : 90,
            'exchanges' : self._build_exchanges_config(ex_to_pairs)
        }

        return config

    def _build_exchanges_config(self, ex_to_pairs: dict[str, list[str]]) -> dict[str, Any]:
        config = {}
        for exchange in ex_to_pairs.keys():
            if exchange not in self.exchanges_config:
                raise Exception('Exchange {} is not supported'.format(exchange))

            # pairs
            pairs = ex_to_pairs[exchange]

            # l2 book
            l2_book = {
                'symbols' : pairs,
                'book_delta' : True,
            }
            max_depth_l2 = self.exchanges_config[exchange][1]
            if max_depth_l2 > 0:
                l2_book['max_depth'] = max_depth_l2

            config[exchange] = {
                'retries' : -1,
                'l2_book' : l2_book,
                'trades' : pairs,
            }

            # l3 book
            include_l3 = self.exchanges_config[exchange][3]
            if include_l3:
                l3_book = {
                    'symbols' : pairs,
                    'book_delta' : True,
                }
                config[exchange]['l3_book'] = l3_book

            # ticker
            include_ticker = self.exchanges_config[exchange][2]
            if include_ticker:
                config[exchange]['ticker'] = pairs

        return config

    @staticmethod
    def _read_aws_credentials() -> list[str]:
        with open(AWS_CREDENTIALS_PATH) as file:
            data = yaml.load(file, Loader = yaml.FullLoader)

        return [data['key_id'], data['secret'], data['bucket']]

    @staticmethod
    def _dump_yaml_config(config: dict, path: str) -> str:
        with open(path, 'w+') as outfile:
            yaml.dump(config, outfile, default_flow_style=False, default_style=None)

        return path