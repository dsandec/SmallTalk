import logging

from flask_login import current_user, login_required
from flask_socketio import emit, join_room, leave_room

from .. import db, socketio

@socketio.on('joined', namespace='/notifs')
def joined(message):
	"""Sent by clients when they open a business contact page"""
	room = current_user.id
	join_room(room)

@socketio.on('profile_scrape_complete', namespace='/notifs')
def profile_scrape_complete(message):
	"""Sent to a client when a profile scraper has completed"""
	emit('profile_scrape_complete', message, room=message['uid'])

@socketio.on('domain_scrape_complete', namespace='/notifs')
def domain_scrape_complete(message):
	"""Sent to a client when domains have been checked"""
	emit('domain_scrape_complete', message, room=message['uid'])

@socketio.on('google_scrape_complete', namespace='/notifs')
def google_scrape_complete(message):
	"""Sent to a client when a google scraper has completed"""
	emit('google_scrape_complete', message, room=message['uid'])
