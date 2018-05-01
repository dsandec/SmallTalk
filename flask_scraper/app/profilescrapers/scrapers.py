import time
import urllib.request
import requests

from lxml import html,etree
from . import *

def extract_one(l, value=None):
	""" Return value if empy list else return first element """
	if len(l) == 0:
		return value
	else:
		return l[0]

def merge(l, seperator=None):
	if isinstance(l, list):
		if seperator:
			return seperator.join(l).strip()
		return ''.join(l).strip()
	return l

class BaseProfileScraper(object):
	def __init__(self, url):
		headers = {
					'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:1.8.1.4) Gecko/20070515 Firefox/2.0.0.4',
					}
		r = requests.Session()
		response = r.get(url, headers=headers)
		self.html_string = response.text
		self.html_content = response.content
		self.url = url

class FacebookProfileScraper(BaseProfileScraper):

	def __init__(self, url):
		super(FacebookProfileScraper, self).__init__(url)

		self.tree = html.fromstring(self.html_string)

		# Education path
		self.xp_education = self.tree.xpath('//div[span[text()="Education"]]//following-sibling::ul//div[div/a[not(img)]]')
		# Links path
		self.xp_city = extract_one(self.tree.xpath('//div[span[text()="Current City and Home Town"]]//following-sibling::ul'))
		# Work path
		self.xp_work = self.tree.xpath('//div[span[text()="Work"]]//following-sibling::ul/li')
		# Professional skills path
		self.xp_professional_skills = self.tree.xpath('//div[span[text()="Professional Skills"]]//following-sibling::ul/li//a//text()')

	@property
	def current_city(self):
		""" Get current city  """
		if not self.xp_city:
			return None
		return extract_one(self.xp_city.xpath('.//li[@id="current_city"]//a/text()'))

	@property
	def home_town(self):
		""" Get home town  """
		if not self.xp_city:
			return None
		return extract_one(self.xp_city.xpath('.//li[@id="hometown"]//a/text()'))

	@property
	def education(self):
		""" Get list of education history  """
		if len(self.xp_education) > 0:
			return [{'name': extract_one(g.xpath('.//a//text()')),
					'summary': ''.join(g.xpath('./div[2]/div//text()'))}
					for g in self.xp_education]
		else:
			return []

	@property
	def professional_skills(self):
		""" Get list of professional skills  """
		return self.tree.xpath('//div[span[text()="Professional Skills"]]//following-sibling::ul/li//a//text()')

	@property
	def work(self):
		""" Get list of work  """
		if len(self.xp_work) > 0:
			return [{'name': extract_one(g.xpath('.//a//text()')),
					'summary': ''.join(g.xpath('.//div[2]/div[not(a)]//text()'))}
					for g in self.xp_work]
		else:
			return []

	@property
	def movies(self):
		return self.tree.xpath('//th[div[text()="Movies"]]/following-sibling::td//a//text()')

	@property
	def sports(self):
		return self.tree.xpath('//th[div[text()="Sports"]]/following-sibling::td//a//text()')

	@property
	def music(self):
		return self.tree.xpath('//th[div[text()="Music"]]/following-sibling::td//a//text()')

	@property
	def sports_team(self):
		return self.tree.xpath('//th[div[text()="Sports teams"]]/following-sibling::td//a//text()')

	@property
	def athletes(self):
		return self.tree.xpath('//th[div[text()="Athletes"]]/following-sibling::td//a//text()')

	@property
	def books(self):
		return self.tree.xpath('//th[div[text()="Books"]]/following-sibling::td//a//text()')

	@property
	def television(self):
		return self.tree.xpath('//th[div[text()="Television"]]/following-sibling::td//a//text()')

	@property
	def inspirational_people(self):
		return self.tree.xpath('//th[div[text()="Inspirational people"]]/following-sibling::td//a//text()')

	@property
	def games(self):
		return self.tree.xpath('//th[div[text()="Games"]]/following-sibling::td//a//text()')

	@property
	def quotes(self):
		return self.tree.xpath('//div[@id="pagelet_quotes"]//li//text()')

	@property
	def other(self):
		return self.tree.xpath('//th[div[text()="Other"]]/following-sibling::td//a//text()')

	@property
	def bio(self):
		return self.tree.xpath('//div[@id="pagelet_bio"]//li//text()')

	def to_dict(self):
		data={
		'url': self.url,
		'current_city': self.current_city,
		'home_town': self.home_town,
		'education': self.education,
		'work': self.work,
		'movies': merge(self.movies,', '),
		'music': merge(self.music,', '),
		'sports_team': merge(self.sports_team,', '),
		'athletes': merge(self.athletes,', '),
		'books': merge(self.books,', '),
		'quotes': merge(self.quotes,', '),
		'television': merge(self.television,', '),
		'inspirational_people': merge(self.inspirational_people,', '),
		'professional_skills': merge(self.professional_skills,', '),
		'games':merge(self.games,', '),
		'other':merge(self.other,', '),
		'bio': merge(self.bio),
		}
		return data

class YouTubeProfileScraper(BaseProfileScraper):

	def __init__(self, url):
		url = url + '/about'
		super(YouTubeProfileScraper, self).__init__(url)

		self.tree = html.fromstring(self.html_string)

	@property
	def bio(self):
		""" Return the number of connections """
		return self.tree.xpath('//div[starts-with(@class,"about-description")]//text()')

	def to_dict(self):
		data={
		'url': self.url,
		'bio': merge(self.bio),
		}
		return data

class TwitterProfileScraper(BaseProfileScraper):

	def __init__(self, url):
		super(TwitterProfileScraper, self).__init__(url)

		self.tree = html.fromstring(self.html_content)

	@property
	def website(self):
		""" Return the website """
		return extract_one(self.tree.xpath('//div[@class="url"]//a/@data-url'))

	@property
	def country(self):
		""" Return country """
		return extract_one(self.tree.xpath('//div[@class="location"]//text()'))

	@property
	def bio(self):
		""" Return bio """
		bio_raw = self.tree.xpath('//div[@class="bio"]//text()')
		if bio_raw:
			bio_raw = ''.join(bio_raw)
		return bio_raw

	def to_dict(self):
		data={
		'url': self.url,
		'bio': merge(self.bio),
		'website': self.website,
		'country': self.country,
		}
		return data


class LinkedInGoogleProfileExtractor():
	def __init__(self, search_result):
		self.search_result = search_result
		self.url = search_result.url

	@property
	def current_city(self):
		""" Get current city  """
		if len(self.search_result.summary) > 0:
			return self.search_result.summary.split('-')[0]
		return None

	@property
	def bio(self):
		""" Get Bio (description)  """
		if len(self.search_result.description) > 0:
			if 'profile on Linkedin' not in self.search_result.description:
				return self.search_result.description

		return None

	@property
	def work(self):
		""" Get list of work  """
		if len(self.search_result.summary) > 0:
			if 'Student at' not in self.search_result.summary:
				values = self.search_result.summary.split('-')
				return [{'name': values[1],
						'summary': values[-1]}]

		return []

	@property
	def education(self):
		""" Get list of education  """
		if len(self.search_result.summary) > 0:
			if 'Student at' in self.search_result.summary:
				values = self.search_result.summary.split('-')
				values = next(x for x in values if 'Student at' in x).split(' at ')
				return [{'name': values[0],
						'summary': values[-1]}]

		return []

	def to_dict(self):
		data={
		'url': self.url,
		'current_city': self.current_city,
		'bio': self.bio,
		'work': self.work,
		'education': self.education,
		}
		return data
