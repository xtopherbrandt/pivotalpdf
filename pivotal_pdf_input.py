import os
from google.appengine.ext.webapp import template
import cgi
import datetime
import urllib
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from busyflow.pivotal import PivotalClient
from pivotal_pdf_output import OutputPDF

class MainPage(webapp.RequestHandler):
    def get(self):

        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class GetProjects(webapp.RequestHandler):
     

  def post(self):

    self.apikey = self.request.get('APIKey')
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
             <div><select name="projects" size="10" cols="60">
    """)
                    
    for project in projects:
      option = """<option value="{0}">{1}</option>""".format( project['id'], project['name'] )
      self.response.out.write( option )  
    
    self.response.out.write("""
            </select></div>
     
             <p>
             <h3>Step 3: Enter Story Search Filter</h3>
             <div><textarea name="filter" rows="1" cols="60" ></textarea></div>
    """)
    
    hiddenApiKey = """<div><input name="hiddenAPIKey" type="hidden" value="{0}"/></div>""".format( self.apikey )
    self.response.out.write( hiddenApiKey )
    self.response.out.write("""

             <p>
             <div><input type="submit" value="Get Stories" ></div>
          </form>

        </body>
      </html>    
    """)
      

class GetStories(webapp.RequestHandler):
  def post(self):
        apiToken = self.request.get('hiddenAPIKey')
        projectId = self.request.get('projects')
        
        client = PivotalClient(token=apiToken, cache=None)
        stories = client.stories.get_filter(projectId, self.request.get('filter'), True )['stories']
        output=OutputPDF ()
        output.get( self, stories, apiToken, projectId )
#           for story in stories:
#               self.response.out.write( story['name'] )
#               self.response.out.write("<p>")

application = webapp.WSGIApplication([
  ('/', MainPage),
  ('/authenticate', GetProjects),
  ('/getStories', GetStories)  
], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
