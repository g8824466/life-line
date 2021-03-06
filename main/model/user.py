# coding: utf-8

from __future__ import absolute_import

import hashlib

from google.appengine.ext import ndb

import model
import util


class User(model.Base):
  name = ndb.StringProperty(required=True)
  username = ndb.StringProperty(required=True)
  email = ndb.StringProperty(default='')
  locale = ndb.StringProperty(default='en')
  auth_ids = ndb.StringProperty(repeated=True)
  active = ndb.BooleanProperty(default=True)
  admin = ndb.BooleanProperty(default=False)
  permissions = ndb.StringProperty(repeated=True)
  verified = ndb.BooleanProperty(default=False)
  token = ndb.StringProperty(default='')
  home = ndb.StringProperty(default='')
  is_public = ndb.BooleanProperty(default=False)

  def has_permission(self, perm):
    return self.admin or perm in self.permissions

  def avatar_url_size(self, size=None):
    return '//gravatar.com/avatar/%(hash)s?d=identicon&r=x%(size)s' % {
        'hash': hashlib.md5(self.email or self.username).hexdigest(),
        'size': '&s=%d' % size if size > 0 else '',
      }
  avatar_url = property(avatar_url_size)

  _PROPERTIES = model.Base._PROPERTIES.union({
      'active',
      'admin',
      'auth_ids',
      'avatar_url',
      'email',
      'home',
      'is_public',
      'locale',
      'name',
      'permissions',
      'username',
      'verified',
    })

  @classmethod
  def get_dbs(cls, admin=None, active=None, verified=None, permissions=None, **kwargs):
    return super(User, cls).get_dbs(
        admin=admin or util.param('admin', bool),
        active=active or util.param('active', bool),
        verified=verified or util.param('verified', bool),
        permissions=permissions or util.param('permissions', list),
        **kwargs
      )

  @classmethod
  def is_username_available(cls, username, self_db=None):
    if self_db is None:
      return cls.get_by('username', username) is None
    user_dbs, _ = util.get_dbs(cls.query(), username=username, limit=2)
    c = len(user_dbs)
    return not (c == 2 or c == 1 and self_db.key != user_dbs[0].key)

  def get_event_dbs(self, order=None, **kwargs):
    return model.Event.get_dbs(
        user_key=self.key,
        order=order or util.param('order') or '-timestamp,accuracy,-created',
        **kwargs
      )

