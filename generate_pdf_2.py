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
      APIKey *
      ProjectID *
      Stories [] *
      Activities (bool)
      Format (fullDocument|summaryDocument)
   '''
   def post (self) :
      
      logging.info ('GeneratePDF_2.post()')

      requestJson = self.request.body
      request = json.loads( requestJson )
      
      logging.info( request )

      filename =  """UserStories-{0}.pdf""".format(time.strftime(self.fileNameDateTimeFormat))
      
      # if they've specified summary then give them summary, 
      if 'Format' in request and request['Format'] == 'summaryDocument' :
         report = AbbreviatedReportOutput()
      else :
         # if we can't find a report format specified assume full.
         report = FullReportOutput()

      if 'Activities' in request and request['Activities'] == false :
         outputActivity = "checked='false'"
      else :
         outputActivity = "checked='true'"
         
      report.GeneratePdf( self.response, request['APIKey'], request['ProjectID'], request['Stories'], filename, outputActivity )
      

      