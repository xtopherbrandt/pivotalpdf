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

        
class GetProjects(webapp2.RequestHandler):

   def post(self):

      output = OutputHTML( self )
      output.post()  
      
class GetStories ( webapp2.RequestHandler ):
   def post ( self ):
      for story in stories:
           self.response.out.write( story['name'] )
           self.response.out.write("<p>")      

class OutputHTML ( webapp2.RequestHandler ):

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
         # if we're authenticating but the session isn't active, it is recommended that you rotate the session ID (security)
         session.regenerate_id()
         self.request.redirect('/SignIn')
            
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

   
   def post ( self ):

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
         
         # but the stored API Key has changed, store the new value and clear everything else
         if self.request.get('APIKey') != '' and self.request.get('APIKey') != session['APIKey'] :
            session['APIKey'] = self.request.get('APIKey')
            session.pop('projectId')
            session.pop('filter')
         
         self.apikey = session['APIKey']
         
         if session.has_key('projectId') :
            self.projectId = session['projectId']            
         
         if session.has_key('labelList') :
            self.labels = session['labelList']
            
      else :
         # if we're authenticating but the session isn't active, it is recommended that you rotate the session ID (security)
         session.regenerate_id()
         self.request.redirect('/SignIn')
            
      client = PivotalClient(token=self.apikey, cache=None)
      projects = client.projects.all()['projects']
      
      stories = []

      # if we havn't selected a project and there is at least 1, the select the first by default
      if self.projectId == None and len(projects) > 0 :
         self.projectId = projects[0]['id']
            
      # if we're getting the stories
      if self.request.get('projects', default_value=None) != None :

         self.projectId = self.request.get('projects')
         session['projectId'] = self.projectId

         # get all of the stories for the project
         stories = client.stories.all( self.projectId )['stories']         
         
         # clear the labels
         self.labels = {}
         
         # go through the stories and pick out the labels
         for story in stories :
            if 'labels' in story :
               for label in story['labels'] :
                  self.labels[label] = label
         
         session['labelList'] = self.labels
         
      # if we're filtering the stories
      elif self.request.get('filter', default_value=None) != None :
         
         self.filter = self.request.get('filter')
         session['filter'] = self.filter
         
         if self.request.get('featuresChecked') != '' :
            self.featuresChecked = "checked='true'"
         else :
            self.featuresChecked = ''

         session['featuresChecked'] = self.featuresChecked
         
         if self.request.get('bugsChecked') != '' :
            self.bugsChecked = "checked='true'"
         else :
            self.bugsChecked = ''
            
         session['bugsChecked'] = self.bugsChecked
         
         if self.request.get('choresChecked') != '' :
            self.choresChecked = "checked='true'"
         else :
            self.choresChecked = ''
            
         session['choresChecked'] = self.choresChecked
         
         if self.request.get('releasesChecked') != '' :
            self.releasesChecked = "checked='true'"
         else :
            self.releasesChecked = ''
            
         session['releasesChecked'] = self.releasesChecked
      
         if self.request.get('labels') != 'Label Filter' and self.request.get('labels') != '' :
            self.labelFilter = 'label:"{0}" '.format( self.request.get('labels') )
            self.selectedLabel = self.request.get('labels')
         else :
            self.labelFilter = ""
            self.selectedLabel = ""
   
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
    



