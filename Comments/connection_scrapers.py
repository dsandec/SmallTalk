#Imports
import pythonwhois
import datetime
from flask import render_template
from . import db, socketio
from .googlescrapers import LinkedInGoogleScraper, TwitterGoogleScraper, YouTubeGoogleScraper, FacebookGoogleScraper
from .profilescrapers import TwitterProfileScraper, YouTubeProfileScraper, FacebookProfileScraper, LinkedInGoogleProfileExtractor
from .models import BusinessConnection, BusinessConnectionSearchResult, BusinessConnectionSearchType, BusinessConnectionDetail
#Imports below not used in the code
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
import logging
from .main import (NewBusinessConnectionForm, TwitterForm, FacebookForm, YouTubeForm, LinkedInForm)

def check_domains(business_connection_id, first_name, last_name):
	"""Perform check on .ac/.edu and .com domains - uses whois to check if the domain is owned """
    #get connection from table business_connection by business connection id
	connection = db.session.query(BusinessConnection).filter_by(id=business_connection_id).first()
    #instantiate list of suffixes
	suffixes = []
    #if personal text in scrapers requested then add .com to suffixes list
	if 'personal' in connection.scrapers_requested:
		suffixes.append('.com')
    #if ac & text in scrapers requested then add ac & to suffixes list
	if 'ac &' in connection.scrapers_requested:
		suffixes.extend(['.edu','.ac.uk'])
     #concatenate two string variables into full name
	full_name = first_name+last_name
    #create list of dicts using suffixes loop, x goes into dict spots 
	domains = [{'suffix':x, 'name':(full_name+x),'is_available':False} for x in suffixes]
    #loop through domains
	for domain in domains:
        #return get whois result list
		dom = pythonwhois.get_whois(domain['name'])
         #check if creation date is not in whois result then domain is available
		domain['is_available'] = (not 'creation_date' in dom)
    #instantiate results list
	results = []
    #if personal is in scrapers requested then
	if 'personal' in connection.scrapers_requested:
         #loop through domains having domain suffix equal .com to filter out those not complying and then take one domain is available
		connection.is_personal_domain_available = next(x for x in domains if x['suffix'] == '.com')['is_available']
          #save current date to connection
		connection.personal_domain_search_completed_on = datetime.datetime.utcnow()
         #render html result using template, input paramters are mapped as is_not_owned <- connection.is_personal_domain_available
		html = render_template('partials/_domain_status.html', is_not_owned=connection.is_personal_domain_available, url_text=connection.personal_domain())
		#append dict to list using information from connection.is_personal_domain_available and html
        results.append({'search_type':'personal', 'is_available':connection.is_personal_domain_available, 'html':html})
    #if ac & is in scrapers requested then
	if 'ac &' in connection.scrapers_requested:
        #add addtional sufixes
		suffixes.extend(['.edu','.ac.uk'])
         #loop through domains having domain suffix equal .edu to filter out those not complying and then take one domain is available
		connection.is_edu_domain_available = next(x for x in domains if x['suffix'] == '.edu')['is_available']
        #similar
		connection.is_ac_domain_available = next(x for x in domains if x['suffix'] == '.ac.uk')['is_available']
         #save current date to connection
		connection.education_domain_search_completed_on = datetime.datetime.utcnow()
         #render html result using template imput paramters are mapped as is_not_owned <- connection.is_personal_domain_available
		html = render_template('partials/_domain_status.html', is_not_owned=connection.is_edu_domain_available, url_text=connection.edu_domain())
		#append dict to list using information from connection.is_personal_domain_available and html
        results.append({'search_type':'edu', 'is_available':connection.is_edu_domain_available, 'html':html})
        #similar
		html = render_template('partials/_domain_status.html', is_not_owned=connection.is_ac_domain_available, url_text=connection.ac_domain())
		results.append({'search_type':'ac', 'is_available':connection.is_ac_domain_available, 'html':html})
    #save db changes
	db.session.commit()
    #create dict message
	message = {
		'uid':connection.user_id,
		'domains':results
	}
    #https://python-socketio.readthedocs.io/en/latest/
	socketio.emit('domain_scrape_complete', message, room=message['uid'], namespace='/notifs')

#function returning google scraper classes based on description parameter
def get_google_scraper(description):
	desc = description.lower()
	if 'linkedin' in desc:
		return LinkedInGoogleScraper()
	elif 'twitter' in desc:
		return TwitterGoogleScraper()
	elif 'youtube' in desc:
		return YouTubeGoogleScraper()
	elif 'facebook' in desc:
		return FacebookGoogleScraper()

