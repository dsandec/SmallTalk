import argparse
import random
import warnings
import os
import unicodecsv as csv
import requests
import re
import socket
import logging
import urllib.request

from lxml import html

socket.setdefaulttimeout(30)

class BaseScraper(object):
	def perform_request(self, url):
		""" Perform a Http request and store the returned page locally """
		headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					'Accept-Encoding':'gzip, deflate, br',
					'Accept-Language':'en-US,en;q=0.5',
					'Cache-Control':'max-age=0',
					'Connection':'keep-alive',
					'Upgrade-Insecure-Requests': '1',
					'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:1.8.1.4) Gecko/20070515 Firefox/2.0.0.4',
					}
		r = requests.Session()
		html_page = r.get(url, headers=headers).text
		return self.parse(html_page, url)

	def parse(self, page_text, url):
		pass

class GoogleScraper(BaseScraper):
	url_template = 'http://www.google.co.uk/search?q={0}'

	def __init__(self, search_suffix=None):
		""" The suffix is to be added to the end of the search string"""
		self.search_suffix = search_suffix

	def search(self, search_term, keywords=None):
		search_string = '"%s"'%search_term

		""" Add keywords to the search string if they exist """
		if keywords:
			search_string = search_string + '+"%s"'%'"+"'.join(keywords.split(','))

		url = self.url_template.format(search_string) + ' ' + urllib.request.quote(self.search_suffix)

		""" OK Google! """
		return self.perform_request(url)

	def parse(self, page_text, url):
		""" Extract the search results """

		parser = html.fromstring(page_text)
		listings = parser.xpath('//div[@class="g card-section"]')
		if not listings:
			listings =  parser.xpath('//div[@class="g"]')

		datas = list()
		for listing in listings:
			raw_description = listing.xpath('.//span[@class="st"]//text()')
			raw_summary = listing.xpath('.//div[contains(@class,"slp")]//text()')
			raw_url = listing.xpath('.//cite//text()')
			raw_title = listing.xpath('.//h3//a//text()')

			raw_description = ''.join(raw_description)
			data = {
				'title': ''.join(raw_title),
				'url': ''.join(raw_url),
				'description': ''.join(raw_description),
				'summary': ''.join(raw_summary),
			}
			datas.append(data)
		return datas

class YouTubeGoogleScraper(GoogleScraper):
	def __init__(self):
		super(YouTubeGoogleScraper, self).__init__('+site:www.youtube.com/user')

class FacebookGoogleScraper(GoogleScraper):
	def __init__(self):
		super(FacebookGoogleScraper, self).__init__('+site:www.facebook.com/people')

class TwitterGoogleScraper(GoogleScraper):
	def __init__(self):
		super(TwitterGoogleScraper, self).__init__('+site:twitter.com -"status" -"statuses" -"moments" -"blog"')

class LinkedInGoogleScraper(GoogleScraper):
	def __init__(self):
		super(LinkedInGoogleScraper, self).__init__('site:uk.linkedin.com/in/ OR site:uk.linkedin.com/pub/ -"profiles"')
