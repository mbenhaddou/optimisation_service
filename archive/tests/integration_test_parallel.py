import datetime
import json
import time

import requests
from concurrent.futures import ThreadPoolExecutor
import os


host= 'http://localhost:5051'
def send_request(data):
    url = f'{host}/soa/routing'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        response_json = response.json()
        solution_routing_id = response_json.get('solution_routing_id', None)
        if solution_routing_id:
            return check_solution_status(solution_routing_id)
    return None

def check_solution_status(solution_routing_id):
    url = f'{host}/soa/solution/routing/{solution_routing_id}'
    status = None
    start_time = datetime.datetime.now()
    while status not in ['FINISHED', 'FAILED']:
        response = requests.get(url)
        if response.status_code == 200:
            response_json = response.json()
            status = response_json.get('status', None)
        time.sleep(2)
    end_time = datetime.datetime.now()
    time_diff = end_time - start_time
    return status, time_diff.total_seconds()

def load_data_from_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def send_parallel_requests(file_path, num_requests):
    data = load_data_from_file(file_path)
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(send_request, data) for _ in range(num_requests)]
    return futures

if __name__ == "__main__":
    file_path = os.path.join(
        os.path.dirname(__file__),
        'optimise',
        'data',
        'clustered',
        'clustered_orders_test.json',
    )
    num_requests = 4
    futures = send_parallel_requests(file_path, num_requests)

    responses = [future.result() for future in futures]
    for response in responses:
        print(response)