#function update completed on date to now in connection using mapping based on scrapers name
def update_completion(description, connection):
	desc = description.lower()
	if 'linkedin' in desc:
		connection.linkedin_search_completed_on = datetime.datetime.utcnow()
	elif 'twitter' in desc:
		connection.twitter_search_completed_on = datetime.datetime.utcnow()
	elif 'youtube' in desc:
		connection.youtube_search_completed_on = datetime.datetime.utcnow()
	elif 'facebook' in desc:
		connection.facebook_search_completed_on = datetime.datetime.utcnow()

def perform_google_search(business_connection_id, first_name, last_name, search_type, keywords, user_id):
	""" Creates a google scraper (specific to the type of search requested - Facebook/YouTube etc...) and retreives the search data from google """
	#get parser by search type name
    parser = get_google_scraper(search_type.name)
     #search google results by first name and last name and keywords
	results = parser.search('{0} {1}'.format(first_name, last_name), keywords=keywords)
     #instantiate db_results list
	db_results = []
    #loop through results
	for result in results:
        #map values to db results which is instance of BusinessConnectionSearchResult
		db_result = BusinessConnectionSearchResult(**result)
		db_result.user_id = user_id
		db_result.business_connection_search_type_id = search_type.id
		db_result.business_connection_id = business_connection_id
		db.session.add(db_result)
        #append to list of db_results
		db_results.append(db_result)
     #get businnes connection by business connection id
	connection = db.session.query(BusinessConnection).filter_by(id=business_connection_id).first()
    #update completion using search type name to connection
	update_completion(search_type.name, connection)
    #save db session
	db.session.commit()

	""" Return the rendered results back to the UI via socketio """
	html = render_template('partials/_search_results_tab.html', search_results=db_results)
     #create meesage dict
	message = {
		'count':len(results),
		'html': html,
		'search_type_id':search_type.id,
		'uid':user_id
	}

	""" Inform the front end that the scrape has completed """
	socketio.emit('google_scrape_complete', message, room=message['uid'], namespace='/notifs')

#function get profile scraper by providing url based on scrape type name 
def get_profile_scraper(url,search_result):
	scrape_type = BusinessConnectionSearchType.query.filter_by(id=search_result.business_connection_search_type_id).first()
    #extract string as lower case to name
	name = scrape_type.name.lower()
	if name == 'linkedin':
         #return scraper class 
		return LinkedInGoogleProfileExtractor(search_result)
	elif name == 'twitter':
		return TwitterProfileScraper(url)
	elif name == 'youtube':
		return YouTubeProfileScraper(url)
	elif name == 'facebook':
		return FacebookProfileScraper(url)

def perform_profile_extraction(search_result, user_id):
	""" Extracts the profile information from the requested website """
	profile = get_profile_scraper(search_result.url, search_result)
     #delete old business connection detail using filter by search type id and business connection id
	db.session.query(BusinessConnectionDetail).filter_by(business_connection_search_type_id=search_result.business_connection_search_type_id,business_connection_id=search_result.business_connection_id).delete()
	#save DB session
    db.session.commit()

	""" Store the profile infomation """
	detail = BusinessConnectionDetail(**profile.to_dict())
	detail.business_connection_search_type_id = search_result.business_connection_search_type_id
	detail.business_connection_id = search_result.business_connection_id
	detail.url = search_result.url
	detail.completed_on = datetime.datetime.utcnow()

	db.session.add(detail)
	db.session.commit()

     #fetch business connection using search resulst business connection id
	business_connection = BusinessConnection.query.filter_by(id=search_result.business_connection_id).first()
    #fetch search type from DB
	search_type = BusinessConnectionSearchType.query.filter_by(id=search_result.business_connection_search_type_id).first()
	html = None

	""" Return the rendered results back to the UI via socketio """
	name = search_type.name.lower()
    #render results using correspoding templates based on search type
	if name == 'linkedin':
		html = render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name, linkedinform=LinkedInForm(obj=detail) )
	elif name == 'twitter':
		html = render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name, twitterform=TwitterForm(obj=detail) )
	elif name == 'youtube':
		html = render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name, youtubeform=YouTubeForm(obj=detail) )
	elif name == 'facebook':
		html = render_template('partials/_connection_profile.html', business_connection=business_connection, business_connection_detail=detail, search_type_name=name, facebookform=FacebookForm(obj=detail) )

	message = {
		'html':html,
		'search_type_id':search_result.business_connection_search_type_id,
		'uid':user_id
	}

	""" Inform the front end that the scrape has completed """
	socketio.emit('profile_scrape_complete', message, room=message['uid'], namespace='/notifs')
