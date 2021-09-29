import datetime
import time
import requests
import os
import numpy
import datetime
import configparser


def func(current_configuration, section):
    run_time = current_configuration[section]["run_time_in_seconds"]
    PROMETHEUS = current_configuration[section]["PROMETHEUS_HOST_URL"]
    stop = datetime.datetime.now() + datetime.timedelta(seconds=int(run_time))
    array = []
    while datetime.datetime.now() < stop:
        query = 'sum(rate(container_cpu_usage_seconds_total{container="carts",pod!="", image!=""}[1m])) by (pod) / 2'
        response = requests.get(
            PROMETHEUS + '/api/v1/query', params={'query': query})
        time.sleep(5)
        results = response.json()['data']['result']
        for result in results:
            array.append('{value[1]}'.format(**result))
    numpy.savetxt("metrics.txt", array, fmt="%s")
    # return array


if __name__ == "__main__":
    design_path = './config/'
    configuration = configparser.ConfigParser()
    configuration.read(os.path.join(design_path, "configuration.ini"))
    #metrics = func(configuration, "DEFAULT")
    #numpy.savetxt("metrics.txt", metrics, fmt="%s")
