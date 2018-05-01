from flask import flash, redirect, render_template, request, url_for
from flask_login import (current_user, login_required, login_user,
						 logout_user)
from flask_rq import get_queue

from . import account
from .. import db

from ..models import User
from .forms import (ChangeEmailForm, ChangePasswordForm, CreatePasswordForm,
					LoginForm, RegistrationForm, RequestResetPasswordForm,
					ResetPasswordForm, ChangeThemeForm)

from wtforms.validators import AnyOf

@account.route('/login', methods=['GET', 'POST'])
def login():
	"""Log in an existing user."""
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None and user.password_hash is not None and \
				user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			flash('You are now logged in. Welcome back!', 'success')
			return redirect(request.args.get('next') or url_for('main.index'))
		else:
			flash('Invalid email or password.', 'form-error')
	return render_template('account/login.html', form=form)


@account.route('/register', methods=['GET', 'POST'])
def register():
	"""Register a new user, and send them a confirmation email."""
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(
			first_name=form.first_name.data,
			last_name=form.last_name.data,
			email=form.email.data,
			confirmed=True,
			password=form.password.data)
		db.session.add(user)
		db.session.commit()
		login_user(user)
		flash('You are now logged in. Welcome {}.'.format(user.first_name), 'success')
		return redirect(url_for('main.index'))
	return render_template('account/register.html', form=form)


@account.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out.', 'info')
	return redirect(url_for('main.index'))


@account.route('/manage', methods=['GET', 'POST'])
@account.route('/manage/info', methods=['GET', 'POST'])
@login_required
def manage():
	"""Display a user's account information."""
	return render_template('account/manage.html', user=current_user, form=None)


@account.route('/manage/change-theme', methods=['GET', 'POST'])
@login_required
def change_theme():
	"""Change an existing user's theme."""
	import os
	dir_path = os.getcwd() + '/app/static/styles/themes'
	print (dir_path)
	themes = []
	for name in os.listdir(dir_path):
		if name.endswith(".css"):
			value = name.split('.')[0]
			themes.append((value,value))

	form = ChangeThemeForm(obj=current_user._get_current_object())
	form.theme.choices = themes

	if form.validate_on_submit():
		user = current_user._get_current_object()
		user.theme = form.theme.data
		db.session.add(current_user)
		db.session.commit()
		flash('Your theme has been updated!', 'form-success')
		return redirect(url_for('main.index'))

	form.validators=[AnyOf([x[0] for x in themes])]
	return render_template('account/manage.html', form=form)

@account.route('/manage/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
	"""Change an existing user's password."""
	form = ChangePasswordForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.old_password.data):
			current_user.password = form.new_password.data
			db.session.add(current_user)
			db.session.commit()
			flash('Your password has been updated.', 'form-success')
			return redirect(url_for('main.index'))
		else:
			flash('Original password is invalid.', 'form-error')

	return render_template('account/manage.html', form=form)


@account.route('/manage/change-email/<token>', methods=['GET', 'POST'])
@login_required
def change_email(token):
	"""Change existing user's email with provided token."""
	if current_user.change_email(token):
		flash('Your email address has been updated.', 'success')
	else:
		flash('The confirmation link is invalid or has expired.', 'error')
	return redirect(url_for('main.index'))

@account.route('/confirm-account/<token>')
@login_required
def confirm(token):
	"""Confirm new user's account with provided token."""
	if current_user.confirmed:
		return redirect(url_for('main.index'))
	if current_user.confirm_account(token):
		flash('Your account has been confirmed.', 'success')
	else:
		flash('The confirmation link is invalid or has expired.', 'error')
	return redirect(url_for('main.index'))

@account.before_app_request
def before_request():
	"""Force user to confirm email before accessing login-required routes."""
	if current_user.is_authenticated \
			and not current_user.confirmed \
			and request.endpoint[:8] != 'account.' \
			and request.endpoint != 'static':
		return redirect(url_for('account.unconfirmed'))


@account.route('/unconfirmed')
def unconfirmed():
	"""Catch users with unconfirmed emails."""
	if current_user.is_anonymous or current_user.confirmed:
		return redirect(url_for('main.index'))
	return render_template('account/unconfirmed.html')
