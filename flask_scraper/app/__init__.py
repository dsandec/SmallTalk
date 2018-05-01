import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_assets import Environment
from flask_wtf import CSRFProtect
from flask_compress import Compress
from flask_rq import RQ

from flask_socketio import SocketIO

from config import config
from .assets import  app_js, vendor_css, vendor_js

basedir = os.path.abspath(os.path.dirname(__file__))

db = SQLAlchemy()
csrf = CSRFProtect()
compress = Compress()
socketio = SocketIO(engineio_logger=True)


# Set up Flask-Login
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'account.login'


def create_app(config_name, main=True):
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	# not using sqlalchemy event system, hence disabling it

	config[config_name].init_app(app)

	# Set up extensions
	db.init_app(app)
	db.sessionmaker(autoflush=False)
	login_manager.init_app(app)
	csrf.init_app(app)
	compress.init_app(app)
	RQ(app)
	socketio.init_app(app, message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'])

	# Register Jinja template functions
	from .utils import register_template_utils
	register_template_utils(app)

	# Set up asset pipeline
	assets_env = Environment(app)
	dirs = ['assets/styles', 'assets/scripts']
	for path in dirs:
		assets_env.append_path(os.path.join(basedir, path))
	assets_env.url_expire = True

	assets_env.register('app_js', app_js)
	assets_env.register('vendor_css', vendor_css)
	assets_env.register('vendor_js', vendor_js)

	# Configure SSL if platform supports it
	if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
		from flask.ext.sslify import SSLify
		SSLify(app)

	# Create app blueprints
	from .main import main as main_blueprint
	app.register_blueprint(main_blueprint)

	from .account import account as account_blueprint
	app.register_blueprint(account_blueprint, url_prefix='/account')

	from .admin import admin as admin_blueprint
	app.register_blueprint(admin_blueprint, url_prefix='/admin')

	return app
