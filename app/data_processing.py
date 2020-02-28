import pandas as pd
from app import db
from app.models import Activity
from flask_login import current_user

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

def Data_Cleanup(activities):
    activities.rename(
        columns={'Activity Date': 'activity_date', 'Activity Type': 'activity_type', 'Elapsed Time': 'elapsed_time'},
        inplace=True)
    activities["Distance"] = pd.to_numeric(activities["Distance"], errors="coerce")
    #activities['activity_date'] = pd.to_datetime(activities['activity_date'], format="%b %d, %Y, %I:%M:%S %p")
    activities['activity_date'] = pd.to_datetime(activities['activity_date'])

    # Convert seconds to hours
    activities["time_in_hours"] = activities['elapsed_time'].div(3600)

    # drop_unused columns
    activities.drop(
        ['Activity Description', 'Activity Gear', 'Filename', 'Relative Effort', 'Commute'], axis=1,
        inplace=True)

    # handle null values in distance
    # inspect null values
    activities.loc[activities['Distance'].isnull()]

    # all null values are Swimming, so fill with estimated swimming distances
    swim_mps = 0.83
    activities['Distance'] = activities['Distance'].fillna((activities['elapsed_time'] * swim_mps) / 1000)

    # Some values are 0 which we can estimate a distance for

    ride_index = (activities['activity_type'] == "Ride") & (activities['Distance'] == 0)
    nordic_ski_index = (activities['activity_type'] == "Nordic Ski") & (activities['Distance'] == 0)
    roller_ski_index = (activities['activity_type'] == "Roller Ski") & (activities['Distance'] == 0)

    activities.loc[ride_index, 'Distance'] = activities['time_in_hours'] * 27
    activities.loc[nordic_ski_index, 'Distance'] = activities['time_in_hours'] * 13
    activities.loc[roller_ski_index, 'Distance'] = activities['time_in_hours'] * 15

    return activities