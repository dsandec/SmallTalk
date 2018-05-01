from flask_assets import Bundle
from flask_login import current_user

app_js = Bundle('app.js', filters='jsmin', output='scripts/app.js')

vendor_css = Bundle('vendor/semantic.min.css','vendor/coverr.css','vendor/accordian.min.css', output='styles/vendor.css')

vendor_js = Bundle(
	'vendor/jquery.min.js',
	'vendor/semantic.min.js',
	'vendor/tablesort.min.js',
	'vendor/accordian.min.js',
	'vendor/zxcvbn.js',
	'vendor/coverr.js',
	'vendor/velocity.js',

	filters='jsmin',
	output='scripts/vendor.js')
