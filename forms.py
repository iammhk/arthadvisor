from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Email, Optional
from flask_wtf.file import FileField, FileAllowed

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    phone = StringField('Phone', validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ResetPasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Reset Password')

class ProfileForm(FlaskForm):
    username = StringField('Username', render_kw={'readonly': True})
    full_name = StringField('Full Name', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    profile_pic = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    submit = SubmitField('Update Profile')

class SettingsForm(FlaskForm):
    risk_appetite = StringField('Risk Appetite', validators=[Optional()])
    goal_short_term = StringField('Short Term Goal', validators=[Optional()])
    goal_medium_term = StringField('Medium Term Goal', validators=[Optional()])
    goal_long_term = StringField('Long Term Goal', validators=[Optional()])
    submit = SubmitField('Save Settings')

