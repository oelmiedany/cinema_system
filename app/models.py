# -*- coding: utf-8 -*-

from app import db
from datetime import datetime
from flask_login import UserMixin


class Film (db.Model):
	id = db.Column(db.Integer, primary_key=True)
	imdb_id = db.Column(db.Integer, unique=True)
	title = db.Column(db.String(128))

class Screen (db.Model):
	id = db.Column(db.Integer, primary_key=True)
	rows = db.Column(db.Integer)
	columns = db.Column(db.Integer)
	row_gaps = db.Column(db.String(128))
	column_gaps = db.Column(db.String(128))
	seat_gaps = db.Column(db.String(128))

class Screening (db.Model):
	id = db.Column(db.Integer, primary_key=True)
	screen_id = db.Column(db.Integer, db.ForeignKey('screen.id'))
	film_id = db.Column(db.Integer, db.ForeignKey('film.id'))
	date_time = db.Column(db.DateTime)
	seat_map = db.Column(db.String(1024))
	price = db.Column(db.Integer) # Divide by 100 for price: 699 = £6.99
	screen = db.relationship('Screen')
	film = db.relationship('Film')

class User (UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(128), unique=True)
	name = db.Column(db.String(128))
	pword = db.Column(db.String(128))
	isAdmin = db.Column(db.Boolean)

class Ticket (db.Model):
	id = db.Column(db.Integer, primary_key=True)
	order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
	screening_id = db.Column(db.Integer, db.ForeignKey('screening.id'))
	type = db.Column(db.Integer, default=0) # 0=Adult 1=Child 2=Senior
	seat = db.Column(db.Integer)
	price = db.Column(db.Integer) # Divide by 100 for price: 699 = £6.99
	screening = db.relationship('Screening')
	order = db.relationship('Order')

class Order (db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	date_time = db.Column(db.DateTime, default=datetime.utcnow())
	tickets = db.relationship('Ticket')
	user = db.relationship('User')
