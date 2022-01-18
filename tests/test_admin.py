import os
import pytest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime

from app import app, models, db
from app.views import intToTicketType
from app.models import Film, User, Screening

from tests.conftest import addFilms, addScreens, addScreenings, admin_priv, add_film, add_screening, remove_screening, remove_film, view_screening

def test_add_screening(client):
    addFilms(client)
    addScreens(client)
    dt1 = datetime.datetime(2020, 5, 3, 14, 30, 0)
    admin_priv(client)
    response = add_screening(client, 1, "1", dt1, "600")
    assert response.status_code == 200
    assert b"The Wolf of Wall Street" in response.data
    assert b"2020-05-03 14:30:00" in response.data
    assert b"600" in response.data

def test_invalid_add_screening(client):
    addFilms(client)
    addScreens(client)
    dt1 = datetime.datetime(2020, 5, 3, 14, 30, 0)
    admin_priv(client)
    response = add_screening(client, "1", "8", dt1, "600")
    print(response.data)
    assert b"Remove Screening" not in response.data #if screening not added, no button to remove it

def test_remove_screening(client):
    addFilms(client)
    addScreens(client)
    addScreenings(client)
    response = remove_screening(client, 1, 2)
    assert b"2020-9-12 16:30:00" not in response.data
    assert b"699" not in response.data

#an admin privilege
def test_add_film_UI(client):
    admin_priv(client)
    addFilms(client)
    response = add_film(client, 'tt0382932')
    assert response.status_code == 200
    assert b"Ratatouille" in response.data

def test_add_film_DB(client):
    admin_priv(client)
    add_film(client, 'tt0382932')
    f = Film.query.get(1)
    assert f.title == "Ratatouille"
    add_film(client, 'tt4633694')
    f = Film.query.get(2)
    assert f.title == "Spider-Man: Into the Spider-Verse"

def test_remove_film(client):
    addFilms(client)
    admin_priv(client)
    response = remove_film(client, 1)
    assert response.status_code == 200
    f = Film.query.filter_by(id=1).first()
    assert f == None
    response = remove_film(client, 2)
    assert response.status_code == 200
    f = Film.query.filter_by(id=2).first()
    assert f == None
