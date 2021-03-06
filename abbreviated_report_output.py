import os
import sys
sys.path.insert(0, 'reportlab.zip')
import re
import wsgiref.handlers
import time
import datetime
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
from pivotal_api_v5 import PivotalClient


class AbbreviatedReportOutput():

   PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
   styles = getSampleStyleSheet()
   iterationDateFormat = "%B %d, %Y"
   iso8601DateFormat = "%Y-%m-%dT%H:%M:%SZ"
   generatedDateFormat = "%A %B %d, %Y"
   activityDateFormat = "%b %d, %Y"
   fileNameDateTimeFormat = "%Y%m%d%H%M%S"
   titleSpace = 0.25*inch
   interStorySpace = 0.25*inch
   intraStorySpace = 0.125*inch
   pageInfo = "Agile Docs"

   styleDocTitle = ParagraphStyle( name='DocumentTitle',
                                 fontName='Helvetica-Bold',
                                 fontSize=22,
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
                                 fontSize=16,
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
                                 fontSize=11,
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

   notesTableStyle = TableStyle([
                           ('FONT',(0,0),(-1,0),'Helvetica-Oblique'),         #Set all of the text to be italized helvetica
                           ('FONTSIZE',(0,0),(-1,0),10),                      #Set all text to be font size 12
                           ('TEXTCOLOR',(0,0),(-1,0),colors.black),           #Set all text to be black
                           ('ALIGNMENT',(0,0),(0,0),'LEFT'),                  #Left align the left column
                           ('ALIGNMENT',(1,0),(1,0),'CENTER'),                #Center the middle column
                           ('ALIGNMENT',(-1,0),(-1,0),'RIGHT')                  #Right align the right column
                           ])

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
      projectName = escape( client.projects.get( projectId )['name'] )

      # Set the http headers
      httpResponse.headers['Content-Type'] = 'application/pdf'
      httpResponse.headers['Pragma'] = 'private'
      httpResponse.headers['Cache-Control'] = 'maxage=1'
      httpResponse.headers['Content-Disposition'] = """inline; filename='{0}'""".format(filename)
      httpResponse.headers['Accept-Ranges'] = 'bytes'
      httpResponse.headers['Expires'] = '0'
      httpResponse.headers.add_header("Access-Control-Allow-Origin", "*")

      doc = SimpleDocTemplate( httpResponse.out, pagesize = letter, allowSplitting=1, title=u"""{0} User Stories""".format( projectName ), author='Agile Docs (http://pivotal-pdf.appspot.com)', leftMargin=0.75*inch, rightMargin=0.75*inch)

      #Create a list of flowables for the document
      flowables = []

      #Add a Document Title
      flowables.append( Paragraph ( projectName, self.styleDocTitle ) )
      flowables.append( Spacer(0, self.titleSpace) )

      tableData = []
      detailRow = []

      detailRow.append( 'Story Summaries' )
      detailRow.append( """As of: {0}""".format(time.strftime(self.generatedDateFormat)))
      tableData.append( detailRow )
      table = Table(tableData, colWidths=[3.5*inch,3.5*inch] )

      table.setStyle( self.detailTableStyle )

      flowables.append(table)
      flowables.append(Spacer(0,self.intraStorySpace))

      #Add the Done Stories
      doneStories = self.GetDoneStories( stories, apiToken, projectId )

      if len( doneStories ) > 0 :

         flowables.append( Paragraph ( 'Completed Work', self.styleSectionTitle ) )
         flowables.append( Spacer(0, self.titleSpace) )

         for storyInfo in doneStories :

            # put all of the story flowables in a list that will be kept together if possible
            storyBlock = []

            # Paragraphs can take HTML so the mark-up characters in the text must be escaped
            storyName = escape ( storyInfo['story']['name'] )

            storyDescription = self.BuildDescription( storyInfo )

            storyBlock.append(Paragraph( storyName,self.styleName))

            #Create a table row for our detail line
            tableData = []
            detailRow = []

            #add some flowables
            if 'accepted_at' in storyInfo['story'] :
               detailRow.append("""Accepted: {0}""".format(datetime.datetime.strptime( storyInfo['story']['accepted_at'], self.iso8601DateFormat ).strftime(self.iterationDateFormat)) )
            else :
               detailRow.append("""Accepted""")

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

            storyDescription = self.BuildDescription( storyInfo )

            storyBlock.append(Paragraph( storyName,self.styleName))

            #Create a table row for our detail line
            tableData = []
            detailRow = []
            #add some flowables
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

            storyDescription = self.BuildDescription( storyInfo )

            storyBlock.append(Paragraph( storyName,self.styleName))

            #Create a table row for our detail line
            tableData = []
            detailRow = []
            #add some flowables
            detailRow.append("""Scheduled Sprint: {0}""".format(datetime.datetime.strptime( storyInfo['start'], self.iso8601DateFormat ).strftime(self.iterationDateFormat)) )

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

            storyDescription = self.BuildDescription( storyInfo )

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
         httpResponse.headers.add_header("Access-Control-Allow-Origin", "*")
         httpResponse.out.write(template.render(path, template_values))

   def BuildDescription (self, storyInfo ) :

         # if a description was retrieved then get it out.
         if 'description' in storyInfo['story'] :
            description = storyInfo['story']['description']
         else :
            description = ''

         # Only want the first paragraph of the story, so separate out the paragraphs
         paragraphMatch = re.match(r"""(^.*$)""", description, re.M)
         storyDescription = []

         # Add first paragraph to a list of paragraph flowables that are then added to the table
         storyDescription.append( Paragraph( self.MarkDownToMarkUp ( paragraphMatch.group(0) ), self.styleNormal ) )

         return storyDescription

   def GetDoneStories (self, filteredStories, apiToken, projectId) :

      doneStories = []

      try :
         # Get the set of done iterations
         client = PivotalClient(token=apiToken, cache=None)
         iterations = client.iterations.done( projectId )
      except httplib.HTTPException as exception :
         logging.error ("An HTTPException occurred in GetDoneStories.\nArgs: " + str( exception.args ))
         return doneStories

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

      try :
         # Get the current iteration
         client = PivotalClient(token=apiToken, cache=None)
         iterations = client.iterations.current( projectId )
      except httplib.HTTPException as exception :
         logging.error ("An HTTPException occurred in GetCurrentStories.\nArgs: " + str( exception.args ))
         return currentStories

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

      try :
         # Get the set of future iterations
         client = PivotalClient(token=apiToken, cache=None)
         iterations = client.iterations.backlog( projectId )
      except httplib.HTTPException as exception :
         logging.error ("An HTTPException occurred in GetFutureStories.\nArgs: " + str( exception.args ))
         return futureStories

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

      try :
         # Get the set of icebox stories
         client = PivotalClient(token=apiToken, cache=None)
         stories = client.stories.get_filter(projectId, 'state:unscheduled', True )
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
            markedUpStrings.append ( """<b>{0}</b>""".format( innerMarkUp ) )

         if match.group('italicized') != None :
            innerMarkUp = self.MarkDownToMarkUp ( match.group('italicized') )
            markedUpStrings.append ( """<i>{0}</i>""".format( innerMarkUp ) )

         if match.group('italicized2') != None :
            innerMarkUp = self.MarkDownToMarkUp ( match.group('italicized2') )
            markedUpStrings.append ( u"""<i>{0}</i>""".format( innerMarkUp ) )

         regularTextIndex = match.end()

      # add the last bit of regular text from the last match to the end of the string
      markedUpStrings.append ( escape ( markedDownText[ regularTextIndex : len( markedDownText ) ] ) )

      return markedUpText.join( markedUpStrings )

   def FindMarkedDownText (self, text) :
      # return the MatchObjects containing bold, underlined or bold underline text
      return re.finditer(r"""(?:(?:(?:(?<=[\s^,(])|(?<=^))\*\*(?=\S)(?P<bold>.+?)(?<=\S)\*\*(?:(?=[\s$,.?!])|(?<=$)))|(?:(?:(?<=[\s^,(])|(?<=^))_(?=\S)(?P<italicized>.+?)(?<=\S)_(?:(?=[\s$,.?!])|(?<=$)))|(?:(?:(?<=[\s^,(])|(?<=^))\*(?=\S)(?P<italicized2>.+?)(?<=\S)\*(?:(?=[\s$,.?!])|(?<=$))))""",text, re.M)


   def pageFooter(self, canvas, doc):
      canvas.saveState()
      canvas.setFont( self.footerFontName, self.footerFontSize, self.footerFontLeading )

      # draw the doc info
      canvas.drawString ( self.footerLeftEdge, self.footerHeight, self.pageInfo )

      # draw the page number
      canvas.drawRightString ( self.footerRightEdge, self.footerHeight, "Page {0}".format (doc.page) )
      canvas.restoreState()
