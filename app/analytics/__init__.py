from flask import Blueprint

bp = Blueprint('analytics', __name__)

from app.analytics import data_processing