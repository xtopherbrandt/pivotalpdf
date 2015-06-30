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
from busyflow.pivotal import PivotalClient
from xml.sax.saxutils import escape
from gaesessions import get_current_session

from user_usage_statistics import *
        
class GetProjects(webapp2.RequestHandler):

   def post(self):

      output = OutputHTML( self )
      output.post()  
      
class GetStories ( webapp2.RequestHandler ):

   def get ( self, projectID ):

      # initialize the class properties
      self.projectId = projectID
      self.filter = ''     
      self.featuresChecked = "checked='true'"
      self.bugsChecked = "checked='true'"
      self.choresChecked = "checked='true'"
      self.releasesChecked = ""
      self.selectedLabel = ""
      self.labelFilter = ""
      self.labels = {}
      self.outputActivityChecked = "checked='true'"

      session = get_current_session()
      
      # if the session is active and it has an APIKey   
      if session.is_active() and session.has_key('APIKey') :
         
         self.apikey = session['APIKey']
         
         if session.has_key('labelList') :
            self.labels = session['labelList']
            
      else :
         return self.redirect('/SignIn')
            
      session['projectId'] = projectID
      
      projects = []
      
      # Connect to Pivotal Tracker and get the user's projects
      client = PivotalClient(token=self.apikey, cache=None)
      clientProjects = client.projects.all()
      
      # if there are any projects, get them
      if 'projects' in clientProjects :
         projects = clientProjects['projects']
      
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
         projectStories = client.stories.get_filter(self.projectId, self.filter, True )
         
         # if it has stories get them
         if 'stories' in projectStories :
            stories = projectStories['stories']         
         
         # clear the labels
         self.labels = {}
         
         # go through the stories and pick out the labels
         for story in stories :
            if 'labels' in story :
               for label in story['labels'] :
                  self.labels[label] = label
         
         session['labelList'] = self.labels
      
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
                        'selected_label' : self.selectedLabel,
                        'outputActivity_checked' : "checked='true'"
                        }
                        
      path = os.path.join(os.path.dirname(__file__), 'index.html')
      self.response.out.write(template.render(path, template_values))        

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
      self.outputActivityChecked = "checked='true'"
      self.usageStatistics = None

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
            
      projects = []
      
      '''Get the user's usage stats'''
      usageStatsKey = user_usage_stats_key( self.apikey )
      usageStats = usageStatsKey.get()
            
      '''if this user doesn't have a statistics record yet, create one'''
      if usageStats == None :
         usageStats = UserUsageStatistics( id=self.apikey )
         usageStats.put()
         logging.info ("New user added {0}".format(self.apikey))
      else :
         logging.info ("User {0} logged back in.".format(self.apikey))
         
      usageStats.project_count_at_last_use = len(projects)
      usageStats.put()
       
      # Connect to Pivotal Tracker and get the user's projects
      client = PivotalClient(token=self.apikey, cache=None)
      clientProjects = client.projects.all()
      
      # if there are any projects, get them
      if 'projects' in clientProjects :
         projects = clientProjects['projects']
      
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
         projectStories = client.stories.get_filter(self.projectId, self.filter, True )
         
         # if it has stories get them
         if 'stories' in projectStories :
            stories = ['stories']         
      
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
                        'selected_label' : self.selectedLabel,
                        'outputActivity_checked' : "checked='true'"
                        }
                        
      path = os.path.join(os.path.dirname(__file__), 'index.html')
      self.response.out.write(template.render(path, template_values))        

   
   def post ( self ):

      # initialize the class properties
      self.projectId = None
      self.filter = u''     
      self.featuresChecked = "checked='true'"
      self.bugsChecked = "checked='true'"
      self.choresChecked = "checked='true'"
      self.releasesChecked = ""
      self.selectedLabel = ""
      self.labelFilter = ""
      self.labels = {}
      self.outputActivityChecked = "checked='true'"

      session = get_current_session()

      # if the request has an API Key then set it in our session
      if self.request.get('APIKey') != '' :
         session['APIKey'] = self.request.get('APIKey')

         session.pop('projectId')
         session.pop('filter')
         
      # if the request has a non-empty user name and password field, then try to sign the user in
      if self.request.get('userName') != '' and self.request.get('password') :
         client = PivotalClient(token='', cache=None)
         session['APIKey'] = client.tokens.active( username=self.request.get('userName'), password=self.request.get('password') )['token']['guid']

         session.pop('projectId')
         session.pop('filter')
      
      # if the session is active and it has an APIKey   
      if session.is_active() and session.has_key('APIKey') :
         
         
         self.apikey = session['APIKey']
         
         if session.has_key('projectId') :
            self.projectId = session['projectId']            
         
         if session.has_key('labelList') :
            self.labels = session['labelList']
            
      else :
         return self.redirect('/SignIn')

      projects = []
      
      # Connect to Pivotal Tracker and get the user's projects
      client = PivotalClient(token=self.apikey, cache=None)
      clientProjects = client.projects.all()
      
      # if there are any projects, get them
      if 'projects' in clientProjects :
         projects = clientProjects['projects']
      
      '''Get the user's usage stats'''
      usageStatsKey = user_usage_stats_key( self.apikey )
      usageStats = usageStatsKey.get()
            
      '''if this user doesn't have a statistics record yet, create one'''
      if usageStats == None :
         usageStats = UserUsageStatistics( id=self.apikey )
         usageStats.put()
         logging.info ("New user added {0}".format(self.apikey))
      else :
         logging.info ("User {0} logged back in.".format(self.apikey))
         
      usageStats.project_count_at_last_use = len(projects)
      usageStats.put()
      
      stories = []

      # if we havn't selected a project and there is at least 1, the select the first by default
      if self.projectId == None and len(projects) > 0 :
         self.projectId = projects[0]['id']
         session['projectId'] = self.projectId
            
      # if we're getting the stories
      if self.request.get('projects', default_value=None) != None :

         self.projectId = self.request.get('projects')
         session['projectId'] = self.projectId

         # get all of the stories for the project      
         projectStories = client.stories.all( self.projectId )
         
         # if there are stories in the project then pull them out
         if 'stories' in projectStories :
            stories = projectStories['stories']
         
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
            self.labelFilter = u'label:"{0}" '.format( self.request.get('labels') )
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
         projectStories = client.stories.get_filter(self.projectId, self.filter, True )
         
         if 'stories' in projectStories :
            stories = projectStories['stories']         
            
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
                        'selected_label' : self.selectedLabel,
                        'version' : os.environ.get('CURRENT_VERSION_ID'),
                        'outputActivity_checked' : self.outputActivityChecked
                        }
                        
      path = os.path.join(os.path.dirname(__file__), 'index.html')
      self.response.out.write(template.render(path, template_values))        
    



