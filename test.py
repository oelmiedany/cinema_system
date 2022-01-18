from app import app, models, db
from app.forms import LoginForm, BookTicketsForm, SearchForm
from app.models import *
from flask import Flask, render_template, flash, redirect, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import stripe
import json
from sqlalchemy import and_
from app.views import get_movie_data
from app.models import Film, Screening

films = []
for film in Film.query.all():
	filmData = get_movie_data(film.imdb_id)
	films.append(filmData)
print(len(films))