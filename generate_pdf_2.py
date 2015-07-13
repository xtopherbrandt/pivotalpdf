import json
import time
from busyflow.pivotal import PivotalClient
import webapp2
from full_report_output import *
from abbreviated_report_output import *
import logging

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
      
      # if they've specified summary then give them summary, 
      if 'format' in request and request['format'] == 'summaryDocument' :
         report = AbbreviatedReportOutput()
      else :
         # if we can't find a report format specified assume full.
         report = FullReportOutput()

      if 'activities' in request and request['activities'] == False :
         outputActivity = "checked='false'"
      else :
         outputActivity = "checked='true'"
         
      report.GeneratePdf( self.response, request['apiKey'], request['projectId'], request['stories'], filename, outputActivity )
      

      