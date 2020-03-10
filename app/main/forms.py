from flask_wtf import FlaskForm
from app.models import User, Activity
from wtforms import StringField, SelectField, DecimalField, IntegerField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError

class CreateActivityForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    activity_type = SelectField('Activity Type', validators=[DataRequired()],
                                choices=[('Running', 'Running'),
                                         ('Cross-country_skiing', 'Cross-Country Skiing'),
                                         ('Cycling', 'Cycling'),
                                         ('Swimming', 'Swimming'),
                                         ('Walking', 'Walking')])
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