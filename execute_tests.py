import os
import time
import argparse
import subprocess
import logging
import requests
import shutil
import configparser
import csv
import sys
import json
import yaml
import pyaml
import math
import datetime
import threading
import pandas as pd
from threading import Thread
from threading import Timer
from metrics.Metric import Metrics
from prettytable import PrettyTable
from lib import perform_test


def create_test_plan():
    # Define command
    command = 'Rscript'
    script_path = './R/dateRequestsOPAggregator.R'
    # Build subprocess command
    cmd = [command, script_path]
    # check_output will run the command and store to result
    workloads = subprocess.check_output(cmd, universal_newlines=True)
    print("---------- WORKLOADS SUCCESFULLY AGGREGATED! ----------")
    # Read file
    csv_data = pd.read_csv("./R/output/worklaods.csv")
    selected_workloads = csv_data['x']
    # Per ogni workload, compila il file test_plan.ini nella forma [Testi+1] LOAD=selected_workloads[i]
    config = configparser.ConfigParser()
    config.read('./config/test_plan.ini')
    for i, workload in enumerate(selected_workloads):
        config[f'Test{i+1}'] = {}
        config[f'Test{i+1}']['LOAD'] = str(selected_workloads[i])
    with open('./config/test_plan.ini', 'w') as configfile:
        config.write(configfile)


def get_metrics_during_test(metric, configuration, section, container_name):
    run_time = configuration[section]["run_time_in_seconds"]
    #run_time_in_minutes = str(int(run_time) // 60)
    prometheus_url = configuration[section]["PROMETHEUS_HOST_URL"]
    stop = datetime.datetime.now() + datetime.timedelta(seconds=int(run_time))
    is_cpu = metric == Metrics().CPU
    is_memory = metric == Metrics().MEMORY

    metrics = []
    # for a time span of the same duration of the test execution
    while datetime.datetime.now() < stop:
        # collect metrics each 5 seconds
        time.sleep(5)
        if(is_cpu):
            query = "sum(rate(container_cpu_usage_seconds_total{container='" + container_name + \
                "',pod!='', image!=''}[1m])) by (pod) / 2"
        if(is_memory):
            query = "sum(container_memory_working_set_bytes{pod!='', image!='', container='" + \
                container_name + "'}) by (pod) / 2"
        response = requests.get(
            prometheus_url + '/api/v1/query', params={'query': query})
        results = response.json()['data']['result']
        for result in results:
            metrics.append('{value[1]}'.format(**result))
    max_metric_value = max(metrics)
    print(f'Max value for {metric} is: {max_metric_value}')
    # numeric_metrics = [float(numeric_string) for numeric_string in metrics]
    # average_metric_value = sum(numeric_metrics) / len(numeric_metrics)
    f = open(f"./metrics/monitored_{metric}.txt", "a")
    f.write(max_metric_value + '\n')
    f.close()
    metrics.clear()

###############################################################
# Controlla il valore medio della cpu su un intervallo di
# tempo (se eseguito alla fine di un test basta mettere
# come intervallo la durata del test ed eseguire il
# metodo subito dopo il test)
################################################################


def get_metric(metric, configuration, section, container_name):
    prometheus_url = configuration[section]["PROMETHEUS_HOST_URL"]
    run_time = configuration[section]["run_time_in_seconds"]
    run_time_in_minutes = str(int(run_time) // 60)
    is_cpu = metric == Metrics().CPU
    is_memory = metric == Metrics().MEMORY
    if(is_cpu):
        query = "sum(rate(container_cpu_usage_seconds_total{container='" + container_name + \
            "',pod!='', image!=''}[" + \
                run_time_in_minutes + "m])) by (pod) / 2"
    if(is_memory):
        query = "sum(container_memory_working_set_bytes{pod!='', image!='', container='" + \
            container_name + "'}) by (pod) / 2"
    response = requests.get(
        prometheus_url + '/api/v1/query', params={'query': query})
    results = response.json()['data']['result']
    for result in results:
        metric_value = ('{value[1]}'.format(**result))

    print(f'{metric}: {metric_value}')
    f = open(f"./metrics/{metric}.txt", "a")
    f.write(metric_value + '\n')
    f.close()


def execute_tests(configuration):
    create_test_plan()
    container_name = configuration["DEFAULT"]["CONTAINER_TO_BE_MONIORED"]
    for section in configuration.sections():
        if section.lower().startswith("test"):
            perform_test(configuration, section, design_path)
            get_metric("cpu", configuration, "DEFAULT",
                       container_name)
            get_metric("memory", configuration, "DEFAULT",
                       container_name)
            time.sleep(60)
            print("-------- " + section + " completed! --------")
    # run_plugins(configuration, "DEFAULT", design_path, None, "teardown")


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "Ki", "Mi", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p)
    return "%s%s" % (s, size_name[i])


