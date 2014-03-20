// JSONTree 
//
// Heavily restructured version of: https://github.com/lmenezes/json-tree
// That that code had some issues with "JSONTree.create".  I changed it to just
// use plain functions.

var JSONTree = function() {

function createNodes(data) {
	return divNode(jsValue(data), {'class': 'json-content'});
}

var id = 0;

var newId = function() {
	id += 1;
	return id;
}

var escapeMap = {
  '&': '&amp;',
	'<': '&lt;',
	'>': '&gt;',
	'"': '&quot;',
	"'": '&#x27;',
  '/': '&#x2F;'
};

var escape = function(text) {
  return text.replace(/[&<>'"]/g, function(t) {
    return escapeMap[t];
  });
}

var divNode = function(text, attrs) {
  return htmlNode('div', text, attrs);
}

var spanNode = function(text, attrs) {
  return htmlNode('span', text, attrs);
}

var htmlNode = function(type, text, attrs) {
  var html = '<' + type;
  if (attrs != null) {
    Object.keys(attrs).forEach(function(attr) {
      html += ' ' + attr + '=\"' + attrs[attr] + '\"';
    });
  }
  html += '>' + text + '</' + type + '>';
  return html;
}

/* icon for collapsing/expanding a json object/array */
var collapseIcon = function(id) {
	var attrs = {'onclick': "JSONTree.toggleVisible('collapse_json" + id + "')" };
	return spanNode(collapse_icon, attrs);
}

/* a json value might be a string, number, boolean, object or an array of other values */
var jsValue = function(value) {
	if (value == null) {
		return jsText("null","null");
	}
	var type = typeof value;
	if (type === 'boolean' || type === 'number') {
		return jsText(type,value);
	} else if (type === 'string') {
		return jsText(type,'"' + escape(value) + '"');
	} else {
		var elementId = newId();
		return value instanceof Array ? jsArray(elementId, value) : jsObject(elementId, value);
	}
}

/* json object is made of property names and jsonValues */
var jsObject = function(id, data) {
	var object_content = "{" + collapseIcon(id);;
	var object_properties = '';
	Object.keys(data).forEach(function(name, position, names) {
		if (position == names.length - 1) { // dont add the comma
			object_properties += divNode(jsProperty(name, data[name]));
		} else {
			object_properties += divNode(jsProperty(name, data[name]) + ',');
		}			
	});
	object_content += divNode(object_properties, {'class': 'json-visible json-object', 'id': "collapse_json" + id});
	return object_content += "}";
}

/* a json property, name + value pair */
var jsProperty = function(name, value) {
	return spanNode('"' + escape(name) + '"', {'class': 'json-property'}) + " : " + jsValue(value);
}

/* array of jsonValues */
var jsArray = function(id, data) {
	var array_content = "[" + collapseIcon(id);;
	var values = '';
	for (var i = 0; i < data.length; i++) {
		if (i == data.length - 1) {
			values += divNode(jsValue(data[i]));
		} else {
			values += divNode(jsValue(data[i]) + ',');
		}
	}
	array_content += divNode(values, {'class':'json-visible json-object', 'id': 'collapse_json' + id});
	return array_content += "]";
}

/* simple value(string, boolean, number...) */
var jsText = function(type, value) {
	return spanNode(value, {'class': "json-" + type});
}

var toggleVisible = function(id) {
	var element = document.getElementById(id);
	var element_class = element.className;
	var classes = element_class.split(" ");
	var visible = false;
	for (var i = 0; i < classes.length; i++) {
		if (classes[i] === "json-visible") {
			visible = true;
			break;
		}
	}
	element.className = visible ? "json-collapsed json-object" : "json-object json-visible";
	element.previousSibling.innerHTML = visible ? expand_icon : collapse_icon;
}

var configure = function(collapse_icon,expand_icon) {
	JSONTree.collapse_icon = collapse_icon;
	JSONTree.expand_icon = expand_icon;
}

var collapse_icon = spanNode('', {'class' : 'json-object-collapse'});

var expand_icon = spanNode('', {'class' : 'json-object-expand'});

// do an XHR for the JSON, and render it.
var getAndRender = function(jsonUrl, elem) {
  var r = new XMLHttpRequest();
  r.open("GET", jsonUrl, true);
  r.onreadystatechange = function () {
    if (r.readyState != 4 || r.status != 200) {
      return;
    }

    //alert("Success: " + r.responseText);
    console.log('success')

    // TODO: catch SyntaxError.  JSONP might not be valid -- we might want to
    // find the first { or [?
    var data = JSON.parse(r.responseText);

    // "content" matches the ID we genreated in the shell script
    elem.innerHTML = JSONTree.createNodes(data);
  };
  r.send();
}

// Public functions

return {
  createNodes: createNodes,
  toggleVisible: toggleVisible,
  getAndRender: getAndRender
};

}();

