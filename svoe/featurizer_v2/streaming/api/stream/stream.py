from abc import ABC
from typing import Optional

from svoe.featurizer_v2.streaming.api.context.streaming_context import StreamingContext
from svoe.featurizer_v2.streaming.api.operator.operator import StreamOperator
from svoe.featurizer_v2.streaming.api.partition.partition import Partition, ForwardPartition


class Stream(ABC):

    def __init__(
        self,
        stream_operator: StreamOperator,
        input_stream: Optional['Stream'] = None,
        streaming_context: Optional[StreamingContext] = None,
        partition: Optional[Partition] = None
    ):
        self.parallelism = 1
        if input_stream is None and streaming_context is None:
            raise RuntimeError('input_stream and streaming_context are both None')
        self.stream_operator = stream_operator
        if input_stream is not None:
            self.input_stream = input_stream
        if streaming_context is None:
            self.streaming_context = input_stream.streaming_context
        else:
            self.streaming_context = streaming_context

        self.id = self.streaming_context.generate_id()
        self.name = f'{self.id}_{self.__class__.__name__}'

        if self.input_stream is not None:
            self.parallelism = self.input_stream.parallelism

        if partition is None:
            self.partition = ForwardPartition()
        else:
            self.partition = partition

    def set_parallelism(self, parallelism: int) -> 'Stream':
        self.parallelism = parallelism
        return self