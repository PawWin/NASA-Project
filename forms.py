from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class RegistrationForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired(), Length(min=2, max=300)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators = [DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class PickConstellationForm(FlaskForm):
    constellation = SelectField(u'Reports', choices=[('Andromeda', 'Andromeda'), ('Aquarius', 'Aquarius'), ('Aquila', 'Aquila'),
                                                     ('Aries', 'Aries'), ('Cancer', 'Cancer'), ('Canis Major', 'Canis Major'),
                                                     ('Capricorn', 'Capricorn'), ('Cassiopeia', 'Cassiopeia'), ('Cygnus', 'Cygnus'),
                                                     ('Gemini', 'Gemini'), ('Leo', 'Leo'), ('Libra', 'Libra'), ('Lyra', 'Lyra'),
                                                     ('Orion', 'Orion'), ('Pisces', 'Pisces'), ('Sagittarius', 'Sagittarius'),
                                                     ('Scorpion', 'Scorpius'), ('Taurus', 'Taurus'), ('Ursa Major', 'Ursa Major'),
                                                     ('Ursa Minor', 'Ursa Minor'), ('Virgo', 'Virgo')])
    submit = SubmitField('Submit')


class ImageForm(FlaskForm):
    submit = SubmitField('Submit')


class DateSelectForm(FlaskForm):
    selected_date = DateField('Wybierz datę', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Wyślij')

