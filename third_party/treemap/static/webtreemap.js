// webtreemap
//
// NOTES:
// - .css files uses -webkit-transition for animation.  I added -moz-transition
//   too.  Not as smooth, but it works OK.

// Size of border around nodes.
// We could support arbitrary borders using getComputedStyle(), but I am
// skeptical the extra complexity (and performance hit) is worth it.
var kBorderWidth = 1;

// Padding around contents.
// TODO: do this with a nested div to allow it to be CSS-styleable.
var kPadding = 4;

// Position a given DOM node with its left corner at (x, y), and resize it to
// (width, height).
function position(dom, x, y, width, height) {
  // CSS width/height does not include border.
  width -= kBorderWidth*2;
  height -= kBorderWidth*2;

  dom.style.left   = x + 'px';
  dom.style.top    = y + 'px';
  dom.style.width  = Math.max(width, 0) + 'px';
  dom.style.height = Math.max(height, 0) + 'px';
}

// Given a list of rectangles |nodes|, the 1-d space available
// |space|, and a starting rectangle index |start|, compute an span of
// rectangles that optimizes a pleasant aspect ratio.
//
// Returns [end, sum], where end is one past the last rectangle and sum is the
// 2-d sum of the rectangles' areas.
function selectSpan(nodes, space, start) {
  // Add rectangle one by one, stopping when aspect ratios begin to go
  // bad.  Result is [start,end) covering the best run for this span.
  // http://scholar.google.com/scholar?cluster=5972512107845615474
  var node = nodes[start];
  var rmin = node.data['$area'];  // Smallest seen child so far.
  var rmax = rmin;                // Largest child.
  var rsum = 0;                   // Sum of children in this span.
  var last_score = 0;             // Best score yet found.
  for (var end = start; node = nodes[end]; ++end) {
    var size = node.data['$area'];
    if (size < rmin)
      rmin = size;
    if (size > rmax)
      rmax = size;
    rsum += size;

    // This formula is from the paper, but you can easily prove to
    // yourself it's taking the larger of the x/y aspect ratio or the
    // y/x aspect ratio.  The additional magic fudge constant of 5
    // makes us prefer wider rectangles to taller ones.
    var score = Math.max(5*space*space*rmax / (rsum*rsum),
                         1*rsum*rsum / (space*space*rmin));
    if (last_score && score > last_score) {
      rsum -= size;  // Undo size addition from just above.
      break;
    }
    last_score = score;
  }
  return [end, rsum];
}

//
// TreeMap
//

function TreeMap(dom, data, statusNode, options) {
  this.dom = dom;
  this.data = data;
  this.focused = null;
  this.statusNode = statusNode;

  options = options || {};
  // not implemented yet: this is supposed to limit the number of boxes drawn?
  // Not sure how hard that is.  Need to look at zIndex and so forth.
  this.maxLevel = options.maxLevel || 0;  // 0 is no max

  // for getting rid of small boxes
  this.minWidth = options.minWidth || 60;
  this.minHeight = options.minHeight || 40;

  // TODO: this could just be inline.  Or should the caller do it?
  this.appendTreemap(dom, data);
}

// Append a treemap to a DOM node, using data from a JSON tree.
TreeMap.prototype.appendTreemap = function(dom, data) {
  var style = getComputedStyle(dom, null);
  var width = parseInt(style.width);
  var height = parseInt(style.height);
  // Make the root node and add it do the document.
  if (!data.dom)
    this.makeDom(data, 0);
  dom.appendChild(data.dom);

  // Position the outermost div.
  position(data.dom, 0, 0, width, height);

  // Recursively layout the tree.
  this.layout(data, 0, width, height);
  // Show status initially.  TODO: refactor with focus()?
  this.showStatus(data);
}

TreeMap.prototype.showStatus = function(tree) {
  var parts = [];
  var t = tree;
  while (t) {
    parts.push(t.name);
    t = t.parent;
  }
  parts.reverse();
  this.statusNode.innerHTML = parts.join(' / ');
}

// Focus on a given subtree.
//   tree: JSON subtree
TreeMap.prototype.focus = function(tree) {
  this.focused = tree;
  this.showStatus(tree);

  // Hide all visible siblings of all our ancestors by lowering them.
  var level = 0;
  var root = tree;
  while (root.parent) {
    root = root.parent;
    level += 1;
    for (var i = 0, sibling; sibling = root.children[i]; ++i) {
      if (sibling.dom)
        sibling.dom.style.zIndex = 0;
    }
  }
  var width = root.dom.offsetWidth;
  var height = root.dom.offsetHeight;
  // Unhide (raise) and maximize us and our ancestors.
  for (var t = tree; t.parent; t = t.parent) {
    // Shift off by border so we don't get nested borders.
    // TODO: actually make nested borders work (need to adjust width/height).

    position(t.dom, -kBorderWidth, -kBorderWidth, width, height);
    t.dom.style.zIndex = 1;
  }
  // And layout into the topmost box.
  this.layout(tree, level, width, height);
}

