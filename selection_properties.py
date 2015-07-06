class SelectionProperties( object ) :
   def __init__ (self):
      # initialize the class properties
      self.apiKey = None
      self.projectId = None
      self.filter = u''     
      self._featuresChecked = "checked='true'"
      self._bugsChecked = "checked='true'"
      self._choresChecked = "checked='true'"
      self._releasesChecked = ""
      self.selectedLabel = ""
      self.labelFilter = ""
      self.labels = {}
      self.outputActivityChecked = "checked='true'"

   '''Features Checked'''
   @property
   def featuresChecked (self):
      return self._featuresChecked
   
   @featuresChecked.setter
   def featuresChecked (self, value ):
      if value != '' :
         self._featuresChecked = "checked='true'"
      else :
         self._featuresChecked = ''
         
   @featuresChecked.deleter
   def featuresChecked (self):
      del self._featuresChecked
      
   '''Bugs Checked'''
   @property
   def bugsChecked (self):
      return self._bugsChecked
   
   @bugsChecked.setter
   def bugsChecked (self, value ):
      if value != '' :
         self._bugsChecked = "checked='true'"
      else :
         self._bugsChecked = ''
         
   @bugsChecked.deleter
   def bugsChecked (self):
      del self._bugsChecked
      
   '''Chores Checked'''
   @property
   def choresChecked (self):
      return self._choresChecked
   
   @choresChecked.setter
   def choresChecked (self, value ):
      if value != '' :
         self._choresChecked = "checked='true'"
      else :
         self._choresChecked = ''
         
   @choresChecked.deleter
   def choresChecked (self):
      del self._choresChecked

   '''Releases Checked'''
   @property
   def releasesChecked (self):
      return self._releasesChecked
   
   @releasesChecked.setter
   def releasesChecked (self, value ):
      if value != '' :
         self._releasesChecked = "checked='true'"
      else :
         self._releasesChecked = ''
         
   @releasesChecked.deleter
   def releasesChecked (self):
      del self._releasesChecked