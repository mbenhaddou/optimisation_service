from typing import Dict, Any, List
from optimise.routing.defaults import DEFAULT_GEOCODING_SERVICE
from optimise.utils.geocoding import get_geolocation, address_str
from optimise.utils.dates import days_ahead_from_date, date_from_string, add_time_with_max_end_of_day
from optimise.routing.preprocessing.handle_workorders import set_and_geolocate_address
def set_and_geolocate_depot(team: Dict[str, Any], default_service="nominatim", enable_geocoding: bool = True) -> None:
    address_dict = {
        'street': team['depot']['street'],
        'city': team['depot']['city'],
        'country': team['depot']['country'],
        'postalcode': team['depot']['postal_code']
    }
    team['depot']['address'] = address_str(address_dict)
    has_coords = isinstance(team['depot'].get('latitude'), (float, int)) and isinstance(
        team['depot'].get('longitude'), (float, int)
    )
    if has_coords:
        return
    if not enable_geocoding:
        raise ValueError("Missing depot latitude/longitude and geocoding is disabled")
    team['depot'].update(get_geolocation(address_dict, default_service=default_service))


def process_worker(worker: Dict[str, Any], team: Dict[str, Any], request: Dict[str, Any], enable_geocoding: bool = True) -> None:
    worker['depot'] = team.get('depot', request.get('depot'))
    worker['team'] = team['name']
    # address_dict = {
    #     'street': worker['street'],
    #     'city': worker['city'],
    #     'country': worker['country'],
    #     'postalcode': worker['postal_code']
    # }
    # worker['address'] = address_str(address_dict)
    #
    # worker.update(get_geolocation(address_dict))
    set_and_geolocate_address(
        worker,
        geolocation_service=request['geocoding_service'],
        enable_geocoding=enable_geocoding,
    )
    if worker['day_starts_at'] in ["0", "", None]:
        worker['day_starts_at'] = "00:00:00"
    if worker['day_ends_at'] in ["0", "", None]:
        worker['day_ends_at'] = "23:59:59"
    if worker['pause_starts_at'] in ["0", "", None]:
        worker['pause_starts_at'] = "00:00:00"
    if worker['pause_ends_at'] in ["0", "", None]:
        worker['pause_ends_at'] = "00:00:00"

    for bt in worker['blocked_times']:
        bt['blocked_date'] = date_from_string(bt['blocked_date'], format_string=request['date_format'])
        bt['blocked_start'] = date_from_string(bt['blocked_start'], request['date_format'].split()[1]).time()
        bt['blocked_end'] = date_from_string(bt['blocked_end'], request['date_format'].split()[1]).time()

    for shift in worker['shifts']:
        shift['shift_date'] = date_from_string(shift['shift_date'], format_string=request['date_format'])
        shift['shift_start'] = date_from_string(shift['shift_start'], request['date_format'].split()[1]).time()
        shift['shift_end'] = date_from_string(shift['shift_end'], request['date_format'].split()[1]).time()
        shift['pause_start'] = date_from_string(shift['pause_start'], request['date_format'].split()[1]).time()
        shift['pause_end'] = date_from_string(shift['pause_end'],
                                                          request['date_format'].split()[1]).time()
        shift['optional']=shift.get('optional', False)

    worker['day_starts_at'] = date_from_string(worker.get('day_starts_at', '00:00:00'), request['date_format'].split()[1]).time()
    worker['day_ends_at'] = date_from_string(worker.get('day_ends_at', '23:59:59'), request['date_format'].split()[1]).time()
    worker['pause_starts_at'] = date_from_string(worker.get('pause_starts_at', '00:00:00'), request['date_format'].split()[1]).time()
    worker['pause_ends_at'] = date_from_string(worker.get('pause_ends_at', '00:00:00'), request['date_format'].split()[1]).time()


def handle_teams_and_workers(request: Dict[str, Any], errors=None, enable_geocoding: bool = True) -> None:
    if errors is None:
        errors = []
    workers_list=[]
    for team_name, team_details in request['teams'].items():
        team_details['name']=team_name
        set_and_geolocate_depot(team_details, request['geocoding_service'], enable_geocoding=enable_geocoding)
        for worker in team_details['workers']:
            process_worker(worker, team_details, request, enable_geocoding=enable_geocoding)
            workers_list.append(worker)

    return workers_list
