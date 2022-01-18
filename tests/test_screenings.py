import os
import pytest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime

from app import app, models, db
from app.views import intToTicketType
from app.models import Screening, Screen

from tests.conftest import addScreenings, addScreens, addFilms, view_screening, add_screening

def test_screens_in_db(client):
    addScreens(client)
    screens = Screen.query.all()
    assert screens[0].rows == 10
    assert screens[0].columns == 10
    assert screens[0].row_gaps == "0"
    assert screens[0].column_gaps == "5"
    assert screens[0].seat_gaps == "0"
    assert screens[1].rows == 6
    assert screens[1].columns == 8
    assert screens[1].row_gaps == "0"
    assert screens[1].column_gaps == "0"
    assert screens[1].seat_gaps == "0"
    assert screens[0].id != screens[1].id

def test_screening_in_db(client):
    addScreenings(client)
    screenings = Screening.query.all()
    dt1 = datetime.datetime(2020, 9, 12, 16, 30, 0)
    dt2 = datetime.datetime(2020, 8, 1)
    assert screenings[0].film_id == 1
    assert screenings[0].screen_id == 2
    assert screenings[0].date_time == dt1
    assert screenings[0].price == 699
    assert screenings[1].film_id == 2
    assert screenings[1].screen_id == 1
    assert screenings[1].date_time == dt2
    assert screenings[1].price == 750
    assert screenings[0].id != screenings[1].id

def test_screenings_UI(client):
    response = view_screening(client, 1)
    assert response.status_code == 200
    assert b"Screenings" in response.data
    assert b"Times" in response.data

def test_view_screenings(client):
    addFilms(client)
    addScreens(client)
    addScreenings(client)
    response = view_screening(client, 1)
    assert b"2020-09-12 16:30:00" in response.data

def test_many_screenings(client):
    addFilms(client)
    addScreens(client)
    addScreenings(client)
    response = view_screening(client, 2)
    assert b"2020-08-01 00:00:00" in response.data
    assert b"2020-08-02 11:00:00" in response.data
    assert b"2020-08-01 16:30:00" not in response.data
