from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,\
    FileField, DecimalField, DateTimeField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo, Length
from app.models import User, Activity

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('This username already exists, please use a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('A user already exists with this email address, please use another one.')


class CreateActivityForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    activity_type = SelectField('Activity Type', validators=[DataRequired()],
                                choices=[('running', 'Running'),
                                         ('cross-country_skiing', 'Cross-Country Skiing'),
                                         ('cycling', 'Cycling'),
                                         ('swimming', 'Swimming'),
                                         ('walking', 'Walking')])
    distance = DecimalField('Distance (KM)', places=2)
    duration_hrs = IntegerField('Hours')
    duration_min = IntegerField('Minutes')
    duration_sec = IntegerField('Seconds')
    submit = SubmitField('Submit')


class UploadForm(FlaskForm):
    file = FileField('File')
    submit = SubmitField('Upload')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
