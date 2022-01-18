from flask_wtf import FlaskForm
from wtforms import TextField, SelectField, PasswordField, StringField, DateTimeField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email
from .models import *


class LoginForm(FlaskForm):
    email = EmailField('Email address', validators=[DataRequired(), Email()])
    password = PasswordField('password', validators=[DataRequired()])


class SignupForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    email = EmailField('Email address', validators=[DataRequired(), Email()])
    password = PasswordField('password', validators=[DataRequired()])
    confirm = PasswordField('password', validators=[DataRequired()])


class BookTicketsForm(FlaskForm):
    choices = [(str(i), i) for i in range(0, 21)]
    childTickets = SelectField(choices=choices)
    adultTickets = SelectField(choices=choices)
    seniorTickets = SelectField(choices=choices)
    disabledTickets = SelectField(choices=choices)
# user will select seat number using graphical representation in final product
# account id, ticket price and VIP status will be obtained on business-logic side


class SearchForm(FlaskForm):
    search = StringField('search', validators=[])

class FiltersForm(FlaskForm):
    genre = SelectField('genre', choices=[('Any'), ('Action'), ('Drama'), ('Comedy'), ('Crime'), ('Sci-Fi'), ('Sport'), ('Romance')])
    ageRating = SelectField('ageRating', choices=[(5, 'Any'), (1, 'U'), (2, 'PG'), (3, '12A'), (4, '15')])


class AddScreeningForm(FlaskForm):
    screen_id = StringField('Screen ID', validators=[DataRequired()])
    date_time = DateTimeField('Date & Time', format='%d/%m/%Y %H:%M:%S', validators=[DataRequired()])
    price = StringField('Ticket Price', validators=[DataRequired()])

class AddFilmForm(FlaskForm):
    imdb_id = StringField('IMDB ID', validators=[DataRequired()])

class EarningsDateForm(FlaskForm):
    startDate = DateTimeField('Start Date', format='%d/%m/%Y', validators=[DataRequired()])
    endDate = DateTimeField('End Date', format='%d/%m/%Y', validators=[DataRequired()])

class AddTicketManuallyForm(FlaskForm):
    user_email= EmailField('Email address', validators=[DataRequired(), Email()])
    screening = StringField(validators=[DataRequired()])
    type = SelectField()
    seat = StringField(validators=[DataRequired()])
    price = StringField(validators=[DataRequired()])


    def __init__(self):
        super(AddTicketManuallyForm, self).__init__()
        self.type.choices = [0,1,2]
