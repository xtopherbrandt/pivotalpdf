import time
import datetime
from poster.encode import multipart_encode
from poster.encode import MultipartParam
from dateutil import parser
import httplib2
import urllib
import json
import logging

def error_from_response(http_response, error_class,
                        response_body=None, parsed_body=None):
   error = error_class('%s: %i, %s' % (http_response.reason, http_response.status,
                                        parsed_body if parsed_body else response_body))
   error.status = http_response.status
   error.reason = http_response.reason
   error.body = response_body
   error.parsed_body = parsed_body
   error.headers = http_response.items()
   return error


class Error(Exception):
   pass


class RequestError(Error):
   """Base http exception"""
   status = None
   reason = None
   body = None
   headers = None
   parsed_body = None


class UnauthorizedError(RequestError):
   """Unauthorized exception"""

_tzmap = None
def get_tzmap():
   global _tzmap
   if _tzmap is None:
      _tzmap = {}
      tzmap_file = pkg_resources.resource_string('busyflow.pivotal', 'tzmap.txt')
      for line in tzmap_file.splitlines():
          [short_name, long_name, offset] = line.split('\t')
          _tzmap[short_name] = offset
   return _tzmap

def parse_string_to_dt(value):
   try:
      time_tuple = time.strptime(value, '%Y/%m/%d %H:%M:%S %Z')
   except ValueError:
      try:
         parts = value.split(' ')
         dt = ' '.join(parts[:-1])
         tz = parts[-1]
         offset = get_tzmap().get(tz, '')
         time_tuple = parser.parse(dt + ' ' + offset).utctimetuple()
      except ValueError:
         time_tuple = time.strptime(dt, '%Y/%m/%d %H:%M:%S')
   return datetime.datetime(
      time_tuple.tm_year,
      time_tuple.tm_mon,
      time_tuple.tm_mday,
      time_tuple.tm_hour,
      time_tuple.tm_min,
      time_tuple.tm_sec)

class Endpoint(object):
   def __init__(self, pivotal):
      self.pivotal = pivotal

   def _get(self, endpoint, **params):
      return self.pivotal._apicall(endpoint, 'GET', **params)

   def _post(self, endpoint, **params):
      return self.pivotal._apicall(endpoint, 'POST', **params)

   def _put(self, endpoint, **params):
      return self.pivotal._apicall(endpoint, 'PUT', **params)

   def _delete(self, endpoint, **params):
      return self.pivotal._apicall(endpoint, 'DELETE', **params)


class ProjectEndpoint(Endpoint):

   def get(self, project_id):
      return self._get("projects/%s" % project_id)

   def all(self):
      return self._get("projects")

   def activity(self, project_id, limit=None, occurred_since_date=None, newer_than_version=None):
      return self._get("projects/%s/activity" % project_id, limit=str(limit),
                      occurred_since_date=occurred_since_date,
                      newer_than_version=str(newer_than_version))



class IterationEndpoint(Endpoint):

   def all(self, project_id, limit=None, offset=None):
      return self._get("projects/%s/iterations" % project_id, limit=limit, offset=offset)

   def done(self, project_id, limit=None, offset=None):
      return self._get("projects/%s/iterations/done" % project_id, limit=limit, offset=offset)

   def done_filtered(self, project_id, limit=None, offset=None, search_filter=None):
      return self._get("projects/%s/iterations/done" % project_id, limit=limit, offset=offset, filter=search_filter)

   def current(self, project_id, limit=None, offset=None):
      return self._get("projects/%s/iterations/current" % project_id, limit=limit, offset=offset)

   def backlog(self, project_id, limit=None, offset=None):
      return self._get("projects/%s/iterations/backlog" % project_id, limit=limit, offset=offset)

   def current_backlog(self, project_id, limit=None, offset=None):
      return self._get("projects/%s/iterations/current_backlog" % project_id, limit=limit, offset=offset)

class ActivityEndpoint(Endpoint):

   def all(self, limit=None, occurred_since_date=None, newer_than_version=None):
      return self._get("activities", limit=limit,
                         occurred_since_date=occurred_since_date,
                         newer_than_version=newer_than_version)

class StoryEndpoint(Endpoint):

   def all(self, project_id, query=None, limit=None, offset=None):
      return self._get("projects/%s/stories" % project_id, query=query, limit=limit, offset=offset)

   def get(self, project_id, story_id):
      return self._get("projects/%s/stories/%s" % (project_id, story_id))

   def get_filter(self, project_id, search_filter, include_done):
      if include_done:
         filter_text = u"{0} includedone:true".format( search_filter )
      else :
         filter_text = search_filter
            
      return self._get("projects/{0}/stories".format( project_id ), filter=filter_text )
               

class EpicEndpoint(Endpoint):

   def all(self, project_id, query=None, limit=None, offset=None):
      return self._get("projects/%s/epics" % project_id, query=query, limit=limit, offset=offset)

   def get(self, project_id, epic_id):
      return self._get("projects/%s/epics/%s" % (project_id, epic_id))

   def get_filter(self, project_id, search_filter, include_done):
      if include_done:
         filter_text = u"{0} includedone:true".format( search_filter )
      else :
         filter_text = search_filter
            
      return self._get("projects/{0}/epics".format( project_id ), filter=filter_text )
        
        

class PivotalClient(object):

   def __init__(self, token,
                 base_url="https://www.pivotaltracker.com/services/v5/",
                 parse_xml=True, cache=None, timeout=None, proxy_info=None):
      self.token = token
      self.base_url = base_url
      self.parse_xml = parse_xml
      self.client = httplib2.Http(cache=cache, timeout=timeout, proxy_info=proxy_info)

      # connect endpoints
      self.projects = ProjectEndpoint(self)
      self.stories = StoryEndpoint(self)
      self.epics = EpicEndpoint(self)
      self.activities = ActivityEndpoint(self)
      self.iterations = IterationEndpoint(self)

   def _apicall(self, endpoint, method, **params):
      url = '%s%s' % (self.base_url, endpoint)
      body = params.pop('body', '')
      _headers = params.pop('headers', {})

      cleaned_params = dict([(k, v.encode('utf-8')) for k, v in params.iteritems() if v])

      headers = {'X-TrackerToken': self.token}
      if method in ['POST', 'PUT'] and body:
         headers['Content-type'] = 'application/xml'

      headers.update(_headers)

      if cleaned_params:
         assert not body # can't have body and parameters at the same time
         body = urllib.urlencode(cleaned_params)
         if method == 'GET':
            url = '%s?%s' % (url, body)
            body = ''

      resp, content = self.client.request(url, method=method, body=body, headers=headers)

      try :
         parsed_content = json.loads( content )
      except e :
         logging.error ("An exception occurred attempting to decode the JSON response from Pivotal Tracker")      
         logging.error ( content )
         logging.error ( e )
         
      error_cls = RequestError
      if resp.status == 401:
         error_cls = UnauthorizedError

      if resp.status != 200:
         raise error_from_response(resp, error_cls, content, parsed_content )

      return parsed_content

