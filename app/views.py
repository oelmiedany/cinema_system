# -*- coding: utf-8 -*-

from __future__ import print_function
from sqlalchemy.sql.expression import column
from app import app, db
from flask import Flask, render_template, flash, request, jsonify, session, make_response, redirect
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import stripe
from flask_wtf import FlaskForm
from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from sqlalchemy import and_
from ast import literal_eval
from datetime import datetime
from .models import *
from .forms import *
import pdfkit
import sys
import base64
from mailjet_rest import Client


stripe.api_key = 'sk_test_51IUAZ0K1PTp3CGw0lHkTmQnFcUuyKXLqPE6aIojQ9DxMpZDnfvrk3gk1LFeR0mDsK2oyp86sNz3AQaGeDjaERuVa00NqCyu61e'

login_manager = LoginManager()
#redirects to login page for routes with @login_required
login_manager.login_view = '/login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

@app.before_request
def init():
	if 'email' not in session:
		session['email'] = None
	if 'basket' not in session:
		session['basket'] = []




@app.route('/chooseSeats/<screening_id>', methods=['GET'])
def choose_seats(screening_id):
	screening = Screening.query.filter_by(id = screening_id).first()
	screen = screening.screen
	try:
		seat_map = list(literal_eval(screening.seat_map))
	except:
		seat_map = [ [-1,-1] for i in range(0, screen.rows * screen.columns) ]

	reserved = []
	prices = [ calc_price(screening.price, i) for i in range(0, 3) ]

	try:
		g_seats = list(literal_eval(screen.seat_gaps))
	except:
		g_seats = []
		g_seats.append(int(screen.seat_gaps))

	try:
		g_columns = list(literal_eval(screen.column_gaps))
	except:
		g_columns = []
		g_columns.append(int(screen.column_gaps))
	
	try:
		g_rows = list(literal_eval(screen.row_gaps))
	except:
		g_rows = []
		g_rows.append(int(screen.row_gaps))


	for ind, seat in enumerate(seat_map):
		if seat[0] != -1 and ind not in g_seats:
			if screen.columns == g_columns or str(ind % screen.columns) in g_columns:
				continue
			elif ind / screen.columns == g_rows or str(ind / screen.columns) in g_columns:
				continue
			reserved.append(ind)
	
	return render_template('chooseSeats.html', screening=screening, screen=screen, g_rows=g_rows, g_columns=g_columns,\
							g_seats=g_seats, prices=prices, reserved=reserved, basket=session['basket'])


@app.route('/chooseSeats/<screening_id>/book', methods=['POST'])
def choose_seats_post(screening_id):
	data = request.get_json()
	basket = session['basket']
	print(data['q']['regular'])
	try:
		for i in data['q']['regular']:
			basket.append([int(screening_id), 0, i])
		for i in data['q']['child']:
			basket.append([int(screening_id), 1, i])
		for i in data['q']['senior']:
			basket.append([int(screening_id), 2, i])
	except:
		pass
	session['basket'] = basket
	return account()


# Update basket quantities
@app.route('/update', methods=['POST'])
def update():
	data = request.get_json()
	basket = session['basket']
	n = 0
	try:
		for i in data['q']:
			if int(i['value']) == 0:
				basket.pop(n)
				continue
			if int(i['value']) != basket[n][1]:
				basket[n][1] = int(i['value'])
			n += 1
	except:
		pass
	session.pop('basket', None)
	session['basket'] = basket
	return account()

@app.route('/', methods=['GET', 'POST'])
def film():
	#gives a number value for the age rating
	switcher = {
		'U': 1,
		'PG': 2,
		'12A': 3,
		'15': 4,
		'18': 5
	}

	filtersForm = FiltersForm()
	searchForm = SearchForm()
	filmsInfo = []
	films = []

	#set up for the search term
	if not searchForm.search.data:
		searchForm.search.data = ""
	search = "%{}%".format(searchForm.search.data)

	#if search is used or filters applied
	if searchForm.validate_on_submit() or filtersForm.validate_on_submit():
		for film in Film.query.filter(Film.title.like(search)).all():
			#get each films data
			filmData = get_movie_data(film.imdb_id)

			#get the rating value
			rating = switcher.get(filmData.age_rating, 0)
			#apply filters
			if rating <= int(filtersForm.ageRating.data):
				if filtersForm.genre.data == 'Any':
					filmsInfo.append(filmData)
					films.append(film)
				elif filtersForm.genre.data in filmData.genre:
					filmsInfo.append(filmData)
					films.append(film)

		return render_template('films.html', films=films, filmsInfo=filmsInfo, searchForm=searchForm, filtersForm=filtersForm)

	#if no search or filter used
	for film in Film.query.all():
		filmData = get_movie_data(film.imdb_id)
		filmsInfo.append(filmData)
		films.append(film)

	return render_template('films.html', films = films, filmsInfo=filmsInfo, searchForm=searchForm, filtersForm=filtersForm)

