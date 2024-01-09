from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class RegistrationForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired(), Length(min=2, max=300)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up',render_kw={"class": "btn-register"})

class LoginForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators = [DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login',render_kw={"class": "btn-favorite"})


class PickConstellationForm(FlaskForm):
    constellation = SelectField(u'Reports', choices=[('Andromeda', 'Andromeda'), ('Aquarius', 'Aquarius'), ('Aquila', 'Aquila'),
                                                     ('Aries', 'Aries'), ('Cancer', 'Cancer'), ('Canis Major', 'Canis Major'),
                                                     ('Capricorn', 'Capricorn'), ('Cassiopeia', 'Cassiopeia'), ('Cygnus', 'Cygnus'),
                                                     ('Gemini', 'Gemini'), ('Leo', 'Leo'), ('Libra', 'Libra'), ('Lyra', 'Lyra'),
                                                     ('Orion', 'Orion'), ('Pisces', 'Pisces'), ('Sagittarius', 'Sagittarius'),
                                                     ('Scorpion', 'Scorpius'), ('Taurus', 'Taurus'), ('Ursa Major', 'Ursa Major'),
                                                     ('Ursa Minor', 'Ursa Minor'), ('Virgo', 'Virgo')],render_kw={"class": "constellation-list"})
    submit = SubmitField('Show',render_kw={"class": "btn-constellation"})


class ImageForm(FlaskForm):
    submit = SubmitField('Add',render_kw={"class": "btn-favorite"})


class DateSelectForm(FlaskForm):
    selected_date = DateField('Wybierz datę', validators=[DataRequired()], format='%Y-%m-%d',render_kw={"class": "pick-field"})
    submit = SubmitField('Compare',render_kw={"class": "btn-favorite"})

