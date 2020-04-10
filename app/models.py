from app import app, db, login
from datetime import datetime
from time import time
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5

followers = db.Table('followers',
                         db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                         db.Column('follows_id', db.Integer, db.ForeignKey('user.id'))
                         )

likes = db.Table('likes',
                        db.Column('athlete_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                        db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True)
                         )

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    activities = db.relationship('Activity', backref='athlete', lazy='dynamic')
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    follows = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.follows_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    liked_activities = db.relationship(
        'Activity', secondary=likes,
        backref=db.backref('liked_by', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.follows.append(user)

    def like(self, activity):
        if not self.likes_activity(activity):
            self.liked_activities.append(activity)

    def unfollow(self, user):
        if self.is_following(user):
            self.follows.remove(user)

    def unlike(self, activity):
        if self.likes_activity(activity):
            self.liked_activities.remove(activity)

    def is_following(self, user):
        return self.follows.filter(
            followers.c.follows_id == user.id).count() > 0

    def likes_activity(self, activity):
        return self.liked_activities.filter(
            likes.c.activity_id == activity.id).count() > 0

    def follows_activities(self):
        follows = Activity.query.join(
            followers, (followers.c.follows_id == Activity.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Activity.query.filter_by(user_id=self.id)
        return follows.union(own).order_by(Activity.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    title = db.Column(db.String, index=True)
    activity_type = db.Column(db.String(64), index=True)
    distance = db.Column(db.Float)
    duration = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login.user_loader
def load_user(id):
    return User.query.get(int(id))