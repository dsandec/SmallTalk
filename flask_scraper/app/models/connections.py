import datetime
import sqlalchemy
import json

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.types import TypeDecorator

from .. import db
from .user import User

SIZE = 256

class TextPickleType(TypeDecorator):
	impl = sqlalchemy.Text(SIZE)

	def process_bind_param(self, value, dialect):
		if value is not None:
			value = json.dumps(value)

		return value

	def process_result_value(self, value, dialect):
		if value is not None:
			value = json.loads(value)
		return value

class BusinessConnection(db.Model):
	__tablename__ = 'business_connection'

	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	id = db.Column(db.Integer, primary_key=True)
	first_name = db.Column(db.String(120))
	last_name = db.Column(db.String(120))

	scrapers_requested = db.Column(db.String(120))
	personal_domain_requested = db.Column(db.Boolean)
	education_domain_search_requested = db.Column(db.Boolean)

	is_ac_domain_available = db.Column(db.Boolean)
	is_edu_domain_available = db.Column(db.Boolean)
	is_personal_domain_available = db.Column(db.Boolean)

	keywords = db.Column(db.Text)
	notes = db.Column(db.Text)

	linkedin_search_completed_on = db.Column(db.DateTime)
	facebook_search_completed_on = db.Column(db.DateTime)
	youtube_search_completed_on = db.Column(db.DateTime)
	twitter_search_completed_on = db.Column(db.DateTime)
	education_domain_search_completed_on = db.Column(db.DateTime)
	personal_domain_search_completed_on = db.Column(db.DateTime)

	requested_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)

	def full_name(self, spaced=True):
		if spaced:
			return '{} {}'.format(self.first_name, self.last_name)

		return '{}{}'.format(self.first_name, self.last_name)

	def ac_domain(self, spaced=True):
		return 'www.{}.ac.uk'.format(self.full_name(False))

	def edu_domain(self, spaced=True):
		return 'www.{}.edu'.format(self.full_name(False))

	def personal_domain(self, spaced=True):
		return 'www.{}.com'.format(self.full_name(False))

	@staticmethod
	def generate_fake(count=100, **kwargs):
		"""Generate a number of fake business connections for testing."""
		from sqlalchemy.exc import IntegrityError
		from random import seed, choice
		from faker import Faker

		fake = Faker()
		users = User.query.all()

		seed()
		for i in range(count):
			u = BusinessConnection(
				first_name=fake.first_name(),
				last_name=fake.last_name(),
				is_ac_domain_available=fake.boolean(),
				is_edu_domain_available=fake.boolean(),
				is_personal_domain_available=fake.boolean(),

				linkedin_search_requested=fake.boolean(),
				facebook_search_requested=fake.boolean(),
				youtube_search_requested=fake.boolean(),
				twitter_search_requested=fake.boolean(),
				personal_site_search_requested=fake.boolean(),
				education_domain_search_requested=fake.boolean(),

				user_id=choice(users).id,
				**kwargs)
			db.session.add(u)

			try:
				db.session.commit()
			except IntegrityError as ie:
				print(ie)
				db.session.rollback()

class BusinessConnectionSearchType(db.Model):
	__tablename__ = 'business_connection_search_type'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))

	@staticmethod
	def insert_search_types():
		names = ['Linkedin','Facebook','YouTube','Twitter']
		for n in names:
			search_type = BusinessConnectionSearchType.query.filter_by(name=n).first()
			if search_type is None:
				search_type = BusinessConnectionSearchType(name=n)
			db.session.add(search_type)
		db.session.commit()

	def __repr__(self):
		return '<BusinessConnectionSearchType \'%s\'>' % self.id

class BusinessConnectionSearchResult(db.Model):
	__tablename__ = 'business_connection_search_results'

	id = db.Column(db.Integer, primary_key=True)
	url = db.Column(db.Text)
	title = db.Column(db.String(255))
	summary = db.Column(db.String(255))
	meta = db.Column(db.String(100))
	description = db.Column(db.Text)

	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	business_connection_search_type_id = db.Column(db.Integer, db.ForeignKey('business_connection_search_type.id'))
	business_connection_id = db.Column(db.Integer, db.ForeignKey('business_connection.id'))

	@staticmethod
	def generate_fake(count=100, **kwargs):
		"""Generate a number of fake business connection searches for testing."""
		from sqlalchemy.exc import IntegrityError
		from random import seed, choice
		from faker import Faker

		fake = Faker()
		users = User.query.all()
		search_types = BusinessConnectionSearchType.query.all()
		connections = BusinessConnection.query.all()

		seed()
		for i in range(count):
			u = BusinessConnectionSearchResult(
				url=fake.url(),
				title=fake.sentence(),
				summary=fake.text(),
				description=fake.text(),
				meta=fake.text(),
				user_id=choice(users).id,
				business_connection_search_type_id=choice(search_types).id,
				business_connection_id=choice(connections).id,
				**kwargs)
			db.session.add(u)

			try:
				db.session.commit()
			except IntegrityError as ie:
				print(ie)
				db.session.rollback()

	def __repr__(self):
		return '<BusinessConnectionSearch \'%s\'>' % self.id


