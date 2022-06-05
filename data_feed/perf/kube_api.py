from perf.defines import *
from perf.utils import cm_name_from_ss, raw_pod_name_from_ss
import yaml
import json
import kubernetes


class KubeApi:
    def __init__(self, core_api, apps_api, custom_objects_api):
        self.core_api = core_api
        self.apps_api = apps_api
        self.custom_objects_api = custom_objects_api

    def get_nodes_metrics(self):
        # needs metrics-server running
        # https://github.com/amelbakry/kube-node-utilization/blob/master/nodeutilization.py
        # https://stackoverflow.com/questions/66453590/how-to-use-kubectl-top-node-in-kubernetes-python
        k8s_nodes = self.custom_objects_api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "nodes")
        res = {}
        for item in k8s_nodes['items']:
            node_name = item['metadata']['name']
            cpu = item['usage']['cpu']
            memory = item['usage']['memory']
            res[node_name] = {
                'cpu': cpu,
                'memory': memory
            }
        # 'minikube-1-m02': {'cpu': '119561578n', 'memory': '1238864Ki'}
        # TODO error check
        return res

    def load_ss_names(self):
        specs = self.apps_api.list_namespaced_stateful_set(namespace=DATA_FEED_NAMESPACE)
        filtered_names = list(map(lambda spec: spec.metadata.name, filter(lambda spec: self.should_estimate(spec), specs.items)))
        print(f'Processing {len(filtered_names)}/{len(specs.items)} ss specs')
        return filtered_names

    def pod_template_from_ss(self, ss_name):
        resp = self.apps_api.list_namespaced_stateful_set(
            namespace=DATA_FEED_NAMESPACE,
            field_selector=f'metadata.name={ss_name}',
            _preload_content=False,
        )
        # TODO edge check
        return json.loads(resp.data)['items'][0]['spec']['template']

    def create_raw_pod(self, ss_name):
        template = self.pod_template_from_ss(ss_name)
        definition = {
            "apiVersion": "v1",
            "kind": "Pod"
        }
        template['metadata']['name'] = raw_pod_name_from_ss(ss_name)
        template['spec']['restartPolicy'] = 'Never'
        # TODO set env testing
        # TODO podPriority

        definition.update(template)
        # TODO success check
        self.core_api.create_namespaced_pod(body=definition, namespace=DATA_FEED_NAMESPACE)

    def delete_pod(self, pod_name):
        self.core_api.delete_namespaced_pod(name=pod_name, namespace=DATA_FEED_NAMESPACE)

    def set_env(self, ss_name, env):
        # https://stackoverflow.com/questions/71163299/how-to-update-env-variables-in-kubernetes-deployment-in-java
        self.apps_api.patch_namespaced_stateful_set(name=ss_name, namespace=DATA_FEED_NAMESPACE,
                                               body={'spec': {'template': {'spec': {'containers': [{'name': DATA_FEED_CONTAINER, 'env': [{'name': 'ENV', 'value': env}]}]}}}})
        print(f'Set ENV={env} for {ss_name}')

    def scale_up(self, ss_name):
        self.apps_api.patch_namespaced_stateful_set_scale(name=ss_name, namespace=DATA_FEED_NAMESPACE,
                                                     body={'spec': {'replicas': 1}})
        print(f'Scaled up {ss_name}')

    def scale_down(self, ss_name):
        self.apps_api.patch_namespaced_stateful_set_scale(name=ss_name, namespace=DATA_FEED_NAMESPACE,
                                                     body={'spec': {'replicas': 0}})
        print(f'Scaled down {ss_name}')

    def get_payload(self, ss_name):
        cm_name = cm_name_from_ss(ss_name)
        cm = self.core_api.read_namespaced_config_map(cm_name, DATA_FEED_NAMESPACE)
        conf = yaml.load(cm.data[DATA_FEED_CM_CONFIG_NAME], Loader=yaml.SafeLoader)
        return conf['payload_config'], conf['payload_hash']

    @staticmethod
    def should_estimate(spec):
        for container in spec.spec.template.spec.containers:
            if container.name == DATA_FEED_CONTAINER \
                    and container.resources.limits is None \
                    and container.resources.requests is None:
                return True
        return False

    def check_health(self, pod_name):
        exec_command = [
            '/bin/sh',
            '-c',
            # TODO figure out correct script
            'echo \'import requests; print(requests.get("http://localhost:8000/metrics"))\' > p.py && python3 p.py && rm p.py']
        resp = kubernetes.stream.stream(self.core_api.connect_get_namespaced_pod_exec,
            pod_name,
            DATA_FEED_NAMESPACE,
            container=DATA_FEED_CONTAINER,
            command=exec_command,
            stderr=True, stdin=False,
            stdout=True, tty=False,
            _preload_content=True
        )
        print("Response: " + resp)