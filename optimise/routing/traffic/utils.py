import math
import requests

HERE_API_KEY = "kOY9XX1AYVJgMx0xQYIlslkR9eFlIcolASsKUsaH2HY"

def latlon_to_tile_xy(latitude, longitude, zoom):
    """
    Convert latitude and longitude to tile x, y coordinates for a given zoom level.
    Based on Web Mercator projection.
    """
    tile_x = int((longitude + 180) / 360 * (2 ** zoom))
    tile_y = int(
        (1 - math.log(math.tan(math.radians(latitude)) + 1 / math.cos(math.radians(latitude))) / math.pi) / 2 * (
                    2 ** zoom))
    return tile_x, tile_y


def get_traffic_data_url_for_lat_lon(latitude, longitude, year=None, month=None, day=None, hour=None, minute=None, second=None, zoom=7, scheme='normal.day', size=256, format_='png'):

    """
    Construct the URL to retrieve traffic data from HERE Technologies centered around a given latitude and longitude.
    Optional parameters for year, month, day, hour, minute, and second are for historical data.
    Default zoom level is 7, scheme is 'normal.day', size is 256, and format is 'png'.
    """
    tile_x, tile_y = latlon_to_tile_xy(latitude, longitude, zoom)

    # Construct the date-time string if date-time parameters are provided
    datetime_str = "newest"
    if year and month and day:
        datetime_str = f"{year:04}{month:02}{day:02}"
        if hour is not None and minute is not None and second is not None:
            datetime_str += f"T{hour:02}{minute:02}{second:02}"

    # Construct the URL using f-string formatting
    server_num = 1
    url = f"https://{server_num}.traffic.maps.ls.hereapi.com/maptile/2.1/flowtile/{datetime_str}/{scheme}/{zoom}/{tile_x}/{tile_y}/{size}/{format_}?apiKey={HERE_API_KEY}"

    return url

def fetch_traffic_data(latitude, longitude, year=None, month=None, day=None, hour=None, minute=None,
                       second=None, zoom=7):
    url = get_traffic_data_url_for_lat_lon(latitude, longitude, year, month, day, hour, minute, second, zoom)

    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        return response.content
    else:
        return f"Error: {response.status_code} - {response.text}"