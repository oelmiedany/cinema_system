import os
import pytest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app import app, db, models
from app.models import User

from tests.conftest import login, logout, signup

#------------------------------------Tests------------------------------------

#Signup
def test_valid_signup(client):
    result = signup(client, 'Sally Anne', 'sallyanne@gmail.com', 'sinema89', 'sinema89')
    assert result.status_code == 200
    assert b'Account created successfully' in result.data
    u = User.query.get(1)
    assert u.name == "Sally Anne"

def test_diff_passwords_signup(client):
    result = signup(client, 'Bobby Jones', 'bobbyjones@gmail.com', 'bbjones2', 'bbjones3')
    assert b'Passwords do not match' in result.data

def test_same_emails_signup(client):
    result = signup(client, 'Bobby Jones', 'bobbyjones@gmail.com', 'bbjones2', 'bbjones2')
    assert result.status_code == 200
    result = signup(client, 'Bobby Jones Jr', 'bobbyjones@gmail.com', 'bbjj', 'bbjj')
    assert b'Email is already in use' in result.data

#logout
def test_valid_logout(client):
    result = signup(client, 'Sally Anne', 'sallyanne@gmail.com', 'sinema89', 'sinema89')
    assert result.status_code == 200
    result = logout(client)
    assert result.status_code == 200
    assert b'Logged out' in result.data

#login
def test_valid_login(client):
    result = signup(client, 'Sally Anne', 'sallyanne@gmail.com', 'sinema89', 'sinema89')
    result = logout(client)
    result = login(client, 'sallyanne@gmail.com', 'sinema89')
    assert result.status_code == 200
    assert b'Logged in successfully' in result.data

def test_wrong_pword_login(client):
    result = signup(client, 'Sally Anne', 'sallyanne@gmail.com', 'sinema89', 'sinema89')
    result = logout(client)
    result = login(client, 'sallyanne@gmail.com', 'cinema89')
    assert b'Please check your login details and try again.' in result.data

def test_nonexisting_account_login(client):
    result = login(client, 'sallyanne@gmail.com', 'cinema89')
    assert b'Please check your login details and try again.' in result.data
