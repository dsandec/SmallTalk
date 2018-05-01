# Profiler
![python3.x](https://img.shields.io/badge/python-3.x-brightgreen.svg)

## Requirements
* Python 3

## Dependencies

### Backend

* Blueprints for project structure
* Flask-Login for User and permissions management
* Flask-SQLAlchemy for databases
* Flask-WTF for forms
* Flask-Assets for asset management and SCSS compilation
* Flask-Mail for sending emails
* Flask-SocketIO for bi-directional communication between front end and scrapers
* gzip compression
* Redis Queue for handling asynchronous tasks
* ZXCVBN password strength checker

### Frontend
* Scrollspy - for fadein on scroll on logged out home page
* SemanticUI - for CSS styling


## Setting up

##### Extraction

```
$ unzip profiler.zip to your base directory
$ cd <<name of directory>>
```


##### Initialize a virtualenv
It is a good idea to run things in a a virtual environment or in a [Docker](https://docs.docker.com/) environment.
I will only demonstrate using virtualenv for this project.

Linux/Mac
```
$ pip install virtualenv
$ virtualenv -p /path/to/python3.x/installation env
$ source env/bin/activate
```

## Add Environment Variables

Create a file called `config.env` in the root directory (the same directory `manage.py` resides in) that contains environment variables in the following syntax: `ENVIRONMENT_VARIABLE=value`. For example,
the mailing environment variables can be set as the following
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=example@domain.com
MAIL_PASSWORD=SuperSecretPassword
EMAIL_SENDER=FromWhom
SECRET_KEY=SuperRandomStringToBeUsedForEncryption
FLASK_CONFIG=default
EMAIL_SUBJECT_PREFIX="Welcome to Profiler"
```

Other Key value pairs:

* `ADMIN_EMAIL`: set to the default email for your first admin account (default is `flask-base-admin@example.com`)
* `ADMIN_PASSWORD`: set to the default password for your first admin account (default is `password`)
* `REDISTOGO_URL`: set to Redis To Go URL or any redis server url (default is `redis://localhost:6379/0`)
* `FLASK_CONFIG`: can be `development` or `testing`. Most of the time you will use `development` or `production`.
* `DEV_DATABASE_URL`: sets connection string for your development database (default is `mysql://profiler:profiler@127.0.0.1/profiler`)
* `DATABASE_URL`: sets connection string for your production database (default is `mysql://profiler:profiler@127.0.0.1/profiler`)

##### Install the dependencies

```
$ cd requirements
$ pip install -r requirements.txt
```

##### Other dependencies for running locally

You need [Redis](http://redis.io/)  

Redis is used to allow the scrapers to run in the background.

**Redis:**

```
$ sudo apt-get install redis-server
```

Uses a gunicorn web server.

**Gunicorn:**

```
$ pip install gunicorn
```

**SocketIO - eventlet:**

You need SocketIO for bi-directional communication between web clients and servers (this communication occurs on the completion of a scraper, the client (front-end user) is informed of the completion via SocketIO), for this to work the eventlet networking library needs to be installed.

```
$ pip install eventlet
```
## Database creation

##### Create the database

```
$ python manage.py recreate_db
```

##### Other setup (e.g. creating roles in database)

```
$ python manage.py setup_dev
```

Note that this will create an admin user with email and password specified by the `ADMIN_EMAIL` and `ADMIN_PASSWORD` config variables. If not specified, they are both `profiler-admin@example.com` and `password` respectively.

##### [Optional] Add fake data to the database

```
$ python manage.py add_fake_data
```

## Running the app

```
$ source env/bin/activate
$ honcho start -f Local
```

_Prod:_


## Running the app via gunicorn

```
$ source env/bin/activate
$ honcho start -f Prod
```
