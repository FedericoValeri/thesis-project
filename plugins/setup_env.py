import os
import logging
import subprocess
import time
from lib import run_external_applicaton

def start_minikube(global_plugin_state, current_configuration, output, test_id):
    #seconds_to_wait_for_starting = int(current_configuration["MINIKUBE_WAITING_FOR_STARTING_IN_SECONDS"])
    run_external_applicaton("minikube start --memory 8192 --cpus 4", False)
    #logging.info(f"Waiting for {seconds_to_wait_for_starting} seconds to allow Minikube to start.")
    #time.sleep(seconds_to_wait_for_starting)

def check_minikube_status(global_plugin_state, current_configuration, output, test_id):
    try:
        result = str(subprocess.check_output('minikube status'))
        is_ready = result.find('Running')
        if(is_ready != -1):
            print("Minikube is ready!")            
    except:
        logging.warning("Minikube is not started")


def install_istio(global_plugin_state, current_configuration, output, test):
    run_external_applicaton("istioctl install --set profile=demo -y")

def inject_proxies(global_plugin_state, current_configuration, output, test):
    run_external_applicaton("kubectl label namespace default istio-injection=enabled")