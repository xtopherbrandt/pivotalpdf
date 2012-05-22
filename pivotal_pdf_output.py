import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.tables import Table, TableStyle, CellStyle, LongTable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib import colors
    
class OutputPDF:

   PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
   styles = getSampleStyleSheet()

   def get(self, requestHandler, stories):
      requestHandler.response.headers['Content-Type'] = 'application/pdf'
      doc = SimpleDocTemplate(requestHandler.response.out,pagesize = letter)
      styles = getSampleStyleSheet()
      styleN = styles['Normal']
      styleH = styles['Heading1']
            
      #Create a list of flowables for the document
      flowables = []
      
      #Create a list for our rows, this will be a list of lists or an array which makes up the table
      tableData = []      
      
      #Create a row for our stories
      storyRow = []
      #add some flowables
      storyRow.append(Paragraph("Story",styleH))
      storyRow.append(Paragraph("Iteration Start",styleH))
      storyRow.append(Paragraph("Iteration End",styleH))
      storyRow.append(Paragraph("Description", styleH))
      tableData.append(storyRow)
      for story in stories :
         
         storyRow = []
         storyRow.append(Paragraph(story['name'],styleH))
         storyRow.append(Paragraph("",styleN))
         storyRow.append(Paragraph("",styleN))
         storyRow.append(Paragraph(story['description'],styleN))
         tableData.append(storyRow)

      table = LongTable(tableData)  
      
      table.setStyle(TableStyle([
                        ('BACKGROUND',(0,0),(-1,0),colors.grey),  #Give the header row a grey background
                        ('TEXTCOLOR',(0,0),(-1,0),colors.white),  #Give the header row white text
                        ('ALIGNMENT',(0,0),(-1,0),'CENTRE'),          #Horizontally align the header row to the center
                        ('VALIGN',(0,0),(-1,0),'MIDDLE'),         #Vertically align the header row in the middle
                        ('TEXTCOLOR',(0,1),(-1,-2),colors.black), #Make the rest of the text white
                        ('VALIGN',(0,1),(-1,-1),'TOP'),           #Make the rest of the cells vertically aligned to the top
                        ('ALIGN',(0,1),(-1,-2),'LEFT'),          #Generally align everything to the right
                        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                        ]))
                              
      flowables.append( table )
      doc.build(flowables)

               
#application = webapp.WSGIApplication([('/helloworld', MainPage)], debug=True)

#def main():
#    application = webapp.WSGIApplication([('/helloworld', MainPage)], debug=True)
#    wsgiref.handlers.CGIHandler().run(application)

#if __name__ == "__main__":
#    main()
