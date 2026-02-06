## Scheduling
Scheduling assign tasks to a team of workers called a work center.
the structure of the request is as follows:

```
{
  "workorders":[],
  "workcenters": [],
  "date_format": "%Y-%m-%d %H:%M:%S",
  "period_start": "2022-01-10",
  "nb_of_days_ahead": 5,
  "time_unit": "hours",
  "day_starts_at": 6,
  "day_ends_at": 16
}
```
###  work orders

A work order have the following data
```
    {
      "WONUm": "WO1",
      "Priority": 1,
      "StockAvailabilityDate": "2022-01-10",
      "RequiredStartDate": "2022-01-10",
      "RequiredStartTime": "06:00:00",
      "RequiredFinishDate": "2021-01-30",
      "RequiredFinishTime": "00:30:00",
      "operations": [
       
      ]
    }


```

- __WONUm__ (string): an identifier for the the work order
- __Priority__ (int): an interger to indicate the priority, the lower the integer the higher the priority
- __StockAvailabilityDate__ ("2022-01-10"): the availability of the thing necessary for the job (spare part for example)
- __RequiredStartDate__ ("2022-01-10"): the work order has to start after this date
- __RequiredStartTime__ ("06:00:00"): the work order has to start after this hour
- __RequiredFinishDate__ ("2021-01-30"): the work order have to  finish befor e this date
- __RequiredFinishTime__ ("00:30:00"): the work order have to finish before this time

The work order is composed of a set of operations. The operations have to be executed in the order in which they apear in the list.

The following is an example of an operation:`
```
        {
          "OPNum": 2,
          "WorkCenter": "wc_3",
          "city": "Namur",
          "street": "Rue du Temple 4 H",
          "postal_code": 5000,
          "WODesc": "CLIENT SANS EAU (1\u00e8re ligne)",
          "Duration": 3,
          "DurationUnit":  "hours",
          "Workload": 3
        }
```

An operation have an id *OPNum*, a *WorkCenter* that will execute it, an address, a *Duration* (how long is the task) and a *Workload* (how many effort the task requires). Both *Duration* and *Workload* are expressed in hours.


### Work Centers
 the work center section of the request is showed bellow.
```
    {
      "WorkCenter": "wc_1",
      "WC_Description": "Descr",
      "Schedule": [
        {
          "Date": "2022-10-01",
          "StartTime": "06:00:00",
          "EndTime": "10:00:00",
          "DayOff": false,
          "Capacity": 8,
          "Workload":1
        },
        {
          "Date": "2022-10-02",
          "StartTime": "08:00:00",
          "EndTime": "09:00:00",
          "DayOff": false,
          "Capacity": 8,
          "Workload":0
        },
        {
          "Date": "2022-10-03",
          "StartTime": "12:00:00",
          "EndTime": "16:00:00",
          "DayOff": false,
          "Capacity": 8,
          "Workload":0
        },
        {
          "Date": "2022-10-04",
          "StartTime": "",
          "EndTime": "",
          "DayOff": false,
          "Capacity": 8,
          "Workload":0
        },
        {
          "Date": "2022-10-05",
          "StartTime": "",
          "EndTime": "",
          "DayOff": false,
          "Capacity": 8,
          "Workload":0
        }
      ]
    },
```

the work center have a schedule for each day.
the schedule is the workload already in the work center agenda. it has the following parameters:

- __Date__ ("2022-10-05"): the exact day of this schedule
- __StartTime__ (10:00:00): the start of the schedule (not taken into account)
- __EndTime__ (12:00:00): the end time of the schedule (not taken into account)
- __DayOff__ (false/true): if yes this day is Off the work center is not working
- __Capacity__ (int): the capacity of the work center that day
- __Workload__ (int): the workload already reserved that day
