import os
import sys
sys.path.insert(0, 'reportlab.zip')
import re
import wsgiref.handlers
import time
import logging
import httplib

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.platypus.tables import Table, TableStyle, CellStyle, LongTable
from reportlab.platypus.doctemplate import LayoutError
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from xml.sax.saxutils import escape 
from busyflow.pivotal import PivotalClient

    
class FullReportOutput():

   PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
   styles = getSampleStyleSheet()
   iterationDateFormat = "%B %d, %Y"
   generatedDateFormat = "%A %B %d, %Y"
   activityDateFormat = "%b %d, %Y"
   fileNameDateTimeFormat = "%Y%m%d%H%M%S"
   titleSpace = 0.25*inch
   interStorySpace = 0.25*inch
   intraStorySpace = 0.125*inch
   pageInfo = "Pivotal PDF"

   styleDocTitle = ParagraphStyle( name='DocumentTitle',
                                 fontName='Helvetica-Bold',
                                 fontSize=20,
                                 leading=20,
                                 leftIndent=0,
                                 rightIndent=0,
                                 firstLineIndent=0,
                                 alignment=TA_CENTER,
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

   styleSectionTitle = ParagraphStyle( name='SectionTitle',
                                 fontName='Helvetica-Bold',
                                 fontSize=16,
                                 leading=20,
                                 leftIndent=0,
                                 rightIndent=0,
                                 firstLineIndent=0,
                                 alignment=TA_LEFT,
                                 spaceBefore=0,
                                 spaceAfter=0,
                                 bulletFontName='Helvetica',
                                 bulletFontSize=10,
                                 textColor=colors.black,
                                 backColor=colors.lightgrey,
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
                                 
   styleH1 = ParagraphStyle( name='H1',
                                 fontName='Helvetica-Bold',
                                 fontSize=13,
                                 leading=15,
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
                                
   styleH2 = ParagraphStyle( name='H2',
                                 fontName='Helvetica-Bold',
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
                                
   styleH3 = ParagraphStyle( name='H3',
                                 fontName='Helvetica-Bold',
                                 fontSize=11,
                                 leading=13,
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
                                 
   styleNormal = ParagraphStyle( name='Normal',
                                 fontName='Helvetica',
                                 fontSize=10,
                                 leading=12,
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
                                 
   styleNotes = ParagraphStyle( name='Notes',
                                 fontName='Helvetica-Oblique',
                                 fontSize=10,
                                 leading=10,
                                 leftIndent=0,
                                 rightIndent=0,
                                 firstLineIndent=0,
                                 alignment=TA_RIGHT,
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
                           
   footerFontName = "Helvetica"   
   footerFontSize = 8
   footerFontLeading = None
   footerLeftEdge = 0.85 * inch # x-coordinate of the left side of the footer
   footerRightEdge = 7.65 * inch # x-coordinate of the right side of the footer
   footerHeight = 0.75 * inch # y-coordinate of the footer
    
   def GeneratePdf(self, httpResponse, apiToken, projectId, stories, filename, outputActivity ):

      # Get the project Name
      client = PivotalClient(token=apiToken, cache=None)
      projectName = escape( client.projects.get( projectId )['project']['name'] )
   
      # Set the http headers
      httpResponse.headers['Content-Type'] = 'application/pdf'
      httpResponse.headers['Pragma'] = 'private'
      httpResponse.headers['Cache-Control'] = 'maxage=1'
      httpResponse.headers['Content-Disposition'] = """inline; filename='{0}'""".format(filename)
      httpResponse.headers['Accept-Ranges'] = 'bytes'
      httpResponse.headers['Expires'] = '0'
     
      doc = SimpleDocTemplate( httpResponse.out, pagesize = letter, allowSplitting=1, title="""{0} User Stories""".format( projectName ), author='Agile Docs (http://pivotal-pdf.appspot.com)', leftMargin=0.75*inch, rightMargin=0.75*inch)
      
      #Create a list of flowables for the document
      flowables = []
      
      #Add a Document Title      
      flowables.append( Paragraph ( projectName, self.styleDocTitle ) )
      flowables.append( Spacer(0, self.titleSpace) )
      
      tableData = []
      detailRow = []      
      
      detailRow.append( 'Detailed Stories' )
      detailRow.append( """As of: {0}""".format(time.strftime(self.generatedDateFormat)))
      tableData.append( detailRow )
      table = Table(tableData, colWidths=[3.5*inch,3.5*inch] )  
               
      table.setStyle( self.detailTableStyle )
      
      flowables.append(table)
      flowables.append(Spacer(0,self.intraStorySpace))
      
      #Add the Done Stories
      doneStories = self.GetDoneStories( stories, apiToken, projectId )
      storyAcceptance = self.GetAcceptanceActivity ( stories, apiToken, projectId )

      if len( doneStories ) > 0 :                  
         flowables.append( Paragraph ( 'Completed Work', self.styleSectionTitle ) )
         flowables.append( Spacer(0, self.titleSpace) )

         for storyInfo in doneStories :
            
            # put all of the story flowables in a list that will be kept together if possible
            storyBlock = []
            
            # Paragraphs can take HTML so the mark-up characters in the text must be escaped
            storyName = escape ( storyInfo['story']['name'] )

            # Get the story acceptance info, if it exists
            storyAcceptanceInfo = None
            
            if storyInfo['story']['id'] in storyAcceptance :
               storyAcceptanceInfo = storyAcceptance[storyInfo['story']['id']]
               
            storyDescription = self.BuildDescription( storyInfo, storyAcceptanceInfo, outputActivity )
            
            storyBlock.append(Paragraph( storyName,self.styleName))
            
            #Create a table row for our detail line
            tableData = []
            detailRow = []
            
            #add some flowables
            # add the date of story acceptance. The activity info returned has a limited history older stories will not have them
            detailRow.append("""Accepted: {0}""".format(storyInfo['story']['accepted_at'].strftime(self.iterationDateFormat)) )
            
            # add the owner if one exists
            if 'owned_by' in storyInfo['story'] :
               detailRow.append(storyInfo['story']['owned_by'])
            else:
               detailRow.append( "" )

            # if the story has an estimate
            if 'estimate' in storyInfo['story'] :
               # and the estimate is not -1
               if storyInfo['story']['estimate'] != -1 :
                  # add the size
                  detailRow.append("""Size: {0}""".format( storyInfo['story']['estimate'] ))
               else:
                  # if the estimate is -1 it is unestimated
                  detailRow.append("Unestimated" )
            else:
               # if there is no estimate, put the story type
               detailRow.append( storyInfo['story']['story_type'].capitalize() )

            tableData.append ( detailRow )
            
            table = Table(tableData, colWidths=[2.33*inch,2.33*inch,2.33*inch] )  
                     
            table.setStyle( self.detailTableStyle )
            
            storyBlock.append(table)
               
            storyBlock.append(Spacer(0,self.intraStorySpace))
                     
            for paragraph in storyDescription:
               storyBlock.append( paragraph )
               
            flowables.append( KeepTogether ( storyBlock ) )
               
            flowables.append(Spacer(0,self.interStorySpace))
         
         # Add a page break before the next section
         flowables.append( PageBreak() )
      
      #Add the Current Stories
      currentStories = self.GetCurrentStories( stories, apiToken, projectId )
                  
      if len( currentStories ) > 0 :
      
         flowables.append( Paragraph ( 'Current Work', self.styleSectionTitle ) )
         flowables.append( Spacer(0, self.titleSpace) )
         
         for storyInfo in currentStories :
            
            # put all of the story flowables in a list that will be kept together if possible
            storyBlock = []
            
            # Paragraphs can take HTML so the mark-up characters in the text must be escaped
            storyName = escape ( storyInfo['story']['name'] )
            
            storyAcceptanceInfo = None
            
            if storyInfo['story']['id'] in storyAcceptance :
               storyAcceptanceInfo = storyAcceptance[storyInfo['story']['id']]

            storyDescription = self.BuildDescription( storyInfo, storyAcceptanceInfo, outputActivity )
            
            storyBlock.append(Paragraph( storyName,self.styleName))
            
            #Create a table row for our detail line
            tableData = []
            detailRow = []
            
            #add some flowables
            # if this story has been accepted then set the detail row appropriately
            if storyInfo['story']['id'] in storyAcceptance :
               detailRow.append("""Accepted: {0}""".format(storyInfo['story']['accepted_at'].strftime(self.iterationDateFormat)) )
            else :
               detailRow.append("In Progress" )
               
            if 'owned_by' in storyInfo['story'] :
               detailRow.append(storyInfo['story']['owned_by'])
            else:
               detailRow.append("" )
            
            # if the story has an estimate
            if 'estimate' in storyInfo['story'] :
               # and the estimate is not -1
               if storyInfo['story']['estimate'] != -1 :
                  # add the size
                  detailRow.append("""Size: {0}""".format( storyInfo['story']['estimate'] ))
               else:
                  # if the estimate is -1 it is unestimated
                  detailRow.append("Unestimated" )
            else:
               # if there is no estimate, put the story type
               detailRow.append( storyInfo['story']['story_type'].capitalize() )

            tableData.append ( detailRow )
            
            table = Table(tableData, colWidths=[2.33*inch,2.33*inch,2.33*inch] )  
            
            table.setStyle( self.detailTableStyle )
            
            storyBlock.append(table)
               
            storyBlock.append(Spacer(0,self.intraStorySpace))
            
            for paragraph in storyDescription:
               storyBlock.append( paragraph )
               
            flowables.append( KeepTogether ( storyBlock ) )
               
            flowables.append(Spacer(0,self.interStorySpace))
         
         # Add a page break before the next section
         flowables.append( PageBreak() )
      
      #Add the Backlog Stories
      backlogStories = self.GetFutureStories( stories, apiToken, projectId )
                  
      if len( backlogStories ) > 0 :
                        
         flowables.append( Paragraph ( 'Upcoming Work', self.styleSectionTitle ) )
         flowables.append( Spacer(0, self.titleSpace) )
         
         for storyInfo in backlogStories :
            
            # put all of the story flowables in a list that will be kept together if possible
            storyBlock = []
            
            # Paragraphs can take HTML so the mark-up characters in the text must be escaped
            storyName = escape ( storyInfo['story']['name'] )

            storyDescription = self.BuildDescription( storyInfo, None, outputActivity )
            
            storyBlock.append(Paragraph( storyName,self.styleName))
            
            #Create a table row for our detail line
            tableData = []
            detailRow = []
            #add some flowables
            detailRow.append("""Scheduled Sprint: {0}""".format(storyInfo['start'].strftime(self.iterationDateFormat)) )

            # if the story has an estimate
            if 'estimate' in storyInfo['story'] :
               # and the estimate is not -1
               if storyInfo['story']['estimate'] != -1 :
                  # add the size
                  detailRow.append("""Size: {0}""".format( storyInfo['story']['estimate'] ))
               else:
                  # if the estimate is -1 it is unestimated
                  detailRow.append("Unestimated" )
            else:
               # if there is no estimate, put the story type
               detailRow.append( storyInfo['story']['story_type'].capitalize() )

            tableData.append ( detailRow )
            
            table = Table(tableData, colWidths=[3.5*inch,3.5*inch] )  
                     
            table.setStyle( self.detailTableStyle )
            
            storyBlock.append(table)
               
            storyBlock.append(Spacer(0,self.intraStorySpace))
            
            for paragraph in storyDescription:
               storyBlock.append( paragraph )
               
            flowables.append( KeepTogether ( storyBlock ) )
               
            flowables.append(Spacer(0,self.interStorySpace))
         
         # Add a page break before the next section
         flowables.append( PageBreak() )
      
      #Add the Ice Box Stories
      iceboxStories = self.GetIceboxStories( stories, apiToken, projectId )
                  
      if len( iceboxStories ) > 0 :
      
         flowables.append( Paragraph ( 'Unscheduled Work', self.styleSectionTitle ) )
         flowables.append( Spacer(0, self.titleSpace) )
         
         for storyInfo in iceboxStories :
            
            # put all of the story flowables in a list that will be kept together if possible
            storyBlock = []
            
            # Paragraphs can take HTML so the mark-up characters in the text must be escaped
            storyName = escape ( storyInfo['story']['name'] )

            storyDescription = self.BuildDescription( storyInfo, None, outputActivity )
            
            storyBlock.append(Paragraph( storyName,self.styleName))
            
            #Create a table row for our detail line
            tableData = []
            detailRow = []
            #add some flowables
            detailRow.append("In the Ice Box" )

            # if the story has an estimate
            if 'estimate' in storyInfo['story'] :
               # and the estimate is not -1
               if storyInfo['story']['estimate'] != -1 :
                  # add the size
                  detailRow.append("""Size: {0}""".format( storyInfo['story']['estimate'] ))
               else:
                  # if the estimate is -1 it is unestimated
                  detailRow.append("Unestimated" )
            else:
               # if there is no estimate, put the story type
               detailRow.append( storyInfo['story']['story_type'].capitalize() )
            
            tableData.append ( detailRow )
            
            table = Table(tableData, colWidths=[3.5*inch,3.5*inch] )  
            
            table.setStyle( self.detailTableStyle )
            
            storyBlock.append(table)
               
            storyBlock.append(Spacer(0,self.intraStorySpace))
            
            for paragraph in storyDescription:
               storyBlock.append( paragraph )
               
            flowables.append( KeepTogether ( storyBlock ) )
               
            flowables.append(Spacer(0,self.interStorySpace))
      
      try :
         doc.build(flowables, onFirstPage = self.pageFooter, onLaterPages = self.pageFooter )
      except LayoutError as exception:
         nameMatch = re.search(r"""('[^']*')""", str(exception), re.M)
                  
         if nameMatch != None :
            template_values = {'storyName': nameMatch.group(0) }
         else :
            template_values = {}
               
         path = os.path.join(os.path.dirname(__file__), 'error.html')
         httpResponse.headers['Content-Type'] = 'html'
         httpResponse.out.write(template.render(path, template_values))

   def BuildDescription (self, storyInfo, storyAcceptanceInfo, outputActivity ) :
   
         rawDescription = []
         
         # if a description was retrieved then get it out.
         if 'description' in storyInfo['story'] :
            rawDescription.append (storyInfo['story']['description'])
         else :
            rawDescription.append ( '' )

         notes = []

         # if we're to output the activity notes
         if outputActivity == "checked='true'" :
            
            # Add activity and acceptance notes            
            notes = self.GetActivityNotes ( storyInfo, storyAcceptanceInfo)
            
         # if we have notes to add then add a header followed by the notes
         if len(notes) > 0 :
            rawDescription.append('\n')
            rawDescription.append('**Activity:**')
            
            for note in notes :
               rawDescription.append( note )
            
         # Concatenate the story description with the activity notes
         description = '\n'.join(rawDescription )
        
         # Need to separate out each paragraph in the story. The Paragraph flowable will remove all 
         # whitespace around end of line characters.
         paragraphMatches = re.finditer(r"""(^.*$)""", description, re.M)
         storyDescription = []
                  
         headerExpression = re.compile(ur'(?:(?:(?<=[\s^,(])|(?<=^))#{1}(?=[\w|\d])(?!#)(?P<H1>.+?)(?<=$)|(?:(?<=[\s^,(])|(?<=^))#{2}(?=[\w|\d])(?!#)(?P<H2>.+?)(?<=$)|(?:(?<=[\s^,(])|(?<=^))#{3}(?=[\w|\d])(?!#)(?P<H3>.+?)(?<=$))', re.MULTILINE)
         
         # Add each paragraph to a list of paragraph flowables that are then added to the table
         for paragraphMatch in paragraphMatches :
                  
            isHeader = False
            
            # Look for headers the text
            headerMatches = re.finditer( headerExpression, paragraphMatch.group(0) )

            # If this paragraph is a header style it appropriately
            for header in headerMatches :
              try:
                 if header.lastgroup == 'H1' :
                    storyDescription.append ( Paragraph ( header.groupdict()['H1'] , self.styleH1 ))
                    isHeader = True
                 elif header.lastgroup == 'H2' :
                    storyDescription.append ( Paragraph ( header.groupdict()['H2'] , self.styleH2 ))
                    isHeader = True
                 elif header.lastgroup == 'H3' :
                    storyDescription.append ( Paragraph ( header.groupdict()['H3'] , self.styleH3 ))
                    isHeader = True
              except ValueError as exception :
                storyDescription.append ( Paragraph( """An error was encountered interpreting the header for this story.""", self.styleNormal ))
                logging.error( "A ValueError occured while interpreing the header of a story. \n Header type: " + header.lastgroup + "\n Args: " + str(exception.args))
              
            if isHeader == False :
               storyDescription.append( Paragraph( self.MarkDownToMarkUp ( paragraphMatch.group(0) ), self.styleNormal ) )
         
         return storyDescription
      
   def GetActivityNotes (self, storyInfo, storyAcceptanceInfo ) :
         
         notes = []
         
         if 'notes' in storyInfo['story'] :
            
            # Get the set of Activity notes for the story
            for note in storyInfo['story']['notes'] :
               # ensure the note has the attributes we need for output
               if not 'author' in note :
                  note['author'] = 'Unknown'
               if not 'noted_at' in note :
                  note['noted_at'] = 'Unknown'
                  
               try:
                  notes.append(u"""**{1} - _{0}_** : {2}""".format(note['author'], note['noted_at'].strftime(self.activityDateFormat), note['text']))
               except Exception as e:
                  notes.append("""**{1} - _{0}_** : NOTE SKIPPED due to an exception interpreting the text: {1}""".format(note['author'], note['noted_at'].strftime(self.activityDateFormat), e ))

         if storyAcceptanceInfo != None :
            notes.append("""**{1} - _{0}_** : Accepted the story""".format(storyAcceptanceInfo['acceptorName'], storyAcceptanceInfo['acceptedDate'].strftime(self.activityDateFormat) ))
            
         return notes
   
   def GetDoneStories (self, filteredStories, apiToken, projectId) :
   
      doneStories = []
        
      try :
         # Get the set of done iterations
         client = PivotalClient(token=apiToken, cache=None)
         project = client.iterations.done( projectId )
      except httplib.HTTPException as exception :
         logging.error ("An HTTPException occurred in GetDoneStories.\nArgs: " + str( exception.args ))
         return doneStories
      
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
        
      try:
         # Get the current iteration
         client = PivotalClient(token=apiToken, cache=None)
         project = client.iterations.current( projectId )
      except httplib.HTTPException as exception :
         logging.error ("An HTTPException occurred in GetCurrentStories.\nArgs: " + str( exception.args ))
         return currentStories

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
        
      try:
         # Get the set of future iterations
         client = PivotalClient(token=apiToken, cache=None)
         project = client.iterations.backlog( projectId )
      except httplib.HTTPException as exception :
         logging.error ("An HTTPException occurred in GetFutureStories.\nArgs: " + str( exception.args ))
         return futureStories
      
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
        
      try:
         # Get the set of icebox stories
         client = PivotalClient(token=apiToken, cache=None)
         stories = client.stories.get_filter(projectId, 'state:unscheduled', True )['stories']
      except httplib.HTTPException as exception :
         logging.error ("An HTTPException occurred in GetIceboxStories.\nArgs: " + str( exception.args ))
         return iceboxStories
            
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
            markedUpStrings.append ( u"""<b>{0}</b>""".format( innerMarkUp ) )
         
         if match.group('italicized') != None :
            innerMarkUp = self.MarkDownToMarkUp ( match.group('italicized') )
            markedUpStrings.append ( u"""<i>{0}</i>""".format( innerMarkUp ) )

         regularTextIndex = match.end()

      # add the last bit of regular text from the last match to the end of the string
      markedUpStrings.append ( escape ( markedDownText[ regularTextIndex : len( markedDownText ) ] ) )
      
      return markedUpText.join( markedUpStrings )
      
   def FindMarkedDownText (self, text) :
      # return the MatchObjects containing bold, underlined or bold underline text
      # 
      return re.finditer(r"""(?:(?:(?:(?<=[\s^,(])|(?<=^))\*\*(?=\S)(?P<bold>.+?)(?<=\S)\*\*(?:(?=[\s$,.?!])|(?<=$)))|(?:(?:(?<=[\s^,(])|(?<=^))_(?=\S)(?P<italicized>.+?)(?<=\S)_(?:(?=[\s$,.?!])|(?<=$))))""",text, re.M)
            
   def pageFooter(self, canvas, doc):
      canvas.saveState()
      canvas.setFont( self.footerFontName, self.footerFontSize, self.footerFontLeading )
      
      # draw the doc info
      canvas.drawString ( self.footerLeftEdge, self.footerHeight, self.pageInfo )
       
      # draw the page number
      canvas.drawRightString ( self.footerRightEdge, self.footerHeight, "Page {0}".format (doc.page) )
      canvas.restoreState()       
       
   
   def GetAcceptanceActivity (self, filteredStories, apiToken, projectId) :
   
      acceptanceActivities = {}
        
      # Get the set of done iterations
      client = PivotalClient(token=apiToken, cache=None)
      project = client.projects.activities( projectId, limit=100 )
      
      # if the project has some done iterations
      if 'activities' in project:
         activities = project['activities']

         # Go through each activity and find the acceptance ones on stories that are in our set
         for activity in activities:
            if 'description' in activity :
               # look for accepted in the description and pull out the name in front of it
               acceptorName = re.match(r"""(?P<name>.*)\saccepted""",activity['description'], re.M)
               
               # if we found a name then get the stories affected
               if acceptorName != None :
                  if 'stories' in activity :
                     activityStories = activity['stories']
                     
                     # go through each affected story and see if it's in our list of filtered stories
                     for story in activityStories:
                        for filteredStory in filteredStories: 
                           if str(story['id']) == filteredStory:
                              
                              # if we have this story in our acceptance list already, update it if this activity has a later version id
                              if story['id'] in acceptanceActivities :
                                 if activity['version'] > acceptanceActivities[story['id']]['version'] :
                                    acceptanceActivities[story['id']] = { 'version' : activity['version'], 'acceptorName' : acceptorName.group('name'), 'acceptedDate' : activity['occurred_at'] }
                              else :  
                                 acceptanceActivities[story['id']] = { 'version' : activity['version'], 'acceptorName' : acceptorName.group('name'), 'acceptedDate' : activity['occurred_at'] }
                              break
               
      return acceptanceActivities
       

