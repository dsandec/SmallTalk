# IMPORTS SECTION
# Importing all required Python built-in and project related source libraries
# Package for logging
import logging
#JSON handling package
import json

# Read https://pythonhow.com/how-a-flask-app-works/
# Flask related imports, more about components can be found http://flask.pocoo.org/
from flask import flash, redirect, render_template, request, url_for, abort
#https://flask-login.readthedocs.io/en/latest/
from flask_login import current_user, login_required
# https://github.com/mattupstate/flask-rq
from flask_rq import get_queue
# https://wtforms.readthedocs.io/en/stable/fields.html
from wtforms.fields import StringField

# import main module from working directory
from . import main
# import db module in the top dir
from .. import db
# import mentioned classes from parallel directory to current files, which is models
from ..models import BusinessConnection, BusinessConnectionDetail, BusinessConnectionUniversity, BusinessConnectionJob, BusinessConnectionSearchResult, BusinessConnectionSearchType
# import from parallel file forms.py mentioned classes
from .forms import (NewBusinessConnectionForm, TwitterForm, FacebookForm, YouTubeForm, CommonDetailForm, SearchForm, LinkedInForm)
# import from connection_scrapers.py mentioned functions
from ..connection_scrapers import check_domains, perform_google_search, perform_profile_extraction

# function enqueue_google_scrapers with input parameters required_scrapers, connection
def enqueue_google_scrapers(required_scrapers, connection):
	""" Queue the requested profile scrapers in RQ inorder for them to run as background tasks """
    # From DB table business_connection_search_type fetch all search types as list
	search_types = BusinessConnectionSearchType.query.all()
    # define list of sites
	sites = ['linkedin','twitter','youtube','facebook']
    # loop all sites, taking them one by one
	for site in sites:
         # if site is mentioned in parameter list required_scrapers then execute further
		if site in required_scrapers:
              # get search_type as next item from the iterator, which is the result x from list search_types if x.name in lower case matched site value
			search_type = next(x for x in search_types if x.name.lower()==site)
              # get flask Redis Queue and enqueue google scraper which is defined in perform_google_search to do the job with parameters
              # business_connection_id=connection.id, 
              # first_name=connection.first_name, 
              # last_name=connection.last_name, 
              # search_type=search_type, 
              # keywords=connection.keywords, 
              # user_id=current_user.id
			get_queue().enqueue(perform_google_search, business_connection_id=connection.id, first_name=connection.first_name, last_name=connection.last_name, search_type=search_type, keywords=connection.keywords, user_id=current_user.id)

# processor function to handle education form
def handle_work_education_form(form_type, values, detail):
	""" Handle the special types work/education """
    # takes provided form_type and prepares form
	form = form_type(values, obj=detail)
    # get education data
	education_data = form.education.data
    # get work data 
	work_data = form.work.data
     # delete work and education parts from form
	del(form.work)
	del(form.education)
     # populate details values into form
	form.populate_obj(detail)
     # reasign work and education data to form
	detail.work = work_data
	detail.education = education_data

# This is flask related defintion to execute function index in case root html path of the site is opened in browser 
@main.route('/')
def index():
	""" Home page - If authenticated then show the user they're custom home page """
	#check if user is authenticated
    if current_user.is_authenticated:
         #Fetch values from table business_connection from current user id
		connections = BusinessConnection.query.filter_by(user_id=current_user.id).all()
         #instantiate object of NewBusinessConnectionForm class
		new_connect_form = NewBusinessConnectionForm()
         #Flask render_template function to render and return html code using defined template and given parameters
		return render_template('main/index.html', connections=connections, form=new_connect_form, search_form=SearchForm())
     #Flask render_template function to render and return html code defined template for user without authentication
	return render_template('main/index.html')

# This is flask related defintion to execute function about in case root/about html path of the site is opened in browser
@main.route('/about')
def about():
      #Flask render_template function to render and return html code defined template for about page
	return render_template('main/about.html')

# check explanations above
@main.route('/terms-of-use')
def terms_of_use():
      #Flask render_template function to render and return html code defined template for terms of use
	return render_template('main/terms-of-use.html')

# check explanations above
@main.route('/privacy-policy')
def privacy_policy():
      #Flask render_template function to render and return html code defined template for privacy policy
	return render_template('main/privacy-policy.html')

# check explanations above
@main.route('/compliance')
def compliance():
      #Flask render_template function to render and return html code defined template for compliance
	return render_template('main/compliance.html')

