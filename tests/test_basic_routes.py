import os
import pytest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app import app, models, db


#------------------------------Tests-------------------------------------------
#basic set of tests checking the routes return expected results
def test_home_route(client):
    response = client.app.get('/')
    assert response.status_code == 200
    assert b"THE HOME OF INDEPENDENT FILM IN LEEDS" in response.data

    response = client.app.post('/')
    assert response.status_code == 200
    assert b"THE HOME OF INDEPENDENT FILM IN LEEDS" in response.data

def test_films_route(client):
    response = client.app.get('/films')
    assert response.status_code == 200
    assert b"What's On" in response.data

def test_logout_route(client):
    response = client.app.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Logged out" in response.data
    assert b"THE HOME OF INDEPENDENT FILM IN LEEDS"

def test_login_route(client):
    response = client.app.get('/login')
    assert response.status_code == 200

def test_signup_route(client):
    response = client.app.get('/signup')
    assert response.status_code == 200

def test_account_route_logged_out(client):
    response = client.app.get('/account', follow_redirects=True)
    assert response.status_code == 200
    assert b"Please log in to access this page" in response.data
