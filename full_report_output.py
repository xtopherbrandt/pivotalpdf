import os
import sys
sys.path.insert(0, 'reportlab.zip')
import re
import wsgiref.handlers
import time

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from gaesessions import get_current_session
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

    
class FullReportOutput(webapp.RequestHandler):

   PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
   styles = getSampleStyleSheet()
   iterationDateFormat = "%B %d, %Y"
   activityDateFormat = "%b %d, %Y"
   fileNameDateTimeFormat = "%Y%m%d%H%M%S"
   interStorySpace = 0.25*inch
   intraStorySpace = 0.125*inch

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
                                 fontSize=14,
                                 leading=16,
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
                                 fontSize=12,
                                 leading=14,
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
                                  
   detailTableStyle = TableStyle([
                           ('FONT',(0,0),(-1,0),'Helvetica-Oblique'),         #Set all of the text to be italized helvetica
                           ('FONTSIZE',(0,0),(-1,0),12),                      #Set all text to be font size 12
                           ('TEXTCOLOR',(0,0),(-1,0),colors.black),           #Set all text to be black
                           ('ALIGNMENT',(0,0),(0,0),'LEFT'),                  #Left align the left column
                           ('ALIGNMENT',(1,0),(1,0),'CENTER'),                #Center the middle column
                           ('ALIGNMENT',(-1,0),(-1,0),'RIGHT')                  #Right align the right column
                           ])
    
   def post(self):
   
      session = get_current_session()

      stories = self.request.get_all('stories')
      filter = ''         
      projectId = None
      filename =  """UserStories-{0}.pdf""".format(time.strftime(self.fileNameDateTimeFormat))

      if session.is_active():
         apiToken = session['APIKey']
          
         if session.has_key('projectId') :
            projectId = session['projectId']
             
         if session.has_key('filter') :
            filter = session['filter']
      
         #store the selected story list
         session['stories'] = stories

      # if no stories were selected, assume all are desired and get all by the filter
      if len(stories) == 0:
         client = PivotalClient(token=apiToken, cache=None)
         stories = [ str(story['id']) for story in client.stories.get_filter(projectId, filter, True )['stories'] ]
            
      self.GeneratePdf( apiToken, projectId, stories, filename )

   def get(self):
   
      session = get_current_session()
      
      stories = []
      filter = ''         
      projectId = None
      filename =  """UserStories-{0}.pdf""".format(time.strftime(self.fileNameDateTimeFormat))
      
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
            
         stories = session['stories']

      # if no stories were selected, assume all are desired and get all by the filter
      if len(stories) == 0:
         client = PivotalClient(token=apiToken, cache=None)
         stories = [ str(story['id']) for story in client.stories.get_filter(projectId, filter, True )['stories'] ]
            
      self.GeneratePdf( apiToken, projectId, stories, filename )
   
   def GeneratePdf(self, apiToken, projectId, stories, filename ):
   
      self.response.headers['Content-Type'] = 'application/pdf'
      
      doc = SimpleDocTemplate(self.response.out,pagesize = letter, allowSplitting=1, title='User Stories', author='Pivotal PDF (http://pivotal-pdf.appspot.com)', leftMargin=0.75*inch, rightMargin=0.75*inch)
      
      #Create a list of flowables for the document
      flowables = []
      
      #Add the Done Stories
      doneStories = self.GetDoneStories( stories, apiToken, projectId )
      
      for storyInfo in doneStories :
         
         # Paragraphs can take HTML so the mark-up characters in the text must be escaped
         storyName = escape ( storyInfo['story']['name'] )

         storyDescription = self.BuildDescription( storyInfo )
         
         flowables.append(Paragraph( storyName,self.styleName))
         
         #Create a table row for our detail line
         tableData = []
         detailRow = []
         #add some flowables
         detailRow.append("""Accepted: {0}""".format(storyInfo['story']['accepted_at'].strftime(self.iterationDateFormat)) )
         detailRow.append(storyInfo['story']['owned_by'])
         detailRow.append("""Size: {0}""".format( storyInfo['story']['estimate'] ))

         tableData.append ( detailRow )
         
         table = Table(tableData, colWidths=[2.33*inch,2.33*inch,2.33*inch] )  
                  
         table.setStyle( self.detailTableStyle )
         
         flowables.append(table)
            
         flowables.append(Spacer(0,self.intraStorySpace))
                  
         for paragraph in storyDescription:
            flowables.append( paragraph )
            
         flowables.append(Spacer(0,self.interStorySpace))
      
      #Add the Current Stories
      currentStories = self.GetCurrentStories( stories, apiToken, projectId )
      
      for storyInfo in currentStories :
         
         # Paragraphs can take HTML so the mark-up characters in the text must be escaped
         storyName = escape ( storyInfo['story']['name'] )

         storyDescription = self.BuildDescription( storyInfo )
         
         flowables.append(Paragraph( storyName,self.styleName))
         
         #Create a table row for our detail line
         tableData = []
         detailRow = []
         #add some flowables
         detailRow.append("In Progress" )
         if 'owned_by' in storyInfo['story'] :
            detailRow.append(storyInfo['story']['owned_by'])
         else:
            detailRow.append("" )
         
         detailRow.append("""Size: {0}""".format( storyInfo['story']['estimate'] ))

         tableData.append ( detailRow )
         
         table = Table(tableData, colWidths=[2.33*inch,2.33*inch,2.33*inch] )  
         
         table.setStyle( self.detailTableStyle )
         
         flowables.append(table)
            
         flowables.append(Spacer(0,self.intraStorySpace))
         
         for paragraph in storyDescription:
            flowables.append( paragraph )
            
         flowables.append(Spacer(0,self.interStorySpace))
      
      #Add the Backlog Stories
      backlogStories = self.GetFutureStories( stories, apiToken, projectId )
      
      for storyInfo in backlogStories :
         
         # Paragraphs can take HTML so the mark-up characters in the text must be escaped
         storyName = escape ( storyInfo['story']['name'] )

         storyDescription = self.BuildDescription( storyInfo )
         
         flowables.append(Paragraph( storyName,self.styleName))
         
         #Create a table row for our detail line
         tableData = []
         detailRow = []
         #add some flowables
         detailRow.append("""Scheduled Sprint: {0}""".format(storyInfo['start'].strftime(self.iterationDateFormat)) )
         detailRow.append("""Size: {0}""".format( storyInfo['story']['estimate'] ))

         tableData.append ( detailRow )
         
         table = Table(tableData, colWidths=[3.5*inch,3.5*inch] )  
                  
         table.setStyle( self.detailTableStyle )
         
         flowables.append(table)
            
         flowables.append(Spacer(0,self.intraStorySpace))
         
         for paragraph in storyDescription:
            flowables.append( paragraph )
            
         flowables.append(Spacer(0,self.interStorySpace))
      
      #Add the Ice Box Stories
      iceboxStories = self.GetIceboxStories( stories, apiToken, projectId )
      
      for storyInfo in iceboxStories :
         
         # Paragraphs can take HTML so the mark-up characters in the text must be escaped
         storyName = escape ( storyInfo['story']['name'] )

         storyDescription = self.BuildDescription( storyInfo )
         
         flowables.append(Paragraph( storyName,self.styleName))
         
         #Create a table row for our detail line
         tableData = []
         detailRow = []
         #add some flowables
         detailRow.append("In the Ice Box" )
         if storyInfo['story']['estimate'] != -1:
            detailRow.append("""Size: {0}""".format( storyInfo['story']['estimate'] ))
         else:
            detailRow.append("Unestimated" )
         

         tableData.append ( detailRow )
         
         table = Table(tableData, colWidths=[3.5*inch,3.5*inch] )  
         
         table.setStyle( self.detailTableStyle )
         
         flowables.append(table)
            
         flowables.append(Spacer(0,self.intraStorySpace))
         
         for paragraph in storyDescription:
            flowables.append( paragraph )
            
         flowables.append(Spacer(0,self.interStorySpace))
      
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
               

