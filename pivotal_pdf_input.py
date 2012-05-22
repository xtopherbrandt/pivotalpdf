import os
from google.appengine.ext.webapp import template
import cgi
import datetime
import urllib
import wsgiref.handlers
import csv

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from busyflow.pivotal import PivotalClient
from pivotal_pdf_output import OutputPDF
from xml.sax.saxutils import escape

class MainPage(webapp.RequestHandler):
    def get(self):

        template_values = {}
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

      
      if self.request.get('APIKey') != '' :
         self.apikey = self.request.get('APIKey')
      else :
         self.apikey = self.request.get('hiddenAPIKey')
      
      if self.request.get('projects') != '' :
         self.projectId = self.request.get('projects')
      else :
         self.projectId = self.request.get('hiddenProjectId')
      
      if self.request.get('filter') != '' :
         self.filter = self.request.get('filter')
      else :
         self.filter = self.request.get('hiddenFilter')
         
      client = PivotalClient(token=self.apikey, cache=None)
      projects = client.projects.all()['projects']
    
      self.response.out.write("""
         <head>
            <link type="text/css" rel="stylesheet" href="/stylesheets/main.css" />
         </head>
         <html>
            <body>
               <h3>Step 1: Authenticate</h3>
               <form action="/authenticate" method="post">
                  Pivotal Tracker API Key
      """)
    
      apiKey = """<div><textarea name="APIKey" rows="1" cols="60">{0}</textarea></div>""".format( self.apikey )
      self.response.out.write( apiKey )
    
      self.response.out.write("""
         <div><input type="submit" value="Set Pivotal Tracker API Key"></div>
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
          
      hiddenApiKey = """<div><input name="hiddenAPIKey" type="hidden" value="{0}"/></div>""".format( self.apikey )
      self.response.out.write( hiddenApiKey )

      self.response.out.write("""

         <p>
         <div><input type="submit" value="Get Stories" ></div>
         </form>
      """)
      
      stories = []
      
      # if a project is selected, get it's stories
      if self.projectId != '' :
         stories = client.stories.get_filter(self.projectId, self.request.get('filter'), True )['stories']

      self.response.out.write("""
         <form action="/PivotalPDFOutput.pdf" method="post">
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
      
      # if there are no stories, disable the Output PDF button
      if len(stories) == 0 :
         self.response.out.write( """
            <div><input type="submit" value="View PDF" disabled="true"></div>
            <div><input type="submit" value="Download PDF" disabled="true"></div>
            """)
      else :
         self.response.out.write( """
            <div><input type="submit" name="outputType" value="View PDF" ></div>
            <div><input type="submit" name="outputType" value="Download PDF" ></div>
            """)
          
      hiddenApiKey = """<div><input name="hiddenAPIKey" type="hidden" value="{0}"/></div>""".format( self.apikey )
      self.response.out.write( hiddenApiKey )
      hiddenProjectId = """<div><input name="hiddenProjectId" type="hidden" value="{0}"/></div>""".format( self.projectId )
      self.response.out.write( hiddenProjectId )
      hiddenFilter = """<div><input name="hiddenFilter" type="hidden" value="{0}"/></div>""".format( self.filter )
      self.response.out.write( hiddenFilter )
            
      self.response.out.write("""
         </form>
         </body>
         </html>    
      """)


application = webapp.WSGIApplication([
  ('/', MainPage),
  ('/authenticate', OutputHTML),
  ('/getStories', OutputHTML),
  ('/PivotalPDFOutput.pdf', OutputPDF)
  
], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
