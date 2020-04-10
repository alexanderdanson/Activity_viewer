import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_PATH = 100000
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['alex.danson2@gmail.com']
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')

    ACTIVITIES_PER_PAGE = 10

    #MAPBOX_JS CONFIG
    MAPBOX_ACCESS_KEY = 'pk.eyJ1IjoiYWxleGRhbnNvbiIsImEiOiJjazc2NWtvNnYwOG12M3RwZjMzdTVxZ3hhIn0.rFr105-gwEKcArfbJ10jqg'
    ROUTE_URL = "https://api.mapbox.com/directions/v5/mapbox/driving/{0}.json?access_token={1}&overview=full&geometries=geojson"
