from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from .momentjs import momentjs
import datetime


app = Flask(__name__)
app.config.from_object(Config)
bootstrap = Bootstrap(app)
login = LoginManager(app)
login.login_view = 'auth.login'
db = SQLAlchemy(app)
migrate = Migrate(app, db, compare_type=True)
mail = Mail(app)

# JINJA GLOBAL VARIABLES
app.jinja_env.globals['momentjs'] = momentjs
app.jinja_env.globals['datetime'] = datetime

# blueprints
from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)
from app.auth import bp as auth_bp
app.register_blueprint(auth_bp, url_prefix="/auth")
from app.main import bp as main_bp
app.register_blueprint(main_bp)
from app.analytics import bp as analytics_bp
app.register_blueprint(analytics_bp)

if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Activity Viewer Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/activity_viewer.log', maxBytes=10240,
                                               backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            app.logger.setLevel(logging.INFO)
            app.logger.info('Activity_Viewer startup')

from app import models
