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
from user import *        
      
class GetStories ( webapp2.RequestHandler ):

   def get ( self, projectID = 'None' ):

      logging.info ( "GetStories.get()" )

      session = get_current_session()
            
      if projectID != 'None' :
         session['projectId'] = projectID
      
      self.post()  
            
   def post ( self ):

      selectionProperties = SelectionProperties()

      logging.info ( "GetStories.post()" )
      
      session = get_current_session()

      # if the request has an API Key then set it in our session
      # this would be the case after authentication
      if self.request.get('APIKey') != '' :
         session['APIKey'] = self.request.get('APIKey')

         session.pop('projectId')
         session.pop('filter')
               
      # if the session is active and it has an APIKey   
      if session.is_active() and session.has_key('APIKey') :

         selectionProperties.apikey = session['APIKey']
         
         if session.has_key('projectId') :
            selectionProperties.projectId = session['projectId']            
             
      else :
         return self.redirect('/SignIn')

      projects = []
      
      # Connect to Pivotal Tracker and get the user's projects
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
         session['projectId'] = selectionProperties.projectId

      labels = client.projects.labels( selectionProperties.projectId )

      # if we're filtering the stories
      if self.request.get('filter', default_value=None) != None :
         
         selectionProperties.filter = self.request.get('filter')
         session['filter'] = selectionProperties.filter
         
         selectionProperties.featuresChecked = self.request.get('featuresChecked')
         session['featuresChecked'] = selectionProperties.featuresChecked
         
         selectionProperties.bugsChecked = self.request.get('bugsChecked')            
         session['bugsChecked'] = selectionProperties.bugsChecked
         
         selectionProperties.choresChecked = self.request.get('choresChecked')            
         session['choresChecked'] = selectionProperties.choresChecked
         
         selectionProperties.releasesChecked = self.request.get('releasesChecked')            
         session['releasesChecked'] = selectionProperties.releasesChecked
      
         if self.request.get('labels') != 'Label Filter' and self.request.get('labels') != '' :
            selectionProperties.labelFilter = u'label:"{0}" '.format( self.request.get('labels') )
            selectionProperties.selectedLabel = self.request.get('labels')
         else :
            selectionProperties.labelFilter = ""
            selectionProperties.selectedLabel = ""
   
      # set up the story filters
      # add the story types to the filter
      typeFilter = ' type:none,'

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
         projectStories = client.stories.get_filter(selectionProperties.projectId, selectionProperties.filter, True )
            
      template_values = {
                        'apiKey' : selectionProperties.apikey,
                        'projects' : projects, 
                        'selected_project' : int(selectionProperties.projectId), 
                        'filter_text' : selectionProperties.filter, 
                        'features_checked' : selectionProperties.featuresChecked, 
                        'bugs_checked' : selectionProperties.bugsChecked, 
                        'chores_checked' : selectionProperties.choresChecked, 
                        'releases_checked' : selectionProperties.releasesChecked,
                        'stories' : projectStories,
                        'labels' : labels,
                        'selected_label' : selectionProperties.selectedLabel,
                        'version' : os.environ.get('CURRENT_VERSION_ID')[0:6],
                        'outputActivity_checked' : selectionProperties.outputActivityChecked
                        }
                        
      path = os.path.join(os.path.dirname(__file__), 'index.html')
      self.response.out.write(template.render(path, template_values))        


   
    



