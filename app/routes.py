from app import app, db
from app import data_processing
from app.forms import LoginForm, UploadForm, RegistrationForm, CreateActivityForm, EditProfileForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Activity
from flask import render_template, request, flash, url_for, redirect, session, g, abort
from werkzeug import secure_filename
from werkzeug.urls import url_parse
from datetime import datetime
from geojson import Point, Feature
import pandas as pd
import os, requests

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/')
@app.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    form = CreateActivityForm()
    page = request.args.get('page', 1, type=int)
    activities = current_user.follows_activities().paginate(
        page, app.config['ACTIVITIES_PER_PAGE'], False)
    next_url = url_for('index', page=activities.next_num) \
        if activities.has_next else None
    prev_url = url_for('index', page=activities.prev_num) \
        if activities.has_prev else None
    if form.validate_on_submit():
        duration = (form.duration_hrs.data * 3600) + (form.duration_min.data * 60) + form.duration_sec.data
        activity = Activity(title=form.title.data, activity_type=form.activity_type.data,
                            distance=form.distance.data, duration=duration,
                            user_id=current_user.id)
        db.session.add(activity)
        db.session.commit()
        flash('Your activity was successfully created!')
    return render_template("index.html", title="Home", form=form, activities=activities.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    activities = Activity.query.order_by(Activity.timestamp.desc()).paginate(
        page, app.config['ACTIVITIES_PER_PAGE'], False)
    next_url = url_for('index', page=activities.next_num) \
        if activities.has_next else None
    prev_url = url_for('index', page=activities.prev_num) \
        if activities.has_prev else None
    return render_template('index.html', title='Explore', activities=activities.items, next_url=next_url, prev_url=prev_url)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid Username or Password")
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegistrationForm()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User successfully created')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout', methods = ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/profile/<username>', methods=['GET', 'POST'])
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    activities = user.activities.order_by(Activity.timestamp.desc()).paginate(
        page, app.config['ACTIVITIES_PER_PAGE'], False)
    next_url = url_for('profile', username=user.username, page=activities.next_num) \
        if activities.has_next else None
    prev_url = url_for('profile', username=user.username, page=activities.prev_num) \
        if activities.has_prev else None
    return render_template('profile.html', title="Profile", user=user, page=page, activities=activities.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/bulk_upload', methods=['GET', 'POST'])
@login_required
def bulk_upload():
    form = UploadForm()
    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        form.file.data.save('{}'.format(app.config['UPLOAD_FOLDER']) + filename)
        data = pd.read_csv(('{}'.format(app.config['UPLOAD_FOLDER']) + filename), index_col=0)
        data = data_processing.Data_Cleanup(data)
        data_processing.map_to_database(data)
        os.remove('{}'.format(app.config['UPLOAD_FOLDER']) + filename)
        flash("Your upload was successful")
        redirect(url_for('bulk_upload'))
    return render_template('bulk_upload.html', title="Bulk Upload", form=form)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('profile', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('profile', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('profile', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('profile', username=username))

# MAPBOX_JS CODE TO TEST MAP FUNCTIONALITY
@app.route('/mapbox_js')
def mapbox_js():
    route_data, waypoints = get_route_data()
    stop_locations = create_stop_locations_details()
    return render_template(
        'mapbox_js.html',
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