def provide_reccomendations(metrics, configuration, section, container_name):
    target_cpu = 0
    target_memory = 0
    cpu_request = 0
    memory_request = 0
    query = ""
    prometheus_url = configuration[section]["PROMETHEUS_HOST_URL"]
    for metric in metrics:
        lines = []
        query = "avg(kube_pod_container_resource_requests{resource='" + \
                metric + "', container='" + container_name + "'})"
        response = requests.get(
            prometheus_url + '/api/v1/query', params={'query': query})
        results = response.json()['data']['result']
        with open(f'./metrics/monitored_{metric}.txt') as f:
            lines = f.readlines()
        target_metric = max(lines)
        if(metric == Metrics().CPU):
            target_cpu = int(float(target_metric) * 1000)
            for result in results:
                value = ('{value[1]}'.format(**result))
                cpu_request = int(float(value) * 1000)
        if(metric == Metrics().MEMORY):
            target_memory = convert_size(int(target_metric))
            for result in results:
                value = ('{value[1]}'.format(**result))
                memory_request = convert_size(int(value))

    target_cpu = str(target_cpu) + 'm'
    # creating an empty PrettyTable
    ascii_table = PrettyTable()

    # adding data into the table column by column
    ascii_table.add_column("Metrics", metrics)
    ascii_table.add_column("Actual requests", [str(
        cpu_request) + 'm', memory_request])
    ascii_table.add_column("Target", [target_cpu, target_memory])

    # printing table
    print(ascii_table)

    yaml_output = dict(
        resources=dict(
            requests=dict(
                cpu=target_cpu,
                memory=target_memory
            )
        )
    )

    with open('test.yaml', 'w') as outfile:
        yaml.dump(yaml_output, outfile, default_flow_style=False)

    yaml.safe_dump(yaml_output, sys.stdout)


# if __name__ == "__main__":
#     design_path = './config/'
#     configuration = configparser.ConfigParser()
#     configuration.read([os.path.join(
#         design_path, "configuration.ini"), os.path.join(design_path, "test_plan.ini")])
#     execute_tests(configuration)
########## THREADING ###########
if __name__ == "__main__":
    # create_test_plan()
    design_path = './config/'
    configuration = configparser.ConfigParser()
    configuration.read([os.path.join(
        design_path, "configuration.ini"), os.path.join(design_path, "test_plan.ini")])
    container_name = configuration["DEFAULT"]["CONTAINER_TO_BE_MONIORED"]
    # for section in configuration.sections():
    #     if section.lower().startswith("test"):
    #         test = Thread(target=perform_test, args=[
    #             configuration, section, design_path])
    #         monitor_cpu = Thread(target=get_metrics_during_test, args=[
    #             "cpu", configuration, "DEFAULT", container_name])
    #         monitor_memory = Thread(target=get_metrics_during_test, args=[
    #             "memory", configuration, "DEFAULT", container_name])
    #         test.start()
    #         monitor_cpu.start()
    #         monitor_memory.start()
    #         test.join()
    #         monitor_cpu.join()
    #         monitor_memory.join()
    metrics = ['cpu', 'memory']
    provide_reccomendations(metrics, configuration, "DEFAULT", container_name)
