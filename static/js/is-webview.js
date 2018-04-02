!function(e){if("object"==typeof exports&&"undefined"!=typeof module)module.exports=e();else if("function"==typeof define&&define.amd)define([],e);else{var f;"undefined"!=typeof window?f=window:"undefined"!=typeof global?f=global:"undefined"!=typeof self&&(f=self),f.isWebview=e()}}(function(){var define,module,exports;return (function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
'use strict';

var userAgentCheck = require('./lib/userAgent.js');
var domCheck = require('./lib/noop.js');
var window = require('global/window');

var hasDOM = typeof domCheck === 'function';

/**
 *
 * @param {String} userAgent
 * @param {=Object} configObject
 */
function isWebView(userAgent, configObject){
  // we can skip everything if we have no DOM to check and no userAgent
  if (!hasDOM && !userAgent){
    return false;
  }

  if (typeof userAgent === 'object'){
    configObject = userAgent;
    userAgent = '';
  }

  configObject = configObject || {};

  // known app name
  if (configObject.appName && userAgentCheck(userAgent, configObject.appName)){
    return true;
  }

  // non-W3C properties injected by wrappers
  if (hasDOM && domCheck(window)){
    return true;
  }

  // Slower User Agent detection
  return userAgentCheck(userAgent);
}

isWebView.getRules = function getRules(){
  return rules;
};

module.exports = isWebView;
},{"./lib/noop.js":2,"./lib/userAgent.js":3,"global/window":4}],2:[function(require,module,exports){
'use strict';

var rules = [
  // webView object exists
  function (w){ return 'webView' in w; },

  // Android object exists
  function (w){ return 'Android' in w; },

  // deviceready event
  function (w){ return w.document && 'ondeviceready' in w.document; },

  // explicitely states it is standalone
  function (w){ return w.navigator && 'standalone' in w.navigator; },

  // can notifiy a parent app
  function (w){ return w.external && 'notify' in w.external; },

  // Ti object exists
  function (w){ return 'Ti' in w; },

  // _cordovaNative object exists
  function (w){ return '_cordovaNative' in w; }

  // served as file (but false positive if a Web page is loaded from the filesystem)
  // function (w){ return w.location.href.indexOf('file:') === 0; }
];

module.exports = function domCheck(window){
  return rules.some(function applyRule(rule){
    return rule(window);
  });
};

},{}],3:[function(require,module,exports){
'use strict';

var rules = [
  // custom app name
  function (userAgent, appName){
    return appName && userAgent.indexOf(appName) !== -1
  },

  // iOS UIWebView
  function (userAgent){
    return userAgent.indexOf(' Mobile/') > 0 && userAgent.indexOf(' Safari/') === -1;
  }
];

module.exports = function userAgentCheck(userAgent, appName){
  userAgent = userAgent || '';

  return rules.some(function applyRule(rule){
    return rule(userAgent, appName);
  });
};
},{}],4:[function(require,module,exports){
(function (global){
if (typeof window !== "undefined") {
    module.exports = window;
} else if (typeof global !== "undefined") {
    module.exports = global;
} else if (typeof self !== "undefined"){
    module.exports = self;
} else {
    module.exports = {};
}

}).call(this,typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : {})
},{}]},{},[1])(1)
});