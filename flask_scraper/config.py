import os
import sys

PYTHON_VERSION = sys.version_info[0]
if PYTHON_VERSION == 3:
	import urllib.parse
else:
	import urlparse

basedir = os.path.abspath(os.path.dirname(__file__))

if os.path.exists('config.env'):
	print('Importing environment from .env file')
	with open('config.env', 'r') as fp:
		for line in fp:
			var = line.strip().split('=')
			if len(var) == 2:
				os.environ[var[0]] = var[1].replace("\"", "")


class Config:
	APP_NAME = os.environ.get('APP_NAME') or 'Profiler'

	if os.environ.get('SECRET_KEY'):
		SECRET_KEY = os.environ.get('SECRET_KEY')
	else:
		SECRET_KEY = 'SECRET_KEY_ENV_VAR_NOT_SET'
		print('SECRET KEY ENV VAR NOT SET! SHOULD NOT SEE IN PRODUCTION')
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True

	MAIL_SERVER =os.environ.get('MAIL_SERVER')
	MAIL_PORT = os.environ.get('MAIL_PORT')
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS')
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

	ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'password'
	ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'profiler-admin@example.com'
	EMAIL_SUBJECT_PREFIX = '[{}]'.format(APP_NAME)
	EMAIL_SENDER = '{app_name} Admin <{email}>'.format(
		app_name=APP_NAME, email=MAIL_USERNAME)

	REDIS_URL = os.environ.get('REDISTOGO_URL') or \
		'redis://localhost:6379/0'
	SOCKETIO_MESSAGE_QUEUE = 'redis://localhost:6379/0'

	# Parse the REDIS_URL to set RQ config variables
	urllib.parse.uses_netloc.append('redis')
	url = urllib.parse.urlparse(REDIS_URL)

	RQ_DEFAULT_HOST = url.hostname
	RQ_DEFAULT_PORT = url.port
	RQ_DEFAULT_PASSWORD = url.password
	RQ_DEFAULT_DB = 0

	@staticmethod
	def init_app(app):
		pass

class DevelopmentConfig(Config):
	DEBUG = True
	ASSETS_DEBUG = True
	SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
		'mysql://root:toor@127.0.0.1/profiler?charset=utf8'
	print('THIS APP IS IN DEBUG MODE. YOU SHOULD NOT SEE THIS IN PRODUCTION.')

class ProductionConfig(Config):
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
		'mysql://root:toor@127.0.0.1/profiler?charset=utf8'
	SSL_DISABLE = (os.environ.get('SSL_DISABLE') or 'True') == 'True'

	@classmethod
	def init_app(cls, app):
		Config.init_app(app)
		assert os.environ.get('SECRET_KEY'), 'SECRET_KEY IS NOT SET!'


config = {
	'development': DevelopmentConfig,
	'production': ProductionConfig,
	'default': DevelopmentConfig,
}
