# testpdf.py - test PDF generator

import sys
sys.path.insert(0, 'reportlab.zip')
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics

import os
import reportlab
folderFonts = os.path.dirname(reportlab.__file__) + os.sep + 'fonts'

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class Main(webapp.RequestHandler):
   def get(self):
      text = self.request.get('t')
      if text:
         pdfmetrics.registerTypeFace(pdfmetrics.EmbeddedType1Face(
            os.path.join(folderFonts, 'DarkGardenMK.afm'),
            os.path.join(folderFonts, 'DarkGardenMK.pfb')))
         pdfmetrics.registerFont(pdfmetrics.Font(
            'DarkGardenMK', 'DarkGardenMK', 'WinAnsiEncoding'))

         p = canvas.Canvas(self.response.out)
         p.drawImage('dog.jpg', 150, 400)
         p.drawString(50, 700, 'The text you entered: ' + text)
         p.setFont('DarkGardenMK', 16)
         p.drawString(50, 600, 'DarkGarden font loaded from reportlab.zip')
         p.showPage()

         self.response.headers['Content-Type'] = 'application/pdf'
         self.response.headers['Content-Disposition'] = 'filename=testpdf.pdf'

         p.save()
      else:
         self.response.out.write(template.render('testpdf.html', {}))

application = webapp.WSGIApplication([('/testpdf', Main)], debug=True)

def main():
   run_wsgi_app(application)

if __name__ == "__main__":
    main()
