import os
import time
import argparse
import math
import logging
import requests
import shutil
import configparser
import csv
import json
import numpy
import datetime
import threading
import pandas as pd
from prettytable import PrettyTable
from lib import perform_test


def baseline_test(configuration):
    for section in configuration.sections():
        if section.lower().startswith("baseline"):
            test_id = perform_test(configuration, section, design_path)
            # time.sleep(30)
            print("-------- " + section + " completed! --------")

    # Read file
    csv_data = pd.read_csv(f"./executed/{test_id}/result_stats.csv")
    action_types = csv_data['Type']
    service_actions = csv_data['Name']
    request_count = csv_data['Request Count']
    average_response_times = csv_data['Average Response Time']

    # generate requests percentages
    total_requests = max(request_count)
    percentages = []
    for req in request_count[:-1]:
        action_request_percentage = round(100*req/total_requests, 2)
        percentages.append(f'{action_request_percentage}%')

    average_response_times_rounded = numpy.round(average_response_times, 2)

    # creating an empty PrettyTable
    ascii_table = PrettyTable()

    # adding data into the table column by column
    ascii_table.add_column("Type", action_types[:-1])
    ascii_table.add_column("Action name", service_actions[:-1])
    ascii_table.add_column("Requests frequency", percentages)
    ascii_table.add_column("Avg response time",
                           average_response_times_rounded[:-1])

    # printing table
    print(ascii_table)


if __name__ == "__main__":
    design_path = './config/'
    configuration = configparser.ConfigParser()
    configuration.read([os.path.join(
        design_path, "configuration.ini"), os.path.join(design_path, "test_plan.ini")])
    baseline_test(configuration)
