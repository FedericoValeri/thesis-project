import logging
import kubernetes
from yaspin import yaspin
from yaspin.spinners import Spinners
from kubernetes import client, config


def check_status():
    # Controllo se tutti i pod sono nello status "Running" programmaticamente
    app_namespace = 'default'
    config.load_kube_config()
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(app_namespace, watch=False)
    pods = ret.items
    pods_status = [pod.status.phase for pod in pods]
    result = all(status == 'Running' for status in pods_status)
    return result


def check_pods_status(global_plugin_state, current_configuration, output, test_id):
    with yaspin(Spinners.line, text="Checking pods to be ready. This could take some minutes...") as sp:
        while(True):
            pods_are_running = check_status()
            if(pods_are_running):
                break
    print("All pods are running!")
