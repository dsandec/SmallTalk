from wtforms import ValidationError, widgets, FieldList
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import BooleanField, TextAreaField, PasswordField, StringField, SubmitField, SelectMultipleField, FormField, HiddenField, SelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Email, EqualTo, InputRequired, Length
from flask import Flask, render_template
from .. import db
from ..models import Role, User
#imports above not used in this source
#import FlaskForm and general Form
from flask_wtf import FlaskForm, Form
#import HTMLString and html_params from wtforms.widgets.core
from wtforms.widgets.core import HTMLString, html_params

#class SemanticListWidget definition
class SemanticListWidget(object):
	""" This sematic list widget allows for semantic radio buttons to be listed in a ul """
    #method to call during instantiate of class
	def __init__(self, html_tag='div', num_items_per_column=3, prefix_label=True):
         #raise exception if num_items_per_column is not > 0
		assert(num_items_per_column > 0)
         #store parameters as class properties
		self.html_tag = html_tag
		self.prefix_label = prefix_label
		self.num_items_per_column = num_items_per_column

	def __call__(self, field, **kwargs):
         #if dict kwargs doesn't have id key then initialize it
		kwargs.setdefault('id', field.id)
         #create column tag string of class property html_tag
		column_tag = '<%s class="eight wide column">' % (self.html_tag)
        #create list tag string of class property html_tag with arguments provided 
		list_tag  = '<%s %s>' % (self.html_tag, html_params(**kwargs))
		html = []
         #loop through fields list by creating idx value and corresponding subfield
		for idx, subfield in enumerate(field):
              #if module remainder of idx by num_items_per_column is equal to 0 then
			if idx % (self.num_items_per_column) == 0:
                  #if idx is more than 0
				if idx > 0:
                       #add html tag string to html list
					html.append('</%s>' % self.html_tag)
					html.append('</%s>' % self.html_tag)
                   #add column tag string to html list
				html.append(column_tag)
                #add list tag string to html list
				html.append(list_tag)
              #if prefix label is present 
			if self.prefix_label:
                  #add to html list div class definition 
				html.append('<div class="item">%s %s</div>' % (subfield.label, subfield()))
			else:
				html.append('<div class="item">%s %s</div>' % (subfield(), subfield.label))
                
		html.append('</%s>' % self.html_tag)
		html.append('</%s>' % self.html_tag)
         #return all as one html string created out of html list
		return HTMLString(''.join(html))

#below are Form classes, value asignments inside classes are the actual fields on those forms
class NewBusinessConnectionForm(FlaskForm):
	""" Form for new business pop up """

	first_name = StringField(
		'First name', validators=[InputRequired(), Length(1, 64)])
	last_name = StringField(
		'Last name', validators=[InputRequired(), Length(1, 64)])

	list_of_scrapers = ['Linkedin', 'Facebook', 'Twitter', 'Youtube', 'Ac & Edu', 'Personal']
	# create a list of value/description tuples
	scraper_list = [(x, x) for x in list_of_scrapers]
    #multiple selection list of scraper names to be selected
	scrapers = SelectMultipleField('Label', choices=scraper_list,
		option_widget=widgets.CheckboxInput(),
		widget=SemanticListWidget(prefix_label=False))

	keywords = TextAreaField('Keywords')

class EducationForm(Form):
	name = StringField('Name')
	summary = TextAreaField('Summary')

class WorkForm(Form):
	name = StringField('Name')
	summary = TextAreaField('Summary')

class BaseForm(FlaskForm):
	bio = TextAreaField('Bio')
	id = HiddenField('id')

class FacebookForm(BaseForm):
	notes = TextAreaField('Notes')

	music = TextAreaField('Music')
	movies = TextAreaField('Movies')
	sports_teams = TextAreaField('Sports teams')
	athletes = TextAreaField('Athletes')
	books = TextAreaField('Books')
	quotes = TextAreaField('Quotes')
	television = TextAreaField('Television')
	inspirational_people = TextAreaField('Inspirational People')
	professional_skills = TextAreaField('Professional Skills')
	games = TextAreaField('Games')
	sports = TextAreaField('Sports')
	current_city = StringField('City')
	home_town = StringField('Home Town')
	other = TextAreaField('Other')

	education = FieldList(FormField(EducationForm))
	work = FieldList(FormField(WorkForm))

class LinkedInForm(BaseForm):
	current_city = StringField('City')
	education = FieldList(FormField(EducationForm))
	work = FieldList(FormField(WorkForm))
	pass

class YouTubeForm(BaseForm):
	pass

class TwitterForm(BaseForm):
	date_of_birth = StringField('Birthday')
	website = StringField('Website')
	country = StringField('Country')

class CommonDetailForm(FlaskForm):
	id = HiddenField('id')
	notes = TextAreaField()

class SearchForm (FlaskForm):
	search_text = StringField('Search')
    #selection list with values 0 - stands for actual selection and 'Recent' is visible to user
	sort_order = SelectField(choices=[(0, 'Recent'),(1,'A-Z'),(2,'Z-A')],id='order_by')
