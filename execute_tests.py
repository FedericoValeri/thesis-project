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

    print("-------- " + section + " completed! --------")
    logging.info(
        f"Test {test_id} completed. Test results can be found in {output}.")


def get_metrics(configuration, section, container_name):
    run_time = configuration[section]["run_time_in_seconds"]
    prometheus_url = configuration[section]["PROMETHEUS_HOST_URL"]
    stop = datetime.datetime.now() + datetime.timedelta(seconds=int(run_time))
    metrics = []
    while datetime.datetime.now() < stop:
        time.sleep(5)
        query = "sum(rate(container_cpu_usage_seconds_total{container='" + \
            container_name + "',pod!='', image!=''}[1m])) by (pod) / 2"
        response = requests.get(
            prometheus_url + '/api/v1/query', params={'query': query})
        results = response.json()['data']['result']
        for result in results:
            metrics.append('{value[1]}'.format(**result))
    max_metric_value = max(metrics)
    metrics.clear()
    print(f'Max cpu value is {max_metric_value}')
    f = open("metrics.txt", "a")
    f.write(max_metric_value + '\n')
    f.close()


def execute(configuration):
    for section in configuration.sections():
        if section.lower().startswith("test"):
            perform_test(configuration, section, design_path)
            # time.sleep(60)
            print("-------- " + section + " completed! --------")

    # run_plugins(configuration, "DEFAULT", design_path, None, "teardown")


# if __name__ == "__main__":
#     design_path = './config/'
#     configuration = configparser.ConfigParser()
#     configuration.read([os.path.join(
#         design_path, "configuration.ini"), os.path.join(design_path, "test_plan.ini")])
#     execute(configuration)

def main():
    design_path = './config/'
    configuration = configparser.ConfigParser()
    configuration.read([os.path.join(
        design_path, "configuration.ini"), os.path.join(design_path, "test_plan.ini")])
    for section in configuration.sections():
        if section.lower().startswith("test"):

            ##### THREAD #####
            testTask = Thread(target=perform_test, args=[
                configuration, section, design_path])
            # time.sleep(60)
            monitorTask = Thread(target=get_metrics, args=[
                configuration, "DEFAULT", "carts"])
            testTask.start()
            monitorTask.start()
            testTask.join()
            monitorTask.join()


main()
