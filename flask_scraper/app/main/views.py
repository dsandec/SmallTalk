import logging
import json

from flask import flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required
from flask_rq import get_queue
from wtforms.fields import StringField

from . import main
from .. import db
from ..models import BusinessConnection, BusinessConnectionDetail, BusinessConnectionUniversity, BusinessConnectionJob, BusinessConnectionSearchResult, BusinessConnectionSearchType
from .forms import (NewBusinessConnectionForm, TwitterForm, FacebookForm, YouTubeForm, CommonDetailForm, SearchForm, LinkedInForm)
from ..connection_scrapers import check_domains, perform_google_search, perform_profile_extraction


def enqueue_google_scrapers(required_scrapers, connection):
	""" Queue the requested profile scrapers in RQ inorder for them to run as background tasks """
	search_types = BusinessConnectionSearchType.query.all()
	sites = ['linkedin','twitter','youtube','facebook']
	for site in sites:
		if site in required_scrapers:
			search_type = next(x for x in search_types if x.name.lower()==site)
			get_queue().enqueue(perform_google_search, business_connection_id=connection.id, first_name=connection.first_name, last_name=connection.last_name, search_type=search_type, keywords=connection.keywords, user_id=current_user.id)


def handle_work_education_form(form_type, values, detail):
	""" Handle the special types work/education """
	form = form_type(values, obj=detail)
	education_data = form.education.data
	work_data = form.work.data

	del(form.work)
	del(form.education)

	form.populate_obj(detail)

	detail.work = work_data
	detail.education = education_data

@main.route('/')
def index():
	""" Home page - If authenticated then show the user they're custom home page """
	if current_user.is_authenticated:
		connections = BusinessConnection.query.filter_by(user_id=current_user.id).all()
		new_connect_form = NewBusinessConnectionForm()

		return render_template('main/index.html', connections=connections, form=new_connect_form, search_form=SearchForm())

	return render_template('main/index.html')

@main.route('/about')
def about():
	return render_template('main/about.html')

@main.route('/terms-of-use')
def terms_of_use():
	return render_template('main/terms-of-use.html')

@main.route('/privacy-policy')
def privacy_policy():
	return render_template('main/privacy-policy.html')

@main.route('/compliance')
def compliance():
	return render_template('main/compliance.html')

@main.route('/business-connection/<int:business_connection_id>')
@login_required
def business_connection_profile(business_connection_id):
	""" Retrieve a previously stored business connection """
	connection = db.session.query(BusinessConnection).filter_by(id=business_connection_id).first()
	if connection is None:
		abort(404)

	search_results = BusinessConnectionSearchResult.query.filter_by(business_connection_id=business_connection_id).all()

	google_search_results = [
		{'name':'linkedin', 'id':1, 'results':[x for x in search_results if x.business_connection_search_type_id==1]},
		{'name':'facebook', 'id':2, 'results':[x for x in search_results if x.business_connection_search_type_id==2]},
		{'name':'youtube', 'id':3, 'results':[x for x in search_results if x.business_connection_search_type_id==3]},
		{'name':'twitter', 'id':4, 'results':[x for x in search_results if x.business_connection_search_type_id==4]}
	]

	scrapers_requested = connection.scrapers_requested.split(',')
	google_search_results = [x for x in google_search_results if x['name'] in scrapers_requested]

	detail = BusinessConnectionDetail.query.filter_by(business_connection_id=business_connection_id, business_connection_search_type_id=1).first()

	form = CommonDetailForm(obj=connection)
	linkedin_form = LinkedInForm(obj=detail)
	return render_template('main/business_connection_profile.html', business_connection=connection, business_connection_detail=detail, google_search_results=google_search_results, search_type_name='linkedin', facebookform=FacebookForm(),twitterform=TwitterForm(),youtubeform=YouTubeForm(),commondetailform=form,linkedinform=linkedin_form)

def update_profile(form_type, request, processor=None):
	""" Update profile information """
	detail = db.session.query(BusinessConnectionDetail).get(request.form['id'])
	if detail is None:
		return False
	if processor:
		processor(form_type, request.values, detail)
	else:
		form = form_type(request.values, obj=detail)
		form.populate_obj(detail)
	db.session.commit()
	return True

@main.route('/business-connection/facebook/', methods=['POST'])
@login_required
def update_facebook_profile():
	if not update_profile(FacebookForm, request, handle_work_education_form):
		abort(404)
	return ''

