#these imports not used
import argparse
import random
import warnings
import os
import unicodecsv as csv
import re
import logging
#import socket package
import socket
#import requests
import requests
#import urlib.request
import urllib.request
#import html from xml
from lxml import html
#define socket timeout to 30s
socket.setdefaulttimeout(30)

#define base scraper class
class BaseScraper(object):
    #function to perform url request
	def perform_request(self, url):
		""" Perform a Http request and store the returned page locally """
         #scraper headers to identify himself as firefox
		headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					'Accept-Encoding':'gzip, deflate, br',
					'Accept-Language':'en-US,en;q=0.5',
					'Cache-Control':'max-age=0',
					'Connection':'keep-alive',
					'Upgrade-Insecure-Requests': '1',
					'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:1.8.1.4) Gecko/20070515 Firefox/2.0.0.4',
					}
         #instantiate request session
		r = requests.Session()
         #retrieve html page 
		html_page = r.get(url, headers=headers).text
         #return html page
		return self.parse(html_page, url)

	def parse(self, page_text, url):
		pass
#define Google scraper class based on Base scraper
class GoogleScraper(BaseScraper):
    #google search url
	url_template = 'http://www.google.co.uk/search?q={0}'
    #method to call during instantiate of class
	def __init__(self, search_suffix=None):
		""" The suffix is to be added to the end of the search string"""
        #asign search string to class property
		self.search_suffix = search_suffix
     #method to make search
	def search(self, search_term, keywords=None):
        #convert to string with double quotes
		search_string = '"%s"'%search_term

		""" Add keywords to the search string if they exist """
		if keywords:
              #create search string by joining keywords
			search_string = search_string + '+"%s"'%'"+"'.join(keywords.split(','))
        #create google call url with all search strings and keywords
		url = self.url_template.format(search_string) + ' ' + urllib.request.quote(self.search_suffix)

		""" OK Google! """
		return self.perform_request(url)

	def parse(self, page_text, url):
		""" Extract the search results """
         #prepare for xpath searching
		parser = html.fromstring(page_text)
         #extarct listings
		listings = parser.xpath('//div[@class="g card-section"]')
		if not listings:
			listings =  parser.xpath('//div[@class="g"]')

		datas = list()
         #process each listing in loop
		for listing in listings:
              #extract info from listing using xpath
			raw_description = listing.xpath('.//span[@class="st"]//text()')
			raw_summary = listing.xpath('.//div[contains(@class,"slp")]//text()')
			raw_url = listing.xpath('.//cite//text()')
			raw_title = listing.xpath('.//h3//a//text()')
              
			raw_description = ''.join(raw_description)
              #create result dict
			data = {
				'title': ''.join(raw_title),
				'url': ''.join(raw_url),
				'description': ''.join(raw_description),
				'summary': ''.join(raw_summary),
			}
              #asign it to list of previous results
			datas.append(data)
		return datas
#define Youtube Google scraper class based on Google scraper
class YouTubeGoogleScraper(GoogleScraper):
    #call this method when class is instantiated
	def __init__(self):
         #call parent __init__ method with google search string
		super(YouTubeGoogleScraper, self).__init__('+site:www.youtube.com/user')
#define Facebook Google scraper class based on Google scraper
class FacebookGoogleScraper(GoogleScraper):
    #call this method when class is instantiated
	def __init__(self):
        #call parent __init__ method with google search string
		super(FacebookGoogleScraper, self).__init__('+site:www.facebook.com/people')
#define Twitter Google scraper class based on Google scraper
class TwitterGoogleScraper(GoogleScraper):
    #call this method when class is instantiated
	def __init__(self):
        #call parent __init__ method with google search string
		super(TwitterGoogleScraper, self).__init__('+site:twitter.com -"status" -"statuses" -"moments" -"blog"')
#define Linkedin Google scraper class based on Google scraper
class LinkedInGoogleScraper(GoogleScraper):
    #call this method when class is instantiated
	def __init__(self):
        #call parent __init__ method with google search string
		super(LinkedInGoogleScraper, self).__init__('site:uk.linkedin.com/in/ OR site:uk.linkedin.com/pub/ -"profiles"')
