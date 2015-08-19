import os
import webapp2
from google.appengine.ext.webapp import template

import datetime
import time
import urllib
import wsgiref.handlers
import csv
import os
import logging

from google.appengine.ext import db
from google.appengine.api import users
from pivotal_api_v5 import PivotalClient
from xml.sax.saxutils import escape
from gaesessions import get_current_session

from selection_properties import *
from story_selection import *
from generate_output import *
from sign_in import *
from sign_out import *
from generate_pdf_2 import *


class MainPage(webapp2.RequestHandler):

   def get ( self ):

      selectionProperties = SelectionProperties()

      session = get_current_session()
      
      logging.info ( "MainPage.get()" )
      
      # if the session is active and it has an APIKey   
      if session.is_active() and session.has_key('APIKey') :
         
         selectionProperties.apikey = session['APIKey']
         
         if session.has_key('projectId') :
            selectionProperties.projectId = session['projectId']            
            
      else :
         return self.redirect('/SignIn')
            
      client = PivotalClient(token=selectionProperties.apikey, cache=None)
      projects = client.projects.all()
      
      '''Get the user's record'''
      userKey = user_key( selectionProperties.apikey )
      user = userKey.get()
            
      '''if this user doesn't have a record yet, create one'''
      if user == None :
         user = User( id=selectionProperties.apikey )
         user.put()
         logging.info ("New user added {0}".format(selectionProperties.apikey))
      else :
         user.last_usage_date = datetime.datetime.today()
         user.put()
         logging.info ("User {0} logged back in.".format(selectionProperties.apikey))

      stories = []
      labels = []

      # if we havn't selected a project and there is at least 1, the select the first by default
      if selectionProperties.projectId == None and len(projects) > 0 :
         selectionProperties.projectId = projects[0]['id']

      labels = client.projects.labels( selectionProperties.projectId )

      # set up the story filters
      # add the story types to the filter
      typeFilter = u' type:none,'

      if selectionProperties.featuresChecked != '' :
         typeFilter += 'feature,'

      if selectionProperties.bugsChecked != '' :
         typeFilter += 'bug,'

      if selectionProperties.choresChecked != '' :
         typeFilter += 'chore,'

      if selectionProperties.releasesChecked != '' :
         typeFilter += 'release'
      
      selectionProperties.filter += selectionProperties.labelFilter
      selectionProperties.filter += typeFilter
      
      session['filter'] = selectionProperties.filter
       
      # if a project is selected, get it's stories
      if selectionProperties.projectId != None :         
         try :
            stories = client.stories.get_filter(selectionProperties.projectId, selectionProperties.filter, True )
         except KeyError as e :
            logging.error ( "An exception occurred trying to retreive the stories for project: " + selectionProperties.projectId)
            logging.error ( "KeyError: " + str(e.args))
            # just leave the stories as an empty list for now
      
      template_values = {
                        'apiKey' : selectionProperties.apikey,
                        'projects' : projects, 
                        'selected_project' : int(selectionProperties.projectId), 
                        'filter_text' : selectionProperties.filter, 
                        'features_checked' : selectionProperties.featuresChecked, 
                        'bugs_checked' : selectionProperties.bugsChecked, 
                        'chores_checked' : selectionProperties.choresChecked, 
                        'releases_checked' : selectionProperties.releasesChecked,
                        'stories' : stories,
                        'labels' : labels,
                        'selected_label' : selectionProperties.selectedLabel,
                        'version' : os.environ.get('CURRENT_VERSION_ID')[0:6]
                        }
                        
      path = os.path.join(os.path.dirname(__file__), 'index.html')
      self.response.out.write(template.render(path, template_values))        


application = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/SignIn', SignIn),
  ('/SignOut', SignOut),
  ('/authenticate', GetStories),
  ('/getStories/(\d+)', GetStories),
  ('/getStories', GetStories),
  ('/filterStories', GetStories),
  ('/generatePDF', GenerateOutput),
  ('/v2/generatePDF', GeneratePDF_2)
  
], debug=True)

