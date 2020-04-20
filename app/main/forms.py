from flask_wtf import FlaskForm
from app.models import User, Activity
from wtforms import StringField, SelectField, DecimalField, IntegerField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange

class CreateActivityForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    activity_type = SelectField('Activity Type', validators=[DataRequired()],
                                choices=[('Run', 'Run'),
                                         ('Cross-country_ski', 'Cross-Country Ski'),
                                         ('Roller Ski', 'Roller Ski'),
                                         ('Ride', 'Ride'),
                                         ('Swim', 'Swim'),
                                         ('Walk', 'Walk')])
    distance = DecimalField('Distance', places=2, validators=[NumberRange(min=0.01, max=9999)])
    duration_hrs = SelectField('Hours', choices=[(val, val) for val in range(100)], coerce=int)
    duration_min = SelectField('Minutes', choices=[(val, val) for val in range(60)], coerce=int)
    duration_sec = SelectField('Seconds', choices=[(val, val) for val in range(60)], coerce=int)
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

# TODO add edit activity form