# Gets all screenings of a film
@app.route('/screenings/<id>', methods=['GET'])
def screenings(id):
	screenings = Screening.query.filter(Screening.film_id == id).order_by(Screening.date_time.asc())
	filmData = get_movie_data(Film.query.filter(Film.id == id).first().imdb_id)

	return render_template('screenings.html', screenings=screenings, film = filmData)

# Gets screenings of a film between two dates, sDate and fDate
@app.route('/screenings/<id>,<sDate>,<fDate>', methods=['GET'])
def date_screenings(id, sDate, fDate):
	screenings = Screening.query.filter(and_(Screening.film_id == id, and_(Screening.date_time >= sDate, Screening.date_time <= fDate)))
	return render_template('screenings.html', screenings=screenings)


# Account page with basket and completed orders w/ tickets
@app.route('/account')
@login_required
def account():
	films = Film.query.all()
	screenings = Screening.query.all()
	#user = User.query.filter_by(email=session['email']).first()
	orders = Order.query.filter_by(user_id=current_user.id).all()
	tickets = []
	basket = session.get('basket')
	#print(basket, file=sys.stdout)
	for order in orders:
		tickets.append(Ticket.query.filter_by(order_id=order.id).all())
	#print(films, file=sys.stdout)
	return render_template('account.html', basket=basket, films=films,\
		orders=orders, email=current_user.email, screenings=screenings, tickets=tickets)


