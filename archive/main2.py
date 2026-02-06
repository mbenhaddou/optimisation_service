import json
import logging
import os
from itertools import cycle
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import backoff
import requests.exceptions
from pprint import pprint
from diskcache import Cache

# Assuming import paths for router classes are correct
from optimise.utils.routing.routers import ORS, Valhalla, Graphhopper, MapboxOSRM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

cache = Cache('./matrix_distance_cache')

from pprint import pprint
routers = {
    'ors': {
        'api_key': '5b3ce3597851110001cf6248465cae97421842fe988ffffdf0b24967',
        'profile': 'driving-car',
        'priority': 2,
        'max_batch_size': 50
    },
    'mapbox_osrm': {
        'api_key': 'pk.eyJ1IjoibWJlbmhhZGRvdSIsImEiOiJjbGNrd3Z0aXMwZDdoM29ucnhxNGdmNWJiIn0.Np6oC7olN_b0LbFSpZhwwA',
        'profile': 'driving',
        'priority': 4,
        'max_batch_size': 25
    },
    'google': {
        'api_key': 'AIzaSyDo7hBFy00Z7OE4JncADlLoBgnW27or4yw',
        'profile': 'driving',
        'priority': 5,
        'max_batch_size': 10
    },
    'graphhopper': {
        'api_key': '91ffd420-4919-4e4d-b3d4-805b98431f26',
        'profile': 'car',
        'priority': 3,
        'max_batch_size': 25
    },
    'osrm': {
        'api_key': '',
        'profile': 'driving',
        'priority': 1,
        'max_batch_size': 50
    }
}

def load_config(config_file):
    """Load router configurations from a JSON file."""
    with open(config_file) as f:
        return json.load(f)

def get_batches(total_count: int, batch_size: int) -> List[Tuple[int, int]]:
    """Generate start and end indices for each batch given the total number of items and the batch size."""
    return [(i, min(i + batch_size, total_count)) for i in range(0, total_count, batch_size)]

#@lru_cache(maxsize=500)  # Cache size can be adjusted based on your environment and needs
def fetch_submatrix(api, coords: List[List[float]], sources: List[int], destinations: List[int], profile: str) -> List[List[float]]:
    """Fetch a submatrix using the API, with caching via diskcache."""
    key = (tuple(map(tuple, coords)), tuple(sources), tuple(destinations), profile)
    if key in cache:
        return cache[key]
    matrix = api.matrix(
        locations=coords,
        sources=sources,
        destinations=destinations,
        profile=profile
    )
    cache[key] = matrix
    return matrix

def get_distance_matrix_batches(coords: List[List[float]], router_api, router_config) -> List[List[float]]:
    num_coords = len(coords)
    max_batch_size = router_config['max_batch_size']
    profile = router_config['profile']
    full_matrix = {}
    full_matrix['durations'] = [[0] * num_coords for _ in range(num_coords)]
    full_matrix['distances'] = [[0] * num_coords for _ in range(num_coords)]
    origin_batches = get_batches(num_coords, max_batch_size)
    destination_batches = get_batches(num_coords, max_batch_size)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for origin_batch in origin_batches:
            for destination_batch in destination_batches:
                origin_batch_indices = list(range(origin_batch[0], origin_batch[1]))
                destination_batch_indices = list(range(destination_batch[0], destination_batch[1]))
                # Submitting fetch_submatrix to ThreadPoolExecutor
                future = executor.submit(
                    fetch_submatrix,
                    router_api,
                    coords,
                    origin_batch_indices,
                    destination_batch_indices,
                    profile
                )
                futures.append((future, origin_batch, destination_batch))

        # Retrieve results from futures and build the full matrix
        for future, origin_batch, destination_batch in futures:
            result = future.result()
            for i, origin_index in enumerate(range(origin_batch[0], origin_batch[1])):
                full_matrix['distances'][origin_index][destination_batch[0]:destination_batch[1]] = result.distances[i]
                full_matrix['durations'][origin_index][destination_batch[0]:destination_batch[1]] = result.durations[i]

    return full_matrix


def initialize_router(router_name: str, config: Dict, key_iterator):
    api_key = next(key_iterator)  # Get next key from the cyclic iterator
    try:
        if router_name == 'ors':
            return ORS(api_key=api_key)
        elif router_name == 'mapbox_osrm':
            return MapboxOSRM(api_key=api_key)
        elif router_name == 'graphhopper':
            return Graphhopper(api_key=api_key)
        elif router_name == 'valhalla':
            return Valhalla(base_url="https://mentis.io/routing")
        else:
            raise ValueError(f"Unsupported router: {router_name}")
    except Exception as e:
        logging.error(f"Failed to initialize router {router_name} with API Key {api_key}: {e}")
        raise


@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException,
                      max_tries=5,
                      giveup=lambda e: not isinstance(e, requests.exceptions.ConnectionError))
def get_distance_matrix_with_retry(coords: List[List[float]], routers: Dict, router_name: str = None) -> Dict:
    if router_name:
        routers_to_try = [(router_name, routers.get(router_name))]
    else:
        # Sort routers by priority if no specific router_name is supplied
        routers_to_try = sorted(routers.items(), key=lambda item: item[1]['priority'])

    for name, router_config in routers_to_try:
        if not router_config:
            continue  # Skip if router configuration is not found

        try:
            key_iterator = cycle(router_config['api_keys'])
            router_api = initialize_router(name, router_config, key_iterator)
            result = get_distance_matrix_batches(coords, router_api, router_config)
            if result:
                return result  # Return the first successful result
        except requests.exceptions.RequestException as e:
            logging.error(f"Network related error with {name}: {str(e)}")
            continue  # Continue with the next router in case of network error
        except Exception as e:
            logging.error(f"Error with {name}: {str(e)}")
            continue  # Continue with the next router in case of other errors

    return {"error": "All routing services failed or no valid router configurations found."}


if __name__ == "__main__":
#    config_path = os.getenv("ROUTER_CONFIG_PATH", "config.json")
#    try:
#        routers = load_config(config_path)
#    except Exception as e:
#        logging.error(f"Failed to start the application due to config loading error: {str(e)}")
#        exit(1)

    coords = [
        [5.563765, 50.6351521],
        [5.587189088426131, 50.6345563],
        [5.58723315271005, 50.63484595],
        [5.587320607184397, 50.63491345],
        [5.587155115673761, 50.63449525],
        [5.5872764899579686, 50.6348796],
        [5.587085661311892, 50.6344432],
        [5.587021023927615, 50.6343825],
        [5.5871646715309335, 50.63481135],
        [5.5871646715309345, 50.63481125]
    ]

    try:
        result = get_distance_matrix_with_retry(coords, routers, 'osrm')
        logging.info("Single request result:")
        logging.info(result)
    except Exception as e:
        logging.error(f"Failed to fetch the distance matrix for the given coordinates: {str(e)}")

pprint(result)