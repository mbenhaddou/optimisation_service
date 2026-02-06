# Routing

[Input Data](#input-data)

[Output Data](#output-data)

# Input data
•	A company has teams and each team has a number of employees
•  Each team has depot. All employees will start from the depot and return to the depot
```
"teams": {
        "team_1": {
            "workers": [],
            "depot": {
                "id": "depot_t1",
                "city": "",
                "street": "",
                "postal_code": 0000,
                "longitude": 45.6661,
                "latitude": 5.32245
            }
        },
        "team_2": {
            "workers": [
            ],
            "depot": {
            }
        },
   
```
•   A worker has a set of skills, an address and a set of blocket times (time slot where the worker is not available)
```
                {
                   "e_id": 152,
                    "skills": [
                        "QERDV"
                    ],
                    "city": "Namur",
                    "street": "Avenue Vauban 43",
                    "postal_code": 5000,
                    "day_starts_at": "08:00:00",
                    "day_ends_at": "16:00:00",
                    "pause_starts_at": "16:00:00",
                    "pause_ends_at": "16:00:00",

                    "blocked_times": [
                            "blocked_date": "2022-01-10",
                            "blocked_start": "08:00:00",
                            "blocked_end": "12:00:00"
                    ]
                    "shifts": [
                          {
                            "shift_date": "2024-01-18",
                            "shift_start": "08:00:00",
                            "shift_end": "16:00:00",
                            "pause_start": "12:00:00",
                            "pause_end": "13:00:00"
                          },
                          {
                            "shift_date": "2024-01-19",
                            "shift_start": "08:00:00",
                            "shift_end": "16:00:00",
                            "pause_start": "12:00:00",
                            "pause_end": "13:00:00"
                          }
                        ],
                }
```

•	a List of work orders that need to be assigned to the workers
•	Every wortk order need to be executed in a specific location specified by an addresse. 
```
    "orders": [
        {
            "id": 20186616,
            "priority": 2,
            "skill": "PLOMBIER",
            "city": "Namur",
            "street": "Tienne de Bouge 5",
            "postal_code": 5004,
            "description": "SORTIE EAU VOIRIE/TROTTOIR (1ère ligne)",
            "work_hours": 1.0,
            "earliest_start_date": "2022-01-10",
            "earliest_start_time": "06:00:00",
            "latest_end_date": "2021-01-30",
            "latest_end_time": "00:30:00",
            "must_start_date": "2022-01-10",
            "must_start_time": "07:00:00",
            "must_end_date": "2022-01-10",
            "must_end_time": "10:30:00",
            "earliest_machine_availability_date": "0",
            "earliest_machine_availability_time": "0",
            "latest_machine_availability_date": "0",
            "latest_machine_availability_time": "0",
            "spare_part_available_date": "0"
        },
        {
        },

```
• Every work order have the following parameters:

- priority: currently still not taken into account
- Skill: the skill needed to execute the job
- city, street, postal_code are the elements of the addresse
- work_hours is the duration that the work would take
- earliest_start_date: the earliest date (dd-mm-yyy) that the job can start
- earliest_start_time: the earliest start hour in the start date (HH:MM:SS)
- latest_end_date: the latest date that the job order have to be performed
- latest_end_time: the latest hour the in  the latest day that the job have to be executed
- must_start_date: currently not used
- must_end_date: currently not used

When the job depends on the availability of a machine that us subject to the intervention, we can set the machine availability period start and end.

- earliest_machine_availability_date: 
- latest_machine_availability_date
- earliest_machine_availability_time
- latest_machine_availability_time


### Global optimizer options


The following option need to be specified in then input json file.

- __period_start__ ("yyyy-mm-dd"): the start date of the optimisation period. The jobs will be scheduled starting this date. 
- __optimization_horizon__  (int): the  number of days of the optimization. The tasks will be scheduled in the period of days starting from __start_date__
- __depot__: the address of the depot, if a team does not have a depot defines, the optimiser will use this global depot
- __start_at_depot__ (true/false): if true all the workers would start form the depot
- __end_at_depot__ (true/false): if true all the worker would end their tour at the depot
- __time_unit__ (hours/minutes) - *default: "hours"*: the working duration are expressed the specified unit
- __date_format__ ("%Y-%m-%d %H:%M:%S"): specify the format of the dates supplied in the json file
- __optimization_target__ ("duration/distance") -*default: "duration"* : specify weather the optimiser will minimize distance or travel time.
- __allow_slack__ (2) amount of time (in the same unit as *time_unit*) an employee is allowed to wait between visits (does not include travel time)
- __distribute_load__ (false/true): if false the optimizer will minimize the usage if workers, it true the opitimiser will use all available workers and give them the same amount of jobs 
- __minimize_vehicles__ (false/true): similar to setting the __distribute_load__ to false
- __time_limit__ (in minutes/hours): the maximum time that the solver will spend on the optimisation, per day
- __result_type__  ("fast", "optimized", "best) -*default "fast": "fast" uses quick heuristics  for the optimisation. "optimized" uses the best heuristics to find a solution, this  take more time than "fast". "best" runs multiple (4) optimized instances in parallel and selects the best run.
- __no_improvement_limit__ (int) -*default (100)*: the maximu number of steps the optimisation  runs without improvement in the results before stpping.

## Output Data

The output is a dictionary / json format organised as follows :

- <_date_> : the date of the routing, there will be typically as many dates as **optimization_horizon**
  - it is a list
  - it is empty if no visit/orders are schedule that day
  - otherwise, it is a list of dictionaries with the following key-values :
    - _id_ : this is the **worker**'s id
    - _adresse_ : this is the **worker**'s address
    - _longitude_ : the worker's address's longitude
    - _latitude_ : the worker's address's latitude
    - _total_distance_ : the total distance driven for the day *(I think)*
    - _tour_driving_time_ : the total driving time for the day *(I think, in ??? minutes ??? )*
    - _total_tour_time_ : the total time for the tour of the day *(in minutes?)*
    - _tour_start_time_ : starting time of the tour (HH:MM)
    - _tour_end_time_ : ending time of the tour or work day (HH:MM)
    - _total_slack_ : number of minutes of waiting between orders
    - _tour_steps_ : a list of dictionaries : the places the worker visits that day
      - _distance_so_far_ : the total distance driven at that step in the route
      - _travel_time_so_far_ : the total time used to travel at that step in the route
      - _slack_time_so_far_ : the total waiting time (slack time) at the step in the route
      - _node_ : a dictionary describing the place. Its keys are : 
        - 'id' : the id of the node, could be a home address, a depot or an order address
        - 'step_number' : the step number, starting from 0
        - 'address' : the address of this place
        - 'latitude' : the latitude of this place
        - 'longitude' : the longitude of this place
        - 'date' : the date of the visit
        - 'traveled_distance_from_last_node' : how much was driven from the previous place
        - 'travel_time_from_last_node' : how much time was used to drive from the previous place
        - 'service_end_time' : the time (HH:MM) at which the worker leaves the place
        - 'service_start_time' : the time (HH:MM) at which the worker arrives at the place
        - 'wait_time' : the time (in minutes?) the worker waits
- _message_ : a dictionary with each date a key, and the value a string describing the routes of the date
- _dropped_ : a list of dropped work orders that are not included in the schedule.
Each work-order dropped is a dictionary which includes in particular the 'id', 'address', 'latitude',
'longitude' and 'reason_for_not_scheduling' (other keys are present but not relevant)
- _errors_ : a list of string that are the errors met during the process
