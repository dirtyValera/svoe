import signal

from perf.kube_api.kube_api import KubeApi
from perf.kube_watcher.kube_watcher import KubeWatcher, CHANNEL_NODE_OBJECT_EVENTS, CHANNEL_NODE_KUBE_EVENTS, CHANNEL_DF_POD_OBJECT_EVENTS, CHANNEL_DF_POD_KUBE_EVENTS
from perf.kube_watcher.kube_watcher_state import KubeWatcherState
from perf.metrics.prom_connection import PromConnection
from perf.state.estimation_state import EstimationState
from perf.scheduler.scheduler import Scheduler
from perf.state.scheduling_state import SchedulingState
from perf.callback.pod_callback import PodCallback
from perf.callback.node_callback import NodeCallback
from perf.stats.stats import Stats

from perf.metrics.metrics import fetch_metrics, _get_data_feed_health_metrics_queries, _get_perf_kube_metrics_server_queries
from perf.utils import nested_set

class Runner:
    def __init__(self):
        self.kube_api = KubeApi.new_instance()
        self.scheduling_state = SchedulingState()
        self.estimation_state = EstimationState()
        self.kube_watcher_state = KubeWatcherState()
        self.stats = Stats()
        self.scheduler = Scheduler(
            self.kube_api,
            self.scheduling_state,
            self.estimation_state,
            self.kube_watcher_state,
            self.stats
        )
        pod_callback = PodCallback(self.scheduler)
        node_callback = NodeCallback(self.scheduler)
        self.kube_watcher_state.register_pod_callback(pod_callback.callback)
        self.kube_watcher_state.register_node_callback(node_callback.callback)

        self.kube_watcher = KubeWatcher(self.kube_api.core_api, self.kube_watcher_state)
        self.prom_connection = PromConnection()
        self.running = False

    def run(self, subset=None):
        for sig in [signal.SIGINT, signal.SIG_IGN, signal.SIGTERM]:
            signal.signal(sig, self.cleanup)
        self.running = True
        print('[Runner] Started estimator')
        self.prom_connection.start() # blocking
        if not self.running:
            return
        self.kube_watcher.start([
            CHANNEL_NODE_OBJECT_EVENTS,
            CHANNEL_NODE_KUBE_EVENTS,
            CHANNEL_DF_POD_OBJECT_EVENTS,
            CHANNEL_DF_POD_KUBE_EVENTS])
        self.scheduler.run(subset)
        self.cleanup()

    def cleanup(self, *args):
        # *args are for signal.signal handler
        if not self.running:
            return
        self.running = False
        if self.prom_connection is not None:
            self.prom_connection.stop()
            self.prom_connection = None
        if self.scheduler is not None:
            self.scheduler.stop()
            self.scheduler = None
        # save stats only after scheduler is done so we write all events
        self.stats.save()
        if self.kube_watcher is not None:
            self.kube_watcher.stop([
                CHANNEL_NODE_OBJECT_EVENTS,
                CHANNEL_NODE_KUBE_EVENTS,
                CHANNEL_DF_POD_OBJECT_EVENTS,
                CHANNEL_DF_POD_KUBE_EVENTS])
            self.kube_watcher = None

if __name__ == '__main__':
    r = Runner()
    sub = [
        # 'data-feed-binance-spot-6d1641b134-ss',
        # 'data-feed-binance-spot-eb540d90be-ss',
        # 'data-feed-binance-spot-18257181b7-ss',
        # 'data-feed-binance-spot-28150ca2ec-ss',
        # 'data-feed-binance-spot-2d2a017a56-ss',
        # 'data-feed-binance-spot-3dd6e42fd0-ss'
        'data-feed-bybit-perpetual-1d2c5c9c38-ss'
    ]
    r.run(sub)