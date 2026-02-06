from environs import Env

env = Env()
env.read_env()

ROUTING_ENGINE = env("ROUTING_ENGINE", "http://206.189.14.139:5000")

GEOLOC_NOMINATIM_USER_AGENT = env("GEOLOC_NOMINATIM_USER_AGENT", "route_optimization")
GOOGLE_API_KEY = env("GOOGLE_API_KEY", "")
GEOLOC_OPENCAGE_API_KEY = env("GEOLOC_OPENCAGE_API_KEY", "")
MAPBOX_OSRM_API_KEYS = env("MAPBOX_OSRM_API_KEYS", "")
ORS_API_KEYS = env("ORS_API_KEYS", "")
GRAPHHOPPER_API_KEYS = env("GRAPHHOPPER_API_KEYS", "")


RATE_LIMIT = env.int("RATE_LIMIT", 50)

#DB
#
# MYSQL_SERVER = env("MYSQL_SERVER", "127.0.0.1:3306")
# MYSQL_USER = env("MYSQL_USER", "SOA_USER")
# MYSQL_PASSWORD = env("MYSQL_PASSWORD", "f*p=UG=`z8K5=}tp")
# MYSQL_DB = env("MYSQL_DB", "SOA")


MYSQL_SERVER = env("MYSQL_SERVER", "localhost:3306")
MYSQL_USER = env("MYSQL_USER", "root")
MYSQL_PASSWORD = env("MYSQL_PASSWORD", "iridia")
MYSQL_DB = env("MYSQL_DB", "SOA")

SQLALCHEMY_DATABASE_URI = (
    f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_SERVER}/{MYSQL_DB}"
)


# DOCUMENTATION
SOLUTION_ROUTING_STATUS_DESC = env("SOLUTION_ROUTING_STATUS_DESC","A list of solution routing statuses. Valid values: ")
SOLUTION_ROUTING_FROM_DATE_DESC = env("SOLUTION_ROUTING_FROM_DATE_DESC","The start date (inclusive) for filtering solution routing (YYYY-MM-DD).")
SOLUTION_ROUTING_TO_DATE_DESC = env("SOLUTION_ROUTING_TO_DATE_DESC","The end date (exclusive) for filtering solution routing (YYYY-MM-DD).")
SOLUTION_ROUTING_INCLUDE_REQUEST_DESC = env("SOLUTION_ROUTING_INCLUDE_REQUEST_DESC","Whether to include the request of the optimization.")
SOLUTION_ROUTING_INCLUDE_PARAMETERS_DESC = env("SOLUTION_ROUTING_INCLUDE_PARAMETERS_DESC","Whether to include the parameters of the optimization.")
