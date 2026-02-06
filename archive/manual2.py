import json
import logging
import os
from itertools import cycle
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import backoff
import requests.exceptions

from optimise.utils.routing.routers import ORS, Valhalla, Graphhopper, MapboxOSRM

routers = {
    'ors': {
        'api_keys': ['5b3ce3597851110001cf6248465cae97421842fe988ffffdf0b24967'],
        'profile': 'driving-car',
        'priority': 1,
        'max_batch_size': 50
    },
    'mapbox_osrm': {
        'api_keys': ['pk.eyJ1IjoibWJlbmhhZGRvdSIsImEiOiJjbGNrd3Z0aXMwZDdoM29ucnhxNGdmNWJiIn0.Np6oC7olN_b0LbFSpZhwwA'],
        'profile': 'driving',
        'priority': 2,
        'max_batch_size': 25
    },
    'google': {
        'api_keys': ['AIzaSyDo7hBFy00Z7OE4JncADlLoBgnW27or4yw'],
        'profile': 'driving',
        'priority': 5,
        'max_batch_size': 10
    },
    'graphhopper': {
        'api_keys': ['91ffd420-4919-4e4d-b3d4-805b98431f26'],
        'profile': 'car',
        'priority': 3,
        'max_batch_size': 25
    },
    'valhalla': {
        'profile': 'auto',
        'priority': 4,
        'max_batch_size': 50
    }
}



# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_file: str) -> Dict:
    """Load router configurations from a JSON file, handling file and parsing errors."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Failed to load or parse the configuration file: {str(e)}")
        raise

def initialize_router(router_name: str, config: Dict, key_iterator) -> 'Router':
    """
    Initialize the appropriate routing service client using an API key from a cyclic iterator.
    Handle router-specific initialization.
    """
    try:
        api_key = next(key_iterator)  # Get next key from the cyclic iterator
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
    except StopIteration:
        logging.error("API key iterator is exhausted.")
        raise

def get_distance_matrix_cached(coords: List[List[float]], routers: Dict, router_name: str = None) -> Dict:
    """ Returns the distance matrix between a set of coordinates using the specified routing service. """
    try:
        if router_name:
            router_config = routers.get(router_name)
            if not router_config:
                raise ValueError(f"Invalid router name: {router_name}")
            key_iterator = cycle(router_config['api_keys'])
            routers_to_try = [(router_name, router_config, key_iterator)]
        else:
            routers_to_try = [(name, config, cycle(config['api_keys'])) for name, config in sorted(routers.items(), key=lambda x: x[1]['priority'])]

        for name, config, key_iter in routers_to_try:
            api = initialize_router(name, config, key_iter)
            all_indices = range(len(coords))
            matrix = api.matrix(locations=coords, sources=all_indices, destinations=all_indices, profile=config['profile'])
            return matrix.distances
    except requests.exceptions.RequestException as e:
        logging.error(f"Network related error: {str(e)}")
    except Exception as e:
        logging.error(f"Error with {name}: {str(e)}")
    return {"error": "All routing services failed"}

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def get_distance_matrix_with_retry(coords: List[List[float]], routers: Dict, router_name: str = None) -> Dict:
    """
    Wrapper function to retry get_distance_matrix with exponential backoff.
    """
    return get_distance_matrix_cached(coords, routers, router_name)

def parallelize_requests(coords_sets: List[List[List[float]]], routers: Dict, max_workers: int = 4) -> List[Dict]:
    """ Parallelize distance matrix requests for multiple coordinate sets using ThreadPoolExecutor. """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(get_distance_matrix_with_retry, coords, routers) for coords in coords_sets]
        results = [future.result() for future in as_completed(futures)]
    return results

if __name__ == "__main__":
#    config_path = os.getenv("ROUTER_CONFIG_PATH", "config.json")
#    try:
#        routers = load_config(config_path)
#    except Exception as e:
#        logging.error(f"Failed to start the application due to config loading error: {str(e)}")
#        exit(1)

    # Example coordinate set
    coords = [
        [5.563765, 50.6351521],
        [5.587189088426131, 50.6345563],
        [5.587320607184397, 50.63491345],
        [5.587155115673761, 50.63449525],
        [5.5872764899579686, 50.6348796],
        [5.587085661311892, 50.6344432],
        [5.58723315271005, 50.63484595],
        [5.5870210239276155, 50.6343825],
        [5.5871646715309335, 50.63481135]
    ]

    # Get distance matrix for a single coordinate set
    try:
        result = get_distance_matrix_with_retry(coords, routers, 'graphhopper')
        logging.info("Single request result:")
        logging.info(result)
    except Exception as e:
        logging.error(f"Failed to fetch the distance matrix for the given coordinates: {str(e)}")


