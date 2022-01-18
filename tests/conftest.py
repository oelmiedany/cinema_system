import os
import pytest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

#PLEASE DON'T DELETE! this needed if you get ModuleNotFound error
#change path to dir where "app" is for you
import sys
sys.path.append('/home/Documents/group/comp-2913')
print(sys.path)
from app import app, models, db
from app.models import Film, User, Screening, Screen

#-------------------------------Fixtures--------------------------------------
@pytest.fixture
def client():
    #setup: creates test app and database
    app.config.from_object('config')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    #creates the test db
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    client.app = app.test_client()
    db.create_all()

    #yields client for test to be ran
    yield client

    #teardown: clears the temp databse
    db.session.remove()
    db.drop_all()

#----------------------------Helper Methods------------------------------------
def addFilms(client):
    films = [None] * 5
    films[0] = Film(title='The Wolf of Wall Street', imdb_id='tt0993846')
    films[1] = Film(title='The Big Lebowski', imdb_id='tt0118715')
    films[2] = Film(title='Apocalypse Now', imdb_id='tt0078788')
    films[3] = Film(title='Spider-Man: Into the Spider-Verse', imdb_id='tt4633694')
    films[4] = Film(title='Titanic', imdb_id='tt0120338')

    for film in films:
        db.session.add(film)
    db.session.commit()

def addScreens(client):
    screens = [None] * 3
    screens[0] = Screen(rows=10, columns=10, row_gaps=0, column_gaps=5, seat_gaps=0)
    screens[1] = Screen(rows=6, columns=8, row_gaps=0, column_gaps=0, seat_gaps=0)
    screens[2] = Screen(rows=10, columns=12, row_gaps=4, column_gaps=0, seat_gaps=0)

    for screen in screens:
        db.session.add(screen)
    db.session.commit()

def addScreenings(client):
    need a film to add film relationship to screening
    screenings = [None] * 3
    time = datetime.datetime(2020, 9, 12, 16, 30, 0)
    screenings[0] = Screening(screen_id=2, film_id=1, date_time=time, price=699)
    time1 = datetime.datetime(2020, 8, 1)
    screenings[1] = Screening(screen_id=1, film_id=2, date_time=time1, price=750)
    time2 = datetime.datetime(2020, 8, 2, 11, 0, 0)
    screenings[2] = Screening(screen_id=1, film_id=2, date_time=time2, price=700)

    for screening in screenings:
        db.session.add(screening)
    db.session.commit()

def signup(client, name, email, password, confirm):
    return client.app.post('/signup',
    data=dict(name=name, email=email, password=password, confirm=confirm),
    follow_redirects=True)

#for testing functions that need admin privilege?
def admin_priv(client):
    signup(client=client, name="admin", email="admin@admin.com", password="password", confirm="password")
    u = User.query.get(1)
    u.isAdmin=True
    return

def login(client, email, password):
    return client.app.post('/login',
    data=dict(email=email, password=password),
    follow_redirects=True)

def logout(client):
    return client.app.get('/logout',
    follow_redirects=True)

def search(client, genre, ageRating):
    return client.app.post('/films',
    data=dict(genre=genre, ageRating=ageRating),
    follow_redirects=True)

def view_screening(client, id):
    return client.app.get('/screenings/'+str(id),
    follow_redirects=False)

def add_screening(client, id, screen_id, date_time, price):
    return client.app.post('adminScreenings/'+str(id),
    data=dict(id=id, screen_id=screen_id, date_time=date_time, price=price),
    follow_redirects=True)

def add_film(client, imdb_id):
    return client.app.post('/admin',
    data=dict(imdb_id=imdb_id),
    follow_redirects=True)

def remove_screening(client, film_id, screen_id):
    return client.app.post('/removeScreening/' + str(film_id) + '/' + str(screen_id),
    data=dict(filmID=film_id, screenID=screen_id),
    follow_redirects=True)

def remove_film(client, film_id):
    return client.app.get('/removeFilm/' + str(film_id),
    data=dict(id=film_id),
    follow_redirects=True)
