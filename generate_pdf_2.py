import json
import time
import datetime
import webapp2
from full_report_output import *
from abbreviated_report_output import *
import logging
from google.appengine.api import users
from google.appengine.ext import db
from user import *

class GeneratePDF_2 (webapp2.RequestHandler):

   fileNameDateTimeFormat = "%Y%m%d%H%M%S"

   '''
   WebServer version of Generate PDF
   Post data:
      apiKey * :: the user's api key ex. "apiKey":"3e62e57a6b0cb453a7d92de0449ae553",
      projectId * :: the project id containing the stories. Ex. "projectId":"527627"
      stories [] * :: list of story IDs as Strings. ie. "stories":["28052389","28052405","28052809"]
      activities (bool) :: whether to include activies or not. Ex. "activities":false
      format (fullDocument|summaryDocument) :: either "fullDocument" or "summaryDocument". Default is fullDocument. Ex. "format":"summaryDocument"
   '''
   def post (self) :

      logging.info ('GeneratePDF_2.post()')

      requestJson = self.request.body
      request = json.loads( requestJson )

      logging.info( request )

      filename =  """UserStories-{0}.pdf""".format(time.strftime(self.fileNameDateTimeFormat))

      '''Get the user's record'''
      userKey = user_key( request['apiKey'] )
      user = userKey.get()

      '''if this user doesn't have a record yet, create one'''
      if user == None :
         user = User( id=request['apiKey'] )
         logging.info ("New extension user added {0}".format(request['apiKey']))
      else :
         user.last_usage_date = datetime.datetime.today()
         logging.info ("User {0} made a request from the extension.".format(request['apiKey']))

      # if they've specified summary then give them summary,
      if 'format' in request and request['format'] == 'summaryDocument' :
         report = AbbreviatedReportOutput()
         user.summary_document_count = (user.summary_document_count + 1) if ( user.summary_document_count != None ) else 1
      else :
         # if we can't find a report format specified assume full.
         report = FullReportOutput()
         user.full_document_count = (user.full_document_count + 1) if ( user.full_document_count != None ) else 1

      '''Save the user info'''
      user.put()

      if 'activities' in request and request['activities'] == False :
         outputActivity = "checked='false'"
      else :
         outputActivity = "checked='true'"

      report.GeneratePdf( self.response, request['apiKey'], request['projectId'], request['stories'], filename, outputActivity )