@app.route('/logout', methods=['GET'])
def logout():
	flash('Logged out')
	logout_user()
	return film()


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()

	if form.validate_on_submit():
		email = form.email.data
		pword = form.password.data
		try:
			user = User.query.filter_by(email=email).first()
		except:
			flash('Please check your login details and try again.')
			return render_template('signin.html', form=form)

		if not user or not check_password_hash(user.pword, pword):
			flash('Please check your login details and try again.')
			return render_template('signin.html', form=form)

		login_user(user)
		session['email'] = email
		app.logger.info(email + " logged in")

		flash('Logged in successfully')
		return account()

	return render_template('signin.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
	form = SignupForm()

	if form.validate_on_submit():
		name = form.name.data
		email = form.email.data
		pword = form.password.data
		confirm = form.confirm.data

		if pword != confirm:
			flash('Passwords do not match.')
			return render_template('signup.html', form=form)

		user = User.query.filter_by(email=email).first()
		if user:
			flash('Email is already in use.')
			return render_template('signup.html', form=form)

		user = User(email=email, name=name, pword=generate_password_hash(pword, method='sha256'), isAdmin=False)

		db.session.add(user)
		db.session.commit()
		login_user(user)
		app.logger.info(email + " signed up")

		flash('Account created successfully.')
		return account()

	return render_template('signup.html', form=form)


# API Key for movie database
OMDB_API_KEY = "870f845a"


# Object to hold infomation about movie from API
class IMDBFilm():
	def __init__(self, d):
		self.id = d["imdbID"]
		self.title = d["Title"]
		self.release_date = d["Released"]
		self.age_rating = d["Rated"]
		self.runtime = d["Runtime"]
		self.genre = d["Genre"]
		self.director = d["Director"]
		self.writer = d["Writer"]
		self.main_actors = d["Actors"]
		self.plot = d["Plot"]
		self.award_summary = d["Awards"]
		self.posterURL = d["Poster"]
		self.age_rating_url = None


# File private function takes the imdb id of the movie,
# calls the OMDb Api to get the movie data
# and serialises the data into a film class which is returned
# TEST DATA: imdb Id = tt0993846 (Wolf of wall street)
def download_movie_data(id):
	response = requests.get("http://www.omdbapi.com/?apikey=" + OMDB_API_KEY + "&i=" + str(id))

	if response.status_code == 200 and not "Error" in response.json():
		return IMDBFilm(response.json())
	else: 
		return None


# Dictionary to hold previously downloaded movie data (movie data cache)
# If not previously downloaded the movie data is downloaded and returned
# If previously downloaded movie data is returned from the cache
cachedMovieData = {}


def get_movie_data(id):
	#convert american ratings to uk ratings
	ageSwitcher = {
		'G': 'U',
		'PG': 'PG',
		'PG-13': '12A',
		'R': '15',
		'NC-17': '18'
	}
	
	#gets the image url for the corresponding age rating
	urlSwitcher = {
		'U': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/BBFC_U_2019.svg/140px-BBFC_U_2019.svg.png',
		'PG': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/BBFC_PG_2019.svg/140px-BBFC_PG_2019.svg.png',
		'12A': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/BBFC_12A_2019.svg/140px-BBFC_12A_2019.svg.png',
		'15': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/BBFC_15_2019.svg/140px-BBFC_15_2019.svg.png',
		'18': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/BBFC_18_2019.svg/140px-BBFC_18_2019.svg.png',
	}

	if id in cachedMovieData:
		return cachedMovieData[id]
	else:
		film = download_movie_data(id)
		if not film:
			return None

		film.age_rating = ageSwitcher.get(film.age_rating, film.age_rating)
		film.age_rating_url = urlSwitcher.get(film.age_rating, 'Invalid rating')
		cachedMovieData[id] = film
		return film


def calc_price(price, ticket_type):
	if ticket_type == 0:    # Regular
		return price

	elif ticket_type == 1:  # Child
		return price * 0.7

	elif ticket_type == 2:  # Senior
		return price * 0.6

	elif ticket_type == 3:  # Disabled
		return price * 0.5


#view earnings
@app.route('/earnings', methods=['GET', 'POST'])
@login_required
def earnings():
	if not current_user.isAdmin:
		flask("You don't have permission to view this page")
		return redirect('/') 

	earningsForm = EarningsDateForm()
	timeFrameEarnings = 0.00
	totalEarnings = 0.00

	for ticket in Ticket.query.all():
		totalEarnings += ticket.price
	totalEarnings = totalEarnings / 100

	if earningsForm.validate_on_submit():
		startDate = earningsForm.startDate.data
		endDate = earningsForm.endDate.data

		#for order in Order.query.filter(Order.date_time.between(startDate, endDate)).all():
		for order in Order.query.all():
			for ticket in order.tickets:
				timeFrameEarnings += ticket.price
		timeFrameEarnings = timeFrameEarnings / 100
			
	return render_template('earnings.html', totalEarnings=totalEarnings, 
							earningsForm=earningsForm, timeFrameEarnings=timeFrameEarnings) 

# Admin panel to add screenings to database
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
	if not current_user.isAdmin:
		flask("You don't have permission to view this page")
		return redirect('/') 

	addFilmForm = AddFilmForm()
	form = AddScreeningForm()
	films = Film.query.all()

	#add films to the database
	if addFilmForm.validate_on_submit():
		imdbID = addFilmForm.imdb_id.data
		if Film.query.filter_by(imdb_id=imdbID).first():
			flash('That film has already been added')
			return redirect('/admin')

		mData = get_movie_data(addFilmForm.imdb_id.data)

		if not mData:
			flash('Could not get a film with that id')
			return redirect('/admin')

		newFilm = Film(title=mData.title, imdb_id=mData.id)
		db.session.add(newFilm)
		db.session.commit()

		return redirect('/admin')


	#total and average revenue for each film as lists
	totalRevenues = []
	avrgRevenues = []

	count = 0
	for film in films:
		totalRevenues.append(0.0)
		avrgRevenues.append(0.0)

		#get all the tickets for the film and then add it to the total revenue list
		tickets = db.session.query(Ticket).join(Screening).filter(Screening.film_id == film.id).all()
		for ticket in tickets:
			totalRevenues[count] += ticket.price / 100
		#get all screenings of film to calculate average reveunue per screening
		screenings = db.session.query(Screening).filter(Screening.film_id == film.id).all()
		numScreenings = len(screenings)
		if numScreenings > 0:
			avrgRevenues[count] = totalRevenues[count] / numScreenings

		count += 1


	if form.validate_on_submit():
		date_time = form.date_time.data
		film_id = form.film_id.data
		screen_id = form.screen_id.data
		price = form.price.data
		film = Film.query.order_by(Film.id.desc()).first()
		screening = Screening.query.order_by(Screening.id.desc()).first()
		id = 0
		if screening:
			id = screening.id + 1

		screen = Screen.query.filter_by(id=screen_id).first()
		seat_map = screening.seat_map
		room_size = screen.room_size

		if not seat_map:
			seat_map = []
			w = room_size.split("x")[0] - 1
			h = room_size.split("x")[1] - 1
			y = 0
			while y <= h:
				x = 0
				row = []
				while x >= w:
					row.append(0) # seat map states: 0 = free, 1 = reserved
					x += 1
				seat_map.append(row)
				y += 1

		db.session.add(Screening(id=id, date_time=date_time, film=film, screen=screen))
		db.session.commit()

		return render_template('admin.html', addFilmForm=addFilmForm, films=films, 
								totalRevenues=totalRevenues, avrgRevenues=avrgRevenues)

	return render_template('admin.html', addFilmForm=addFilmForm, films=films, 
							totalRevenues=totalRevenues, avrgRevenues=avrgRevenues)

@app.route('/adminScreenings/<id>', methods=['GET', 'POST'])
@login_required
def adminScreenings(id):
	if not current_user.isAdmin:
		flask("You don't have permission to view this page")
		return redirect('/')  
	
	film = Film.query.filter_by(id=id).first()
	screenings = Screening.query.filter_by(film_id=id).all()
	form = AddScreeningForm()

	if form.validate_on_submit():
		date_time = form.date_time.data
		screen_id = form.screen_id.data
		price = form.price.data

		screen = Screen.query.filter_by(id=screen_id).first()
		room_size = screen.room_size

		'''seat_map = []
		w = room_size.split("x")[0] - 1
		h = room_size.split("x")[1] - 1
		y = 0
		while y <= h:
			x = 0
			row = []
			while x >= w:
				row.append(0) # seat map states: 0 = free, 1 = reserved 
				x += 1
			seat_map.append(row)
			y += 1'''
			
		db.session.add(Screening(date_time=date_time, film=film, screen=screen, price=price))
		db.session.commit()

		return redirect('/adminScreenings/' + str(id))


	return render_template('adminScreenings.html', form=form, film=film, screenings=screenings)

@app.route('/removeFilm/<id>', methods=['GET'])
@login_required
def removeFilm(id):
	if not current_user.isAdmin:
		flask("You don't have permission to view this page")
		return redirect('/') 

	film = Film.query.filter_by(id=id).first()
	db.session.delete(film)
	db.session.commit()

	flash('Removed ' + film.title)

	return admin()

@app.route('/removeScreening/<filmId>/<screeningId>', methods=['GET'])
@login_required
def removeScreening(filmId, screeningId):
	if not current_user.isAdmin:
		flask("You don't have permission to view this page")
		return home()

	screening = Screening.query.filter_by(id=screeningId).first()
	db.session.delete(screening)
	db.session.commit()

	flash('Screening removed')

	return redirect('/adminScreenings/' + str(filmId))


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
	lineitems = []
	for i in session['basket']:
		screening = Screening.query.filter_by(id=i[0]).first()
		lineitem = {
			'price_data': {
				'currency': 'gbp',
				'unit_amount': int(calc_price(screening.price, i[1])),
				'product_data': {
					'name': screening.film.title + " - " + intToTicketType(i[1]),
					'images': ["url_for('static',filename='img/replaceme.png')"],
				},
			},
			'quantity': 1,
		}
		lineitems.append(lineitem)
	metadata = {}
	email = []
	if session.get('email'):
		email = session['email']
	try:
		checkout_session = stripe.checkout.Session.create(
			customer_email=email,
			submit_type='pay',
			billing_address_collection='auto',
			shipping_address_collection={
				'allowed_countries': [],
			},
			payment_method_types=['card'],
			line_items=lineitems,
			metadata=metadata,
			mode='payment',
			success_url='http://localhost:5000/success?session_id={CHECKOUT_SESSION_ID}',
			cancel_url='http://localhost:5000/account',
		)
		return jsonify({'id': checkout_session.id})
	except Exception as e:
		#app.logger.warn(checkout_session.id + " transaction failed")
		app.logger.warn("transaction failed")
		return jsonify(error=str(e)), 403

@app.route('/checkout')
@login_required
def checkout():
	return redirect('/')

@app.route('/success')
def success():
	s_id = request.args.get('session_id')
	s = stripe.checkout.Session.retrieve(s_id, expand=['customer', 'line_items', 'payment_intent'])
	# quantity = s.line_items.data[-1].quantity
	email = s.customer.email

	ord = Order.query.order_by(Order.id.desc()).first()
	o_id = 0
	if ord:
		o_id = ord.id + 1

	tic = Ticket.query.order_by(Ticket.id.desc()).first()
	t_id = 0
	if tic:
		t_id = tic.id + 1

	user = User.query.filter_by(email=email).first()
	order = Order(id=o_id, user_id=user.id, date_time=datetime.utcnow())

	for t in session.get('basket'):
		screening = Screening.query.filter_by(id=t[0]).first()
		ticket = Ticket(id=t_id, order_id=order.id, screening_id=t[0], type=t[1],\
						price=calc_price(screening.price, t[1]), seat=t[2])
		order.tickets.append(ticket)
		db.session.add(ticket)
		t_id += 1

	db.session.add(order)
	db.session.commit()
	session.pop('basket', None)
	app.logger.info(str(o_id) + " transaction success")
	print(order.id, file=sys.stdout)

	sendEmailConfirmation(order.id)
	return account()

@app.route('/tickets_manually')
def tickets_manually():
	form = AddTicketManuallyForm()

	if form.validate_on_submit():
		email = form.user_email.data
		screening = form.screening.data
		type = form.type.data
		seat = form.seat.data
		price = form.price.data

		ord = Order.query.order_by(Order.id.desc()).first()
		o_id = 0
		if ord:
			o_id = ord.id + 1

		tic = Ticket.query.order_by(Ticket.id.desc()).first()
		t_id = 0
		if tic:
			t_id = tic.id + 1

		user = User.query.filter_by(email=email).first()
		order = Order(id=o_id, user_id=user.id, date_time=datetime.utcnow())

		screening = Screening.query.filter_by(id=t[0]).first()
		ticket = Ticket(id=t_id, order_id=order.id, screening_id=screening, type=type, \
						price=calc_price(screening.price, price), seat=seat)

		order.tickets.append(ticket)
		db.session.add(ticket)
		t_id += 1
		db.session.add(order)
		db.session.commit()
		app.logger.info(str(o_id) + " transaction success")

		sendEmailConfirmation(order.id)
		return admin()


	return render_template('adminTickets.html', form=form)


@app.route('/pdfTicket/<id>')
def pdfTicket(id):

	pdf = generatePDFTicket(id)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=ticket.pdf'
	return response

def generatePDFTicket(id):
	ticket = Ticket.query.filter_by(id=id).first()
	rendered = render_template('pdfTicket.html',
							   Title = ticket.screening.film.title,
							   Screen = ticket.screening.screen_id,
							   DateTime = ticket.screening.date_time,
							   order_id = ticket.order_id,
							   Ticket_type = intToTicketType(ticket.type),
							   Ticket_id = ticket.id,
							   Price = str(ticket.price/100))

	pdf = pdfkit.from_string(rendered, False)

	return pdf

def generateEmailConfirmationHTML(orderId):
	tickets = Ticket.query.filter_by(order_id=orderId).all()
	print("Tickets", file=sys.stdout)

	print(render_template('email.html', tickets = tickets), file=sys.stdout)

	return render_template('email.html', tickets = tickets)

def sendEmailConfirmation(orderId):
	html = generateEmailConfirmationHTML(orderId)
	order = Order.query.filter_by(id=orderId).first()

	api_key = 'f1e40ff5953fe85381afba58b1a3d0a7'
	api_secret = '7dbe6d402b5d1d89475247f2918ac1dd'
	mailjet = Client(auth=(api_key, api_secret))
	data = {
		'FromEmail': 'sc19gbd@leeds.ac.uk',
		'FromName': 'Hyde Park Picture House',
		'Subject': 'Your tickets are waiting for you',
		'Html-part': html,
		'Recipients': [{'Email': order.user.email}],
	}
	result = mailjet.send.create(data=data)
	print(result.status_code, file=sys.stdout)
	print(result, file=sys.stdout)


	return "hello"

#Function converts integer to word ticket type
def intToTicketType(x):
	if (x == 0):
		return "Adult"
	elif (x==1):
		return "Child"
	elif x == 2:
		return "Senior"
	else:
		return "Unknown Ticket Type"
