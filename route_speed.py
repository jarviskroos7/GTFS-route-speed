import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

import logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

import warnings
warnings.filterwarnings("ignore")
error_msg = 'failed to calculate route speed: '

# set default path to be the current directory where GTFS feed is assumed to be stored
path_default = os.getcwd()

def get_avg_route_speed(route_short_name=None, route_id=None, trip_id=None, path=path_default, hasShape=False, hour=None, day=None):

    os.chdir(path)
    try:
        routes = pd.read_csv('routes.txt')
        trips = pd.read_csv('trips.txt')
        stop_times = pd.read_csv('stop_times.txt')
        calendar = pd.read_csv('calendar.txt')
        if hasShape == True:
            shapes = pd.read_csv('shapes.txt')
        else:
            pass
    except:
        #logging.error(error_msg, 'not all required feed files exist, check your feed or directory before running the script')
        sys.exit(f"{error_msg} not all required feed files exist, check your feed or directory before running the script")
        return

    ## TODO: implement estimated route distance calculation with stops.txt only
    if hasShape == False:
        pass

    if type(route_short_name) is str and route_short_name != '':
        print("- for bus route with route_short_name:", route_short_name, "...")
        return speed_short_name(route_short_name, routes, trips, stop_times, shapes, calendar, hour, day)
    elif type(route_id) is np.int64:
        print("- for bus route with route_id", route_id, "...")
        return speed_route_id(route_id, routes, trips, stop_times, shapes, calendar, hour, day)
    elif type(trip_id) is str and trip_id != '':
        print("- for trip_id", trip_id, "...")
        return speed_trip_id(trip_id, trips, route_id, stop_times, shapes, calendar, day)
    elif route_short_name == None and route_id == None and trip_id == None:
        sys.exit(f"{error_msg} missing valid trip/route identifier")
        #logging.error(error_msg, 'missing valid trip/route identifier')
        return

def haversine_distance(lat1, lon1, lat2, lon2):
    
    """ Haversine distance determines the great-circle distance between two points on a 
        sphere given their longitudes and latitudes

    Keyword arguments:
    lat1 -- latitude of first point
    lon1 -- longitude of first point
    lat2 -- latitude of second point
    lon2 -- longitude of second point
    """
    
    r = 6371 # earth equater length, according to Google

    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)

    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2)**2    
    res = r * (2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))

    return res * 0.621371 # unit in km --> mile

def speed_trip_id(trip_id, trips, route_id, stop_times, shapes, calendar, day):
    try:
        trips_route = trips.loc[trips['trip_id'] == trip_id]

        if day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            service_id = check_day_of_week(trips_route, trips, calendar, day, route_id, trip_id=trip_id)
            trips_route = trips_route.loc[trips_route['service_id'] == service_id]
        elif day == None or day == False:
            pass
        else:
            #logging.error(error_msg, "invalid 'day' parameter was given.")
            sys.exit(f"{error_msg} invalid 'day' parameter was given")
            return

        shape_id = trips_route.shape_id.iloc[0]
        shapes_route = shapes.loc[shapes['shape_id'] == shape_id]

        lat_prev, lon_prev = shapes_route.iloc[0].shape_pt_lat, shapes_route.iloc[0].shape_pt_lon
        distance = 0

        # looping through all rows in the shape points and calculate distance between each other
        for index, row in shapes_route.iterrows():
            lat_curr = shapes_route.loc[index].shape_pt_lat
            lon_curr = shapes_route.loc[index].shape_pt_lon
            
            distance += haversine_distance(lat_prev, lon_prev, lat_curr, lon_curr)
            
            lat_prev = lat_curr
            lon_prev = lon_curr

        print('* route distance=', distance, 'miles')
        
        route_travel_time = get_route_travel_time(trip_id, stop_times)

        route_speed_avg = (distance / (route_travel_time / 60)) * 60
        print('.')
        print('.')
        print('.')
        print('result: average route speed of specified bus route =', route_speed_avg, 'mph')
        return route_speed_avg
    except Exception as e:
        print(str(e))
        #logging.error(error_msg, 'input trip_id does not exist or invalid values are given')
        sys.exit(f"{error_msg} input trip_id does not exist or invalid values are given")
        return

def get_route_travel_time(trip_id, stop_times):

    stop_times_trip = stop_times[stop_times['trip_id'] == trip_id]
    
    stop_times_trip['arrival_time'] = pd.to_datetime(stop_times_trip['arrival_time'], format='%H:%M:%S', errors='coerce')
    stop_times_trip.sort_values(by='arrival_time', inplace=True)

    start = stop_times_trip.iloc[0, 1]
    end = stop_times_trip.iloc[-1, 1]

    duration = end - start
    duration_in_s = duration.total_seconds()

    print('* route travel time =', duration_in_s, 'seconds')
    return duration_in_s


