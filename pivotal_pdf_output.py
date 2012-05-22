import os
import sys
sys.path.insert(0, 'reportlab.zip')
import re
import wsgiref.handlers
import time

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.tables import Table, TableStyle, CellStyle, LongTable
from reportlab.platypus.doctemplate import LayoutError
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from xml.sax.saxutils import escape 
from busyflow.pivotal import PivotalClient

    
class OutputPDF(webapp.RequestHandler):

   PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
   styles = getSampleStyleSheet()
   iterationDateFormat = "%B %d, %Y"
   activityDateFormat = "%b %d, %Y"
   fileNameDateTimeFormat = "%Y%m%d%H%M%S"
   styleHeader = ParagraphStyle( name='TableHeader',
                                 fontName='Helvetica-Bold',
                                 fontSize=14,
                                 leading=17,
                                 leftIndent=0,
                                 rightIndent=0,
                                 firstLineIndent=0,
                                 alignment=TA_CENTER,
                                 spaceBefore=0,
                                 spaceAfter=0,
                                 bulletFontName='Helvetica',
                                 bulletFontSize=10,
                                 textColor=colors.white,
                                 backColor=None,
                                 wordWrap=None,
                                 borderWidth=0,
                                 borderPadding=0,
                                 borderColor=None,
                                 borderRadius=None,
                                 allowWidows=0,
                                 allowOrphans=0 )
      
   styleName = ParagraphStyle( name='Name',
                                 fontName='Helvetica-Bold',
                                 fontSize=12,
                                 leading=14,
                                 leftIndent=0,
                                 rightIndent=0,
                                 firstLineIndent=0,
                                 alignment=TA_LEFT,
                                 spaceBefore=0,
                                 spaceAfter=0,
                                 bulletFontName='Helvetica',
                                 bulletFontSize=10,
                                 textColor=colors.black,
                                 backColor=None,
                                 wordWrap=None,
                                 borderWidth=0,
                                 borderPadding=0,
                                 borderColor=None,
                                 borderRadius=None,
                                 allowWidows=0,
                                 allowOrphans=0 )
                                 
   styleNormal = ParagraphStyle( name='Normal',
                                 fontName='Helvetica',
                                 fontSize=8,
                                 leading=10,
                                 leftIndent=0,
                                 rightIndent=0,
                                 firstLineIndent=0,
                                 alignment=TA_LEFT,
                                 spaceBefore=0,
                                 spaceAfter=4,
                                 bulletFontName='Helvetica',
                                 bulletFontSize=10,
                                 textColor=colors.black,
                                 backColor=None,
                                 wordWrap=None,
                                 borderWidth=0,
                                 borderPadding=0,
                                 borderColor=None,
                                 borderRadius=None,
                                 allowWidows=0,
                                 allowOrphans=1 )
    
   def post(self):
      apiToken = self.request.get('hiddenAPIKey')
      projectId = self.request.get('hiddenProjectId')
      filter = self.request.get('hiddenFilter')
      
      stories = self.request.get_all('stories')

      # if no stories were selected, assume all are desired and get all by the filter
      if len(stories) == 0:
         client = PivotalClient(token=apiToken, cache=None)
         stories = [ str(story['id']) for story in client.stories.get_filter(projectId, filter, True )['stories'] ]

      if self.request.get('outputType') == 'View PDF':
         view = True
      else :
         view = False
         
      self.GeneratePdf( stories, apiToken, projectId, view )

   def GeneratePdf(self, stories, apiToken, projectId, view):
   
      if view :
         self.response.headers['Content-Type'] = 'application/pdf'
      else :
         self.response.headers['Content-Type'] = 'application/octet-stream'
         self.response.headers['Content-Disposition'] = """attachment; filename=UserStories-{0}.pdf""".format(time.strftime(self.fileNameDateTimeFormat))
      
      doc = SimpleDocTemplate(self.response.out,pagesize = letter, allowSplitting=1, title='User Stories', author='Pivotal PDF (http://pivotal-pdf.appspot.com)')
      
      #Create a list of flowables for the document
      flowables = []
      
      #Create a list for our rows, this will be a list of lists or an array which makes up the table
      tableData = []      
      
      #Create a row for our stories
      storyRow = []
      #add some flowables
      storyRow.append(Paragraph("Story",self.styleHeader))
      storyRow.append(Paragraph("Iteration Start",self.styleHeader))
      storyRow.append(Paragraph("Iteration End",self.styleHeader))
      storyRow.append(Paragraph("Description", self.styleHeader))
      tableData.append(storyRow)
      
      #Add the Done Stories
      doneStories = self.GetDoneStories( stories, apiToken, projectId )
      
      for storyInfo in doneStories :
         
         # Paragraphs can take HTML so the mark-up characters in the text must be escaped
         storyName = escape ( storyInfo['story']['name'] )

         storyDescription = self.BuildDescription( storyInfo )
         
         storyRow = []
         storyRow.append(Paragraph( storyName,self.styleName))
         storyRow.append(Paragraph(storyInfo['start'].strftime(self.iterationDateFormat),self.styleNormal))
         storyRow.append(Paragraph(storyInfo['finish'].strftime(self.iterationDateFormat),self.styleNormal))
         storyRow.append( storyDescription )
         tableData.append(storyRow)
      
      #Add the Current Stories
      currentStories = self.GetCurrentStories( stories, apiToken, projectId )
      
      for storyInfo in currentStories :
         
         # Paragraphs can take HTML so the mark-up characters in the text must be escaped
         storyName = escape ( storyInfo['story']['name'] )

         storyDescription = self.BuildDescription( storyInfo )
        
         storyRow = []
         storyRow.append(Paragraph( storyName,self.styleName))
         storyRow.append(Paragraph("Current",self.styleNormal))
         storyRow.append(Paragraph("Current",self.styleNormal))
         
         storyRow.append(storyDescription)
   
         tableData.append(storyRow)
      
      #Add the Future Stories
      futureStories = self.GetFutureStories( stories, apiToken, projectId )
      
      for storyInfo in futureStories :

         # Paragraphs can take HTML so the mark-up characters in the text must be escaped
         storyName = escape ( storyInfo['story']['name'] )

         storyDescription = self.BuildDescription( storyInfo )
         
         storyRow = []
         storyRow.append(Paragraph( storyName,self.styleName))
         storyRow.append(Paragraph(storyInfo['start'].strftime(self.iterationDateFormat),self.styleNormal))
         storyRow.append(Paragraph(storyInfo['finish'].strftime(self.iterationDateFormat),self.styleNormal))
         storyRow.append( storyDescription )
         tableData.append(storyRow)
      
      #Add the Icebox Stories
      iceboxStories = self.GetIceboxStories( stories, apiToken, projectId )
      
      for storyInfo in iceboxStories :

         # Paragraphs can take HTML so the mark-up characters in the text must be escaped
         storyName = escape ( storyInfo['story']['name'] )

         storyDescription = self.BuildDescription( storyInfo )
         
         storyRow = []
         storyRow.append(Paragraph( storyName,self.styleName))
         storyRow.append(Paragraph("Icebox",self.styleNormal))
         storyRow.append(Paragraph('Icebox',self.styleNormal))
         storyRow.append( storyDescription )
         tableData.append(storyRow)

      table = LongTable(tableData, colWidths=[2*inch,1*inch,1*inch,3.5*inch] )  
      
      table.setStyle(TableStyle([
                        ('BACKGROUND',(0,0),(-1,0),colors.darkslategray),        #Give the header row a grey background
                        ('BACKGROUND',(0,1),(-1, len(doneStories) ),colors.lightgrey),  #Shade the Done stories in light grey
                        ('BACKGROUND',(0, len(doneStories) + len(currentStories) + 1 ),(-1, -1 ),colors.grey),  #Shade the backlog stories in light grey
                        ('BACKGROUND',(0, len(doneStories) + len(currentStories) + len(futureStories) + 1 ),(-1, -1 ),colors.dimgrey),  #Shade the backlog stories in light grey
                        ('TEXTCOLOR',(0,0),(-1,0),colors.white),        #Give the header row white text
                        ('ALIGNMENT',(0,0),(-1,0),'CENTRE'),            #Horizontally align the header row to the center
                        ('VALIGN',(0,0),(-1,0),'MIDDLE'),               #Vertically align the header row in the middle
                        ('TEXTCOLOR',(0,1),(-1,-2),colors.black),       #Make the rest of the text white
                        ('VALIGN',(0,1),(-1,-1),'TOP'),                 #Make the rest of the cells vertically aligned to the top
                        ('ALIGN',(0,1),(-1,-2),'LEFT'),                 #Generally align everything to the right
                        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                        ]))
                              
      flowables.append( table )
      
      try :
         doc.build(flowables)
      except LayoutError as exception:
         nameMatch = re.search(r"""('[^']*')""", str(exception), re.M)
                  
         if nameMatch != None :
            template_values = {'storyName': nameMatch.group(0) }
         else :
            template_values = {}
               
         path = os.path.join(os.path.dirname(__file__), 'error.html')
         self.response.headers['Content-Type'] = 'html'
         self.response.out.write(template.render(path, template_values))

   def BuildDescription (self, storyInfo ) :
   
         rawDescription = []
         
         rawDescription.append (storyInfo['story']['description'])
         
         # If there are Activity notes, start our list with a heading
         if 'notes' in storyInfo['story'] :
            rawDescription.append('*Activity:*')
            
            # Get the set of Activity notes for the story
            for note in storyInfo['story']['notes'] :
               rawDescription.append("""_{0}_ - {1}""".format(note['noted_at'].strftime(self.activityDateFormat), note['text']))
                  
         # Concatenate the story description with the activity notes
         description = '\n'.join(rawDescription )
                  
         # Need to separate out each paragraph in the story. The Paragraph flowable will remove all 
         # whitespace around end of line characters.
         paragraphMatches = re.finditer(r"""(^.*$)""", description, re.M)
         storyDescription = []
                  
         # Add each paragraph to a list of paragraph flowables that are then added to the table
         for paragraphMatch in paragraphMatches :
            storyDescription.append( Paragraph( self.MarkDownToMarkUp ( paragraphMatch.group(0) ), self.styleNormal ) )
         
         return storyDescription
   
   def GetDoneStories (self, filteredStories, apiToken, projectId) :
   
      doneStories = []
        
      # Get the set of done iterations
      client = PivotalClient(token=apiToken, cache=None)
      project = client.iterations.done( projectId )
      
      # if the project has some done iterations
      if 'iterations' in project:
         iterations = project['iterations']
        
         # Go through each iteration and find the stories that are in our set
         for iteration in iterations:
            stories = iteration['stories']
            found = False
            for story in stories:
               for filteredStory in filteredStories: 
                  if str(story['id']) == filteredStory:
                     storyInfo = { 'story' : story, 'start' : iteration['start'], 'finish' : iteration['finish'] }
                     doneStories.append ( storyInfo )
                     found = True
                     break
               
      return doneStories

   def GetCurrentStories (self, filteredStories, apiToken, projectId) :
   
      currentStories = []
        
      # Get the current iteration
      client = PivotalClient(token=apiToken, cache=None)
      project = client.iterations.current( projectId )
      
      # if the project has a current iteration
      if 'iterations' in project:
         iterations = project['iterations']
        
         # Go through each iteration and find the stories that are in our set
         for iteration in iterations:
            stories = iteration['stories']
            
            found = False
            for story in stories:
               for filteredStory in filteredStories:               
                  if str(story['id']) == filteredStory:
                     storyInfo = { 'story' : story, 'start' : iteration['start'], 'finish' : iteration['finish'] }
                     currentStories.append ( storyInfo )
                     found = True
                     break
               
      return currentStories

   def GetFutureStories (self, filteredStories, apiToken, projectId) :
   
      futureStories = []
        
      # Get the set of future iterations
      client = PivotalClient(token=apiToken, cache=None)
      project = client.iterations.backlog( projectId )
      
      # if the project has a current iteration
      if 'iterations' in project:
         iterations = project['iterations']
        
         # Go through each iteration and find the stories that are in our set
         for iteration in iterations:
            stories = iteration['stories']
            
            found = False
            for story in stories:
               for filteredStory in filteredStories:               
                  if str(story['id']) == filteredStory:
                     storyInfo = { 'story' : story, 'start' : iteration['start'], 'finish' : iteration['finish'] }
                     futureStories.append ( storyInfo )
                     found = True
                     break
               
      return futureStories

   def GetIceboxStories (self, filteredStories, apiToken, projectId) :
   
      iceboxStories = []
        
      # Get the set of icebox stories
      client = PivotalClient(token=apiToken, cache=None)
      stories = client.stories.get_filter(projectId, 'state:unscheduled', True )['stories']
            
      for story in stories:
         for filteredStory in filteredStories:               
            if str(story['id']) == filteredStory:
               storyInfo = { 'story' : story, 'start' : None, 'finish' : None }
               iceboxStories.append ( storyInfo )
               break
               
      return iceboxStories

   def MarkDownToMarkUp (self, markedDownText) :
      markedUpText = ''
      markedUpStrings = []
      regularTextIndex = 0
      
      textMatches = self.FindMarkedDownText( markedDownText )
      
      for match in textMatches :
      
         # add the next bit of regular text up to the next marked down chunk
         markedUpStrings.append ( escape ( markedDownText[ regularTextIndex : match.start() ] ) )
         
         # add a chunk of text with mark up appropriate to the group it was found in
         if match.group('bold') != None :
            innerMarkUp = self.MarkDownToMarkUp ( match.group('bold') )
            markedUpStrings.append ( """<b>{0}</b>""".format( innerMarkUp ) )
         
         if match.group('italicized') != None :
            innerMarkUp = self.MarkDownToMarkUp ( match.group('italicized') )
            markedUpStrings.append ( """<i>{0}</i>""".format( innerMarkUp ) )
            
         regularTextIndex = match.end()

      # add the last bit of regular text from the last match to the end of the string
      markedUpStrings.append ( escape ( markedDownText[ regularTextIndex : len( markedDownText ) ] ) )
      
      return markedUpText.join( markedUpStrings )
      
   def FindMarkedDownText (self, text) :
      # return the MatchObjects containing bold, underlined or bold underline text
      return re.finditer(r"""(?:(?:(?:(?<=[\s^,(])|(?<=^))\*(?=\S)(?P<bold>.+?)(?<=\S)\*(?:(?=[\s$,.?!])|(?<=$)))|(?:(?:(?<=[\s^,(])|(?<=^))_(?=\S)(?P<italicized>.+?)(?<=\S)_(?:(?=[\s$,.?!])|(?<=$))))""",text, re.M)
               