# check explanations above
@main.route('/business-connection/<int:business_connection_id>')
# flask definition to forse login
@login_required
def business_connection_profile(business_connection_id):
	""" Retrieve a previously stored business connection """
    #Fetch values from table business_connection using current connection id
	connection = db.session.query(BusinessConnection).filter_by(id=business_connection_id).first()
    #if no connection found return not allowed page
	if connection is None:
		abort(404)
     #Fetch results from DB table business_connection_search_results using business connection id
	search_results = BusinessConnectionSearchResult.query.filter_by(business_connection_id=business_connection_id).all()

     #create google search results as list of dictionaries with search results as list by search type id 
	google_search_results = [
		{'name':'linkedin', 'id':1, 'results':[x for x in search_results if x.business_connection_search_type_id==1]},
		{'name':'facebook', 'id':2, 'results':[x for x in search_results if x.business_connection_search_type_id==2]},
		{'name':'youtube', 'id':3, 'results':[x for x in search_results if x.business_connection_search_type_id==3]},
		{'name':'twitter', 'id':4, 'results':[x for x in search_results if x.business_connection_search_type_id==4]}
	]
     #get scrapers requested from connection and separate them into scrapers_requested list using comma
	scrapers_requested = connection.scrapers_requested.split(',')
    #remove dicts from google search list of dicts which were not requested 
	google_search_results = [x for x in google_search_results if x['name'] in scrapers_requested]
     
    #get details from DB table business_connection_detail using business connection id and search type equal to 1
	detail = BusinessConnectionDetail.query.filter_by(business_connection_id=business_connection_id, business_connection_search_type_id=1).first()
     #instantiate Flask form of CommonDetailForm class
	form = CommonDetailForm(obj=connection)
    #instantiate BaseForm form of LinkedInForm class
	linkedin_form = LinkedInForm(obj=detail)
    #incorporate instantiated and prepared forms and values into HTML business_connection_profile template 
	return render_template('main/business_connection_profile.html', business_connection=connection, business_connection_detail=detail, google_search_results=google_search_results, search_type_name='linkedin', facebookform=FacebookForm(),twitterform=TwitterForm(),youtubeform=YouTubeForm(),commondetailform=form,linkedinform=linkedin_form)

def update_profile(form_type, request, processor=None):
	""" Update profile information """
    #get details from DB business_connection_detail table using request form id
	detail = db.session.query(BusinessConnectionDetail).get(request.form['id'])
    #if no result fetched the return from function with false
	if detail is None:
		return False
    #if form processor is provided as prarameter then call it with details to be placed 
	if processor:
		processor(form_type, request.values, detail)
	else:
    #if no processor then handle it as regular form and popupalet details
		form = form_type(request.values, obj=detail)
		form.populate_obj(detail)
    #save DB session
	db.session.commit()
    #return from function with true result
	return True

#if user changes Facebook profile form values and posts then call function below
@main.route('/business-connection/facebook/', methods=['POST'])
@login_required
def update_facebook_profile():
    #call Facebook form profile handling if result is false then abort with html status 404 
	if not update_profile(FacebookForm, request, handle_work_education_form):
		abort(404)
	return ''

#if user changes Youtube profile form values and posts then call function below
@main.route('/business-connection/youtube/', methods=['POST'])
@login_required
def update_youtube_profile():
     #call YouTubeForm form profile handling if result is false then abort with html status 404 
	if not update_profile(YouTubeForm, request):
		abort(404)
	return ''

#if user changes Twitter profile form values and posts then call function below
@main.route('/business-connection/twitter/', methods=['POST'])
@login_required
def update_twitter_profile():
     #call Twitter (although YoutubeForm is used) form profile handling if result is false then abort with html status 404 
	if not update_profile(YouTubeForm, request):
		abort(404)
	return ''

#if user changes Linkedin profile form values and posts then call function below
@main.route('/business-connection/linkedin/', methods=['POST'])
@login_required
def update_linkedin_profile():
	print ('HELLP!!!!!!!')
     #call LinkedInForm form profile handling if result is false then abort with html status 404 
	if not update_profile(LinkedInForm, request, handle_work_education_form):
		abort(404)
	return ''

#if user changes common details form values and posts then call function below
@main.route('/business-connection/common_detail/', methods=['POST'])
@login_required
def update_common_details():
    #Fetch values from DB of business connection using form id
	connection = db.session.query(BusinessConnection).get(request.form['id'])
    # if no values fetched then return html status 404 
	if connection is None:
		abort(404)
     #instantiate common detail form with request values
	form = CommonDetailForm(request.values, obj=connection)
	form.populate_obj(connection)
    #
	db.session.commit()
	flash('Updated!', 'success')
	return render_template('partials/_flashes.html')

