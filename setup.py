import os
import time
import argparse
import logging
import shutil
import configparser
import datetime
import csv
import json
from pluginbase import PluginBase
from lib import run_plugins, replace_values_in_file


def setup_all(configuration, design_path):

    # Minikube start
    run_plugins(configuration, "DEFAULT", design_path, None, "start_minikube")
    # Check minikube status
    run_plugins(configuration, "DEFAULT", design_path,
                None, "check_minikube_status")
    time.sleep(5)
    # Install Istio
    # run_plugins(configuration, "DEFAULT", design_path, None, "install_istio")
    # Inject Istio proxies into the system
    # run_plugins(configuration, "DEFAULT", design_path, None, "inject_proxies")
    # time.sleep(5)
    # Deploy the application
    run_plugins(configuration, "DEFAULT", design_path, None, "deploy_app")
    # Check if all pods are running
    run_plugins(configuration, "DEFAULT", design_path,
                None, "check_pods_status")
    time.sleep(10)
    # Install Prometheus, Grafana, Kiali and other addons
    # run_plugins(configuration, "DEFAULT", design_path, None, "install_addons")
    # time.sleep(10)
    # Access NodePort
    run_plugins(configuration, "DEFAULT", design_path,
                None, "minikube_nodeport_access")

    logging.info(f"Everything is ready.")


if __name__ == "__main__":
    design_path='./design/'
    configuration=configparser.ConfigParser()
    configuration.read([os.path.join(
        design_path, "configuration.ini"), os.path.join(design_path, "test_plan.ini")])
    setup_all(configuration, design_path)
