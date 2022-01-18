import os
import pytest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app import app, models, db
from app.models import Film

from tests.conftest import addFilms, search, add_film, admin_priv

#tests the film functionality of the app
#------------------------------Tests-------------------------------------------
#check film details
def test_film_details(client):
    addFilms(client)
    films = Film.query.all()
    assert films[0].title == 'The Wolf of Wall Street'
    assert films[0].imdb_id == 'tt0993846'
    assert films[0].id
    assert films[1].title == 'The Big Lebowski'
    assert films[1].imdb_id == 'tt0118715'
    assert films[1].id != films[0].id

#check films show on home screen correctly
def test_films_ui(client):
    addFilms(client)
    response = client.app.get('/')
    assert response.status_code == 200
    #check for all titles
    assert b"The Wolf of Wall Street" in response.data
    assert b"The Big Lebowski" in response.data
    assert b"Apocalypse Now" in response.data
    #check that the genres are correct (for wolf of wall street)
    assert b"Biography, Crime, Drama" in response.data

def test_home_search_wolf(client):
    addFilms(client)
    #search for 'Wolf' on home screen
    response = client.app.post('/', data=dict(search='Wolf'))
    #check that only wolf of wall street shows up
    assert response.status_code == 200
    assert b"The Wolf of Wall Street" in response.data
    assert b"The Big Lebowski" not in response.data
    assert b"Apocalypse Now" not in response.data

def test_home_search_the(client):
    addFilms(client)
    #search for 'the' on home screen
    response = client.app.post('/', data=dict(search='the'))
    #check that only wolf of wall street and big lebowski shows up
    assert response.status_code == 200
    assert b"The Wolf of Wall Street" in response.data
    assert b"The Big Lebowski" in response.data
    assert b"Apocalypse Now" not in response.data

def test_home_search_blank(client):
    addFilms(client)
    #search for '' on home screen
    response = client.app.post('/', data=dict(search=''))
    #check that all films show up
    assert response.status_code == 200
    assert b"The Wolf of Wall Street" in response.data
    assert b"The Big Lebowski" in response.data
    assert b"Apocalypse Now" in response.data

def test_search_action(client):
    addFilms(client)
    response = search(client, 'Action', 5)
    assert response.status_code == 200
    assert b"Spider-Man: Into the Spider-Verse" in response.data

def test_search_crime(client):
    addFilms(client)
    response = search(client, 'Crime', 5)
    assert response.status_code == 200
    assert b"The Wolf of Wall Street" in response.data
    assert b"The Big Lebowski" in response.data

def test_search_romance(client):
    addFilms(client)
    response = search(client, 'Romance', 5)
    assert response.status_code == 200
    assert b"Titanic" in response.data

def test_search_ratingPG(client):
    addFilms(client)
    response = search(client, 'Any', 2)
    assert response.status_code == 200
    assert b"Spider-Man: Into the Spider-Verse" in response.data
    assert b"Titanic" not in response.data

def test_search_action12A(client):
    addFilms(client)
    response = search(client, 'Any', 3)
    assert response.status_code == 200
    assert b"Spider-Man: Into the Spider-Verse" in response.data
    assert b"Titanic" in response.data
    assert b"The Wolf of Wall Street" not in response.data
