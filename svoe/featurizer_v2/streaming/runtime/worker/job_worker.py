import logging

import ray

from svoe.featurizer_v2.streaming.runtime.core.execution_graph.execution_graph import ExecutionVertex
from svoe.featurizer_v2.streaming.runtime.core.processor.processor import Processor, SourceProcessor, OneInputProcessor
from svoe.featurizer_v2.streaming.runtime.worker.task.stream_task import StreamTask, SourceStreamTask, \
    OneInputStreamTask, TwoInputStreamTask

logger = logging.getLogger(__name__)


@ray.remote
class JobWorker:

    def __init__(self, execution_vertex: ExecutionVertex):
        self.execution_vertex = execution_vertex


    def _create_stream_task(self) -> StreamTask:
        task = None
        stream_processor = Processor.build_processor(self.execution_vertex.stream_operator)
        if isinstance(stream_processor, SourceProcessor):
            task = SourceStreamTask(
                processor=stream_processor,
                job_worker=self
            )
        elif isinstance(stream_processor, OneInputProcessor):
            task = OneInputStreamTask(
                processor=stream_processor,
                job_worker=self
            )
        else:
            input_op_ids = set()
            for input_edge in self.execution_vertex.input_edges:
                input_op_ids.add(input_edge.source_execution_vertex.job_vertex.vertex_id)
            input_op_ids = list(input_op_ids)
            if len(input_op_ids) != 2:
                raise RuntimeError(f'Two input vertex should have exactly 2 edges, {len(input_op_ids)} given')
            left_stream_name = str(input_op_ids[0])
            right_stream_name = str(input_op_ids[1])
            task = TwoInputStreamTask(
                processor=stream_processor,
                job_worker=self,
                left_stream_name=left_stream_name,
                right_stream_name=right_stream_name
            )

        logger.info(f'Created {task} stream task')
        return task
