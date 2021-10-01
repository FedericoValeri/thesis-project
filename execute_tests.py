import os
import time
import argparse
import logging
import requests
import shutil
import configparser
import csv
import json
import datetime
import threading
import asyncio
from pluginbase import PluginBase
from threading import Thread
from metrics.Metric import Metrics
from lib import run_plugins, create_output_directory, replace_values_in_file


def perform_test(configuration, section, design_path):
    output, test_id, now = create_output_directory(configuration, section)
    if output == None:
        return

    logging.debug(f"Created a folder name {test_id} in {output}.")

    plugin_files = run_plugins(
        configuration, section, output, test_id, "get_configuration_files")
    plugin_files = [item for sublist in plugin_files for item in sublist]
    for plugin_file in plugin_files:
        if os.path.exists(os.path.join(design_path, plugin_file)):
            shutil.copyfile(os.path.join(design_path, plugin_file),
                            os.path.join(output, plugin_file))

    replacements = []
    for entry in configuration[section].keys():
        replacements.append({"search_for": "${" + entry.upper() + "}",
                             "replace_with": configuration[section][entry]})
        replacements.append({"search_for": "${" + entry.lower() + "}",
                             "replace_with": configuration[section][entry]})

    replacements.append(
        {"search_for": "${TEST_NAME}", "replace_with": test_id})

    logging.debug(f"Replacing values.")
    for plugin_file in plugin_files:
        if os.path.join(output, plugin_file):
            replace_values_in_file(os.path.join(
                output, plugin_file), replacements)

    # Workload intensity with 1 minute ramp-up
    ramp_up = 60
    load = int(configuration[section]['load'])
    spawn_rate = str(load/ramp_up)

    with open(os.path.join(output, "configuration.ini"), "w") as f:
        f.write(f"[CONFIGURATION]\n")
        for option in configuration.options(section):
            if(option.upper() == "SPAWN_RATE_PER_SECOND"):
                f.write(f"{option.upper()}={spawn_rate}\n")
            else:
                f.write(f"{option.upper()}={configuration[section][option]}\n")
        f.write(f"TIMESTAMP={now.timestamp()}\n")
        f.write(f"TEST_NAME={test_id}\n")

    logging.info(f"Executing test case {test_id}.")

    run_plugins(configuration, section, output, test_id, "run_locust")

    logging.info(
        f"Test {test_id} completed. Test results can be found in {output}.")

############################################################
# PROBABLY OVERKILL: basta prendere il valore della cpu
#  alla fine del test con la query PromQL settata con la
# stessa average time window della durata del test
############################################################

# def get_metrics_during_test(configuration, section, container_name):
#     run_time = configuration[section]["run_time_in_seconds"]
#     prometheus_url = configuration[section]["PROMETHEUS_HOST_URL"]
#     stop = datetime.datetime.now() + datetime.timedelta(seconds=int(run_time))
#     metrics = []
#     while datetime.datetime.now() < stop:
#         time.sleep(5)
#         query = "sum(rate(container_cpu_usage_seconds_total{container='" + \
#             container_name + "',pod!='', image!=''}[5m])) by (pod) / 2"
#         response = requests.get(
#             prometheus_url + '/api/v1/query', params={'query': query})
#         results = response.json()['data']['result']
#         for result in results:
#             metrics.append('{value[1]}'.format(**result))
#     max_metric_value = max(metrics)
#     metrics.clear()
#     print(f'Max cpu value is {max_metric_value}')
#     f = open("metrics.txt", "a")
#     f.write(max_metric_value + '\n')
#     f.close()

###############################################################
# Controlla il valore medio della cpu su un intervallo
# di tempo (se eseguito alla fine di un test basta mettere
# come intervallo la durata del test ed eseguire il
# metodo subito dopo il test) e della memoria
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


def execute(configuration):
    for section in configuration.sections():
        if section.lower().startswith("test"):
            perform_test(configuration, section, design_path)
            get_metric("cpu", configuration, "DEFAULT",
                       "carts")
            get_metric("memory", configuration, "DEFAULT",
                       "carts")
            time.sleep(60)
            print("-------- " + section + " completed! --------")
    # run_plugins(configuration, "DEFAULT", design_path, None, "teardown")


if __name__ == "__main__":
    design_path = './config/'
    configuration = configparser.ConfigParser()
    configuration.read([os.path.join(
        design_path, "configuration.ini"), os.path.join(design_path, "test_plan.ini")])
    execute(configuration)

########## THREADING ###########

# if __name__ == "__main__":
#     design_path = './config/'
#     configuration = configparser.ConfigParser()
#     configuration.read([os.path.join(
#         design_path, "configuration.ini"), os.path.join(design_path, "test_plan.ini")])
#     for section in configuration.sections():
#         if section.lower().startswith("test"):

#             testTask = Thread(target=perform_test, args=[
#                 configuration, section, design_path])
#             monitorTask = Thread(target=get_metrics, args=[
#                 configuration, "DEFAULT", "carts"])
#             testTask.start()
#             monitorTask.start()
#             testTask.join()
#             monitorTask.join()
