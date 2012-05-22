import sys
sys.path.insert(0, 'reportlab.zip')
import re
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.tables import Table, TableStyle, CellStyle, LongTable
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
   
   def post(self):
      apiToken = self.request.get('hiddenAPIKey')
      projectId = self.request.get('hiddenProjectId')
      filter = self.request.get('hiddenFilter')

      client = PivotalClient(token=apiToken, cache=None)
      stories = client.stories.get_filter(projectId, filter, True )['stories']
      self.get( stories, apiToken, projectId )

   def get(self, stories, apiToken, projectId):
      self.response.headers['Content-Type'] = 'application/pdf'
      doc = SimpleDocTemplate(self.response.out,pagesize = letter, allowSplitting=1)
      styles = getSampleStyleSheet()
      styleN = styles['Normal']
      styleH = styles['Heading2']
      
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
                                    allowOrphans=0 )
                                    
    
      #Create a list of flowables for the document
      flowables = []
      
      #Create a list for our rows, this will be a list of lists or an array which makes up the table
      tableData = []      
      
      #Create a row for our stories
      storyRow = []
      #add some flowables
      storyRow.append(Paragraph("Story",styleHeader))
      storyRow.append(Paragraph("Iteration Start",styleHeader))
      storyRow.append(Paragraph("Iteration End",styleHeader))
      storyRow.append(Paragraph("Description", styleHeader))
      tableData.append(storyRow)
      
      #Add the Done Stories
      doneStories = self.GetDoneStories( stories, apiToken, projectId )
      
      for story in doneStories :
         
         # Paragraphs can take HTML so the mark-up characters in the text must be escaped
         storyName = escape ( story['name'] )
         
         # Need to separate out each paragraph in the story. The Paragraph flowable will remove all 
         # whitespace around end of line characters.
         paragraphMatches = re.finditer(r"""(^.*$)""",story['description'], re.M)
         storyDescription = []
                  
         # Add each paragraph to a list of paragraph flowables that are then added to the table
         for paragraphMatch in paragraphMatches :
            storyDescription.append( Paragraph( escape( paragraphMatch.group(0) ) , styleNormal ) )
         
         storyRow = []
         storyRow.append(Paragraph( storyName,styleName))
         storyRow.append(Paragraph("",styleNormal))
         storyRow.append(Paragraph("",styleNormal))
         storyRow.append( storyDescription )
         tableData.append(storyRow)
      
      #Add the Current Stories
      currentStories = self.GetCurrentStories( stories, apiToken, projectId )
      
      for story in currentStories :
         
         # Paragraphs can take HTML so the mark-up characters in the text must be escaped
         storyName = escape ( story['name'] )
         
         # Need to separate out each paragraph in the story. The Paragraph flowable will remove all 
         # whitespace around end of line characters.
         paragraphMatches = re.finditer(r"""(^.*$)""",story['description'], re.M)
         storyDescription = []
                  
         # Add each paragraph to a list of paragraph flowables that are then added to the table
         for paragraphMatch in paragraphMatches :
            storyDescription.append( Paragraph( escape( paragraphMatch.group(0) ) , styleNormal ) )
        
         storyRow = []
         storyRow.append(Paragraph( storyName,styleName))
         storyRow.append(Paragraph("",styleNormal))
         storyRow.append(Paragraph("",styleNormal))
         
         storyRow.append(storyDescription)
   
         tableData.append(storyRow)
      
      #Add the Future Stories
      futureStories = self.GetFutureStories( stories, apiToken, projectId )
      
      for story in futureStories :

         # Paragraphs can take HTML so the mark-up characters in the text must be escaped
         storyName = escape ( story['name'] )
         
         # Need to separate out each paragraph in the story. The Paragraph flowable will remove all 
         # whitespace around end of line characters.
         paragraphMatches = re.finditer(r"""(^.*$)""",story['description'], re.M)
         storyDescription = []
                  
         # Add each paragraph to a list of paragraph flowables that are then added to the table
         for paragraphMatch in paragraphMatches :
            storyDescription.append( Paragraph( escape( paragraphMatch.group(0) ) , styleNormal ) )
         
         storyRow = []
         storyRow.append(Paragraph( storyName,styleName))
         storyRow.append(Paragraph("",styleNormal))
         storyRow.append(Paragraph("",styleNormal))
         storyRow.append( storyDescription )
         tableData.append(storyRow)

      table = LongTable(tableData, colWidths=[2*inch,1*inch,1*inch,3*inch] )  
      
      table.setStyle(TableStyle([
                        ('BACKGROUND',(0,0),(-1,0),colors.grey),        #Give the header row a grey background
                        ('BACKGROUND',(0,1),(-1, len(doneStories) ),colors.lightgrey),  #Shade the Done stories in light grey
                        ('BACKGROUND',(0, len(doneStories) + len(currentStories) + 1 ),(-1, -1 ),colors.lightgrey),  #Shade the backlog stories in light grey
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
      doc.build(flowables)

   def GetDoneStories (self, filteredStories, apiToken, projectId) :
   
      doneStories = []
        
      # Get the set of done iterations
      client = PivotalClient(token=apiToken, cache=None)
      iterations = client.iterations.done( projectId )['iterations']
        
      # Go through each iteration and find the stories that are in our set
      for iteration in iterations:
         stories = iteration['stories']
         
         found = False
         for story in stories:
            for filteredStory in filteredStories:               
               if story['name'] == filteredStory['name']:
                  doneStories.append ( story )
                  found = True
                  break
               
      return doneStories

   def GetCurrentStories (self, filteredStories, apiToken, projectId) :
   
      currentStories = []
        
      # Get the current iteration
      client = PivotalClient(token=apiToken, cache=None)
      iterations = client.iterations.current( projectId )['iterations']
        
      # Go through each iteration and find the stories that are in our set
      for iteration in iterations:
         stories = iteration['stories']
         
         found = False
         for story in stories:
            for filteredStory in filteredStories:               
               if story['name'] == filteredStory['name']:
                  currentStories.append ( story )
                  found = True
                  break
               
      return currentStories

   def GetFutureStories (self, filteredStories, apiToken, projectId) :
   
      futureStories = []
        
      # Get the set of future iterations
      client = PivotalClient(token=apiToken, cache=None)
      iterations = client.iterations.backlog( projectId )['iterations']
        
      # Go through each iteration and find the stories that are in our set
      for iteration in iterations:
         stories = iteration['stories']
         
         found = False
         for story in stories:
            for filteredStory in filteredStories:               
               if story['name'] == filteredStory['name']:
                  futureStories.append ( story )
                  found = True
                  break
               
      return futureStories
               
#application = webapp.WSGIApplication([('/helloworld', MainPage)], debug=True)

#def main():
#    application = webapp.WSGIApplication([('/helloworld', MainPage)], debug=True)
#    wsgiref.handlers.CGIHandler().run(application)

#if __name__ == "__main__":
#    main()
