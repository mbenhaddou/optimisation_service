# Geolocation and Geocoding – Detailed Documentation

## Overview

Geolocation in the routing solution is responsible for converting textual address information into latitude and longitude coordinates. This information is essential for building routing matrices and enabling accurate time and distance calculations between work orders and depots.

## Components Involved

- `geocoding.py`: Main logic for geolocation
- `geopy`: External library to access different geocoding services
- `geo_entries_crud`: Local cache backed by a database to store past geocoding results
- `config.defaults`: Stores API keys and rate limits

## Workflow

### 1. Address Standardization

The function `address_str(address_dict)` constructs a full address string from fields like `street`, `postalcode`, `city`, and `country`.

```python
def address_str(address_dict):
    return f"{address_dict['street']}, {address_dict['postalcode']} {address_dict['city']}, {address_dict['country']}"
```

### 2. Caching and Retrieval

Before querying external services, the system checks if a cached location is available using a hash of the address. This prevents redundant API calls and speeds up processing.

```python
if ENABLE_GEOCODING_CACHE:
    lat_long = geo_entries_crud.get(session, geo_entries_crud.hash_key(address_str(address_dict)))
```

If no valid cache is found or if geolocation failed previously, a new request is triggered.

### 3. Geocoding Strategy

The function `geocode_addresses()` cycles through several providers in priority order, starting with a default (usually `"nominatim"`) and falling back if needed:

- Nominatim (OpenStreetMap)
- Mapbox
- OpenCage
- Google Maps

```python
services = {
    "nominatim": geoloc_nominatim,
    "mapbox": geoloc_mapbox,
    "opencage": geoloc_opencage,
    "google": geoloc_google
}
```

### 4. Rate Limiting

The `@rate_limited(RATE_LIMIT)` decorator is applied to control the request rate to each service. This helps avoid being banned or throttled by APIs.

### 5. Validation and Postcode Matching

If the `postcode` returned from the geolocation result does not match the input, the result is rejected:

```python
if "postcode" in address_dict and "address" in geoloc.raw:
    postcode_service = str(geoloc.raw["address"].get("postcode", "")).replace(" ", "")
    postcode_dict = str(address_dict.get("postalcode", "")).replace(" ", "")
    if postcode_service != postcode_dict:
        geoloc = None
```

### 6. Result Storage

Successful geocoding results are stored in the cache for future reuse.

---

## Configuration

Key values in `defaults.py` include:

- `ENABLE_GEOCODING_CACHE`: Toggle local result storage
- `RATE_LIMIT`: Max number of API calls per second
- `DEFAULT_GEOCODING_SERVICE`: Fallback strategy (e.g., `"nominatim"` or `"google"`)

---

## Fallback Logic

If a geolocation attempt fails, the system retries using other providers in sequence. Logs are generated for each failed service call to help trace issues.

---

## Summary

Geolocation is handled in a modular, fault-tolerant way, with caching and validation steps ensuring reliability and API efficiency. This enables robust support for walking/driving matrix construction and time estimations in the optimization core.

## Cascading Fallback Mechanism

The geolocation system is designed with resilience in mind. It uses a cascading fallback strategy to maximize the chances of resolving valid coordinates even when certain services fail or rate-limit.

### Geocoding Fallback Logic

1. **Address Hashing & Caching**: 
   - The address is first converted into a string using fields like `street`, `postalcode`, `city`, and `country`.
   - A hash of the address is checked against a cache (`geo_entries_crud`) to avoid repeated external lookups.

2. **Primary Lookup**: 
   - The default provider is used (e.g., `nominatim` or as specified by `DEFAULT_GEOCODING_SERVICE`).

3. **Validation**: 
   - The returned geolocation is validated by comparing postcodes between the returned and input address.
   - If the result is deemed incorrect, it is discarded.

4. **Fallback Sequence**:
   - If the primary lookup fails or is invalidated, the following services are tried in order:
     - `nominatim`
     - `mapbox`
     - `opencage`
     - `google`
   - Each geolocator is tried sequentially until a valid result is returned or all options are exhausted.

5. **Rate Limiting**:
   - Each geolocator function is decorated with `@rate_limited(RATE_LIMIT)` to avoid being throttled or blocked.

6. **Logging**:
   - Each fallback attempt and result is logged to provide traceability and for debugging service failures.

This mechanism ensures high availability of coordinates with graceful degradation.