@main.route('/business-connection/youtube/', methods=['POST'])
@login_required
def update_youtube_profile():
	if not update_profile(YouTubeForm, request):
		abort(404)
	return ''

@main.route('/business-connection/twitter/', methods=['POST'])
@login_required
def update_twitter_profile():
	if not update_profile(YouTubeForm, request):
		abort(404)
	return ''

@main.route('/business-connection/linkedin/', methods=['POST'])
@login_required
def update_linkedin_profile():
	if not update_profile(LinkedInForm, request, handle_work_education_form):
		abort(404)
	return ''

@main.route('/business-connection/common_detail/', methods=['POST'])
@login_required
def update_common_details():
	connection = db.session.query(BusinessConnection).get(request.form['id'])
	if connection is None:
		abort(404)
	form = CommonDetailForm(request.values, obj=connection)
	form.populate_obj(connection)
	db.session.commit()
	flash('Updated!', 'success')
	return render_template('partials/_flashes.html')

@main.route('/business-connection/create', methods=['POST'])
@login_required
def business_connection_create():
	""" Stores the requested search parameters and queues the relevant scrapers  """
	form = NewBusinessConnectionForm()
	if form.validate_on_submit:
		scrapers = ','.join(request.form.getlist('scrapers'))
		connection = BusinessConnection(
		first_name = request.form['first_name'],
		last_name = request.form['last_name'],
		user_id = current_user.id,
		scrapers_requested = scrapers.lower())

		if request.form['keywords']:
			connection.keywords = request.form['keywords']

		db.session.add(connection)
		db.session.commit()

		scraper_lower = scrapers.lower()

		""" Queue the domain checkers to run in the background if required """
		if ('ac & edu' in scraper_lower) or ('personal' in scraper_lower):
			logging.warning('>>> domain check')
			get_queue().enqueue(check_domains, business_connection_id=connection.id, first_name=connection.first_name, last_name=connection.last_name)

		""" Queue the google scrapers to run in the background if required """
		enqueue_google_scrapers(scraper_lower, connection)
	else:
		flash('Invalid submission - unable to create new business connection')

	return url_for('main.business_connection_profile', business_connection_id=connection.id)


@main.route('/business-connection/extract', methods=['POST'])
@login_required
def business_connection_extract():
	""" Queues the profile extraction request  """
	search_result = BusinessConnectionSearchResult.query.filter_by(id=request.form['result_id']).first()
	if search_result is None:
		abort(404)

	get_queue().enqueue(perform_profile_extraction, search_result=search_result, user_id=current_user.id)
	return 'Success'

@main.route('/business-connection/results/<int:business_connection_id>/<int:search_type_id>', methods=['GET'])
@login_required
def business_connection_search_results(business_connection_id, search_type_id):
	""" Handles a search request as well as ordering or results """
	search_results = BusinessConnectionSearchResult.query.filter_by(business_connection_id=business_connection_id,business_connection_search_type_id=search_type_id).all()
	if search_results is None:
		abort(404)

	detail = BusinessConnectionDetail.query.filter_by(business_connection_id=business_connection_id, business_connection_search_type_id=search_type_id).first()
	search_type = BusinessConnectionSearchType.query.filter_by(id=search_type_id).first()

	business_connection = BusinessConnection.query.filter_by(id=business_connection_id).first()

	name = search_type.name.lower()
	logging.warning('>>> search_type.name' + name)
	if name == 'linkedin':
		return render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name, linkedinform=LinkedInForm(obj=detail))
	elif name == 'twitter':
		return render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name, twitterform=TwitterForm(obj=detail) )
	elif name == 'youtube':
		return render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name, youtubeform=YouTubeForm(obj=detail) )
	elif name == 'facebook':
		return render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name, facebookform=FacebookForm(obj=detail) )

	return ''


@main.route('/business-connection/search', methods=['POST'])
@login_required
def business_connection_search():
	""" Handles a search request as well as ordering or results """
	form = SearchForm()

	order_by = int(form.sort_order.data)
	search_term = form.search_text.data

	sql_query = BusinessConnection.query
	if search_term:
		sql_query = sql_query.filter(BusinessConnection.last_name.like(form.search_text.data + '%'))

	if order_by == 0:
		sql_query = sql_query.order_by(BusinessConnection.requested_on.desc())
	elif order_by == 1:
		sql_query = sql_query.order_by(BusinessConnection.first_name.desc())
	elif order_by == 2:
		sql_query = sql_query.order_by(BusinessConnection.first_name)
	items = sql_query.all()

	return render_template('partials/_list_connections.html',connections=items)
