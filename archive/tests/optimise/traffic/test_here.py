from optimise.routing.traffic.utils import get_traffic_data_url_for_lat_lon, fetch_traffic_data, HERE_API_KEY

import unittest

class TestRoutingTraffic(unittest.TestCase):
    def test_here_url(self):

        url="""https://1.traffic.maps.ls.hereapi.com/maptile/2.1/flowtile/20220923T150000/normal.day/7/68/41/256/png?apiKey={YOUR_API_KEY}""".format(YOUR_API_KEY=HERE_API_KEY)
        lat=52.52
        lon=13.405
        month=9
        day=23
        year=2022
        hour=15
        minute=0
        seconds=0

        _url=get_traffic_data_url_for_lat_lon(lat, lon, year, month, day, hour, minute, seconds,zoom=7)
        self.assertEqual(url,_url)


    def test_get_traffic_data(self):
        data = fetch_traffic_data(52.52, 13.405, year=2022, month=9, day=23, hour=15, minute=0, second=0)
        # with open("traffic_data.png", "wb") as file:
        #     file.write(data)


if __name__ == '__main__':
    unittest.main()
