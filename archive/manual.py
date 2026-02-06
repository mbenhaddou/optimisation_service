import json
import logging
from typing import Dict, List, Tuple
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import backoff
from itertools import combinations

from optimise.utils.routing.routers import ORS, Valhalla, Graphhopper, MapboxOSRM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

routers = {
    'ors': {
        'api_key': '5b3ce3597851110001cf6248465cae97421842fe988ffffdf0b24967',
        'profile': 'driving-car',
        'priority': 1
    },
    'mapbox_osrm': {
        'api_key': 'pk.eyJ1IjoibWJlbmhhZGRvdSIsImEiOiJjbGNrd3Z0aXMwZDdoM29ucnhxNGdmNWJiIn0.Np6oC7olN_b0LbFSpZhwwA',
        'profile': 'driving',
        'priority': 2
    },
    'google': {
        'api_key': 'AIzaSyDo7hBFy00Z7OE4JncADlLoBgnW27or4yw',
        'profile': 'driving',
        'priority': 5
    },
    'graphhopper': {
        'api_key': '91ffd420-4919-4e4d-b3d4-805b98431f26',
        'profile': 'car',
        'priority': 3
    },
    'valhalla': {
        'profile': 'auto',
        'priority': 4
    }
}


import json
import logging
from typing import Dict, List, Tuple
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import backoff
from itertools import combinations
from pprint import pprint
from optimise.utils.routing.routers import ORS, Valhalla, Graphhopper, MapboxOSRM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_file):
    """Load router configurations from a JSON file."""
    with open(config_file) as f:
        return json.load(f)

def initialize_router(router_name: str, config: Dict) -> 'Router':
    """
    Initialize the appropriate routing service client.
    """
    if router_name == 'ors':
        return ORS(api_key=config['api_key'])
    elif router_name == 'mapbox_osrm':
        return MapboxOSRM(api_key=config['api_key'])
    elif router_name == 'graphhopper':
        return Graphhopper(api_key=config['api_key'])
    elif router_name == 'valhalla':
        # Assuming Mentis uses a Valhalla-like service at a custom URL
        return Valhalla(base_url="https://mentis.io/routing")
    else:
        raise ValueError(f"Unsupported router: {router_name}")

def get_distance_matrix_cached(source: List[List[float]],destination: List[List[float]], routers: Dict, router_name: str = None) -> Dict:
    """
    Returns the distance matrix between a set of coordinates using the specified routing service.
    If no router_name is provided, tries each router based on priority until one succeeds.
    """
    if router_name:
        # Single router specified, use it directly
        router_config = routers.get(router_name)
        if not router_config:
            raise ValueError(f"Invalid router name: {router_name}")
        routers_to_try = [(router_name, router_config)]
    else:
        # Sort routers by priority and prepare to try them in order
        routers_to_try = sorted(routers.items(), key=lambda x: x[1]['priority'])

    for name, config in routers_to_try:
        try:
            api = initialize_router(name, config)
            all_indices_source = list(range(len(source)))
            all_indices_destination = list(range(len(destination)))
            matrix = api.matrix(
                locations=coords,
                sources=all_indices_source,
                destinations=all_indices_destination,
                profile=config['profile']
            )
            return matrix.distances  # Assuming you want the distances; use matrix.durations for times
        except Exception as e:
            # Log error and try the next router
            logging.error(f"Error with {name}: {str(e)}")

    return {"error": "All routing services failed"}

@backoff.on_exception(backoff.expo, Exception, max_tries=5)
def get_distance_matrix_with_retry(source: List[List[float]],destination: List[List[float]],  routers: Dict, router_name: str = None) -> Dict:
    """
    Wrapper function to retry get_distance_matrix with exponential backoff.
    """
    return get_distance_matrix_cached(source,destination, routers, router_name)

def get_distance_matrix_batched(coords_src: List[List[float]], coords_dst: List[List[float]], routers: Dict, router_name: str = None, batch_size: int = 25) -> Dict:
    """
    Returns the distance matrix between a set of source and destination coordinates by splitting the requests into batches.
    If the number of coordinates exceeds the batch_size, multiple requests are sent, and the results are collated.
    """
    router_config = routers.get(router_name)
    if not router_config:
        raise ValueError(f"Invalid router name: {router_name}")

    n_src = len(coords_src)
    n_dst = len(coords_dst)
    distance_matrix = [[float('inf')] * n_dst for _ in range(n_src)]

    # Calculate the number of batches for source and destination coordinates
    num_src_batches = (n_src + batch_size - 1) // batch_size
    num_dst_batches = (n_dst + batch_size - 1) // batch_size

    for src_batch_idx in range(num_src_batches):
        src_start = src_batch_idx * batch_size
        src_end = min(src_start + batch_size, n_src)
        src_batch_coords = coords_src[src_start:src_end]
        src_batch_indices = list(range(src_start, src_end))

        for dst_batch_idx in range(num_dst_batches):
            dst_start = dst_batch_idx * batch_size
            dst_end = min(dst_start + batch_size, n_dst)
            dst_batch_coords = coords_dst[dst_start:dst_end]
            dst_batch_indices = list(range(dst_start, dst_end))

            # Get the sub-matrix for the current source and destination batches
            submatrix = get_distance_matrix_with_retry(src_batch_coords, dst_batch_coords, routers, router_name)

            # Fill the corresponding entries in the complete distance matrix
            for i, row in enumerate(submatrix):
                for j, value in enumerate(row):
                    distance_matrix[src_start + i][dst_start + j] = value

    return distance_matrix

def parallelize_requests(coords_sets: List[List[List[float]]], routers: Dict, max_workers: int = 4) -> List[Dict]:
    """
    Parallelize distance matrix requests for multiple coordinate sets.
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(get_distance_matrix_with_retry, coords, routers) for coords in coords_sets]
        results = [future.result() for future in as_completed(futures)]
    return results

if __name__ == "__main__":
    # Load configurations from a JSON file
#    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
#    routers = load_config(config_file)

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


    # Get distance matrix with batched requests
    batch_size = 4
    batched_result = get_distance_matrix_batched(coords, coords, routers, 'graphhopper', batch_size)
    logging.info("Batched request result:")
    logging.info(batched_result)

    pprint(batched_result)