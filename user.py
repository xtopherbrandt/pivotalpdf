import logging
from google.appengine.ext import ndb

def user_key( api_key ):
   return ndb.Key('User', api_key)

class User (ndb.Model):
   first_usage_date = ndb.DateTimeProperty( auto_now_add = True )
   last_usage_date = ndb.DateTimeProperty( auto_now = True )
   full_document_count = ndb.IntegerProperty( default = 0 )
   summary_document_count = ndb.IntegerProperty( default = 0 )
   
