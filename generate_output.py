import os
import sys
sys.path.insert(0, 'reportlab.zip')
import re
import wsgiref.handlers
import time
import datetime
# see: http://effbot.org/zone/import-confusion.htm

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from gaesessions import get_current_session
from busyflow.pivotal import PivotalClient

from full_report_output import *
from abbreviated_report_output import *
from google.appengine.api import users
from google.appengine.ext import db
from user import *

class GenerateOutput(webapp.RequestHandler):

   fileNameDateTimeFormat = "%Y%m%d%H%M%S"

    
   def post(self):
   
      session = get_current_session()

      stories = []
      
      # if there are stories then get them
      if self.request.get_all('stories', default_value=None) != None :
         stories = self.request.get_all('stories')
         
      filter = ''         
      projectId = None
      filename =  """UserStories-{0}.pdf""".format(time.strftime(self.fileNameDateTimeFormat))
      
      reportFormat = 'full'
      outputActivityChecked = ''

      # if the format was included in the post, get it
      if self.request.get_all('format', default_value=None) != None :
         reportFormat = self.request.get('format')
      
      # are we to output the user activity
         
      if self.request.get('outputActivityChecked') != '' :
         outputActivityChecked = "checked='true'"
         
      session['outputActivityChecked'] = outputActivityChecked
      
      if session.is_active():
         apiToken = session['APIKey']
          
         if session.has_key('projectId') :
            projectId = session['projectId']
             
         if session.has_key('filter') :
            filter = session['filter']
                   
         #store the selected story list
         session['stories'] = stories
         
         #store the selected output format
         session['format'] = reportFormat
         
         # if no stories were selected, assume all are desired and get all by the filter
         if len(stories) == 0:
            client = PivotalClient(token=apiToken, cache=None)
            stories = [ str(story['id']) for story in client.stories.get_filter(projectId, filter, True )['stories'] ]
               
         self.GeneratePdf( apiToken, projectId, stories, filename, reportFormat, outputActivityChecked )
      else :
            
         template_values = {'Error' : 'An active session was not found. This web app requires cookies to store session information.'}
         path = os.path.join(os.path.dirname(__file__), 'error.html')
         self.response.out.write(template.render(path, template_values))        


   def get(self):
   
      session = get_current_session()
      
      stories = []
      filter = ''         
      projectId = None
      filename =  """UserStories-{0}.pdf""".format(time.strftime(self.fileNameDateTimeFormat))
      reportFormat = self.request.get('format')
      outputActivity = "checked='true'"
      
      if session.is_active():
         apiToken = session['APIKey']
          
         if session.has_key('projectId') :
            projectId = session['projectId']
         else :
            projectId = None
             
         if session.has_key('filter') :
            filter = session['filter']
         else :
            filter = ''         

         # if there were stories saved in the session            
         if 'stories' in session :
            # the stories should have been saved on the inital post, so can get them from the session
            stories = session['stories']
            
         if 'format' in session :
            # the report format should have been saved on the inital post, so can get it from the session
            reportFormat = session['format']

         # if no stories were selected, assume all are desired and get all by the filter
         if len(stories) == 0:
            client = PivotalClient(token=apiToken, cache=None)
            stories = [ str(story['id']) for story in client.stories.get_filter(projectId, filter, True )['stories'] ]
            
         if 'outputActivityChecked' in session :
            # the output activity flag should have been saved on the inital post, so can get it from the session
            outputActivity = session['outputActivityChecked']
               
         self.GeneratePdf( apiToken, projectId, stories, filename, reportFormat, outputActivity )

      else :
         # if the session isn't active, send them back to the sign in page
         
         template_values = {'version' : os.environ.get('CURRENT_VERSION_ID')}
         path = os.path.join(os.path.dirname(__file__), 'sign_in.html')
         self.response.out.write(template.render(path, template_values))        

      
   
   def GeneratePdf(self, apiToken, projectId, stories, filename, reportFormat, outputActivity ):
      
      '''Get the user's record'''
      userKey = user_key( apiToken )
      user = userKey.get()
            
      '''if this user doesn't have a record yet, create one'''
      if user == None :
         user = User( id=apiToken )
         logging.info ("New site user added {0}".format(apiToken))
      else :
         user.last_usage_date = datetime.datetime.today()
         logging.info ("User {0} made a request from the site.".format(apiToken))
      
      # if they've specified summary then give them summary, 
      if reportFormat == 'summary' :
         report = AbbreviatedReportOutput()
         user.summary_document_count = user.summary_document_count + 1
      else :
         # if we can't find a report format specified assume full.
         report = FullReportOutput()
         user.full_document_count = user.full_document_count + 1

      '''Save the user info'''
      user.put()

      report.GeneratePdf( self.response, apiToken, projectId, stories, filename, outputActivity )
      
      

