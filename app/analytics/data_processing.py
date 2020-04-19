import pandas as pd
from app import db, app
from app.analytics import bp
from app.models import Activity, User
from flask_login import current_user
from sqlalchemy import func, create_engine
from flask import render_template
from geojson import Point, Feature
import requests
import sqlite3
from flask.json import jsonify

@bp.route('/total_distance_per_activity/<user_id>')
def total_distance_per_activity(user_id):
    distance_per_activity = total_per_activity(Activity.distance, user_id)
    return jsonify(distance_per_activity)

@bp.route('/total_time_per_activity/<user_id>')
def total_time_per_activity(user_id):
    distance_per_activity = total_per_activity(Activity.duration, user_id)
    return jsonify(distance_per_activity)   

def Data_Cleanup(activities):
    activities.rename(
        columns={'Activity Date': 'activity_date', 'Activity Type': 'activity_type', 'Elapsed Time': 'elapsed_time'},
        inplace=True)
    activities["Distance"] = pd.to_numeric(activities["Distance"], errors="coerce")
    activities['activity_date'] = pd.to_datetime(activities['activity_date'])

    # drop_unused columns
    activities.drop(
        ['Activity Description', 'Activity Gear', 'Filename', 'Relative Effort', 'Commute'], axis=1,
        inplace=True)

    # fill null and 0 values

    swim_mps = 0.83
    activities['Distance'] = activities['Distance'].fillna((activities['elapsed_time'] * swim_mps) / 1000)

    ride_index = (activities['activity_type'] == "Ride") & (activities['Distance'] == 0)
    nordic_ski_index = (activities['activity_type'] == "Nordic Ski") & (activities['Distance'] == 0)
    roller_ski_index = (activities['activity_type'] == "Roller Ski") & (activities['Distance'] == 0)

    activities.loc[ride_index, 'Distance'] = (activities['elapsed_time'] * 27) / 3600
    activities.loc[nordic_ski_index, 'Distance'] = (activities['elapsed_time'] * 13) / 3600
    activities.loc[roller_ski_index, 'Distance'] = (activities['elapsed_time'] * 15) / 3600

    return activities

def map_to_database(data):
    for row in data.index:
        activity = Activity()
        activity.title = data['Activity Name'][row]
        activity.timestamp = data['activity_date'][row]
        activity.duration = int(data['elapsed_time'][row])
        activity.distance = data['Distance'][row]
        activity.activity_type = data['activity_type'][row]
        activity.user_id = current_user.id
        db.session.add(activity)
    db.session.commit()

def total_column(column, user_id):
    total_column = db.session.query(func.sum(column)). \
        filter(Activity.user_id == user_id).scalar()
    if total_column:
        total_column = round(total_column, 2)
    else:
        total_column = 0
    return total_column

def total_per_activity(column, user_id):
    acitvity_totals_list = []
    total_per_activity = db.session.query(Activity.activity_type, func.sum(column)). \
        filter(Activity.user_id == user_id).group_by(Activity.activity_type)
    for u in total_per_activity:
        acitvity_totals_list.append(u)
    activity_totals_dict = dict(acitvity_totals_list)
    return activity_totals_dict

def get_activities_by_date(from_year, from_month, from_day, to_year, to_month, to_day):
    from_date = pd.Timestamp(from_year, from_month, from_day)
    to_date = pd.Timestamp(to_year, to_month, to_day)
    filtered_activities = Activity.query.filter(Activity.timestamp.between(from_date, to_date))
    return filtered_activities

# MAPBOX_JS CODE TO TEST MAP FUNCTIONALITY (WIP)
@app.route('/mapbox_js')
def mapbox_js():
    route_data, waypoints = get_route_data()
    stop_locations = create_stop_locations_details()
    return render_template(
        'analytics/mapbox_js.html',
        ACCESS_KEY=app.config['MAPBOX_ACCESS_KEY'],
        route_data=route_data,
        stop_locations=stop_locations
    )

ROUTE = [
    {"lat": 64.0027441, "long": -22.7066262, "name": "Keflavik Airport", "is_stop_location": True},
    {"lat": 64.0317168, "long": -22.1092311, "name": "Hafnarfjordur", "is_stop_location": True},
    {"lat": 63.99879, "long": -21.18802, "name": "Hveragerdi", "is_stop_location": True},
    {"lat": 63.4194089, "long": -19.0184548, "name": "Vik", "is_stop_location": True},
    {"lat": 63.5302354, "long": -18.8904333, "name": "Thakgil", "is_stop_location": True},
    {"lat": 64.2538507, "long": -15.2222918, "name": "Hofn", "is_stop_location": True},
    {"lat": 64.913435, "long": -14.01951, "is_stop_location": False},
    {"lat": 65.2622588, "long": -14.0179538, "name": "Seydisfjordur", "is_stop_location": True},
    {"lat": 65.2640083, "long": -14.4037548, "name": "Egilsstadir", "is_stop_location": True},
    {"lat": 66.0427545, "long": -17.3624953, "name": "Husavik", "is_stop_location": True},
    {"lat": 65.659786, "long": -20.723364, "is_stop_location": False},
    {"lat": 65.3958953, "long": -20.9580216, "name": "Hvammstangi", "is_stop_location": True},
    {"lat": 65.0722555, "long": -21.9704238, "is_stop_location": False},
    {"lat": 65.0189519, "long": -22.8767959, "is_stop_location": False},
    {"lat": 64.8929619, "long": -23.7260926, "name": "Olafsvik", "is_stop_location": True},
    {"lat": 64.785334, "long": -23.905765, "is_stop_location": False},
    {"lat": 64.174537, "long": -21.6480148, "name": "Mosfellsdalur", "is_stop_location": True},
    {"lat": 64.0792223, "long": -20.7535337, "name": "Minniborgir", "is_stop_location": True},
    {"lat": 64.14586, "long": -21.93955, "name": "Reykjavik", "is_stop_location": True},
]

def create_route_url():
    # Create a string with all the geo coordinates
    lat_longs = ";".join(["{0},{1}".format(point["long"], point["lat"]) for point in ROUTE])
    # Create a url with the geo coordinates and access token
    url = app.config['ROUTE_URL'].format(lat_longs, app.config['MAPBOX_ACCESS_KEY'])
    return url

def get_route_data():
    # Get the route url
    route_url = create_route_url()
    # Perform a GET request to the route API
    result = requests.get(route_url)
    # Convert the return value to JSON
    data = result.json()

    # Create a geo json object from the routing data
    geometry = data["routes"][0]["geometry"]
    route_data = Feature(geometry=geometry, properties={})
    waypoints = data["waypoints"]
    return route_data, waypoints

def create_stop_locations_details():
    stop_locations = []
    for location in ROUTE:
        # Skip anything that is not a stop location
        if not location["is_stop_location"]:
            continue
        # Create a geojson object for stop location
        point = Point([location['long'], location['lat']])
        properties = {
            'title': location['name'],
            'icon': 'campsite',
            'marker-color': '#3bb2d0',
            'marker-symbol': len(stop_locations) + 1
        }
        feature = Feature(geometry = point, properties = properties)
        stop_locations.append(feature)
    return stop_locations