#if user adds business connection and posts then call function below
@main.route('/business-connection/create', methods=['POST'])
@login_required
def business_connection_create():
	""" Stores the requested search parameters and queues the relevant scrapers  """
    #instantiate business connection form
	form = NewBusinessConnectionForm()
    #call Flask form validation on form submit, if true then execute below
	if form.validate_on_submit:
         #join scrapers as string separated by comma
		scrapers = ','.join(request.form.getlist('scrapers'))
         #instantiate connection using class  BusinessConnection with parameters
		connection = BusinessConnection(
         #get value from form field first_name and put it as first_name variable
		first_name = request.form['first_name'],
         #get value from form field last_name and put it as last_name variable
		last_name = request.form['last_name'],
         #get value from Flask current_user
		user_id = current_user.id,
         #asign scrapers string value to scrapers_requested
		scrapers_requested = scrapers.lower())
         #form has keywords values then store then as well into connection
		if request.form['keywords']:
			connection.keywords = request.form['keywords']
         #store connection in db session 
		db.session.add(connection)
         #and save db
		db.session.commit()
         #scrapers string assigned to scraper_lower in lower case
		scraper_lower = scrapers.lower()

		""" Queue the domain checkers to run in the background if required """
         #if scraper_lower has strings mentioned 
		if ('ac & edu' in scraper_lower) or ('personal' in scraper_lower):
              #create log output
			logging.warning('>>> domain check')
              #enqueue process for domain check
			get_queue().enqueue(check_domains, business_connection_id=connection.id, first_name=connection.first_name, last_name=connection.last_name)

		""" Queue the google scrapers to run in the background if required """
		enqueue_google_scrapers(scraper_lower, connection)
	else:
		flash('Invalid submission - unable to create new business connection')
    #returns url to re-route browser 
	return url_for('main.business_connection_profile', business_connection_id=connection.id)

#if user submits for profile extraction then call function below
@main.route('/business-connection/extract', methods=['POST'])
@login_required
def business_connection_extract():
	""" Queues the profile extraction request  """
	search_result = BusinessConnectionSearchResult.query.filter_by(id=request.form['result_id']).first()
	if search_result is None:
		abort(404)
     #enqueue process to perform profile extraction
	get_queue().enqueue(perform_profile_extraction, search_result=search_result, user_id=current_user.id)
	return 'Success'

#if url is called as below, then treat what goes after results/ as input parameters for function below
@main.route('/business-connection/results/<int:business_connection_id>/<int:search_type_id>', methods=['GET'])
@login_required
def business_connection_search_results(business_connection_id, search_type_id):
	""" Handles a search request as well as ordering or results """
	search_results = BusinessConnectionSearchResult.query.filter_by(business_connection_id=business_connection_id,business_connection_search_type_id=search_type_id).all()
	if search_results is None:
		abort(404)
     #fetch detail from DB table business_connection_detail using business conection id
	detail = BusinessConnectionDetail.query.filter_by(business_connection_id=business_connection_id, business_connection_search_type_id=search_type_id).first()
	#search_type detail from DB table business_connection_search_type using search type id
    search_type = BusinessConnectionSearchType.query.filter_by(id=search_type_id).first()
     #fetch business connection from DB table
	business_connection = BusinessConnection.query.filter_by(id=business_connection_id).first()
     #get search type name from search_type
	name = search_type.name.lower()
	logging.warning('>>> search_type.name' + name)
	if name == 'linkedin':
         #render result using parameters
		return render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name)
	elif name == 'twitter':
		return render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name, twitterform=TwitterForm(obj=detail) )
	elif name == 'youtube':
		return render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name, youtubeform=YouTubeForm(obj=detail) )
	elif name == 'facebook':
		return render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name, facebookform=FacebookForm(obj=detail) )

	return ''

# if user 
@main.route('/business-connection/search', methods=['POST'])
@login_required
def business_connection_search():
	""" Handles a search request as well as ordering or results """
     #instantiate Flask form
	form = SearchForm()
     #order by get as int from form sort_order_data
	order_by = int(form.sort_order.data)
    #get search_term from form
	search_term = form.search_text.data
     #get sql query string from business connection class
	sql_query = BusinessConnection.query
	if search_term:
        #search term provided use it to find businness connection
		sql_query = sql_query.filter(BusinessConnection.last_name.like(form.search_text.data + '%'))
     #sort result based on users choise
	if order_by == 0:
		sql_query = sql_query.order_by(BusinessConnection.requested_on.desc())
	elif order_by == 1:
		sql_query = sql_query.order_by(BusinessConnection.first_name.desc())
	elif order_by == 2:
		sql_query = sql_query.order_by(BusinessConnection.first_name)
	items = sql_query.all()
     #render result inside list items using template 
	return render_template('partials/_list_connections.html',connections=items)
