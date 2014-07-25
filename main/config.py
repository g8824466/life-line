# coding: utf-8

import os
import operator


PRODUCTION = os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Eng')
DEBUG = DEVELOPMENT = not PRODUCTION

try:
  # This part is surrounded in try/except because the config.py file is
  # also used in the run.py script which is used to compile/minify the client
  # side files (*.less, *.coffee, *.js) and is not aware of the GAE
  from google.appengine.api import app_identity
  APPLICATION_ID = app_identity.get_application_id()
except (ImportError, AttributeError):
  pass
else:
  from datetime import datetime
  CURRENT_VERSION_ID = os.environ.get('CURRENT_VERSION_ID')
  CURRENT_VERSION_NAME = CURRENT_VERSION_ID.split('.')[0]
  CURRENT_VERSION_TIMESTAMP = long(CURRENT_VERSION_ID.split('.')[1]) >> 28
  if DEVELOPMENT:
    import calendar
    CURRENT_VERSION_TIMESTAMP = calendar.timegm(datetime.utcnow().timetuple())
  CURRENT_VERSION_DATE = datetime.utcfromtimestamp(CURRENT_VERSION_TIMESTAMP)

  import model

  CONFIG_DB = model.Config.get_master_db()
  SECRET_KEY = CONFIG_DB.flask_secret_key.encode('ascii')
  LOCALE_DEFAULT = CONFIG_DB.locale

DEFAULT_DB_LIMIT = 256
MAX_DB_LIMIT = 1024


###############################################################################
# i18n Stuff
###############################################################################

# Languages: http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
# Countries: http://en.wikipedia.org/wiki/ISO_3166-1
# To Add/Modify languages use one of the filenames in: libx/babel/localedata/
# Examples with country included: en_GB, ru_RU, de_CH
LOCALE = {
  'en': u'English',
  'el': u'Ελληνικά',
}

LOCALE_SORTED = sorted(LOCALE.iteritems(), key=operator.itemgetter(1))
LANGUAGES = [l.lower().replace('_', '-') for l in LOCALE.keys()]

###############################################################################
# Client modules, also used by the run.py script.
###############################################################################
STYLES = [
    'src/style/style.less',
  ]

SCRIPTS = [
    ('one', [
        'ext/js/color/one-color.js',
      ]),
    ('libs', [
        'ext/js/jquery/jquery.js',
        'ext/js/momentjs/moment.js',
        'ext/js/nprogress/nprogress.js',
        'ext/js/bootstrap/alert.js',
        'ext/js/bootstrap/button.js',
        'ext/js/bootstrap/transition.js',
        'ext/js/bootstrap/collapse.js',
        'ext/js/bootstrap/dropdown.js',
        'ext/js/bootstrap/tooltip.js',
      ] + ['ext/js/momentjs/lang/%s.js' % l for l in LANGUAGES if l != 'en']),
    ('scripts', [
        'src/script/common/service.coffee',
        'src/script/common/util.coffee',
        'src/script/site/app.coffee',
        'src/script/site/welcome.coffee',
        'src/script/site/admin.coffee',
        'src/script/site/profile.coffee',
        'src/script/site/signin.coffee',
        'src/script/site/user.coffee',
        'src/script/site/event.coffee',
        'src/script/site/map/map_utils.coffee',
        'src/script/site/map/geocoder_map.coffee',
        'src/script/site/map/chart_map.coffee',
      ]),
  ]
