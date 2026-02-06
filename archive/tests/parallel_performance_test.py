import datetime
import json
import time
import requests
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
import os

host = 'http://localhost:5051'


def send_request(data):
    url = f'{host}/soa/routing'
    headers = {'Content-Type': 'application/json'}
    start_time = time.time()
    response = requests.post(url, headers=headers, data=json.dumps(data))
    end_time = time.time()
    response_time = end_time - start_time

    if response.status_code == 200:
        response_json = response.json()
        solution_routing_id = response_json.get('solution_routing_id', None)
        if solution_routing_id:
            status, _ = check_solution_status(solution_routing_id)
            return status, response_time
    return None, response_time


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


def measure_performance(metrics, duration):
    process = psutil.Process()
    start_time = time.time()

    while time.time() - start_time < duration:
        cpu_usage = process.cpu_percent(interval=0.1)
        memory_usage = process.memory_info().rss / (1024 * 1024)  # Convert to MB
        metrics['cpu'].append(cpu_usage)
        metrics['memory'].append(memory_usage)


def main():
    file_path = os.path.join(
        os.path.dirname(__file__),
        'optimise',
        'data',
        'clustered',
        'clustered_orders_test.json',
    )
    results = []

    for num_requests in range(1, 33):
        print(f"Running test with {num_requests} concurrent requests")

        metrics = {'cpu': [], 'memory': []}
        response_times = []

        # Start performance measurement in a separate thread
        duration = 10  # Measure for 10 seconds
        performance_thread = threading.Thread(target=measure_performance, args=(metrics, duration))
        performance_thread.start()

        start_time = time.time()
        futures = send_parallel_requests(file_path, num_requests)
        responses = [future.result() for future in futures]
        end_time = time.time()

        response_time=end_time-start_time
        # Wait for the performance measurement thread to finish
        performance_thread.join()

        peak_cpu = max(metrics['cpu']) if metrics['cpu'] else 0
        peak_memory = max(metrics['memory']) if metrics['memory'] else 0
        avg_response_time = response_time / num_requests

        results.append((num_requests, peak_cpu, peak_memory, avg_response_time, response_time))

        # Output the responses and performance metrics
        for response in responses:
            print(response)
        print(
            f"Concurrent Requests: {num_requests}, Peak CPU: {peak_cpu}%, Peak Memory: {peak_memory}MB, Avg Response Time: {avg_response_time}s, Response Time: {response_time}s")

    # Print final results
    print("\nFinal Results:")
    for num_requests, peak_cpu, peak_memory, avg_response_time in results:
        print(
            f"Concurrent Requests: {num_requests}, Peak CPU: {peak_cpu}%, Peak Memory: {peak_memory}MB, Avg Response Time: {avg_response_time}s")


if __name__ == "__main__":
    main()
