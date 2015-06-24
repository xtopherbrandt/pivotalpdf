import os
import webapp2
from google.appengine.ext.webapp import template

import datetime
import time
import urllib
import wsgiref.handlers
import csv
import os

from google.appengine.ext import db
from google.appengine.api import users
from busyflow.pivotal import PivotalClient
from xml.sax.saxutils import escape
from gaesessions import get_current_session

class SignIn(webapp2.RequestHandler):
    def get(self):

      self.apikey = ""

      #Try to get the apiKey from a session cookie
      session = get_current_session()
      
      # if the session is active      
      if session.is_active() and session.has_key('APIKey') :
            self.apikey = session['APIKey']
            
      # if the session is not active, create it and store the empty api key
      else :
         session.regenerate_id()
      
      template_values = {'apiKey' : self.apikey,
                        'version' : os.environ.get('CURRENT_VERSION_ID')[0:6]
                        }
      path = os.path.join(os.path.dirname(__file__), 'sign_in.html')
      self.response.out.write(template.render(path, template_values))        

