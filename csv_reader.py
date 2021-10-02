import pandas as pd

# Read file
csv_data = pd.read_csv(
    "./executed/202110021801-sock_shop-test0/result_stats.csv")

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
print(max_percentage)

zip_iterator_1 = zip(service_action, percentages)
dictionary_1 = dict(zip_iterator_1)
print(dictionary_1)

# Controllo per average response time
max_avg_response_time = max(average_response_times)
print(max_avg_response_time)
zip_iterator_2 = zip(service_action, average_response_times)
dictionary_2 = dict(zip_iterator_2)
print(dictionary_2)


