from geopy.geocoders import Nominatim, GoogleV3, OpenCage, MapBox
import os
from optimise.routing.defaults import ENABLE_GEOCODING_CACHE, GEOLOC_CACHE_BACKEND, GEOLOC_LOCAL_CACHE_DIR
import time

import logging

logger = logging.getLogger("app")

from optimise.utils.decorators import rate_limited
from geocode_entries.geo_entries_CRUD import geo_entries_crud
from db.session import  db_session
from diskcache import Cache

try:
    from config import defaults as config
    from config.defaults import RATE_LIMIT
except ModuleNotFoundError:
    class _Config:
        GEOLOC_NOMINATIM_USER_AGENT = os.getenv("GEOLOC_NOMINATIM_USER_AGENT", "route_optimization")
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        GEOLOC_OPENCAGE_API_KEY = os.getenv("GEOLOC_OPENCAGE_API_KEY", "")
        MAPBOX_OSRM_API_KEYS = os.getenv("MAPBOX_OSRM_API_KEYS", "")

    config = _Config()
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", "50"))
#sql_cache_path = os.path.join(os.path.split(os.path.dirname(__file__))[0], 'cache', 'golocations')
# sql_cache = SqliteCache(sql_cache_path)

geoloc_nominatim = Nominatim(user_agent=config.GEOLOC_NOMINATIM_USER_AGENT)
geoloc_google = GoogleV3(api_key=config.GOOGLE_API_KEY)
geoloc_opencage = OpenCage(api_key=config.GEOLOC_OPENCAGE_API_KEY)
geoloc_mapbox = MapBox(api_key=config.MAPBOX_OSRM_API_KEYS)

_local_cache = None


def _get_local_cache():
    global _local_cache
    if _local_cache is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cache_dir = GEOLOC_LOCAL_CACHE_DIR
        if not os.path.isabs(cache_dir):
            cache_dir = os.path.join(base_dir, cache_dir)
        _local_cache = Cache(cache_dir)
    return _local_cache


def get_geolocation(address_dict, default_service="nominatim"):
    # address = address_str(address_dict)
    #
    # if not isinstance(address, str):
    #     return None

    if default_service != "google":
        default_service = "nominatim"
    session = None
    try:
        lat_long = None
        if ENABLE_GEOCODING_CACHE:
            key = geo_entries_crud.hash_key(address_str(address_dict))
            if GEOLOC_CACHE_BACKEND == "db":
                session = db_session()
                lat_long = geo_entries_crud.get(session, key)
            elif GEOLOC_CACHE_BACKEND == "local":
                lat_long = _get_local_cache().get(key)


        if lat_long is None or lat_long['latitude'] is None or lat_long['longitude'] is None:
            geoloc = geocode_addresses(address_dict, default_service=default_service)
            if geoloc is not None:
                lat_long = {"latitude": geoloc.latitude, "longitude": geoloc.longitude}
                if ENABLE_GEOCODING_CACHE:
                    if GEOLOC_CACHE_BACKEND == "db":
                        if session is None:
                            session = db_session()
                        geo_entries_crud.create(session, key, lat_long)
                    elif GEOLOC_CACHE_BACKEND == "local":
                        _get_local_cache().set(key, lat_long)
            else:
                lat_long = {"latitude": "", "longitude": ""}
        return lat_long
    except Exception as e:
        logger.error(e)
    finally:
        if session is not None:
            session.close()


@rate_limited(RATE_LIMIT)
def geocode_addresses(address_dict, default_service="nominatim"):
    services = {
        "nominatim": geoloc_nominatim,
        "mapbox": geoloc_mapbox,
        "opencage": geoloc_opencage,
        "google": geoloc_google
    }

    if default_service.lower() not in services:
        raise ValueError("Invalid default service specified")

    # Determine the order of services based on the default_service parameter
    ordered_services = [services[default_service.lower()]] + [services[key] for key in services if
                                                              key != default_service.lower()]

    for service in ordered_services:
        try:
            geoloc = service.geocode(address_str(address_dict))
            if geoloc is not None:
                # Check postcode if necessary
                if "postcode" in address_dict and "address" in geoloc.raw:
                    postcode_service = str(geoloc.raw["address"].get("postcode", "")).replace(" ", "")
                    postcode_dict = str(address_dict.get("postalcode", "")).replace(" ", "")
                    if postcode_service != postcode_dict:
                        geoloc = None
                        #continue
                return geoloc
        except Exception as e:
            logger.error(f"Error while using {service.__class__.__name__}: {e}")

    logger.info("No geoloc found")
    return None


@rate_limited(RATE_LIMIT)
def geocode_addresses_(address_dict):
    try:
        geoloc = geoloc_nominatim.geocode(address_dict, addressdetails=True)
        if geoloc is not None and (str(geoloc.raw["address"]["postcode"]).replace(" ", "") !=str(address_dict["postalcode"]).replace(" ", "")):
            geoloc = None
    except Exception as e:
        logger.error(e)
        geoloc = None
        pass
    if geoloc is None:
        try:
            geoloc = geoloc_mapbox.geocode(address_str(address_dict))
        except Exception as e:
            logger.error(e)
            geoloc = None
            pass
    if geoloc is None:
        try:
            geoloc = geoloc_opencage.geocode(address_str(address_dict))
        except Exception as e:
            logger.error(e)
            geoloc = None
            pass
    if geoloc is None:
        try:
            geoloc = geoloc_google.geocode(address_str(address_dict))
        except Exception as e:
            logger.error(e)
            raise e
    if geoloc is None:
        logger.info("No geoloc found")
    return geoloc


def address_str(address_dict):
    return f"{address_dict['street']}, {address_dict['postalcode']} {address_dict['city']}, {address_dict['country']}"
