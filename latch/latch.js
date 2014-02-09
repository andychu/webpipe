// Continuously get from a latch.  Depends on jQuery.

function waitForLatch() {
  //$('#latch-status').text("Waiting for change");

  var url = '/HOST/latch/default';

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

waitForLatch();
