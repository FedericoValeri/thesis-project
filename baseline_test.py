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
import pandas as pd
from lib import perform_test


def baseline_test(configuration):
    for section in configuration.sections():
        if section.lower().startswith("baseline"):
            test_id = perform_test(configuration, section, design_path)
            # time.sleep(60)
            print("-------- " + section + " completed! --------")

    # Read file
    csv_data = pd.read_csv(f"./executed/{test_id}/result_stats.csv")

    service_action = csv_data['Name']
    request_count = csv_data['Request Count']
    average_response_times = csv_data['Average Response Time']

    # Controllo per numero di richieste
    total_requests = max(request_count)
    percentages = []
    for req in request_count[:-1]:
        action_request_percentage = 100*req/total_requests
        percentages.append(action_request_percentage)
    max_percentage = max(percentages)
    zip_iterator_1 = zip(service_action, percentages)
    service_calls_percentages = dict(zip_iterator_1)
    dict(sorted(service_calls_percentages.items(),
         key=lambda item: item[1], reverse=True))
    #most_called_action = next(iter(service_calls_percentages.items()))
    most_called_action = list(service_calls_percentages.keys())[0]

    # Controllo per average response time
    max_avg_response_time = max(average_response_times)
    zip_iterator_2 = zip(service_action, average_response_times)
    service_calls_reponse_times = dict(zip_iterator_2)
    dict(sorted(service_calls_reponse_times.items(),
         key=lambda item: item[1], reverse=True))
    #slowest_action = next(iter(service_calls_reponse_times.items()))
    slowest_action = list(service_calls_reponse_times.keys())[0]

    header = ['Max requests percentage', 'Max average response time']
    data = [most_called_action, slowest_action]

    with open('./profiling/data.csv', 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        # write the header
        writer.writerow(header)
        # write the data
        writer.writerow(data)

if __name__ == "__main__":
    design_path = './config/'
    configuration = configparser.ConfigParser()
    configuration.read([os.path.join(
        design_path, "configuration.ini"), os.path.join(design_path, "test_plan.ini")])
    baseline_test(configuration)
