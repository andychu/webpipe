// Copyright 2014 Google Inc. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be found
// in the LICENSE file or at https://developers.google.com/open-source/licenses/bsd

// Continuously get from a latch.  Depends on jQuery.

function waitForLatch(name) {
  //$('#latch-status').text("Waiting for change");

  var url = '/-/latch/' + name;

  // TODO: use raw XHR to get rid of jQuery dependency.
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

function getLatchName(path) {
  // /README.html -> README.html
  // TODO: what about index.html?
  return path.substring(1);
}

// Each document has its own latch.
var latchName = getLatchName(window.location.pathname);
waitForLatch(latchName);

