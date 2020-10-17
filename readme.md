# GTFS route speed calculation in Python3

---

![image](assets/GTFS_post_title_600x200@2x.png)

## about

current [GTFS](https://gtfs.org/best-practices/#introduction) feeds are versitle in describing the operating and routing of the public transit services on trip planning and servicing schedules. while the specification has been made public and is widely adopted by cities and trip planning agencies, the interpretibility of the feeds requires proprietary softwares that had few expandability. the idea of this open-source project is to expand and build upon my experience working closely with GTFS feeds in Python.

## `route_speed.py`

this simple script allows for the bus route speed calculation with a user input of either a valid `route_short_name`, `route_id`, or `trip_id` that describe a particular bus route of interest with the GTFS feed at hand. the script used the [Haversine formula](https://en.wikipedia.org/wiki/Haversine_formula) to determine the great-circle distance between two points on a sphere like the earth given their longitudes and latitudes, which are common geocoordinate metric adopted when generating the GTFS feeds.

in practice, an unique `trip_id` is usually sufficient to determine one unique bus trip operating on a (assumed to be) fixed route and its corresponding shape/[LingString](https://shapely.readthedocs.io/en/latest/manual.html#linestrings) object if a `shapes.txt` is provided in the valid GTFS feeds. however, the `trip_id` usually varies a lot and carries little to no meaning across GTFS feeds, so `route_short_name` and `route_id` are also available options for convenience.

- if a valid `route_short_name` or `route_id` is given, the current implementation select the first available `trip_id` from the `trips.txt`.
- `stops.txt` can also be used for an estimate of straight-line distance between stops for a given route when the `shapes.txt` is not available. this alternative is being developed.


### getting started

first proceed to install the dependencies in a conda env needed for the script.

```bash
$ pip install -r requirements.txt
```

#### command line usage

```bash
$ python3 route_speed.py -r <route_short_name> -rid <route_id> -tid <trip_id> -t <hour of departure> -d <day of week> -p <abs_path_to_gtfs> -s <True/False>
```

- `-r` or `--route_short_name`: the **route_short_name** of the target bus route for route speed estimate, string;
- `-rid` or `--route_id`: the **route_id** of the target bus route for route speed estimate, np.int64;
- `-tid` or `--trip_id`: the **trip_id** of the target bus route for route speed estimate, string;
- `-p` or `--path`: the **absolute path** to the GTFS feed directory, if none is provided, will be using the current directory as the feed directory, string;
- `-t` or `--time`: the specific hour of trip departure, np.int64, *optional*;
- `-d` or `--day`: a day in the week, *optional*;
  - ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
- `-s` or `--shape`: whether a `shape.txt` is used for the route distance estimate, if `False` then it will use `stops.txt` for less accurate estimate [under development as of 10/02/2020].
- either **one** valid `route_short_name`, `route_id`, or `trip_id` is sufficient.
- ...

#### jupyter notebook usage

- open a notebook anywhere locally, and navigate to the directory where this repo is cloned. 

```bash
from route_speed import get_avg_route_speed

get_avg_route_speed(route_short_name, route_id, trip_id, absolute path, hasShape, hour, day)
```
Refer to [this example usage notebook](https://github.com/jarviskroos7/GTFS-route-speed/tree/main/example) for more examples
