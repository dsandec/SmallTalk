from flask import Blueprint

main = Blueprint('main', __name__)


from .events import *
from .forms import *
from . import views, errors  # noqa
