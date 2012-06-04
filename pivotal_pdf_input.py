import os
from google.appengine.ext.webapp import template
import cgi
import datetime
import time
import urllib
import wsgiref.handlers
import csv

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from busyflow.pivotal import PivotalClient
from xml.sax.saxutils import escape
from gaesessions import get_current_session

from generate_output import *

class MainPage(webapp.RequestHandler):
    def get(self):

      #Try to get the apiKey from a session cookie
      session = get_current_session()

      self.apikey = ''
      
      # if the session is active      
      if session.is_active():
         
         # and it has an APIKey, get it
         if session.has_key('APIKey') :
            self.apiKey = session['APIKey']
      
      template_values = {'apiKey' : self.apiKey}
      path = os.path.join(os.path.dirname(__file__), 'index.html')
      self.response.out.write(template.render(path, template_values))
        
class GetProjects(webapp.RequestHandler):

   def post(self):

      output = OutputHTML( self )
      output.post()  
      
class GetStories ( webapp.RequestHandler ):
   def post ( self ):
      for story in stories:
           self.response.out.write( story['name'] )
           self.response.out.write("<p>")      

class OutputHTML ( webapp.RequestHandler ):

   def post ( self ):

      # initialize the class properties
      self.projectId = None
      self.filter = ''         
      self.rememberMyKeyCheckedAttribute = ''         

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
    
      apiKey = """<div><textarea name="APIKey" rows="1" cols="60">{0}</textarea></div>""".format( self.apikey )
      self.response.out.write( apiKey )
    
      self.response.out.write("""
         <div><input type="submit" value="Login"></div>
         </form>

         <p>
         <h3>Step 2: Select Project</h3>

         <form action="/getStories" method="post">             
         <div><select name="projects" size="10"  style="width:300px;margin:5px 0 5px 0;">
       """)
                    
      for project in projects:
         if project['id'] == self.projectId :
            option = """<option selected="selected" value="{0}">{1}</option>""".format( project['id'], project['name'] )
         else:
            option = """<option value="{0}">{1}</option>""".format( project['id'], project['name'] )
         self.response.out.write( option )  
    
      self.response.out.write("""
         </select></div>
     
         <p>
         <h3>Step 3: Enter Story Search Filter</h3>
         This is the same as the Search box in Pivotal Tracker
         <div><textarea name="filter" rows="1" cols="60" >{0}</textarea></div>
      """.format( self.filter ))

      self.response.out.write("""

         <p>
         <div><input type="submit" value="Get Stories" ></div>
         </form>
      """)
      
      stories = []
      
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


application = webapp.WSGIApplication([
  ('/', MainPage),
  ('/authenticate', OutputHTML),
  ('/getStories', OutputHTML),
  ('/generatePDF', GenerateOutput)
  
], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
