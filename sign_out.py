import os
import webapp2
from google.appengine.ext.webapp import template

import datetime
import time
import urllib
import wsgiref.handlers
import csv

from google.appengine.ext import db
from google.appengine.api import users
from busyflow.pivotal import PivotalClient
from xml.sax.saxutils import escape
from gaesessions import get_current_session

class SignOut(webapp2.RequestHandler):
    def get(self):

      self.apikey = ""

      #Try to get the apiKey from a session cookie
      session = get_current_session()
      
      # if the session is active      
      if session.is_active():
         session.terminate( clear_data=True )
      
      template_values = {}
      path = os.path.join(os.path.dirname(__file__), 'sign_in.html')
      self.response.out.write(template.render(path, template_values))        

