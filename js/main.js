var main = function() {
   //Enroll button click handler
   $('#filter-btn').click(function()
      {
         $.ajax(
         {
            type: 'POST',
            url: "/filterStories",
            data: 
            {
               features: $('#featuresChecked').val(),
               bugs: $('#bugsChecked').val(),
               chores: $('#choresChecked').val(),
               releases: $('#releasesChecked').val()
            },
            success: function( data ) 
            {
               var stories = JSON.parse(data);
               console.log (stories)
               for ( var story in stories ){
                  console.log (story)
                  $('#stories').children().append( stories[story] );   
               }
               

            }
         });
   });
};

$(document).ready(main);