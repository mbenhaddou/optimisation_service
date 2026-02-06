import json
import logging
import os
from itertools import cycle
from typing import Dict, List, Tuple

import backoff
import requests.exceptions
from diskcache import Cache
from pprint import pprint

from optimise.routing.defaults import ENABLE_DISTANCE_MATRIX_CACHE, DISTANCE_MATRIX_CACHE_DIR

try:
    from config.defaults import ROUTING_ENGINE
    from config import defaults as config
except ModuleNotFoundError:
    ROUTING_ENGINE = os.getenv("ROUTING_ENGINE", "http://localhost:5000")

    class _Config:
        ORS_API_KEYS = os.getenv("ORS_API_KEYS", "")
        MAPBOX_OSRM_API_KEYS = os.getenv("MAPBOX_OSRM_API_KEYS", "")
        GRAPHHOPPER_API_KEYS = os.getenv("GRAPHHOPPER_API_KEYS", "")
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

    config = _Config()

# # Load environment variables from .env file
# load_dotenv()
# Assuming import paths for router classes are correct
from optimise.utils.routing.routers import ORS, Graphhopper, MapboxOSRM, OSRM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_cache = None


def _get_cache():
    global _cache
    if _cache is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cache_dir = DISTANCE_MATRIX_CACHE_DIR
        if not os.path.isabs(cache_dir):
            cache_dir = os.path.join(base_dir, cache_dir)
        _cache = Cache(cache_dir)
    return _cache



def get_api_keys(key_name):
    keys = getattr(config, key_name, '')
    return keys.split(',')


routers = {
    'ors': {
        'api_keys': get_api_keys('ORS_API_KEYS'),
        'profile': 'driving-car',
        'priority': 2,
        'max_batch_size': 25
    },
    'mapbox_osrm': {
        'api_keys': get_api_keys('MAPBOX_OSRM_API_KEYS'),
        'profile': 'driving',
        'priority': 4,
        'max_batch_size': 25
    },
    'google': {
        'api_keys': [os.getenv('GOOGLE_API_KEY')],
        'profile': 'driving',
        'priority': 5,
        'max_batch_size': 10
    },
    'graphhopper': {
        'api_keys': get_api_keys('GRAPHHOPPER_API_KEYS'),
        'profile': 'car',
        'priority': 3,
        'max_batch_size': 25
    },
    'osrm': {
        'api_keys': [''],  # Assuming OSRM is locally hosted and does not require an API key
        'profile': 'auto',
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

    if ENABLE_DISTANCE_MATRIX_CACHE:
        cache = _get_cache()
        key = (tuple(map(tuple, coords)), tuple(sources), tuple(destinations), profile)
        if key in cache:
            res=cache[key]
            if res.distances[0][0] is None:
                del cache[key]
            else:
                return res
    matrix = api.matrix(
        locations=coords,
        sources=sources,
        destinations=destinations,
        profile=profile
    )
    if ENABLE_DISTANCE_MATRIX_CACHE:
        cache = _get_cache()
        cache[key] = matrix
    return matrix


def get_distance_matrix_batches(coords: List[List[float]], router_api, router_config) -> Dict:
    num_coords = len(coords)
    max_batch_size = router_config['max_batch_size']
    profile = router_config['profile']
    full_matrix = {'durations': [[0] * num_coords for _ in range(num_coords)],
                   'distances': [[0] * num_coords for _ in range(num_coords)]}

    origin_batches = get_batches(num_coords, max_batch_size)
    destination_batches = get_batches(num_coords, max_batch_size)

    for origin_batch in origin_batches:
        for destination_batch in destination_batches:
            origin_batch_indices = list(range(origin_batch[0], origin_batch[1]))
            destination_batch_indices = list(range(destination_batch[0], destination_batch[1]))
            result = fetch_submatrix(router_api, coords, origin_batch_indices, destination_batch_indices, profile)

            for i, origin_index in enumerate(origin_batch_indices):
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
        elif router_name == 'osrm':
            return OSRM(base_url=ROUTING_ENGINE)
        else:
            raise ValueError(f"Unsupported router: {router_name}")
    except Exception as e:
        logging.error(f"Failed to initialize router {router_name} with API Key {api_key}: {e}")
        raise


@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException,
                      max_tries=5,
                      giveup=lambda e: not isinstance(e, requests.exceptions.ConnectionError))
def get_distance_matrix_with_retry(coords: List[List[float]], routers: Dict=routers, router_name: str = None) -> Dict:
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

    raise Exception("All routing services failed or no valid router configurations found")


if __name__ == "__main__":
#    config_path = os.getenv("ROUTER_CONFIG_PATH", "config.json")
#    try:
#        routers = load_config(config_path)
#    except Exception as e:
#        logging.error(f"Failed to start the application due to config loading error: {str(e)}")
#        exit(1)

    # coords = [
    #     [5.563765, 50.6351521],
    #     [5.587189088426131, 50.6345563],
    #     [5.58723315271005, 50.63484595],
    #     [5.587320607184397, 50.63491345],
    #     [5.587155115673761, 50.63449525],
    #     [5.5872764899579686, 50.6348796],
    #     [5.587085661311892, 50.6344432],
    #     [5.587021023927615, 50.6343825],
    #     [5.5871646715309335, 50.63481135],
    #     [5.5871646715309345, 50.63481125]
    # ]

    coords = [[5.563804457746493, 50.63526246392369],
            [5.564626497568471, 50.63276915440556],
            [5.5576886887425365, 50.63184399154585],
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
