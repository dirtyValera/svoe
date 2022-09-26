import awswrangler as wr
import pandas as pd
import boto3
from prefect_aws.credentials import AwsCredentials
import concurrent.futures
import asyncio
import functools
from typing import List, Tuple
import featurizer.features.loader.concurrency_utils as cu
import featurizer.features.loader.s3_utils as s3u


def load_single_file(path: str, credentials: AwsCredentials = None) -> pd.DataFrame:
    # split path into prefix and suffix
    # this is needed because if dataset=True data wrangler handles input path as a glob pattern,
    # hence messing up special characters
    split = path.split('/')
    suffix = split[len(split) - 1]
    prefix = path.removesuffix(suffix)
    if credentials is not None:
        session = credentials.get_boto3_session()
    else:
        session = boto3.session.Session()
    return wr.s3.read_parquet(path=prefix, path_suffix=suffix, dataset=True, boto3_session=session)


def load_files(paths: List[str], credentials: AwsCredentials = None) -> List[pd.DataFrame]:
    callables = [functools.partial(load_single_file, path=path, credentials=credentials) for path in paths]
    return cu.run_concurrently(callables)


def sub_df(df: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    # includes end
    return df[start: end + 1].reset_index(drop=True)


def concat(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(dfs, ignore_index=True)


def time_range(df: pd.DataFrame) -> Tuple[float, int, int]:
    # time between start and finish
    start = df.iloc[0].timestamp
    end = df.iloc[-1].timestamp

    return end - start, start, end


def get_len(df: pd.DataFrame) -> int:
    return len(df.index)


def get_size_kb(df: pd.DataFrame) -> int:
    return int(df.memory_usage(index=True, deep=True).sum()/1000.0)


def get_time_diff(df1: pd.DataFrame, df2: pd.DataFrame) -> float:
    if df1 is None or df2 is None:
        return 0
    start1 = df1.iloc[0].timestamp
    start2 = df2.iloc[0].timestamp
    return start1 - start2

