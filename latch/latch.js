// Continuously get from a latch.  Depends on jQuery.

function waitForLatch(name) {
  //$('#latch-status').text("Waiting for change");

  var url = '/-/latch/' + name;

  $.ajax({
      url: url,
      type: 'GET',
      success: function(data){ 
          $('#latch-status').text("response: " + data);
          location.reload();
      },
      error: function(jqXhr, textStatus, errorThrown) {
        // Show error from the server.
        $('#latch-status').text(
          "error contacting " + url + ": " + jqXhr.responseText);
      }
  });
}

// TODO: get doc name
waitForLatch('README.html');

