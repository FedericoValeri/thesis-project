import os
import time
import argparse
import subprocess
import logging
import requests
import shutil
import configparser
import csv
import json
import datetime
import threading
import pandas as pd
from threading import Thread
from threading import Timer
from metrics.Metric import Metrics
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


def get_metrics_during_test(configuration, section, container_name):
    run_time = configuration[section]["run_time_in_seconds"]
    run_time_in_minutes = str(int(run_time) // 60)
    prometheus_url = configuration[section]["PROMETHEUS_HOST_URL"]
    stop = datetime.datetime.now() + datetime.timedelta(seconds=int(run_time))
    metrics = []
    # for a time span of the same duration of the test execution
    while datetime.datetime.now() < stop:
        # collect metrics each 5 seconds
        time.sleep(5)
        query = "sum(rate(container_cpu_usage_seconds_total{container='" + \
            container_name + \
                "',pod!='', image!=''}[1m])) by (pod) / 2"
        response = requests.get(
            prometheus_url + '/api/v1/query', params={'query': query})
        results = response.json()['data']['result']
        for result in results:
            metrics.append('{value[1]}'.format(**result))
    max_metric_value = max(metrics)
    numeric_metrics = [float(numeric_string) for numeric_string in metrics]
    average_metric_value = sum(numeric_metrics) / len(numeric_metrics)
    print(f'Max cpu value is {max_metric_value}')
    print(f'Average cpu value is {average_metric_value}')
    f2 = open("./metrics/cpu_values.txt", "a")
    f2.write(max_metric_value + '\n')
    f2.write(str(average_metric_value) + '\n')
    f2.close()
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
    # create_test_plan()
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


# if __name__ == "__main__":
#     design_path = './config/'
#     configuration = configparser.ConfigParser()
#     configuration.read([os.path.join(
#         design_path, "configuration.ini"), os.path.join(design_path, "test_plan.ini")])
#     execute_tests(configuration)

########## THREADING ###########

if __name__ == "__main__":
    design_path = './config/'
    configuration = configparser.ConfigParser()
    configuration.read([os.path.join(
        design_path, "configuration.ini"), os.path.join(design_path, "test_plan.ini")])
    for section in configuration.sections():
        if section.lower().startswith("test"):
            testTask = Thread(target=perform_test, args=[
                configuration, section, design_path])
            # monitorTask = Thread(target=get_metrics_during_test, args=[
            #     configuration, "DEFAULT", "carts"])
            testTask.start()
            monitorTask = Timer(60.0, get_metrics_during_test, [configuration, "DEFAULT", "carts"])
            monitorTask.start()
            testTask.join()
            monitorTask.join()