class BaseLinkedModelMixin(object):
	@declared_attr
	def business_connection_id(cls):
		return db.Column(db.Integer, db.ForeignKey('business_connection.id'))

	@declared_attr
	def business_connection_search_type_id(cls):
		return db.Column(db.Integer, db.ForeignKey('business_connection_search_type.id'))

	id = db.Column(db.Integer, primary_key=True)
	is_current = db.Column(db.Boolean, default=False)
	name = db.Column(db.String(255))
	url = db.Column(db.Text)
	start_date = db.Column(db.Date)
	end_date = db.Column(db.Date)

class BusinessConnectionUniversity(BaseLinkedModelMixin, db.Model):
	__tablename__ = 'business_connection_university'
	major = db.Column(db.String(120))
	degree = db.Column(db.String(120))

	@staticmethod
	def generate_fake(count=100, **kwargs):
		"""Generate a number of fake business connections for testing."""
		from sqlalchemy.exc import IntegrityError
		from random import seed, choice
		from faker import Faker

		fake = Faker()
		business_connection = BusinessConnection.query.all()
		search_types = BusinessConnectionSearchType.query.all()

		seed()
		for i in range(count):
			u = BusinessConnectionUniversity(
				name=fake.company(),
				is_current=False,
				url=fake.url(),
				start_date=fake.date_this_decade(),
				end_date=fake.date_this_decade(),
				degree=fake.word(),
				major=fake.word(),
				business_connection_id=choice(business_connection).id,
				business_connection_search_type_id=choice(search_types).id,
				**kwargs)
			db.session.add(u)

			try:
				db.session.commit()
			except IntegrityError as ie:
				print(ie)
				db.session.rollback()

	def __repr__(self):
		return '<BusinessConnectionUniversity \'%s\'>' % self.id

class BusinessConnectionJob(BaseLinkedModelMixin, db.Model):
	__tablename__ = 'business_connection_job'
	position = db.Column(db.String(120))

	@staticmethod
	def generate_fake(count=100, **kwargs):
		"""Generate a number of fake business connections for testing."""
		from sqlalchemy.exc import IntegrityError
		from random import seed, choice
		from faker import Faker

		fake = Faker()
		business_connection = BusinessConnection.query.all()
		search_types = BusinessConnectionSearchType.query.all()

		seed()
		for i in range(count):
			u = BusinessConnectionJob(
				name=fake.company(),
				position=fake.job(),
				is_current=False,
				url=fake.url(),
				start_date=fake.date_this_decade(),
				end_date=fake.date_this_decade(),
				business_connection_id=choice(business_connection).id,
				business_connection_search_type_id=1,
				**kwargs)
			db.session.add(u)
			try:
				db.session.commit()
			except IntegrityError as ie:
				print(ie)
				db.session.rollback()

	def __repr__(self):
		return '<BusinessConnectionJob \'%s\'>' % self.id


class BusinessConnectionDetail(db.Model):
	__tablename__ = 'business_connection_detail'

	business_connection_id = db.Column(db.Integer, db.ForeignKey('business_connection.id'))
	business_connection_search_type_id =  db.Column(db.Integer, db.ForeignKey('business_connection_search_type.id'))

	id = db.Column(db.Integer, primary_key=True)
	url = db.Column(db.Text)

	email = db.Column(db.String(120), unique=True)
	date_of_birth = db.Column(db.String(120))
	phone_number = db.Column(db.String(120))

	street_address = db.Column(db.String(120))
	country = db.Column(db.String(120))
	post_code = db.Column(db.String(120))

	note = db.Column(db.String(255))
	description = db.Column(db.Text)

	current_city = db.Column(db.String(255))
	home_town = db.Column(db.String(255))
	website = db.Column(db.String(255))

	education = db.Column(TextPickleType())
	work = db.Column(TextPickleType())
	movies = db.Column(db.Text)
	music = db.Column(db.Text)
	sports_team = db.Column(db.Text)
	sports = db.Column(db.Text)
	athletes = db.Column(db.Text)
	books = db.Column(db.Text)
	quotes = db.Column(db.Text)
	television = db.Column(db.Text)
	inspirational_people = db.Column(db.Text)
	professional_skills = db.Column(db.Text)
	games = db.Column(db.Text)
	other = db.Column(db.Text)
	bio = db.Column(db.Text)

	tweets = db.Column(db.Integer)
	following_count = db.Column(db.Integer)
	follower_count = db.Column(db.Integer)

	completed_on = db.Column(db.DateTime)

	@staticmethod
	def generate_fake(count=100, **kwargs):
		"""Generate a number of fake business connections for testing."""
		from sqlalchemy.exc import IntegrityError
		from random import seed, choice
		from faker import Faker

		fake = Faker()
		business_connection = BusinessConnection.query.all()
		search_types = BusinessConnectionSearchType.query.all()

		seed()
		for i in range(count):
			u = BusinessConnectionDetail(
				first_name=fake.first_name(),
				last_name=fake.last_name(),
				email=fake.email(),
				phone_number=fake.phone_number(),
				post_code=fake.postalcode(),
				country=fake.country(),
				street_address=fake.street_address(),
				city=fake.city(),
				url=fake.url(),
				note=fake.text(),
				business_connection_id=choice(business_connection).id,
				business_connection_search_type_id=choice(search_types).id,
				**kwargs)
			db.session.add(u)

			try:
				db.session.commit()
			except IntegrityError as ie:
				print(ie)
				db.session.rollback()

	def __repr__(self):
		return '<BusinessConnectionDetail \'%s\'>' % self.id
