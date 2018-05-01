import pythonwhois
import datetime
import logging

from flask import render_template
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from . import db, socketio
from .googlescrapers import LinkedInGoogleScraper, TwitterGoogleScraper, YouTubeGoogleScraper, FacebookGoogleScraper
from .profilescrapers import TwitterProfileScraper, YouTubeProfileScraper, FacebookProfileScraper, LinkedInGoogleProfileExtractor
from .models import BusinessConnection, BusinessConnectionSearchResult, BusinessConnectionSearchType, BusinessConnectionDetail
from .main import (NewBusinessConnectionForm, TwitterForm, FacebookForm, YouTubeForm, LinkedInForm)

def check_domains(business_connection_id, first_name, last_name):
	"""Perform check on .ac/.edu and .com domains - uses whois to check if the domain is owned """
	connection = db.session.query(BusinessConnection).filter_by(id=business_connection_id).first()
	suffixes = []
	if 'personal' in connection.scrapers_requested:
		suffixes.append('.com')
	if 'ac &' in connection.scrapers_requested:
		suffixes.extend(['.edu','.ac.uk'])

	full_name = first_name+last_name
	domains = [{'suffix':x, 'name':(full_name+x),'is_available':False} for x in suffixes]
	for domain in domains:
		dom = pythonwhois.get_whois(domain['name'])
		domain['is_available'] = (not 'creation_date' in dom)

	results = []
	if 'personal' in connection.scrapers_requested:
		connection.is_personal_domain_available = next(x for x in domains if x['suffix'] == '.com')['is_available']
		connection.personal_domain_search_completed_on = datetime.datetime.utcnow()
		html = render_template('partials/_domain_status.html', is_not_owned=connection.is_personal_domain_available, url_text=connection.personal_domain())
		results.append({'search_type':'personal', 'is_available':connection.is_personal_domain_available, 'html':html})

	if 'ac &' in connection.scrapers_requested:
		suffixes.extend(['.edu','.ac.uk'])
		connection.is_edu_domain_available = next(x for x in domains if x['suffix'] == '.edu')['is_available']
		connection.is_ac_domain_available = next(x for x in domains if x['suffix'] == '.ac.uk')['is_available']
		connection.education_domain_search_completed_on = datetime.datetime.utcnow()

		html = render_template('partials/_domain_status.html', is_not_owned=connection.is_edu_domain_available, url_text=connection.edu_domain())
		results.append({'search_type':'edu', 'is_available':connection.is_edu_domain_available, 'html':html})

		html = render_template('partials/_domain_status.html', is_not_owned=connection.is_ac_domain_available, url_text=connection.ac_domain())
		results.append({'search_type':'ac', 'is_available':connection.is_ac_domain_available, 'html':html})

	db.session.commit()

	message = {
		'uid':connection.user_id,
		'domains':results
	}
	socketio.emit('domain_scrape_complete', message, room=message['uid'], namespace='/notifs')

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
	parser = get_google_scraper(search_type.name)

	results = parser.search('{0} {1}'.format(first_name, last_name), keywords=keywords)

	db_results = []
	for result in results:
		db_result = BusinessConnectionSearchResult(**result)
		db_result.user_id = user_id
		db_result.business_connection_search_type_id = search_type.id
		db_result.business_connection_id = business_connection_id
		db.session.add(db_result)
		db_results.append(db_result)

	connection = db.session.query(BusinessConnection).filter_by(id=business_connection_id).first()
	update_completion(search_type.name, connection)
	db.session.commit()

	""" Return the rendered results back to the UI via socketio """
	html = render_template('partials/_search_results_tab.html', search_results=db_results)

	message = {
		'count':len(results),
		'html': html,
		'search_type_id':search_type.id,
		'uid':user_id
	}

	""" Inform the front end that the scrape has completed """
	socketio.emit('google_scrape_complete', message, room=message['uid'], namespace='/notifs')


def get_profile_scraper(url,search_result):
	scrape_type = BusinessConnectionSearchType.query.filter_by(id=search_result.business_connection_search_type_id).first()
	name = scrape_type.name.lower()
	if name == 'linkedin':
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

	db.session.query(BusinessConnectionDetail).filter_by(business_connection_search_type_id=search_result.business_connection_search_type_id,business_connection_id=search_result.business_connection_id).delete()
	db.session.commit()

	""" Store the profile infomation """
	detail = BusinessConnectionDetail(**profile.to_dict())
	detail.business_connection_search_type_id = search_result.business_connection_search_type_id
	detail.business_connection_id = search_result.business_connection_id
	detail.url = search_result.url
	detail.completed_on = datetime.datetime.utcnow()

	db.session.add(detail)
	db.session.commit()

	business_connection = BusinessConnection.query.filter_by(id=search_result.business_connection_id).first()
	search_type = BusinessConnectionSearchType.query.filter_by(id=search_result.business_connection_search_type_id).first()
	html = None

	""" Return the rendered results back to the UI via socketio """
	name = search_type.name.lower()
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