def speed_route_id(route_id, routes, trips, stop_times, shapes, calendar, hour, day):

    
    try:
        trips_route = trips.loc[trips['route_id'] == route_id]

        if day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            service_id = check_day_of_week(trips_route, trips, calendar, day, route_id)
            trips_route = trips_route.loc[trips_route['service_id'] == service_id]
            day = False
        elif day is None:
            logging.info('no specific day of week was given, selecting trips at an arbitary available service')
            pass
        else:
            #logging.error(error_msg, "invalid 'day' parameter was given.")
            sys.exit(f"{error_msg} invalid 'day' parameter was given")

        trip_id_random = trips_route.reset_index().loc[0, 'trip_id'] # extract the first trip_id with input route_id for now
        if hour:
            print('-- at hour:', hour)
            try:
                merged = trips_route[['trip_id']].merge(stop_times[['trip_id', 'arrival_time']], how='left', on='trip_id')
                merged['arrival_time'] = pd.to_datetime(merged['arrival_time'], format='%H:%M:%S', errors='coerce')
                merged['date_hour'] = merged['arrival_time'].dt.hour
                merged_trip_route =  merged.loc[merged['date_hour'] == hour].sort_values(by='date_hour')
                trip_id_random = merged_trip_route.reset_index().loc[0, 'trip_id'] # extract the first trip_id with input route_id for now
                print('actual departing time of trip', trip_id_random, ':', str(merged_trip_route.loc[merged_trip_route['trip_id'] == trip_id_random]['arrival_time'].dt.time.iloc[1]))
            except Exception as e:
                #logging.error(error_msg, 'no trips were available at input departing hour')
                sys.exit(f"{error_msg} no trips were available at hour {hour}")
                return
        else:
            logging.info('no specific hour was given, selecting trips at an arbitary departing time...')
        return speed_trip_id(trip_id_random, trips_route, route_id, stop_times, shapes, calendar, day)
    except Exception as e:
        print(str(e))
        return
    

def speed_short_name(route_short_name, routes, trips, stop_times, shapes, calendar, hour, day):

    try:
        route_id = routes.loc[routes['route_short_name'] == route_short_name].route_id.iloc[0]
        return speed_route_id(route_id, routes, trips, stop_times, shapes, calendar, hour, day)
    except:
        #logging.error(f"{error_msg} input route_short_name does not exist or invalid values are given")
        sys.exit(f"{error_msg} input route_short_name {route_short_name} does not exist or invalid values are given")

def check_day_of_week(trips_route, trips, calendar, day, route_id, trip_id=None):

    status = False

    for service_id in trips_route.service_id.unique():
        service = calendar.loc[calendar['service_id'] == service_id]
        
        if service[day].iloc[0] == 1: # should only be returning on row here
            print('-- service is available on', day, 'for route', route_id)
            print('-- cauculating route speed on', day)
            status = True
            return service_id
    if status == False:
        if route_id:
            sys.exit(f"no available service of route {route_id} is found on {day}")
        else:
            #logging.error(error_msg, 'no available service of trip', trip_id, 'is found on', day)
            sys.exit(f"no available service of trip {trip_id} is found on {day}")
    


parser = argparse.ArgumentParser()

parser.add_argument("--route_short_name", "-r", help="set route_short_name")
parser.add_argument("--route_id", "-rid", help="set route_id")
parser.add_argument("--trip_id", "-tid", help="set trip_id")
parser.add_argument("--path", "-p", help="set absolute path to the GTFS feed")
parser.add_argument("--shape", "-s", help="tell the program if distance is to be calculated from shapes.txt")
parser.add_argument("-t", "--time", help="calculate route speed at certain hour, optional")
parser.add_argument("-d", "--day", help="calculate route speed at given day of week, optional")
parser.add_argument("-f", "--fff", help="a dummy argument to fool ipython", default="1")


# Read arguments from the command line
args = parser.parse_args()
route_short_name = None
route_id = None
trip_id = None
time_in_hour = None
day = None
shape = False


if args.path:
    path_default = args.path
    print("GTFS route speed calculation script: loaded!")
    print()
    logging.info(f"- set absolute path to GTFS feeds to {args.path}")
else:
    print("GTFS route speed calculation script: loaded!")
    print(f"default feed path {os.getcwd()}")
    logging.warning(f"no path was inputed, set absolute path to GTFS feeds to current directory {path_default}")

if args.shape:
    shape = True
    print("- using provided shapes.txt: %s" % args.shape)
else:
    logging.warning("no shapes.txt exists in the GTFS feed provided, will be using stops.txt for straightline route disatnce approximation")

if args.time:
    time_in_hour = args.time
    print("- calculating route speed at hour: %s" % args.time)

if args.day:
    day = args.day
    print("- calculating route speed operating on: %s" % args.day)
    
if args.route_short_name:
    route_short_name = args.route_short_name
    print("- set route_short_name to %s" % args.route_short_name)
elif args.route_id:
    route_id = args.route_id
    print("- set route_id to %s" % args.route_id)
elif args.trip_id:
    trip_id = args.trip_id
    print("- set trip_id to %s" % args.trip_id)



def main(route_short_name, route_id, trip_id, path_default, shape, hour, day):
    return get_avg_route_speed(route_short_name=route_short_name, 
    route_id=route_id, trip_id=trip_id, path=path_default, hasShape=shape, hour=hour, day=day)



if __name__ == "__main__":
    main(route_short_name, route_id, trip_id, path_default, shape, time_in_hour, day)   