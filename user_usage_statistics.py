import logging
from google.appengine.ext import ndb

def user_usage_stats_key( api_key ):
   return ndb.Key('UserUsageStatistics', api_key)

class UserUsageStatistics (ndb.Model):
   first_usage_date = ndb.DateTimeProperty( auto_now_add = True )
   last_usage_date = ndb.DateTimeProperty( auto_now = True )
   full_document_count = ndb.IntegerProperty()
   summary_document_count = ndb.IntegerProperty()
   page_count = ndb.IntegerProperty()
   document_count_with_features = ndb.IntegerProperty()
   document_count_with_bugs = ndb.IntegerProperty()
   document_count_with_chores = ndb.IntegerProperty()
   document_count_with_releases = ndb.IntegerProperty()
   document_count_with_activities = ndb.IntegerProperty()
   '''the total number of times the Filter button was pushed'''
   total_filter_request_count = ndb.IntegerProperty()
   '''the total number of times a label was used to filter'''
   label_filter_count = ndb.IntegerProperty()
   '''the total number of times the keyword search was used'''
   total_keyword_search_count = ndb.IntegerProperty()
   '''the total number of times individual stories were selected from the list box'''
   stories_selected_count = ndb.IntegerProperty()
   project_count_at_last_use = ndb.IntegerProperty()
   '''total number of stories documented
   average stories per document can be computed from story_count'''
   story_count = ndb.IntegerProperty()
   
