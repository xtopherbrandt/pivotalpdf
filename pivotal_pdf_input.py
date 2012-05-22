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
from gaesessions import get_current_session

class MainPage(webapp.RequestHandler):
    def get(self):

      #Try to get the apiKey from a cookie, the existance of the cookie also indicates that the user wants to have their key remembered
      if self.request.cookies.get('apiKey') != None :
         self.apiKey = self.request.cookies.get('apiKey')  
         self.rememberMyKey = 'checked=True'       
      else :
         self.apiKey = ''
         self.rememberMyKey = ''
         
      
      template_values = {'apiKey' : self.apiKey, 'checked' : self.rememberMyKey}
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

      session = get_current_session()
      
      if session.is_active():
         self.apikey = session['APIKey']
          
         if session.has_key('projectId') :
            self.projectId = session['projectId']
         else :
            self.projectId = None
             
         if session.has_key('filter') :
            self.filter = session['filter']
         else :
            self.filter = ''         
             
         if session.has_key('rememberMyKeyCheckedAttribute') :
            self.rememberMyKeyCheckedAttribute = session['rememberMyKeyCheckedAttribute']
         else :
            self.rememberMyKeyCheckedAttribute = ''         
            
      else:
         # when the user logs in, it is recommended that you rotate the session ID (security)
         session.regenerate_id()
         self.apikey = self.request.get('APIKey')
         session['APIKey'] = self.apikey
      
      if self.request.get('projects') != '' :
         self.projectId = self.request.get('projects')
         session['projectId'] = self.projectId
      
      if self.request.get('filter') != '' :
         self.filter = self.request.get('filter')
         session['filter'] = self.filter
      
      # if the remember My Key checkbox is set then store the key in a cookie
      if self.request.get('rememberMyKey', default_value='False') == 'True' :
         #explicitly setting the domain does not seem to work, at least on the localhost
         self.response.set_cookie('apiKey', value=self.apikey, secure=False, httponly=True, expires=datetime.datetime.now() + datetime.timedelta(days=365), overwrite=True )         
         self.rememberMyKeyCheckedAttribute = "checked='True'"
         session['rememberMyKeyCheckedAttribute'] = self.rememberMyKeyCheckedAttribute
      else :
         #if we didn't get the value in the form and we don't remember having the checkbox set then delete the cookie 
         if session.has_key('rememberMyKeyCheckedAttribute') == False :
            self.response.delete_cookie('apiKey')
            self.rememberMyKeyCheckedAttribute = ''         
               
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
         <div><input type="submit" value="Set Pivotal Tracker API Key"><input type="checkbox" value="True" {0} name="rememberMyKey">Remember My Key</div>
         </form>

         <p>
         <h3>Step 2: Select Project</h3>

         <form action="/getStories" method="post">             
         <div><select name="projects" size="10"  style="width:300px;margin:5px 0 5px 0;">
       """.format(self.rememberMyKeyCheckedAttribute))
                    
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