// Make a div for a box, and a div for its label.  Attaches it the box to the
// 'dom' property of the subtree.  Each node in the JSON tree is lazily created.
//
// Called from appendTreemap() and layout().  
//
// Args:
//   tree: JSON subtree
//   level: integer depth, 0..
//
// Returns:
//   DOM node representing the box div.

TreeMap.prototype.makeDom = function(tree, level) {
  var dom = document.createElement('div');
  dom.style.zIndex = 1;
  dom.className = 'webtreemap-node webtreemap-level' + Math.min(level, 6);

  // inside the event handler, 'this' is the element, not TreeMap() instance.
  var that = this;

  // Register the click.
  dom.onmousedown = function(e) {
    if (e.button == 0) {  // What does this do?
      if (that.focused && tree == that.focused && that.focused.parent) {
        that.focus(that.focused.parent);  // zoom out
      } else {
        that.focus(tree);  // zoom in
      }
    }
    e.stopPropagation();
    return true;
  };

  var caption = document.createElement('div');
  caption.className = 'webtreemap-caption';
  caption.innerHTML = tree.name;
  dom.appendChild(caption);

  tree.dom = dom;
  return dom;
}

// Layout a JSON subtree.
//
// It should have 'name', '$area', and then a 'children' array of further
// subtrees.
TreeMap.prototype.layout = function(tree, level, width, height) {
  if (!('children' in tree))
    return;

  var total = tree.data['$area'];

  // XXX why do I need an extra -1/-2 here for width/height to look right?
  var x1 = 0, y1 = 0, x2 = width - 1, y2 = height - 2;
  x1 += kPadding; y1 += kPadding;
  x2 -= kPadding; y2 -= kPadding;
  y1 += 14;  // XXX get first child height for caption spacing

  var pixels_to_units = Math.sqrt(total / ((x2 - x1) * (y2 - y1)));

  for (var start = 0, child; child = tree.children[start]; ++start) {
    // AC: I think this is getting rid of small nodes, which speeds things up.
    if (x2 - x1 < this.minWidth || y2 - y1 < this.minHeight) {
      // AC: push it to the back?  We may or may not have a dom node.
      if (child.dom) {
        child.dom.style.zIndex = 0;
        position(child.dom, -2, -2, 0, 0);
      }
      //console.log('Stopping after small dimensions: ' + (x2-x1) + ' ' + (y2-y1));
      continue;
    }

    // In theory we can dynamically decide whether to split in x or y based
    // on aspect ratio.  In practice, changing split direction with this
    // layout doesn't look very good.
    //   var ysplit = (y2 - y1) > (x2 - x1);
    var ysplit = true;

    var space;  // Space available along layout axis.
    if (ysplit)
      space = (y2 - y1) * pixels_to_units;
    else
      space = (x2 - x1) * pixels_to_units;

    var span = selectSpan(tree.children, space, start);
    var end = span[0], rsum = span[1];

    // Now that we've selected a span, lay out rectangles [start,end) in our
    // available space.
    var x = x1, y = y1;
    for (var i = start; i < end; ++i) {
      child = tree.children[i];
      if (!child.dom) {
        child.parent = tree;
        child.dom = this.makeDom(child, level + 1);
        tree.dom.appendChild(child.dom);
      } else {
        child.dom.style.zIndex = 1;
      }
      var size = child.data['$area'];
      var frac = size / rsum;
      if (ysplit) {
        width = rsum / space;
        height = size / width;
      } else {
        height = rsum / space;
        width = size / height;
      }
      width /= pixels_to_units;
      height /= pixels_to_units;
      width = Math.round(width);
      height = Math.round(height);
      position(child.dom, x, y, width, height);
      if ('children' in child) {
        this.layout(child, level + 1, width, height);
      }
      if (ysplit)
        y += height;
      else
        x += width;
    }

    // Shrink our available space based on the amount we used.
    if (ysplit)
      x1 += Math.round((rsum / space) / pixels_to_units);
    else
      y1 += Math.round((rsum / space) / pixels_to_units);

    // end points one past where we ended, which is where we want to
    // begin the next iteration, but subtract one to balance the ++ in
    // the loop.
    start = end - 1;
  }
}

// zoom to root
TreeMap.prototype.focusRoot = function() {
  this.focus(this.data);
}

// zoom out
TreeMap.prototype.focusUp = function() {
  var p = this.focused.parent;
  if (p) {
    this.focus(p);
  }
}

