# Import all the models, so that Base has them before being
# imported by Alembic


from solution_routing.solution_routing_model  import SolutionRouting
from geocode_entries.geo_entries_model import GeoEntries