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

   def post ( self ):

      # initialize the class properties
      self.projectId = None
      self.filter = ''     
      self.featuresChecked = "checked='true'"
      self.bugsChecked = "checked='true'"
      self.choresChecked = "checked='true'"
      self.releasesChecked = ""

      session = get_current_session()

      # if we're authenticating get the key from the input
      if self.request.get('APIKey', default_value=None) != None :
         self.apikey = self.request.get('APIKey')
            
         # if the session is active      
         if session.is_active():
            
            # and it has an APIKey
            if session.has_key('APIKey') :
            
               # but the stored API Key has changed, store the new value and clear everything else
               if self.request.get('APIKey') != session['APIKey'] :
                  session['APIKey'] = self.request.get('APIKey')
                  session.pop('projectId')
                  session.pop('filter')
         
         else :
            # if we're authenticating but the session isn't active, it is recommended that you rotate the session ID (security)
            session.regenerate_id()
            session['APIKey'] = self.apikey
            
      # if we're getting the stories
      elif self.request.get('projects', default_value=None) != None :

         self.apikey = session['APIKey']

         self.projectId = self.request.get('projects')
         session['projectId'] = self.projectId
         
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
      
      client = PivotalClient(token=self.apikey, cache=None)
      projects = client.projects.all()['projects']
    
      self.response.out.write("""
         <head>
            <link type="text/css" rel="stylesheet" href="/stylesheets/main.css" />
         </head>
         <html>
            <body>
               <h1>Pivotal PDF</h1>
               <h2>A User Story Document Generator</h2>
               <h3>Step 1: Authenticate</h3>
               <form action="/authenticate" method="post">
                  Pivotal Tracker API Key
      """)
    
      apiKey = """<div><input type="text" name="APIKey" size="60" value="{0}"></input></div>""".format( self.apikey )
      self.response.out.write( apiKey )
    
      self.response.out.write("""
         <div><input type="submit" value="Login"></div>
         </form>

         <p>
         <h3>Step 2: Select Project</h3>

         <form action="/getStories" method="post">             
         <div><select name="projects" size="10"  style="width:300px;margin:5px 0 5px 0;">
       """)
                    
      # if we havn't selected a project and there is at least 1, the select the first by default
      if self.projectId == None and len(projects) > 0 :
         self.projectId = projects[0]['id']
                                      
      for project in projects:
         if project['id'] == self.projectId :
            option = """<option selected="selected" value="{0}">{1}</option>""".format( project['id'], project['name'] )
         else:
            option = """<option value="{0}">{1}</option>""".format( project['id'], project['name'] )
         self.response.out.write( option )  
    
      self.response.out.write("""
         </select></div>
     
         <p>
         <h3>Step 3: Select Story Types and Enter Story Search Filter</h3>
         <div><label for="featuresChecked">Features</label><input type="checkbox" id="featuresChecked" name="featuresChecked" {1}>
         <label for="bugsChecked">Bugs</label><input type="checkbox" id="bugsChecked" name="bugsChecked" {2} >
         <label for="choresChecked">Chores</label><input type="checkbox" id="choresChecked" name="choresChecked" {3} >
         <label for="releasesChecked">Releases</label><input type="checkbox" id="releasesChecked" name="releasesChecked" {4} >
         </div>
         <br/>
         This is the same as the Search box in Pivotal Tracker
         <div><input type="text" name="filter" size="60" value="{0}"></input></div>
      """.format( self.filter, self.featuresChecked, self.bugsChecked, self.choresChecked, self.releasesChecked ))

      self.response.out.write("""

         <p>
         <div><input type="submit" value="Get Stories" ></div>
         </form>
      """)
      
      stories = []
      labels = {}
      
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
      
      self.filter += typeFilter
      session['filter'] = self.filter
      
      # if a project is selected, get it's stories
      if self.projectId != None :         
         stories = client.stories.get_filter(self.projectId, self.filter, True )['stories']         

      self.response.out.write("""
         <form action="/generatePDF" method="post">
      """)
     
      # list the stories
      self.response.out.write("""
    
         <p>
         <h3>Story List</h3>
         <div><select name="stories" size="20" style="width:300px;margin:5px 0 5px 0;" multiple="multiple">
      """)
      
      for story in stories :
         option = """<option value="{0}">{1}</option>""".format( story['id'], story['name'] )
         self.response.out.write( option )
   
         # as we go through each, pick out the label and add it to our list
         if 'labels' in story :
            for label in story['labels'] :
               labels[label] = label
                    
      self.response.out.write("""
         </select></div>
      """)
       
     # list the labels
      self.response.out.write("""
    
         <p>
         <h3>Label List</h3>
         <div><select name="labels" size="20" style="width:300px;margin:5px 0 5px 0;" multiple="multiple">
      """)
      
      for label in labels :
         option = """<option value="{0}">{0}</option>""".format( label )
         self.response.out.write( option )
                    
      self.response.out.write("""
         </select></div>
      """)
      
      self.response.out.write("""
         <p>
         <div>
            <input type="radio" name="format" value="full" checked="True"/>Full Report<br/>
            <input type="radio" name="format" value="summary"/>Summary Report<br/>
         </div>
         <p>
      """)
      
      # if there are no stories, disable the Output PDF button
      if len(stories) == 0 :
         self.response.out.write( """
            <div><input type="submit" value="Generate PDF" disabled="true"></div>
            """)
      else :
         self.response.out.write( """
            <div><input type="submit" name="outputType" value="Generate PDF" ></div>
            """)
                      
      self.response.out.write("""
         </form>
         </body>
         </html>    
      """)



