# coding: utf-8

import logging

from flask.ext import wtf
from flask.ext.babel import Babel
from flask.ext.babel import gettext as __
from flask.ext.babel import lazy_gettext as _
import flask

import config
import i18n
import util

app = flask.Flask(__name__)
app.config.from_object(config)
app.jinja_env.line_statement_prefix = '#'
app.jinja_env.line_comment_prefix = '##'
app.jinja_env.globals.update(
    check_form_fields=util.check_form_fields,
    is_iterable=util.is_iterable,
    slugify=util.slugify,
    update_query_argument=util.update_query_argument,
  )
app.config['BABEL_DEFAULT_LOCALE'] = config.LOCALE_DEFAULT
babel = Babel(app)

import admin
import admin
import auth
import event
import model
import task
import user
import util


if config.DEVELOPMENT:
  from werkzeug import debug
  app.wsgi_app = debug.DebuggedApplication(app.wsgi_app, evalex=True)



###############################################################################
# Main page
###############################################################################
@flask.request_started.connect_via(app)
def request_started(sender, **extra):
  flask.request.country = None
  flask.request.region = None
  flask.request.city = None
  flask.request.city_lat_lng = '40.6393495,22.944606399999998'
  if 'X-AppEngine-Country' in flask.request.headers:
    flask.request.country = flask.request.headers['X-AppEngine-Country']
  if 'X-AppEngine-Region' in flask.request.headers:
    flask.request.region = flask.request.headers['X-AppEngine-Region']
  if 'X-AppEngine-City' in flask.request.headers:
    flask.request.city = flask.request.headers['X-AppEngine-City']
  if 'X-AppEngine-CityLatLong' in flask.request.headers:
    flask.request.city_lat_lng = flask.request.headers['X-AppEngine-CityLatLong']


###############################################################################
# Main page
###############################################################################
@app.route('/')
def welcome():
  return flask.render_template('welcome.html', html_class='welcome')


###############################################################################
# Sitemap stuff
###############################################################################
@app.route('/sitemap.xml')
def sitemap():
  response = flask.make_response(flask.render_template(
      'sitemap.xml',
      host_url=flask.request.host_url[:-1],
      lastmod=config.CURRENT_VERSION_DATE.strftime('%Y-%m-%d'),
    ))
  response.headers['Content-Type'] = 'application/xml'
  return response


###############################################################################
# Profile stuff
###############################################################################
class ProfileUpdateForm(i18n.Form):
  name = wtf.StringField(_('Name'),
      [wtf.validators.required()], filters=[util.strip_filter],
    )
  email = wtf.StringField(_('Email'),
      [wtf.validators.optional(), wtf.validators.email()],
      filters=[util.email_filter],
    )
  locale = wtf.SelectField(_('Language'),
      choices=config.LOCALE_SORTED, filters=[util.strip_filter],
    )
  home = wtf.StringField(_('Home'),
      [wtf.validators.optional()], filters=[util.strip_filter],
    )
  is_public = wtf.BooleanField(_('Public. Used as sample data on homepage for anonymous users.'), [wtf.validators.optional()])


@app.route('/_s/profile/', endpoint='profile_service')
@app.route('/profile/', methods=['GET', 'POST'])
@auth.login_required
def profile():
  user_db = auth.current_user_db()
  form = ProfileUpdateForm(obj=user_db)

  if form.validate_on_submit():
    send_verification = not user_db.token or user_db.email != form.email.data
    form.populate_obj(user_db)
    if send_verification:
      user_db.verified = False
      task.verify_email_notification(user_db)
    user_db.put()
    return flask.redirect(flask.url_for(
        'set_locale', locale=user_db.locale, next=flask.url_for('welcome')
      ))

  if flask.request.path.startswith('/_s/'):
    return util.jsonify_model_db(user_db)

  return flask.render_template(
      'profile.html',
      title=user_db.name,
      html_class='profile',
      form=form,
      user_db=user_db,
      has_json=True,
    )


###############################################################################
# Feedback
###############################################################################
class FeedbackForm(i18n.Form):
  subject = wtf.StringField(_('Subject'),
      [wtf.validators.required()], filters=[util.strip_filter],
    )
  message = wtf.TextAreaField(_('Message'),
      [wtf.validators.required()], filters=[util.strip_filter],
    )
  email = wtf.StringField(_('Your email (optional)'),
      [wtf.validators.optional(), wtf.validators.email()],
      filters=[util.email_filter],
    )


@app.route('/feedback/', methods=['GET', 'POST'])
def feedback():
  if not config.CONFIG_DB.feedback_email:
    return flask.abort(418)

  form = FeedbackForm(obj=auth.current_user_db())
  if form.validate_on_submit():
    body = '%s\n\n%s' % (form.message.data, form.email.data)
    kwargs = {'reply_to': form.email.data} if form.email.data else {}
    task.send_mail_notification(form.subject.data, body, **kwargs)
    flask.flash(__('Thank you for your feedback!'), category='success')
    return flask.redirect(flask.url_for('welcome'))

  return flask.render_template(
      'feedback.html',
      title=_('Feedback'),
      html_class='feedback',
      form=form,
    )


###############################################################################
# Warmup request
###############################################################################
@app.route('/_ah/warmup')
def warmup():
  # TODO: put your warmup code here
  return 'success'


###############################################################################
# Error Handling
###############################################################################
@app.errorhandler(400)  # Bad Request
@app.errorhandler(401)  # Unauthorized
@app.errorhandler(403)  # Forbidden
@app.errorhandler(404)  # Not Found
@app.errorhandler(405)  # Method Not Allowed
@app.errorhandler(410)  # Gone
@app.errorhandler(418)  # I'm a Teapot
@app.errorhandler(500)  # Internal Server Error
def error_handler(e):
  logging.exception(e)
  try:
    e.code
  except AttributeError:
    e.code = 500
    e.name = 'Internal Server Error'

  if flask.request.path.startswith('/_s/'):
    return util.jsonpify({
        'status': 'error',
        'error_code': e.code,
        'error_name': util.slugify(e.name),
        'error_message': e.name,
        'error_class': e.__class__.__name__,
      }), e.code

  return flask.render_template(
      'error.html',
      title='Error %d (%s)!!1' % (e.code, e.name),
      html_class='error-page',
      error=e,
    ), e.code


if config.PRODUCTION:
  @app.errorhandler(Exception)
  def production_error_handler(e):
    return error_handler(e)
