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

from story_selection import *
from generate_output import *
from sign_in import *
from sign_out import *

class MainPage(webapp2.RequestHandler):

   def get ( self ):

      # initialize the class properties
      self.projectId = None
      self.filter = ''     
      self.featuresChecked = "checked='true'"
      self.bugsChecked = "checked='true'"
      self.choresChecked = "checked='true'"
      self.releasesChecked = ""
      self.selectedLabel = ""
      self.labelFilter = ""
      self.labels = {}

      session = get_current_session()
      
      # if the session is active and it has an APIKey   
      if session.is_active() and session.has_key('APIKey') :
         
         self.apikey = session['APIKey']
         
         if session.has_key('projectId') :
            self.projectId = session['projectId']            
         
         if session.has_key('labelList') :
            self.labels = session['labelList']
            
      else :
         return self.redirect('/SignIn')
            
      client = PivotalClient(token=self.apikey, cache=None)
      projects = client.projects.all()['projects']
      
      stories = []

      # if we havn't selected a project and there is at least 1, the select the first by default
      if self.projectId == None and len(projects) > 0 :
         self.projectId = projects[0]['id']
  
      # set up the story filters
      # add the story types to the filter
      typeFilter = ' type:none,'

      if self.featuresChecked != '' :
         typeFilter += 'feature,'

      if self.bugsChecked != '' :
         typeFilter += 'bug,'

      if self.choresChecked != '' :
         typeFilter += 'chore,'

      if self.releasesChecked != '' :
         typeFilter += 'release'
      
      self.filter += self.labelFilter
      self.filter += typeFilter
      
      session['filter'] = self.filter
       
      # if a project is selected, get it's stories
      if self.projectId != None :         
         stories = client.stories.get_filter(self.projectId, self.filter, True )['stories']         
      
      template_values = {
                        'apiKey' : self.apikey,
                        'projects' : projects, 
                        'selected_project' : self.projectId, 
                        'filter_text' : self.filter, 
                        'features_checked' : self.featuresChecked, 
                        'bugs_checked' : self.bugsChecked, 
                        'chores_checked' : self.choresChecked, 
                        'releases_checked' : self.releasesChecked,
                        'stories' : stories,
                        'labels' : self.labels,
                        'selected_label' : self.selectedLabel
                        }
                        
      path = os.path.join(os.path.dirname(__file__), 'index.html')
      self.response.out.write(template.render(path, template_values))        


application = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/SignIn', SignIn),
  ('/SignOut', SignOut),
  ('/authenticate', OutputHTML),
  ('/getStories', OutputHTML),
  ('/filterStories', OutputHTML),
  ('/generatePDF', GenerateOutput)
  
], debug=True)

