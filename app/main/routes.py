from flask_login import current_user, login_required
from flask import request, url_for, render_template, flash, redirect
from app.main import bp
from app.main.forms import UploadForm, CreateActivityForm, EditProfileForm
from app import app, db
from app.analytics import data_processing
from app.models import Activity, User
from datetime import datetime
import pandas as pd


#TODO move "like" and "follow" functionality to own blueprint called "social" 

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@bp.route('/')
@bp.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    activities = current_user.follows_activities().paginate(
        page, app.config['ACTIVITIES_PER_PAGE'], False)
    next_url = url_for('main.index', page=activities.next_num) \
        if activities.has_next else None
    prev_url = url_for('main.index', page=activities.prev_num) \
        if activities.has_prev else None
    return render_template("index.html", title="Home", activities=activities.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    # pie_keys, pie_values = data_processing.total_per_activity(current_user.id)
    users = User.query.order_by(User.last_seen.desc()).paginate(
        page, app.config['ACTIVITIES_PER_PAGE'], False)
    next_url = url_for('main.explore', page=users.next_num) \
        if users.has_next else None
    prev_url = url_for('main.explore', page=users.prev_num) \
        if users.has_prev else None
    return render_template('explore.html', title='Explore', users=users.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/profile/<username>', methods=['GET', 'POST'])
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    activities = user.activities.order_by(Activity.timestamp.desc()).paginate(
        page, app.config['ACTIVITIES_PER_PAGE'], False)
    total_distance = data_processing.total_column(Activity.distance, user.id)
    total_time = data_processing.total_column(Activity.duration, user.id)
    next_url = url_for('main.profile', username=user.username, page=activities.next_num) \
        if activities.has_next else None
    prev_url = url_for('main.profile', username=user.username, page=activities.prev_num) \
        if activities.has_prev else None
    return render_template('profile.html', title="Profile", user=user, page=page, activities=activities.items,
                           total_distance=total_distance, total_time=total_time,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/bulk_upload', methods=['GET', 'POST'])
@login_required
def bulk_upload():
    form = UploadForm()
    if form.validate_on_submit():
        data = pd.read_csv(form.file.data, index_col=0)
        data = data_processing.Data_Cleanup(data)
        data_processing.map_to_database(data)
        flash("Your upload was successful")
        return redirect(url_for('main.bulk_upload'))
    return render_template('bulk_upload.html', title="Bulk Upload", form=form)

@bp.route('/manual_upload', methods=['GET', 'POST'])
@login_required
def manual_upload():
    form = CreateActivityForm()
    if request.method == 'GET':
        form.title.data = "New Activity"
    if form.validate_on_submit():
        duration = (form.duration_hrs.data * 3600) + (form.duration_min.data * 60) + form.duration_sec.data
        activity = Activity(title=form.title.data, activity_type=form.activity_type.data,
                            distance=form.distance.data, duration=duration,
                            user_id=current_user.id)
        db.session.add(activity)
        db.session.commit()
        flash('Your activity was successfully created!')
        return redirect(url_for('main.index'))
    return render_template('manual_upload.html', title="Manual Activity Upload", form=form)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('main.profile', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(request.referrer)

@bp.route('/like/<activity_id>')
@login_required
def like(activity_id):
    activity = Activity.query.filter_by(id=activity_id).first()
    if activity is None:
        flash('Activity {} not found.'.format(activity.title))
    if current_user.likes_activity(activity):
        current_user.unlike(activity)
        flash('You no longer like {}!'.format(activity.title))
    else:
        current_user.like(activity)
        flash('You like {}!'.format(activity.title))
    db.session.commit()
    return redirect(request.referrer)

@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('main.profile', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(request.referrer)

@bp.route('/delete_activity/<activity_id>')
@login_required
def delete_activity(activity_id):
    activity = Activity.query.filter_by(id=activity_id).first()
    if activity.athlete.id == current_user.id:
        db.session.delete(activity)
        db.session.commit()
        flash('The following activity was successfully deleted: {}'.format(activity.title))
    else:
        flash('Stop trying to delete other peoples\' activities!')
    return redirect(request.referrer)



# TODO add edit activity functionality