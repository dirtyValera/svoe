from typing import Dict, List, Optional

from svoe.featurizer_v2.streaming.api.job_graph.job_graph import JobGraph
from svoe.featurizer_v2.streaming.api.operator.operator import StreamOperator
from svoe.featurizer_v2.streaming.api.partition.partition import RoundRobinPartition, Partition

import pygraphviz as pgv


class ExecutionEdge:

    def __init__(
        self,
        source_execution_vertex: 'ExecutionVertex',
        target_execution_vertex: 'ExecutionVertex',
        partition: Partition
    ):
        self.source_execution_vertex = source_execution_vertex
        self.target_execution_vertex = target_execution_vertex
        self.partition = partition


class ExecutionVertex:

    def __init__(
        self,
        vertex_id: str,
        parallelism: int,
        stream_operator: StreamOperator,
        resources: Optional[Dict[str, float]] = None
    ):
        self.vertex_id = vertex_id
        self.parallelism = parallelism
        self.stream_operator = stream_operator
        self.resources = resources
        self.input_edges: List[ExecutionEdge] = []
        self.output_edges: List[ExecutionEdge] = []


class ExecutionGraph:

    def __init__(self):
        self.execution_vertices_by_id: Dict[str, ExecutionVertex] = {}
        self.execution_edges: List[ExecutionEdge] = []

        # parallelism groups for same operator
        self._execution_vertices_groups_by_job_vertex_id: Dict[int, List[ExecutionVertex]] = {}

    @classmethod
    def from_job_graph(cls, job_graph: JobGraph) -> 'ExecutionGraph':
        execution_graph = ExecutionGraph()

        # create exec vertices
        for job_vertex in job_graph.job_vertices:
            for i in range(job_vertex.parallelism):
                execution_vertex_id = f'{job_vertex.vertex_id}_{i + 1}'
                execution_vertex = ExecutionVertex(
                    vertex_id=execution_vertex_id,
                    parallelism=job_vertex.parallelism,
                    stream_operator=job_vertex.stream_operator
                )

                if job_vertex.vertex_id in execution_graph._execution_vertices_groups_by_job_vertex_id:
                    execution_graph._execution_vertices_groups_by_job_vertex_id[job_vertex.vertex_id].append(execution_vertex)
                else:
                    execution_graph._execution_vertices_groups_by_job_vertex_id[job_vertex.vertex_id] = [execution_vertex]

                execution_graph.execution_vertices_by_id[execution_vertex_id] = execution_vertex

        # create exec edges
        for job_edge in job_graph.job_edges:
            source_job_vertex_id = job_edge.source_vertex_id
            target_job_vertex_id = job_edge.target_vertex_id

            for source_exec_vertex in execution_graph._execution_vertices_groups_by_job_vertex_id[source_job_vertex_id]:

                target_exec_vertices = execution_graph._execution_vertices_groups_by_job_vertex_id[target_job_vertex_id]

                for target_exec_vertex in target_exec_vertices:
                    partition = job_edge.partition
                    # update partition
                    # TODO should this depend on operator type?
                    if len(target_exec_vertices) > 1:
                        partition = RoundRobinPartition()
                    edge = ExecutionEdge(
                        source_execution_vertex=source_exec_vertex,
                        target_execution_vertex=target_exec_vertex,
                        partition=partition
                    )
                    source_exec_vertex.output_edges.append(edge)
                    target_exec_vertex.input_edges.append(edge)
                    execution_graph.execution_edges.append(edge)

        return execution_graph

    def gen_digraph(self) -> pgv.AGraph:
        G = pgv.AGraph()
        for v in self.execution_vertices_by_id.values():
            G.add_node(v.vertex_id, label=f'{v.stream_operator.__class__.__name__}_{v.vertex_id} p={v.parallelism}')

        for e in self.execution_edges:
            G.add_edge(e.source_execution_vertex.vertex_id, e.target_execution_vertex.vertex_id, label=e.partition.__class__.__name__)

        return G
