import os
import pytest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app import app, models, db
from app.views import intToTicketType

def test_ticket_type_valid(client):
    assert intToTicketType(0) == 'Adult'
    assert intToTicketType(1) == 'Child'
    assert intToTicketType(2) == 'Senior'

def test_ticket_type_invalid(client):
    assert intToTicketType(3) == 'Unknown Ticket Type'
    assert intToTicketType(11) == 'Unknown Ticket Type'

#ADD MORE WHEN SEAT CHOOSER READY
