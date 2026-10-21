var Xo = { exports: {} }, As = {}, Go = { exports: {} }, H = {};
/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var wl = Symbol.for("react.element"), xd = Symbol.for("react.portal"), yd = Symbol.for("react.fragment"), jd = Symbol.for("react.strict_mode"), Nd = Symbol.for("react.profiler"), wd = Symbol.for("react.provider"), kd = Symbol.for("react.context"), Cd = Symbol.for("react.forward_ref"), Sd = Symbol.for("react.suspense"), bd = Symbol.for("react.memo"), Ed = Symbol.for("react.lazy"), Aa = Symbol.iterator;
function Md(e) {
  return e === null || typeof e != "object" ? null : (e = Aa && e[Aa] || e["@@iterator"], typeof e == "function" ? e : null);
}
var Jo = { isMounted: function() {
  return !1;
}, enqueueForceUpdate: function() {
}, enqueueReplaceState: function() {
}, enqueueSetState: function() {
} }, Zo = Object.assign, _o = {};
function Rn(e, t, n) {
  this.props = e, this.context = t, this.refs = _o, this.updater = n || Jo;
}
Rn.prototype.isReactComponent = {};
Rn.prototype.setState = function(e, t) {
  if (typeof e != "object" && typeof e != "function" && e != null) throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
  this.updater.enqueueSetState(this, e, t, "setState");
};
Rn.prototype.forceUpdate = function(e) {
  this.updater.enqueueForceUpdate(this, e, "forceUpdate");
};
function $o() {
}
$o.prototype = Rn.prototype;
function wi(e, t, n) {
  this.props = e, this.context = t, this.refs = _o, this.updater = n || Jo;
}
var ki = wi.prototype = new $o();
ki.constructor = wi;
Zo(ki, Rn.prototype);
ki.isPureReactComponent = !0;
var Pa = Array.isArray, eu = Object.prototype.hasOwnProperty, Ci = { current: null }, tu = { key: !0, ref: !0, __self: !0, __source: !0 };
function nu(e, t, n) {
  var s, r = {}, i = null, a = null;
  if (t != null) for (s in t.ref !== void 0 && (a = t.ref), t.key !== void 0 && (i = "" + t.key), t) eu.call(t, s) && !tu.hasOwnProperty(s) && (r[s] = t[s]);
  var u = arguments.length - 2;
  if (u === 1) r.children = n;
  else if (1 < u) {
    for (var o = Array(u), d = 0; d < u; d++) o[d] = arguments[d + 2];
    r.children = o;
  }
  if (e && e.defaultProps) for (s in u = e.defaultProps, u) r[s] === void 0 && (r[s] = u[s]);
  return { $$typeof: wl, type: e, key: i, ref: a, props: r, _owner: Ci.current };
}
function Ld(e, t) {
  return { $$typeof: wl, type: e.type, key: t, ref: e.ref, props: e.props, _owner: e._owner };
}
function Si(e) {
  return typeof e == "object" && e !== null && e.$$typeof === wl;
}
function Ad(e) {
  var t = { "=": "=0", ":": "=2" };
  return "$" + e.replace(/[=:]/g, function(n) {
    return t[n];
  });
}
var za = /\/+/g;
function Xs(e, t) {
  return typeof e == "object" && e !== null && e.key != null ? Ad("" + e.key) : t.toString(36);
}
function Kl(e, t, n, s, r) {
  var i = typeof e;
  (i === "undefined" || i === "boolean") && (e = null);
  var a = !1;
  if (e === null) a = !0;
  else switch (i) {
    case "string":
    case "number":
      a = !0;
      break;
    case "object":
      switch (e.$$typeof) {
        case wl:
        case xd:
          a = !0;
      }
  }
  if (a) return a = e, r = r(a), e = s === "" ? "." + Xs(a, 0) : s, Pa(r) ? (n = "", e != null && (n = e.replace(za, "$&/") + "/"), Kl(r, t, n, "", function(d) {
    return d;
  })) : r != null && (Si(r) && (r = Ld(r, n + (!r.key || a && a.key === r.key ? "" : ("" + r.key).replace(za, "$&/") + "/") + e)), t.push(r)), 1;
  if (a = 0, s = s === "" ? "." : s + ":", Pa(e)) for (var u = 0; u < e.length; u++) {
    i = e[u];
    var o = s + Xs(i, u);
    a += Kl(i, t, n, o, r);
  }
  else if (o = Md(e), typeof o == "function") for (e = o.call(e), u = 0; !(i = e.next()).done; ) i = i.value, o = s + Xs(i, u++), a += Kl(i, t, n, o, r);
  else if (i === "object") throw t = String(e), Error("Objects are not valid as a React child (found: " + (t === "[object Object]" ? "object with keys {" + Object.keys(e).join(", ") + "}" : t) + "). If you meant to render a collection of children, use an array instead.");
  return a;
}
function El(e, t, n) {
  if (e == null) return e;
  var s = [], r = 0;
  return Kl(e, s, "", "", function(i) {
    return t.call(n, i, r++);
  }), s;
}
function Pd(e) {
  if (e._status === -1) {
    var t = e._result;
    t = t(), t.then(function(n) {
      (e._status === 0 || e._status === -1) && (e._status = 1, e._result = n);
    }, function(n) {
      (e._status === 0 || e._status === -1) && (e._status = 2, e._result = n);
    }), e._status === -1 && (e._status = 0, e._result = t);
  }
  if (e._status === 1) return e._result.default;
  throw e._result;
}
var ye = { current: null }, Xl = { transition: null }, zd = { ReactCurrentDispatcher: ye, ReactCurrentBatchConfig: Xl, ReactCurrentOwner: Ci };
function lu() {
  throw Error("act(...) is not supported in production builds of React.");
}
H.Children = { map: El, forEach: function(e, t, n) {
  El(e, function() {
    t.apply(this, arguments);
  }, n);
}, count: function(e) {
  var t = 0;
  return El(e, function() {
    t++;
  }), t;
}, toArray: function(e) {
  return El(e, function(t) {
    return t;
  }) || [];
}, only: function(e) {
  if (!Si(e)) throw Error("React.Children.only expected to receive a single React element child.");
  return e;
} };
H.Component = Rn;
H.Fragment = yd;
H.Profiler = Nd;
H.PureComponent = wi;
H.StrictMode = jd;
H.Suspense = Sd;
H.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = zd;
H.act = lu;
H.cloneElement = function(e, t, n) {
  if (e == null) throw Error("React.cloneElement(...): The argument must be a React element, but you passed " + e + ".");
  var s = Zo({}, e.props), r = e.key, i = e.ref, a = e._owner;
  if (t != null) {
    if (t.ref !== void 0 && (i = t.ref, a = Ci.current), t.key !== void 0 && (r = "" + t.key), e.type && e.type.defaultProps) var u = e.type.defaultProps;
    for (o in t) eu.call(t, o) && !tu.hasOwnProperty(o) && (s[o] = t[o] === void 0 && u !== void 0 ? u[o] : t[o]);
  }
  var o = arguments.length - 2;
  if (o === 1) s.children = n;
  else if (1 < o) {
    u = Array(o);
    for (var d = 0; d < o; d++) u[d] = arguments[d + 2];
    s.children = u;
  }
  return { $$typeof: wl, type: e.type, key: r, ref: i, props: s, _owner: a };
};
H.createContext = function(e) {
  return e = { $$typeof: kd, _currentValue: e, _currentValue2: e, _threadCount: 0, Provider: null, Consumer: null, _defaultValue: null, _globalName: null }, e.Provider = { $$typeof: wd, _context: e }, e.Consumer = e;
};
H.createElement = nu;
H.createFactory = function(e) {
  var t = nu.bind(null, e);
  return t.type = e, t;
};
H.createRef = function() {
  return { current: null };
};
H.forwardRef = function(e) {
  return { $$typeof: Cd, render: e };
};
H.isValidElement = Si;
H.lazy = function(e) {
  return { $$typeof: Ed, _payload: { _status: -1, _result: e }, _init: Pd };
};
H.memo = function(e, t) {
  return { $$typeof: bd, type: e, compare: t === void 0 ? null : t };
};
H.startTransition = function(e) {
  var t = Xl.transition;
  Xl.transition = {};
  try {
    e();
  } finally {
    Xl.transition = t;
  }
};
H.unstable_act = lu;
H.useCallback = function(e, t) {
  return ye.current.useCallback(e, t);
};
H.useContext = function(e) {
  return ye.current.useContext(e);
};
H.useDebugValue = function() {
};
H.useDeferredValue = function(e) {
  return ye.current.useDeferredValue(e);
};
H.useEffect = function(e, t) {
  return ye.current.useEffect(e, t);
};
H.useId = function() {
  return ye.current.useId();
};
H.useImperativeHandle = function(e, t, n) {
  return ye.current.useImperativeHandle(e, t, n);
};
H.useInsertionEffect = function(e, t) {
  return ye.current.useInsertionEffect(e, t);
};
H.useLayoutEffect = function(e, t) {
  return ye.current.useLayoutEffect(e, t);
};
H.useMemo = function(e, t) {
  return ye.current.useMemo(e, t);
};
H.useReducer = function(e, t, n) {
  return ye.current.useReducer(e, t, n);
};
H.useRef = function(e) {
  return ye.current.useRef(e);
};
H.useState = function(e) {
  return ye.current.useState(e);
};
H.useSyncExternalStore = function(e, t, n) {
  return ye.current.useSyncExternalStore(e, t, n);
};
H.useTransition = function() {
  return ye.current.useTransition();
};
H.version = "18.3.1";
Go.exports = H;
var P = Go.exports;
/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Td = P, Rd = Symbol.for("react.element"), Fd = Symbol.for("react.fragment"), Od = Object.prototype.hasOwnProperty, Dd = Td.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, Id = { key: !0, ref: !0, __self: !0, __source: !0 };
function su(e, t, n) {
  var s, r = {}, i = null, a = null;
  n !== void 0 && (i = "" + n), t.key !== void 0 && (i = "" + t.key), t.ref !== void 0 && (a = t.ref);
  for (s in t) Od.call(t, s) && !Id.hasOwnProperty(s) && (r[s] = t[s]);
  if (e && e.defaultProps) for (s in t = e.defaultProps, t) r[s] === void 0 && (r[s] = t[s]);
  return { $$typeof: Rd, type: e, key: i, ref: a, props: r, _owner: Dd.current };
}
As.Fragment = Fd;
As.jsx = su;
As.jsxs = su;
Xo.exports = As;
var l = Xo.exports, ru = { exports: {} }, Ae = {}, iu = { exports: {} }, au = {};
/**
 * @license React
 * scheduler.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
(function(e) {
  function t(E, T) {
    var b = E.length;
    E.push(T);
    e: for (; 0 < b; ) {
      var B = b - 1 >>> 1, W = E[B];
      if (0 < r(W, T)) E[B] = T, E[b] = W, b = B;
      else break e;
    }
  }
  function n(E) {
    return E.length === 0 ? null : E[0];
  }
  function s(E) {
    if (E.length === 0) return null;
    var T = E[0], b = E.pop();
    if (b !== T) {
      E[0] = b;
      e: for (var B = 0, W = E.length, ae = W >>> 1; B < ae; ) {
        var Xe = 2 * (B + 1) - 1, Dn = E[Xe], Ue = Xe + 1, It = E[Ue];
        if (0 > r(Dn, b)) Ue < W && 0 > r(It, Dn) ? (E[B] = It, E[Ue] = b, B = Ue) : (E[B] = Dn, E[Xe] = b, B = Xe);
        else if (Ue < W && 0 > r(It, b)) E[B] = It, E[Ue] = b, B = Ue;
        else break e;
      }
    }
    return T;
  }
  function r(E, T) {
    var b = E.sortIndex - T.sortIndex;
    return b !== 0 ? b : E.id - T.id;
  }
  if (typeof performance == "object" && typeof performance.now == "function") {
    var i = performance;
    e.unstable_now = function() {
      return i.now();
    };
  } else {
    var a = Date, u = a.now();
    e.unstable_now = function() {
      return a.now() - u;
    };
  }
  var o = [], d = [], m = 1, p = null, v = 3, j = !1, y = !1, C = !1, k = typeof setTimeout == "function" ? setTimeout : null, c = typeof clearTimeout == "function" ? clearTimeout : null, h = typeof setImmediate < "u" ? setImmediate : null;
  typeof navigator < "u" && navigator.scheduling !== void 0 && navigator.scheduling.isInputPending !== void 0 && navigator.scheduling.isInputPending.bind(navigator.scheduling);
  function f(E) {
    for (var T = n(d); T !== null; ) {
      if (T.callback === null) s(d);
      else if (T.startTime <= E) s(d), T.sortIndex = T.expirationTime, t(o, T);
      else break;
      T = n(d);
    }
  }
  function x(E) {
    if (C = !1, f(E), !y) if (n(o) !== null) y = !0, U(N);
    else {
      var T = n(d);
      T !== null && _(x, T.startTime - E);
    }
  }
  function N(E, T) {
    y = !1, C && (C = !1, c(S), S = -1), j = !0;
    var b = v;
    try {
      for (f(T), p = n(o); p !== null && (!(p.expirationTime > T) || E && !D()); ) {
        var B = p.callback;
        if (typeof B == "function") {
          p.callback = null, v = p.priorityLevel;
          var W = B(p.expirationTime <= T);
          T = e.unstable_now(), typeof W == "function" ? p.callback = W : p === n(o) && s(o), f(T);
        } else s(o);
        p = n(o);
      }
      if (p !== null) var ae = !0;
      else {
        var Xe = n(d);
        Xe !== null && _(x, Xe.startTime - T), ae = !1;
      }
      return ae;
    } finally {
      p = null, v = b, j = !1;
    }
  }
  var g = !1, M = null, S = -1, A = 5, w = -1;
  function D() {
    return !(e.unstable_now() - w < A);
  }
  function L() {
    if (M !== null) {
      var E = e.unstable_now();
      w = E;
      var T = !0;
      try {
        T = M(!0, E);
      } finally {
        T ? V() : (g = !1, M = null);
      }
    } else g = !1;
  }
  var V;
  if (typeof h == "function") V = function() {
    h(L);
  };
  else if (typeof MessageChannel < "u") {
    var q = new MessageChannel(), F = q.port2;
    q.port1.onmessage = L, V = function() {
      F.postMessage(null);
    };
  } else V = function() {
    k(L, 0);
  };
  function U(E) {
    M = E, g || (g = !0, V());
  }
  function _(E, T) {
    S = k(function() {
      E(e.unstable_now());
    }, T);
  }
  e.unstable_IdlePriority = 5, e.unstable_ImmediatePriority = 1, e.unstable_LowPriority = 4, e.unstable_NormalPriority = 3, e.unstable_Profiling = null, e.unstable_UserBlockingPriority = 2, e.unstable_cancelCallback = function(E) {
    E.callback = null;
  }, e.unstable_continueExecution = function() {
    y || j || (y = !0, U(N));
  }, e.unstable_forceFrameRate = function(E) {
    0 > E || 125 < E ? console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported") : A = 0 < E ? Math.floor(1e3 / E) : 5;
  }, e.unstable_getCurrentPriorityLevel = function() {
    return v;
  }, e.unstable_getFirstCallbackNode = function() {
    return n(o);
  }, e.unstable_next = function(E) {
    switch (v) {
      case 1:
      case 2:
      case 3:
        var T = 3;
        break;
      default:
        T = v;
    }
    var b = v;
    v = T;
    try {
      return E();
    } finally {
      v = b;
    }
  }, e.unstable_pauseExecution = function() {
  }, e.unstable_requestPaint = function() {
  }, e.unstable_runWithPriority = function(E, T) {
    switch (E) {
      case 1:
      case 2:
      case 3:
      case 4:
      case 5:
        break;
      default:
        E = 3;
    }
    var b = v;
    v = E;
    try {
      return T();
    } finally {
      v = b;
    }
  }, e.unstable_scheduleCallback = function(E, T, b) {
    var B = e.unstable_now();
    switch (typeof b == "object" && b !== null ? (b = b.delay, b = typeof b == "number" && 0 < b ? B + b : B) : b = B, E) {
      case 1:
        var W = -1;
        break;
      case 2:
        W = 250;
        break;
      case 5:
        W = 1073741823;
        break;
      case 4:
        W = 1e4;
        break;
      default:
        W = 5e3;
    }
    return W = b + W, E = { id: m++, callback: T, priorityLevel: E, startTime: b, expirationTime: W, sortIndex: -1 }, b > B ? (E.sortIndex = b, t(d, E), n(o) === null && E === n(d) && (C ? (c(S), S = -1) : C = !0, _(x, b - B))) : (E.sortIndex = W, t(o, E), y || j || (y = !0, U(N))), E;
  }, e.unstable_shouldYield = D, e.unstable_wrapCallback = function(E) {
    var T = v;
    return function() {
      var b = v;
      v = T;
      try {
        return E.apply(this, arguments);
      } finally {
        v = b;
      }
    };
  };
})(au);
iu.exports = au;
var Ud = iu.exports;
/**
 * @license React
 * react-dom.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Bd = P, Le = Ud;
function z(e) {
  for (var t = "https://reactjs.org/docs/error-decoder.html?invariant=" + e, n = 1; n < arguments.length; n++) t += "&args[]=" + encodeURIComponent(arguments[n]);
  return "Minified React error #" + e + "; visit " + t + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
}
var ou = /* @__PURE__ */ new Set(), rl = {};
function $t(e, t) {
  Cn(e, t), Cn(e + "Capture", t);
}
function Cn(e, t) {
  for (rl[e] = t, e = 0; e < t.length; e++) ou.add(t[e]);
}
var ut = !(typeof window > "u" || typeof window.document > "u" || typeof window.document.createElement > "u"), Mr = Object.prototype.hasOwnProperty, Vd = /^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/, Ta = {}, Ra = {};
function Wd(e) {
  return Mr.call(Ra, e) ? !0 : Mr.call(Ta, e) ? !1 : Vd.test(e) ? Ra[e] = !0 : (Ta[e] = !0, !1);
}
function qd(e, t, n, s) {
  if (n !== null && n.type === 0) return !1;
  switch (typeof t) {
    case "function":
    case "symbol":
      return !0;
    case "boolean":
      return s ? !1 : n !== null ? !n.acceptsBooleans : (e = e.toLowerCase().slice(0, 5), e !== "data-" && e !== "aria-");
    default:
      return !1;
  }
}
function Hd(e, t, n, s) {
  if (t === null || typeof t > "u" || qd(e, t, n, s)) return !0;
  if (s) return !1;
  if (n !== null) switch (n.type) {
    case 3:
      return !t;
    case 4:
      return t === !1;
    case 5:
      return isNaN(t);
    case 6:
      return isNaN(t) || 1 > t;
  }
  return !1;
}
function je(e, t, n, s, r, i, a) {
  this.acceptsBooleans = t === 2 || t === 3 || t === 4, this.attributeName = s, this.attributeNamespace = r, this.mustUseProperty = n, this.propertyName = e, this.type = t, this.sanitizeURL = i, this.removeEmptyString = a;
}
var he = {};
"children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(e) {
  he[e] = new je(e, 0, !1, e, null, !1, !1);
});
[["acceptCharset", "accept-charset"], ["className", "class"], ["htmlFor", "for"], ["httpEquiv", "http-equiv"]].forEach(function(e) {
  var t = e[0];
  he[t] = new je(t, 1, !1, e[1], null, !1, !1);
});
["contentEditable", "draggable", "spellCheck", "value"].forEach(function(e) {
  he[e] = new je(e, 2, !1, e.toLowerCase(), null, !1, !1);
});
["autoReverse", "externalResourcesRequired", "focusable", "preserveAlpha"].forEach(function(e) {
  he[e] = new je(e, 2, !1, e, null, !1, !1);
});
"allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(e) {
  he[e] = new je(e, 3, !1, e.toLowerCase(), null, !1, !1);
});
["checked", "multiple", "muted", "selected"].forEach(function(e) {
  he[e] = new je(e, 3, !0, e, null, !1, !1);
});
["capture", "download"].forEach(function(e) {
  he[e] = new je(e, 4, !1, e, null, !1, !1);
});
["cols", "rows", "size", "span"].forEach(function(e) {
  he[e] = new je(e, 6, !1, e, null, !1, !1);
});
["rowSpan", "start"].forEach(function(e) {
  he[e] = new je(e, 5, !1, e.toLowerCase(), null, !1, !1);
});
var bi = /[\-:]([a-z])/g;
function Ei(e) {
  return e[1].toUpperCase();
}
"accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(e) {
  var t = e.replace(
    bi,
    Ei
  );
  he[t] = new je(t, 1, !1, e, null, !1, !1);
});
"xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(e) {
  var t = e.replace(bi, Ei);
  he[t] = new je(t, 1, !1, e, "http://www.w3.org/1999/xlink", !1, !1);
});
["xml:base", "xml:lang", "xml:space"].forEach(function(e) {
  var t = e.replace(bi, Ei);
  he[t] = new je(t, 1, !1, e, "http://www.w3.org/XML/1998/namespace", !1, !1);
});
["tabIndex", "crossOrigin"].forEach(function(e) {
  he[e] = new je(e, 1, !1, e.toLowerCase(), null, !1, !1);
});
he.xlinkHref = new je("xlinkHref", 1, !1, "xlink:href", "http://www.w3.org/1999/xlink", !0, !1);
["src", "href", "action", "formAction"].forEach(function(e) {
  he[e] = new je(e, 1, !1, e.toLowerCase(), null, !0, !0);
});
function Mi(e, t, n, s) {
  var r = he.hasOwnProperty(t) ? he[t] : null;
  (r !== null ? r.type !== 0 : s || !(2 < t.length) || t[0] !== "o" && t[0] !== "O" || t[1] !== "n" && t[1] !== "N") && (Hd(t, n, r, s) && (n = null), s || r === null ? Wd(t) && (n === null ? e.removeAttribute(t) : e.setAttribute(t, "" + n)) : r.mustUseProperty ? e[r.propertyName] = n === null ? r.type === 3 ? !1 : "" : n : (t = r.attributeName, s = r.attributeNamespace, n === null ? e.removeAttribute(t) : (r = r.type, n = r === 3 || r === 4 && n === !0 ? "" : "" + n, s ? e.setAttributeNS(s, t, n) : e.setAttribute(t, n))));
}
var ft = Bd.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED, Ml = Symbol.for("react.element"), ln = Symbol.for("react.portal"), sn = Symbol.for("react.fragment"), Li = Symbol.for("react.strict_mode"), Lr = Symbol.for("react.profiler"), uu = Symbol.for("react.provider"), cu = Symbol.for("react.context"), Ai = Symbol.for("react.forward_ref"), Ar = Symbol.for("react.suspense"), Pr = Symbol.for("react.suspense_list"), Pi = Symbol.for("react.memo"), gt = Symbol.for("react.lazy"), du = Symbol.for("react.offscreen"), Fa = Symbol.iterator;
function In(e) {
  return e === null || typeof e != "object" ? null : (e = Fa && e[Fa] || e["@@iterator"], typeof e == "function" ? e : null);
}
var te = Object.assign, Gs;
function Qn(e) {
  if (Gs === void 0) try {
    throw Error();
  } catch (n) {
    var t = n.stack.trim().match(/\n( *(at )?)/);
    Gs = t && t[1] || "";
  }
  return `
` + Gs + e;
}
var Js = !1;
function Zs(e, t) {
  if (!e || Js) return "";
  Js = !0;
  var n = Error.prepareStackTrace;
  Error.prepareStackTrace = void 0;
  try {
    if (t) if (t = function() {
      throw Error();
    }, Object.defineProperty(t.prototype, "props", { set: function() {
      throw Error();
    } }), typeof Reflect == "object" && Reflect.construct) {
      try {
        Reflect.construct(t, []);
      } catch (d) {
        var s = d;
      }
      Reflect.construct(e, [], t);
    } else {
      try {
        t.call();
      } catch (d) {
        s = d;
      }
      e.call(t.prototype);
    }
    else {
      try {
        throw Error();
      } catch (d) {
        s = d;
      }
      e();
    }
  } catch (d) {
    if (d && s && typeof d.stack == "string") {
      for (var r = d.stack.split(`
`), i = s.stack.split(`
`), a = r.length - 1, u = i.length - 1; 1 <= a && 0 <= u && r[a] !== i[u]; ) u--;
      for (; 1 <= a && 0 <= u; a--, u--) if (r[a] !== i[u]) {
        if (a !== 1 || u !== 1)
          do
            if (a--, u--, 0 > u || r[a] !== i[u]) {
              var o = `
` + r[a].replace(" at new ", " at ");
              return e.displayName && o.includes("<anonymous>") && (o = o.replace("<anonymous>", e.displayName)), o;
            }
          while (1 <= a && 0 <= u);
        break;
      }
    }
  } finally {
    Js = !1, Error.prepareStackTrace = n;
  }
  return (e = e ? e.displayName || e.name : "") ? Qn(e) : "";
}
function Yd(e) {
  switch (e.tag) {
    case 5:
      return Qn(e.type);
    case 16:
      return Qn("Lazy");
    case 13:
      return Qn("Suspense");
    case 19:
      return Qn("SuspenseList");
    case 0:
    case 2:
    case 15:
      return e = Zs(e.type, !1), e;
    case 11:
      return e = Zs(e.type.render, !1), e;
    case 1:
      return e = Zs(e.type, !0), e;
    default:
      return "";
  }
}
function zr(e) {
  if (e == null) return null;
  if (typeof e == "function") return e.displayName || e.name || null;
  if (typeof e == "string") return e;
  switch (e) {
    case sn:
      return "Fragment";
    case ln:
      return "Portal";
    case Lr:
      return "Profiler";
    case Li:
      return "StrictMode";
    case Ar:
      return "Suspense";
    case Pr:
      return "SuspenseList";
  }
  if (typeof e == "object") switch (e.$$typeof) {
    case cu:
      return (e.displayName || "Context") + ".Consumer";
    case uu:
      return (e._context.displayName || "Context") + ".Provider";
    case Ai:
      var t = e.render;
      return e = e.displayName, e || (e = t.displayName || t.name || "", e = e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef"), e;
    case Pi:
      return t = e.displayName || null, t !== null ? t : zr(e.type) || "Memo";
    case gt:
      t = e._payload, e = e._init;
      try {
        return zr(e(t));
      } catch {
      }
  }
  return null;
}
function Qd(e) {
  var t = e.type;
  switch (e.tag) {
    case 24:
      return "Cache";
    case 9:
      return (t.displayName || "Context") + ".Consumer";
    case 10:
      return (t._context.displayName || "Context") + ".Provider";
    case 18:
      return "DehydratedFragment";
    case 11:
      return e = t.render, e = e.displayName || e.name || "", t.displayName || (e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef");
    case 7:
      return "Fragment";
    case 5:
      return t;
    case 4:
      return "Portal";
    case 3:
      return "Root";
    case 6:
      return "Text";
    case 16:
      return zr(t);
    case 8:
      return t === Li ? "StrictMode" : "Mode";
    case 22:
      return "Offscreen";
    case 12:
      return "Profiler";
    case 21:
      return "Scope";
    case 13:
      return "Suspense";
    case 19:
      return "SuspenseList";
    case 25:
      return "TracingMarker";
    case 1:
    case 0:
    case 17:
    case 2:
    case 14:
    case 15:
      if (typeof t == "function") return t.displayName || t.name || null;
      if (typeof t == "string") return t;
  }
  return null;
}
function zt(e) {
  switch (typeof e) {
    case "boolean":
    case "number":
    case "string":
    case "undefined":
      return e;
    case "object":
      return e;
    default:
      return "";
  }
}
function hu(e) {
  var t = e.type;
  return (e = e.nodeName) && e.toLowerCase() === "input" && (t === "checkbox" || t === "radio");
}
function Kd(e) {
  var t = hu(e) ? "checked" : "value", n = Object.getOwnPropertyDescriptor(e.constructor.prototype, t), s = "" + e[t];
  if (!e.hasOwnProperty(t) && typeof n < "u" && typeof n.get == "function" && typeof n.set == "function") {
    var r = n.get, i = n.set;
    return Object.defineProperty(e, t, { configurable: !0, get: function() {
      return r.call(this);
    }, set: function(a) {
      s = "" + a, i.call(this, a);
    } }), Object.defineProperty(e, t, { enumerable: n.enumerable }), { getValue: function() {
      return s;
    }, setValue: function(a) {
      s = "" + a;
    }, stopTracking: function() {
      e._valueTracker = null, delete e[t];
    } };
  }
}
function Ll(e) {
  e._valueTracker || (e._valueTracker = Kd(e));
}
function fu(e) {
  if (!e) return !1;
  var t = e._valueTracker;
  if (!t) return !0;
  var n = t.getValue(), s = "";
  return e && (s = hu(e) ? e.checked ? "true" : "false" : e.value), e = s, e !== n ? (t.setValue(e), !0) : !1;
}
function is(e) {
  if (e = e || (typeof document < "u" ? document : void 0), typeof e > "u") return null;
  try {
    return e.activeElement || e.body;
  } catch {
    return e.body;
  }
}
function Tr(e, t) {
  var n = t.checked;
  return te({}, t, { defaultChecked: void 0, defaultValue: void 0, value: void 0, checked: n ?? e._wrapperState.initialChecked });
}
function Oa(e, t) {
  var n = t.defaultValue == null ? "" : t.defaultValue, s = t.checked != null ? t.checked : t.defaultChecked;
  n = zt(t.value != null ? t.value : n), e._wrapperState = { initialChecked: s, initialValue: n, controlled: t.type === "checkbox" || t.type === "radio" ? t.checked != null : t.value != null };
}
function pu(e, t) {
  t = t.checked, t != null && Mi(e, "checked", t, !1);
}
function Rr(e, t) {
  pu(e, t);
  var n = zt(t.value), s = t.type;
  if (n != null) s === "number" ? (n === 0 && e.value === "" || e.value != n) && (e.value = "" + n) : e.value !== "" + n && (e.value = "" + n);
  else if (s === "submit" || s === "reset") {
    e.removeAttribute("value");
    return;
  }
  t.hasOwnProperty("value") ? Fr(e, t.type, n) : t.hasOwnProperty("defaultValue") && Fr(e, t.type, zt(t.defaultValue)), t.checked == null && t.defaultChecked != null && (e.defaultChecked = !!t.defaultChecked);
}
function Da(e, t, n) {
  if (t.hasOwnProperty("value") || t.hasOwnProperty("defaultValue")) {
    var s = t.type;
    if (!(s !== "submit" && s !== "reset" || t.value !== void 0 && t.value !== null)) return;
    t = "" + e._wrapperState.initialValue, n || t === e.value || (e.value = t), e.defaultValue = t;
  }
  n = e.name, n !== "" && (e.name = ""), e.defaultChecked = !!e._wrapperState.initialChecked, n !== "" && (e.name = n);
}
function Fr(e, t, n) {
  (t !== "number" || is(e.ownerDocument) !== e) && (n == null ? e.defaultValue = "" + e._wrapperState.initialValue : e.defaultValue !== "" + n && (e.defaultValue = "" + n));
}
var Kn = Array.isArray;
function xn(e, t, n, s) {
  if (e = e.options, t) {
    t = {};
    for (var r = 0; r < n.length; r++) t["$" + n[r]] = !0;
    for (n = 0; n < e.length; n++) r = t.hasOwnProperty("$" + e[n].value), e[n].selected !== r && (e[n].selected = r), r && s && (e[n].defaultSelected = !0);
  } else {
    for (n = "" + zt(n), t = null, r = 0; r < e.length; r++) {
      if (e[r].value === n) {
        e[r].selected = !0, s && (e[r].defaultSelected = !0);
        return;
      }
      t !== null || e[r].disabled || (t = e[r]);
    }
    t !== null && (t.selected = !0);
  }
}
function Or(e, t) {
  if (t.dangerouslySetInnerHTML != null) throw Error(z(91));
  return te({}, t, { value: void 0, defaultValue: void 0, children: "" + e._wrapperState.initialValue });
}
function Ia(e, t) {
  var n = t.value;
  if (n == null) {
    if (n = t.children, t = t.defaultValue, n != null) {
      if (t != null) throw Error(z(92));
      if (Kn(n)) {
        if (1 < n.length) throw Error(z(93));
        n = n[0];
      }
      t = n;
    }
    t == null && (t = ""), n = t;
  }
  e._wrapperState = { initialValue: zt(n) };
}
function mu(e, t) {
  var n = zt(t.value), s = zt(t.defaultValue);
  n != null && (n = "" + n, n !== e.value && (e.value = n), t.defaultValue == null && e.defaultValue !== n && (e.defaultValue = n)), s != null && (e.defaultValue = "" + s);
}
function Ua(e) {
  var t = e.textContent;
  t === e._wrapperState.initialValue && t !== "" && t !== null && (e.value = t);
}
function vu(e) {
  switch (e) {
    case "svg":
      return "http://www.w3.org/2000/svg";
    case "math":
      return "http://www.w3.org/1998/Math/MathML";
    default:
      return "http://www.w3.org/1999/xhtml";
  }
}
function Dr(e, t) {
  return e == null || e === "http://www.w3.org/1999/xhtml" ? vu(t) : e === "http://www.w3.org/2000/svg" && t === "foreignObject" ? "http://www.w3.org/1999/xhtml" : e;
}
var Al, gu = function(e) {
  return typeof MSApp < "u" && MSApp.execUnsafeLocalFunction ? function(t, n, s, r) {
    MSApp.execUnsafeLocalFunction(function() {
      return e(t, n, s, r);
    });
  } : e;
}(function(e, t) {
  if (e.namespaceURI !== "http://www.w3.org/2000/svg" || "innerHTML" in e) e.innerHTML = t;
  else {
    for (Al = Al || document.createElement("div"), Al.innerHTML = "<svg>" + t.valueOf().toString() + "</svg>", t = Al.firstChild; e.firstChild; ) e.removeChild(e.firstChild);
    for (; t.firstChild; ) e.appendChild(t.firstChild);
  }
});
function il(e, t) {
  if (t) {
    var n = e.firstChild;
    if (n && n === e.lastChild && n.nodeType === 3) {
      n.nodeValue = t;
      return;
    }
  }
  e.textContent = t;
}
var Jn = {
  animationIterationCount: !0,
  aspectRatio: !0,
  borderImageOutset: !0,
  borderImageSlice: !0,
  borderImageWidth: !0,
  boxFlex: !0,
  boxFlexGroup: !0,
  boxOrdinalGroup: !0,
  columnCount: !0,
  columns: !0,
  flex: !0,
  flexGrow: !0,
  flexPositive: !0,
  flexShrink: !0,
  flexNegative: !0,
  flexOrder: !0,
  gridArea: !0,
  gridRow: !0,
  gridRowEnd: !0,
  gridRowSpan: !0,
  gridRowStart: !0,
  gridColumn: !0,
  gridColumnEnd: !0,
  gridColumnSpan: !0,
  gridColumnStart: !0,
  fontWeight: !0,
  lineClamp: !0,
  lineHeight: !0,
  opacity: !0,
  order: !0,
  orphans: !0,
  tabSize: !0,
  widows: !0,
  zIndex: !0,
  zoom: !0,
  fillOpacity: !0,
  floodOpacity: !0,
  stopOpacity: !0,
  strokeDasharray: !0,
  strokeDashoffset: !0,
  strokeMiterlimit: !0,
  strokeOpacity: !0,
  strokeWidth: !0
}, Xd = ["Webkit", "ms", "Moz", "O"];
Object.keys(Jn).forEach(function(e) {
  Xd.forEach(function(t) {
    t = t + e.charAt(0).toUpperCase() + e.substring(1), Jn[t] = Jn[e];
  });
});
function xu(e, t, n) {
  return t == null || typeof t == "boolean" || t === "" ? "" : n || typeof t != "number" || t === 0 || Jn.hasOwnProperty(e) && Jn[e] ? ("" + t).trim() : t + "px";
}
function yu(e, t) {
  e = e.style;
  for (var n in t) if (t.hasOwnProperty(n)) {
    var s = n.indexOf("--") === 0, r = xu(n, t[n], s);
    n === "float" && (n = "cssFloat"), s ? e.setProperty(n, r) : e[n] = r;
  }
}
var Gd = te({ menuitem: !0 }, { area: !0, base: !0, br: !0, col: !0, embed: !0, hr: !0, img: !0, input: !0, keygen: !0, link: !0, meta: !0, param: !0, source: !0, track: !0, wbr: !0 });
function Ir(e, t) {
  if (t) {
    if (Gd[e] && (t.children != null || t.dangerouslySetInnerHTML != null)) throw Error(z(137, e));
    if (t.dangerouslySetInnerHTML != null) {
      if (t.children != null) throw Error(z(60));
      if (typeof t.dangerouslySetInnerHTML != "object" || !("__html" in t.dangerouslySetInnerHTML)) throw Error(z(61));
    }
    if (t.style != null && typeof t.style != "object") throw Error(z(62));
  }
}
function Ur(e, t) {
  if (e.indexOf("-") === -1) return typeof t.is == "string";
  switch (e) {
    case "annotation-xml":
    case "color-profile":
    case "font-face":
    case "font-face-src":
    case "font-face-uri":
    case "font-face-format":
    case "font-face-name":
    case "missing-glyph":
      return !1;
    default:
      return !0;
  }
}
var Br = null;
function zi(e) {
  return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
}
var Vr = null, yn = null, jn = null;
function Ba(e) {
  if (e = Sl(e)) {
    if (typeof Vr != "function") throw Error(z(280));
    var t = e.stateNode;
    t && (t = Fs(t), Vr(e.stateNode, e.type, t));
  }
}
function ju(e) {
  yn ? jn ? jn.push(e) : jn = [e] : yn = e;
}
function Nu() {
  if (yn) {
    var e = yn, t = jn;
    if (jn = yn = null, Ba(e), t) for (e = 0; e < t.length; e++) Ba(t[e]);
  }
}
function wu(e, t) {
  return e(t);
}
function ku() {
}
var _s = !1;
function Cu(e, t, n) {
  if (_s) return e(t, n);
  _s = !0;
  try {
    return wu(e, t, n);
  } finally {
    _s = !1, (yn !== null || jn !== null) && (ku(), Nu());
  }
}
function al(e, t) {
  var n = e.stateNode;
  if (n === null) return null;
  var s = Fs(n);
  if (s === null) return null;
  n = s[t];
  e: switch (t) {
    case "onClick":
    case "onClickCapture":
    case "onDoubleClick":
    case "onDoubleClickCapture":
    case "onMouseDown":
    case "onMouseDownCapture":
    case "onMouseMove":
    case "onMouseMoveCapture":
    case "onMouseUp":
    case "onMouseUpCapture":
    case "onMouseEnter":
      (s = !s.disabled) || (e = e.type, s = !(e === "button" || e === "input" || e === "select" || e === "textarea")), e = !s;
      break e;
    default:
      e = !1;
  }
  if (e) return null;
  if (n && typeof n != "function") throw Error(z(231, t, typeof n));
  return n;
}
var Wr = !1;
if (ut) try {
  var Un = {};
  Object.defineProperty(Un, "passive", { get: function() {
    Wr = !0;
  } }), window.addEventListener("test", Un, Un), window.removeEventListener("test", Un, Un);
} catch {
  Wr = !1;
}
function Jd(e, t, n, s, r, i, a, u, o) {
  var d = Array.prototype.slice.call(arguments, 3);
  try {
    t.apply(n, d);
  } catch (m) {
    this.onError(m);
  }
}
var Zn = !1, as = null, os = !1, qr = null, Zd = { onError: function(e) {
  Zn = !0, as = e;
} };
function _d(e, t, n, s, r, i, a, u, o) {
  Zn = !1, as = null, Jd.apply(Zd, arguments);
}
function $d(e, t, n, s, r, i, a, u, o) {
  if (_d.apply(this, arguments), Zn) {
    if (Zn) {
      var d = as;
      Zn = !1, as = null;
    } else throw Error(z(198));
    os || (os = !0, qr = d);
  }
}
function en(e) {
  var t = e, n = e;
  if (e.alternate) for (; t.return; ) t = t.return;
  else {
    e = t;
    do
      t = e, t.flags & 4098 && (n = t.return), e = t.return;
    while (e);
  }
  return t.tag === 3 ? n : null;
}
function Su(e) {
  if (e.tag === 13) {
    var t = e.memoizedState;
    if (t === null && (e = e.alternate, e !== null && (t = e.memoizedState)), t !== null) return t.dehydrated;
  }
  return null;
}
function Va(e) {
  if (en(e) !== e) throw Error(z(188));
}
function eh(e) {
  var t = e.alternate;
  if (!t) {
    if (t = en(e), t === null) throw Error(z(188));
    return t !== e ? null : e;
  }
  for (var n = e, s = t; ; ) {
    var r = n.return;
    if (r === null) break;
    var i = r.alternate;
    if (i === null) {
      if (s = r.return, s !== null) {
        n = s;
        continue;
      }
      break;
    }
    if (r.child === i.child) {
      for (i = r.child; i; ) {
        if (i === n) return Va(r), e;
        if (i === s) return Va(r), t;
        i = i.sibling;
      }
      throw Error(z(188));
    }
    if (n.return !== s.return) n = r, s = i;
    else {
      for (var a = !1, u = r.child; u; ) {
        if (u === n) {
          a = !0, n = r, s = i;
          break;
        }
        if (u === s) {
          a = !0, s = r, n = i;
          break;
        }
        u = u.sibling;
      }
      if (!a) {
        for (u = i.child; u; ) {
          if (u === n) {
            a = !0, n = i, s = r;
            break;
          }
          if (u === s) {
            a = !0, s = i, n = r;
            break;
          }
          u = u.sibling;
        }
        if (!a) throw Error(z(189));
      }
    }
    if (n.alternate !== s) throw Error(z(190));
  }
  if (n.tag !== 3) throw Error(z(188));
  return n.stateNode.current === n ? e : t;
}
function bu(e) {
  return e = eh(e), e !== null ? Eu(e) : null;
}
function Eu(e) {
  if (e.tag === 5 || e.tag === 6) return e;
  for (e = e.child; e !== null; ) {
    var t = Eu(e);
    if (t !== null) return t;
    e = e.sibling;
  }
  return null;
}
var Mu = Le.unstable_scheduleCallback, Wa = Le.unstable_cancelCallback, th = Le.unstable_shouldYield, nh = Le.unstable_requestPaint, le = Le.unstable_now, lh = Le.unstable_getCurrentPriorityLevel, Ti = Le.unstable_ImmediatePriority, Lu = Le.unstable_UserBlockingPriority, us = Le.unstable_NormalPriority, sh = Le.unstable_LowPriority, Au = Le.unstable_IdlePriority, Ps = null, et = null;
function rh(e) {
  if (et && typeof et.onCommitFiberRoot == "function") try {
    et.onCommitFiberRoot(Ps, e, void 0, (e.current.flags & 128) === 128);
  } catch {
  }
}
var He = Math.clz32 ? Math.clz32 : oh, ih = Math.log, ah = Math.LN2;
function oh(e) {
  return e >>>= 0, e === 0 ? 32 : 31 - (ih(e) / ah | 0) | 0;
}
var Pl = 64, zl = 4194304;
function Xn(e) {
  switch (e & -e) {
    case 1:
      return 1;
    case 2:
      return 2;
    case 4:
      return 4;
    case 8:
      return 8;
    case 16:
      return 16;
    case 32:
      return 32;
    case 64:
    case 128:
    case 256:
    case 512:
    case 1024:
    case 2048:
    case 4096:
    case 8192:
    case 16384:
    case 32768:
    case 65536:
    case 131072:
    case 262144:
    case 524288:
    case 1048576:
    case 2097152:
      return e & 4194240;
    case 4194304:
    case 8388608:
    case 16777216:
    case 33554432:
    case 67108864:
      return e & 130023424;
    case 134217728:
      return 134217728;
    case 268435456:
      return 268435456;
    case 536870912:
      return 536870912;
    case 1073741824:
      return 1073741824;
    default:
      return e;
  }
}
function cs(e, t) {
  var n = e.pendingLanes;
  if (n === 0) return 0;
  var s = 0, r = e.suspendedLanes, i = e.pingedLanes, a = n & 268435455;
  if (a !== 0) {
    var u = a & ~r;
    u !== 0 ? s = Xn(u) : (i &= a, i !== 0 && (s = Xn(i)));
  } else a = n & ~r, a !== 0 ? s = Xn(a) : i !== 0 && (s = Xn(i));
  if (s === 0) return 0;
  if (t !== 0 && t !== s && !(t & r) && (r = s & -s, i = t & -t, r >= i || r === 16 && (i & 4194240) !== 0)) return t;
  if (s & 4 && (s |= n & 16), t = e.entangledLanes, t !== 0) for (e = e.entanglements, t &= s; 0 < t; ) n = 31 - He(t), r = 1 << n, s |= e[n], t &= ~r;
  return s;
}
function uh(e, t) {
  switch (e) {
    case 1:
    case 2:
    case 4:
      return t + 250;
    case 8:
    case 16:
    case 32:
    case 64:
    case 128:
    case 256:
    case 512:
    case 1024:
    case 2048:
    case 4096:
    case 8192:
    case 16384:
    case 32768:
    case 65536:
    case 131072:
    case 262144:
    case 524288:
    case 1048576:
    case 2097152:
      return t + 5e3;
    case 4194304:
    case 8388608:
    case 16777216:
    case 33554432:
    case 67108864:
      return -1;
    case 134217728:
    case 268435456:
    case 536870912:
    case 1073741824:
      return -1;
    default:
      return -1;
  }
}
function ch(e, t) {
  for (var n = e.suspendedLanes, s = e.pingedLanes, r = e.expirationTimes, i = e.pendingLanes; 0 < i; ) {
    var a = 31 - He(i), u = 1 << a, o = r[a];
    o === -1 ? (!(u & n) || u & s) && (r[a] = uh(u, t)) : o <= t && (e.expiredLanes |= u), i &= ~u;
  }
}
function Hr(e) {
  return e = e.pendingLanes & -1073741825, e !== 0 ? e : e & 1073741824 ? 1073741824 : 0;
}
function Pu() {
  var e = Pl;
  return Pl <<= 1, !(Pl & 4194240) && (Pl = 64), e;
}
function $s(e) {
  for (var t = [], n = 0; 31 > n; n++) t.push(e);
  return t;
}
function kl(e, t, n) {
  e.pendingLanes |= t, t !== 536870912 && (e.suspendedLanes = 0, e.pingedLanes = 0), e = e.eventTimes, t = 31 - He(t), e[t] = n;
}
function dh(e, t) {
  var n = e.pendingLanes & ~t;
  e.pendingLanes = t, e.suspendedLanes = 0, e.pingedLanes = 0, e.expiredLanes &= t, e.mutableReadLanes &= t, e.entangledLanes &= t, t = e.entanglements;
  var s = e.eventTimes;
  for (e = e.expirationTimes; 0 < n; ) {
    var r = 31 - He(n), i = 1 << r;
    t[r] = 0, s[r] = -1, e[r] = -1, n &= ~i;
  }
}
function Ri(e, t) {
  var n = e.entangledLanes |= t;
  for (e = e.entanglements; n; ) {
    var s = 31 - He(n), r = 1 << s;
    r & t | e[s] & t && (e[s] |= t), n &= ~r;
  }
}
var Q = 0;
function zu(e) {
  return e &= -e, 1 < e ? 4 < e ? e & 268435455 ? 16 : 536870912 : 4 : 1;
}
var Tu, Fi, Ru, Fu, Ou, Yr = !1, Tl = [], Ct = null, St = null, bt = null, ol = /* @__PURE__ */ new Map(), ul = /* @__PURE__ */ new Map(), jt = [], hh = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");
function qa(e, t) {
  switch (e) {
    case "focusin":
    case "focusout":
      Ct = null;
      break;
    case "dragenter":
    case "dragleave":
      St = null;
      break;
    case "mouseover":
    case "mouseout":
      bt = null;
      break;
    case "pointerover":
    case "pointerout":
      ol.delete(t.pointerId);
      break;
    case "gotpointercapture":
    case "lostpointercapture":
      ul.delete(t.pointerId);
  }
}
function Bn(e, t, n, s, r, i) {
  return e === null || e.nativeEvent !== i ? (e = { blockedOn: t, domEventName: n, eventSystemFlags: s, nativeEvent: i, targetContainers: [r] }, t !== null && (t = Sl(t), t !== null && Fi(t)), e) : (e.eventSystemFlags |= s, t = e.targetContainers, r !== null && t.indexOf(r) === -1 && t.push(r), e);
}
function fh(e, t, n, s, r) {
  switch (t) {
    case "focusin":
      return Ct = Bn(Ct, e, t, n, s, r), !0;
    case "dragenter":
      return St = Bn(St, e, t, n, s, r), !0;
    case "mouseover":
      return bt = Bn(bt, e, t, n, s, r), !0;
    case "pointerover":
      var i = r.pointerId;
      return ol.set(i, Bn(ol.get(i) || null, e, t, n, s, r)), !0;
    case "gotpointercapture":
      return i = r.pointerId, ul.set(i, Bn(ul.get(i) || null, e, t, n, s, r)), !0;
  }
  return !1;
}
function Du(e) {
  var t = Wt(e.target);
  if (t !== null) {
    var n = en(t);
    if (n !== null) {
      if (t = n.tag, t === 13) {
        if (t = Su(n), t !== null) {
          e.blockedOn = t, Ou(e.priority, function() {
            Ru(n);
          });
          return;
        }
      } else if (t === 3 && n.stateNode.current.memoizedState.isDehydrated) {
        e.blockedOn = n.tag === 3 ? n.stateNode.containerInfo : null;
        return;
      }
    }
  }
  e.blockedOn = null;
}
function Gl(e) {
  if (e.blockedOn !== null) return !1;
  for (var t = e.targetContainers; 0 < t.length; ) {
    var n = Qr(e.domEventName, e.eventSystemFlags, t[0], e.nativeEvent);
    if (n === null) {
      n = e.nativeEvent;
      var s = new n.constructor(n.type, n);
      Br = s, n.target.dispatchEvent(s), Br = null;
    } else return t = Sl(n), t !== null && Fi(t), e.blockedOn = n, !1;
    t.shift();
  }
  return !0;
}
function Ha(e, t, n) {
  Gl(e) && n.delete(t);
}
function ph() {
  Yr = !1, Ct !== null && Gl(Ct) && (Ct = null), St !== null && Gl(St) && (St = null), bt !== null && Gl(bt) && (bt = null), ol.forEach(Ha), ul.forEach(Ha);
}
function Vn(e, t) {
  e.blockedOn === t && (e.blockedOn = null, Yr || (Yr = !0, Le.unstable_scheduleCallback(Le.unstable_NormalPriority, ph)));
}
function cl(e) {
  function t(r) {
    return Vn(r, e);
  }
  if (0 < Tl.length) {
    Vn(Tl[0], e);
    for (var n = 1; n < Tl.length; n++) {
      var s = Tl[n];
      s.blockedOn === e && (s.blockedOn = null);
    }
  }
  for (Ct !== null && Vn(Ct, e), St !== null && Vn(St, e), bt !== null && Vn(bt, e), ol.forEach(t), ul.forEach(t), n = 0; n < jt.length; n++) s = jt[n], s.blockedOn === e && (s.blockedOn = null);
  for (; 0 < jt.length && (n = jt[0], n.blockedOn === null); ) Du(n), n.blockedOn === null && jt.shift();
}
var Nn = ft.ReactCurrentBatchConfig, ds = !0;
function mh(e, t, n, s) {
  var r = Q, i = Nn.transition;
  Nn.transition = null;
  try {
    Q = 1, Oi(e, t, n, s);
  } finally {
    Q = r, Nn.transition = i;
  }
}
function vh(e, t, n, s) {
  var r = Q, i = Nn.transition;
  Nn.transition = null;
  try {
    Q = 4, Oi(e, t, n, s);
  } finally {
    Q = r, Nn.transition = i;
  }
}
function Oi(e, t, n, s) {
  if (ds) {
    var r = Qr(e, t, n, s);
    if (r === null) ur(e, t, s, hs, n), qa(e, s);
    else if (fh(r, e, t, n, s)) s.stopPropagation();
    else if (qa(e, s), t & 4 && -1 < hh.indexOf(e)) {
      for (; r !== null; ) {
        var i = Sl(r);
        if (i !== null && Tu(i), i = Qr(e, t, n, s), i === null && ur(e, t, s, hs, n), i === r) break;
        r = i;
      }
      r !== null && s.stopPropagation();
    } else ur(e, t, s, null, n);
  }
}
var hs = null;
function Qr(e, t, n, s) {
  if (hs = null, e = zi(s), e = Wt(e), e !== null) if (t = en(e), t === null) e = null;
  else if (n = t.tag, n === 13) {
    if (e = Su(t), e !== null) return e;
    e = null;
  } else if (n === 3) {
    if (t.stateNode.current.memoizedState.isDehydrated) return t.tag === 3 ? t.stateNode.containerInfo : null;
    e = null;
  } else t !== e && (e = null);
  return hs = e, null;
}
function Iu(e) {
  switch (e) {
    case "cancel":
    case "click":
    case "close":
    case "contextmenu":
    case "copy":
    case "cut":
    case "auxclick":
    case "dblclick":
    case "dragend":
    case "dragstart":
    case "drop":
    case "focusin":
    case "focusout":
    case "input":
    case "invalid":
    case "keydown":
    case "keypress":
    case "keyup":
    case "mousedown":
    case "mouseup":
    case "paste":
    case "pause":
    case "play":
    case "pointercancel":
    case "pointerdown":
    case "pointerup":
    case "ratechange":
    case "reset":
    case "resize":
    case "seeked":
    case "submit":
    case "touchcancel":
    case "touchend":
    case "touchstart":
    case "volumechange":
    case "change":
    case "selectionchange":
    case "textInput":
    case "compositionstart":
    case "compositionend":
    case "compositionupdate":
    case "beforeblur":
    case "afterblur":
    case "beforeinput":
    case "blur":
    case "fullscreenchange":
    case "focus":
    case "hashchange":
    case "popstate":
    case "select":
    case "selectstart":
      return 1;
    case "drag":
    case "dragenter":
    case "dragexit":
    case "dragleave":
    case "dragover":
    case "mousemove":
    case "mouseout":
    case "mouseover":
    case "pointermove":
    case "pointerout":
    case "pointerover":
    case "scroll":
    case "toggle":
    case "touchmove":
    case "wheel":
    case "mouseenter":
    case "mouseleave":
    case "pointerenter":
    case "pointerleave":
      return 4;
    case "message":
      switch (lh()) {
        case Ti:
          return 1;
        case Lu:
          return 4;
        case us:
        case sh:
          return 16;
        case Au:
          return 536870912;
        default:
          return 16;
      }
    default:
      return 16;
  }
}
var wt = null, Di = null, Jl = null;
function Uu() {
  if (Jl) return Jl;
  var e, t = Di, n = t.length, s, r = "value" in wt ? wt.value : wt.textContent, i = r.length;
  for (e = 0; e < n && t[e] === r[e]; e++) ;
  var a = n - e;
  for (s = 1; s <= a && t[n - s] === r[i - s]; s++) ;
  return Jl = r.slice(e, 1 < s ? 1 - s : void 0);
}
function Zl(e) {
  var t = e.keyCode;
  return "charCode" in e ? (e = e.charCode, e === 0 && t === 13 && (e = 13)) : e = t, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
}
function Rl() {
  return !0;
}
function Ya() {
  return !1;
}
function Pe(e) {
  function t(n, s, r, i, a) {
    this._reactName = n, this._targetInst = r, this.type = s, this.nativeEvent = i, this.target = a, this.currentTarget = null;
    for (var u in e) e.hasOwnProperty(u) && (n = e[u], this[u] = n ? n(i) : i[u]);
    return this.isDefaultPrevented = (i.defaultPrevented != null ? i.defaultPrevented : i.returnValue === !1) ? Rl : Ya, this.isPropagationStopped = Ya, this;
  }
  return te(t.prototype, { preventDefault: function() {
    this.defaultPrevented = !0;
    var n = this.nativeEvent;
    n && (n.preventDefault ? n.preventDefault() : typeof n.returnValue != "unknown" && (n.returnValue = !1), this.isDefaultPrevented = Rl);
  }, stopPropagation: function() {
    var n = this.nativeEvent;
    n && (n.stopPropagation ? n.stopPropagation() : typeof n.cancelBubble != "unknown" && (n.cancelBubble = !0), this.isPropagationStopped = Rl);
  }, persist: function() {
  }, isPersistent: Rl }), t;
}
var Fn = { eventPhase: 0, bubbles: 0, cancelable: 0, timeStamp: function(e) {
  return e.timeStamp || Date.now();
}, defaultPrevented: 0, isTrusted: 0 }, Ii = Pe(Fn), Cl = te({}, Fn, { view: 0, detail: 0 }), gh = Pe(Cl), er, tr, Wn, zs = te({}, Cl, { screenX: 0, screenY: 0, clientX: 0, clientY: 0, pageX: 0, pageY: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, getModifierState: Ui, button: 0, buttons: 0, relatedTarget: function(e) {
  return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
}, movementX: function(e) {
  return "movementX" in e ? e.movementX : (e !== Wn && (Wn && e.type === "mousemove" ? (er = e.screenX - Wn.screenX, tr = e.screenY - Wn.screenY) : tr = er = 0, Wn = e), er);
}, movementY: function(e) {
  return "movementY" in e ? e.movementY : tr;
} }), Qa = Pe(zs), xh = te({}, zs, { dataTransfer: 0 }), yh = Pe(xh), jh = te({}, Cl, { relatedTarget: 0 }), nr = Pe(jh), Nh = te({}, Fn, { animationName: 0, elapsedTime: 0, pseudoElement: 0 }), wh = Pe(Nh), kh = te({}, Fn, { clipboardData: function(e) {
  return "clipboardData" in e ? e.clipboardData : window.clipboardData;
} }), Ch = Pe(kh), Sh = te({}, Fn, { data: 0 }), Ka = Pe(Sh), bh = {
  Esc: "Escape",
  Spacebar: " ",
  Left: "ArrowLeft",
  Up: "ArrowUp",
  Right: "ArrowRight",
  Down: "ArrowDown",
  Del: "Delete",
  Win: "OS",
  Menu: "ContextMenu",
  Apps: "ContextMenu",
  Scroll: "ScrollLock",
  MozPrintableKey: "Unidentified"
}, Eh = {
  8: "Backspace",
  9: "Tab",
  12: "Clear",
  13: "Enter",
  16: "Shift",
  17: "Control",
  18: "Alt",
  19: "Pause",
  20: "CapsLock",
  27: "Escape",
  32: " ",
  33: "PageUp",
  34: "PageDown",
  35: "End",
  36: "Home",
  37: "ArrowLeft",
  38: "ArrowUp",
  39: "ArrowRight",
  40: "ArrowDown",
  45: "Insert",
  46: "Delete",
  112: "F1",
  113: "F2",
  114: "F3",
  115: "F4",
  116: "F5",
  117: "F6",
  118: "F7",
  119: "F8",
  120: "F9",
  121: "F10",
  122: "F11",
  123: "F12",
  144: "NumLock",
  145: "ScrollLock",
  224: "Meta"
}, Mh = { Alt: "altKey", Control: "ctrlKey", Meta: "metaKey", Shift: "shiftKey" };
function Lh(e) {
  var t = this.nativeEvent;
  return t.getModifierState ? t.getModifierState(e) : (e = Mh[e]) ? !!t[e] : !1;
}
function Ui() {
  return Lh;
}
var Ah = te({}, Cl, { key: function(e) {
  if (e.key) {
    var t = bh[e.key] || e.key;
    if (t !== "Unidentified") return t;
  }
  return e.type === "keypress" ? (e = Zl(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? Eh[e.keyCode] || "Unidentified" : "";
}, code: 0, location: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, repeat: 0, locale: 0, getModifierState: Ui, charCode: function(e) {
  return e.type === "keypress" ? Zl(e) : 0;
}, keyCode: function(e) {
  return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
}, which: function(e) {
  return e.type === "keypress" ? Zl(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
} }), Ph = Pe(Ah), zh = te({}, zs, { pointerId: 0, width: 0, height: 0, pressure: 0, tangentialPressure: 0, tiltX: 0, tiltY: 0, twist: 0, pointerType: 0, isPrimary: 0 }), Xa = Pe(zh), Th = te({}, Cl, { touches: 0, targetTouches: 0, changedTouches: 0, altKey: 0, metaKey: 0, ctrlKey: 0, shiftKey: 0, getModifierState: Ui }), Rh = Pe(Th), Fh = te({}, Fn, { propertyName: 0, elapsedTime: 0, pseudoElement: 0 }), Oh = Pe(Fh), Dh = te({}, zs, {
  deltaX: function(e) {
    return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
  },
  deltaY: function(e) {
    return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
  },
  deltaZ: 0,
  deltaMode: 0
}), Ih = Pe(Dh), Uh = [9, 13, 27, 32], Bi = ut && "CompositionEvent" in window, _n = null;
ut && "documentMode" in document && (_n = document.documentMode);
var Bh = ut && "TextEvent" in window && !_n, Bu = ut && (!Bi || _n && 8 < _n && 11 >= _n), Ga = " ", Ja = !1;
function Vu(e, t) {
  switch (e) {
    case "keyup":
      return Uh.indexOf(t.keyCode) !== -1;
    case "keydown":
      return t.keyCode !== 229;
    case "keypress":
    case "mousedown":
    case "focusout":
      return !0;
    default:
      return !1;
  }
}
function Wu(e) {
  return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
}
var rn = !1;
function Vh(e, t) {
  switch (e) {
    case "compositionend":
      return Wu(t);
    case "keypress":
      return t.which !== 32 ? null : (Ja = !0, Ga);
    case "textInput":
      return e = t.data, e === Ga && Ja ? null : e;
    default:
      return null;
  }
}
function Wh(e, t) {
  if (rn) return e === "compositionend" || !Bi && Vu(e, t) ? (e = Uu(), Jl = Di = wt = null, rn = !1, e) : null;
  switch (e) {
    case "paste":
      return null;
    case "keypress":
      if (!(t.ctrlKey || t.altKey || t.metaKey) || t.ctrlKey && t.altKey) {
        if (t.char && 1 < t.char.length) return t.char;
        if (t.which) return String.fromCharCode(t.which);
      }
      return null;
    case "compositionend":
      return Bu && t.locale !== "ko" ? null : t.data;
    default:
      return null;
  }
}
var qh = { color: !0, date: !0, datetime: !0, "datetime-local": !0, email: !0, month: !0, number: !0, password: !0, range: !0, search: !0, tel: !0, text: !0, time: !0, url: !0, week: !0 };
function Za(e) {
  var t = e && e.nodeName && e.nodeName.toLowerCase();
  return t === "input" ? !!qh[e.type] : t === "textarea";
}
function qu(e, t, n, s) {
  ju(s), t = fs(t, "onChange"), 0 < t.length && (n = new Ii("onChange", "change", null, n, s), e.push({ event: n, listeners: t }));
}
var $n = null, dl = null;
function Hh(e) {
  ec(e, 0);
}
function Ts(e) {
  var t = un(e);
  if (fu(t)) return e;
}
function Yh(e, t) {
  if (e === "change") return t;
}
var Hu = !1;
if (ut) {
  var lr;
  if (ut) {
    var sr = "oninput" in document;
    if (!sr) {
      var _a = document.createElement("div");
      _a.setAttribute("oninput", "return;"), sr = typeof _a.oninput == "function";
    }
    lr = sr;
  } else lr = !1;
  Hu = lr && (!document.documentMode || 9 < document.documentMode);
}
function $a() {
  $n && ($n.detachEvent("onpropertychange", Yu), dl = $n = null);
}
function Yu(e) {
  if (e.propertyName === "value" && Ts(dl)) {
    var t = [];
    qu(t, dl, e, zi(e)), Cu(Hh, t);
  }
}
function Qh(e, t, n) {
  e === "focusin" ? ($a(), $n = t, dl = n, $n.attachEvent("onpropertychange", Yu)) : e === "focusout" && $a();
}
function Kh(e) {
  if (e === "selectionchange" || e === "keyup" || e === "keydown") return Ts(dl);
}
function Xh(e, t) {
  if (e === "click") return Ts(t);
}
function Gh(e, t) {
  if (e === "input" || e === "change") return Ts(t);
}
function Jh(e, t) {
  return e === t && (e !== 0 || 1 / e === 1 / t) || e !== e && t !== t;
}
var Qe = typeof Object.is == "function" ? Object.is : Jh;
function hl(e, t) {
  if (Qe(e, t)) return !0;
  if (typeof e != "object" || e === null || typeof t != "object" || t === null) return !1;
  var n = Object.keys(e), s = Object.keys(t);
  if (n.length !== s.length) return !1;
  for (s = 0; s < n.length; s++) {
    var r = n[s];
    if (!Mr.call(t, r) || !Qe(e[r], t[r])) return !1;
  }
  return !0;
}
function eo(e) {
  for (; e && e.firstChild; ) e = e.firstChild;
  return e;
}
function to(e, t) {
  var n = eo(e);
  e = 0;
  for (var s; n; ) {
    if (n.nodeType === 3) {
      if (s = e + n.textContent.length, e <= t && s >= t) return { node: n, offset: t - e };
      e = s;
    }
    e: {
      for (; n; ) {
        if (n.nextSibling) {
          n = n.nextSibling;
          break e;
        }
        n = n.parentNode;
      }
      n = void 0;
    }
    n = eo(n);
  }
}
function Qu(e, t) {
  return e && t ? e === t ? !0 : e && e.nodeType === 3 ? !1 : t && t.nodeType === 3 ? Qu(e, t.parentNode) : "contains" in e ? e.contains(t) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(t) & 16) : !1 : !1;
}
function Ku() {
  for (var e = window, t = is(); t instanceof e.HTMLIFrameElement; ) {
    try {
      var n = typeof t.contentWindow.location.href == "string";
    } catch {
      n = !1;
    }
    if (n) e = t.contentWindow;
    else break;
    t = is(e.document);
  }
  return t;
}
function Vi(e) {
  var t = e && e.nodeName && e.nodeName.toLowerCase();
  return t && (t === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || t === "textarea" || e.contentEditable === "true");
}
function Zh(e) {
  var t = Ku(), n = e.focusedElem, s = e.selectionRange;
  if (t !== n && n && n.ownerDocument && Qu(n.ownerDocument.documentElement, n)) {
    if (s !== null && Vi(n)) {
      if (t = s.start, e = s.end, e === void 0 && (e = t), "selectionStart" in n) n.selectionStart = t, n.selectionEnd = Math.min(e, n.value.length);
      else if (e = (t = n.ownerDocument || document) && t.defaultView || window, e.getSelection) {
        e = e.getSelection();
        var r = n.textContent.length, i = Math.min(s.start, r);
        s = s.end === void 0 ? i : Math.min(s.end, r), !e.extend && i > s && (r = s, s = i, i = r), r = to(n, i);
        var a = to(
          n,
          s
        );
        r && a && (e.rangeCount !== 1 || e.anchorNode !== r.node || e.anchorOffset !== r.offset || e.focusNode !== a.node || e.focusOffset !== a.offset) && (t = t.createRange(), t.setStart(r.node, r.offset), e.removeAllRanges(), i > s ? (e.addRange(t), e.extend(a.node, a.offset)) : (t.setEnd(a.node, a.offset), e.addRange(t)));
      }
    }
    for (t = [], e = n; e = e.parentNode; ) e.nodeType === 1 && t.push({ element: e, left: e.scrollLeft, top: e.scrollTop });
    for (typeof n.focus == "function" && n.focus(), n = 0; n < t.length; n++) e = t[n], e.element.scrollLeft = e.left, e.element.scrollTop = e.top;
  }
}
var _h = ut && "documentMode" in document && 11 >= document.documentMode, an = null, Kr = null, el = null, Xr = !1;
function no(e, t, n) {
  var s = n.window === n ? n.document : n.nodeType === 9 ? n : n.ownerDocument;
  Xr || an == null || an !== is(s) || (s = an, "selectionStart" in s && Vi(s) ? s = { start: s.selectionStart, end: s.selectionEnd } : (s = (s.ownerDocument && s.ownerDocument.defaultView || window).getSelection(), s = { anchorNode: s.anchorNode, anchorOffset: s.anchorOffset, focusNode: s.focusNode, focusOffset: s.focusOffset }), el && hl(el, s) || (el = s, s = fs(Kr, "onSelect"), 0 < s.length && (t = new Ii("onSelect", "select", null, t, n), e.push({ event: t, listeners: s }), t.target = an)));
}
function Fl(e, t) {
  var n = {};
  return n[e.toLowerCase()] = t.toLowerCase(), n["Webkit" + e] = "webkit" + t, n["Moz" + e] = "moz" + t, n;
}
var on = { animationend: Fl("Animation", "AnimationEnd"), animationiteration: Fl("Animation", "AnimationIteration"), animationstart: Fl("Animation", "AnimationStart"), transitionend: Fl("Transition", "TransitionEnd") }, rr = {}, Xu = {};
ut && (Xu = document.createElement("div").style, "AnimationEvent" in window || (delete on.animationend.animation, delete on.animationiteration.animation, delete on.animationstart.animation), "TransitionEvent" in window || delete on.transitionend.transition);
function Rs(e) {
  if (rr[e]) return rr[e];
  if (!on[e]) return e;
  var t = on[e], n;
  for (n in t) if (t.hasOwnProperty(n) && n in Xu) return rr[e] = t[n];
  return e;
}
var Gu = Rs("animationend"), Ju = Rs("animationiteration"), Zu = Rs("animationstart"), _u = Rs("transitionend"), $u = /* @__PURE__ */ new Map(), lo = "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
function Rt(e, t) {
  $u.set(e, t), $t(t, [e]);
}
for (var ir = 0; ir < lo.length; ir++) {
  var ar = lo[ir], $h = ar.toLowerCase(), ef = ar[0].toUpperCase() + ar.slice(1);
  Rt($h, "on" + ef);
}
Rt(Gu, "onAnimationEnd");
Rt(Ju, "onAnimationIteration");
Rt(Zu, "onAnimationStart");
Rt("dblclick", "onDoubleClick");
Rt("focusin", "onFocus");
Rt("focusout", "onBlur");
Rt(_u, "onTransitionEnd");
Cn("onMouseEnter", ["mouseout", "mouseover"]);
Cn("onMouseLeave", ["mouseout", "mouseover"]);
Cn("onPointerEnter", ["pointerout", "pointerover"]);
Cn("onPointerLeave", ["pointerout", "pointerover"]);
$t("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" "));
$t("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" "));
$t("onBeforeInput", ["compositionend", "keypress", "textInput", "paste"]);
$t("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" "));
$t("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" "));
$t("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
var Gn = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), tf = new Set("cancel close invalid load scroll toggle".split(" ").concat(Gn));
function so(e, t, n) {
  var s = e.type || "unknown-event";
  e.currentTarget = n, $d(s, t, void 0, e), e.currentTarget = null;
}
function ec(e, t) {
  t = (t & 4) !== 0;
  for (var n = 0; n < e.length; n++) {
    var s = e[n], r = s.event;
    s = s.listeners;
    e: {
      var i = void 0;
      if (t) for (var a = s.length - 1; 0 <= a; a--) {
        var u = s[a], o = u.instance, d = u.currentTarget;
        if (u = u.listener, o !== i && r.isPropagationStopped()) break e;
        so(r, u, d), i = o;
      }
      else for (a = 0; a < s.length; a++) {
        if (u = s[a], o = u.instance, d = u.currentTarget, u = u.listener, o !== i && r.isPropagationStopped()) break e;
        so(r, u, d), i = o;
      }
    }
  }
  if (os) throw e = qr, os = !1, qr = null, e;
}
function G(e, t) {
  var n = t[$r];
  n === void 0 && (n = t[$r] = /* @__PURE__ */ new Set());
  var s = e + "__bubble";
  n.has(s) || (tc(t, e, 2, !1), n.add(s));
}
function or(e, t, n) {
  var s = 0;
  t && (s |= 4), tc(n, e, s, t);
}
var Ol = "_reactListening" + Math.random().toString(36).slice(2);
function fl(e) {
  if (!e[Ol]) {
    e[Ol] = !0, ou.forEach(function(n) {
      n !== "selectionchange" && (tf.has(n) || or(n, !1, e), or(n, !0, e));
    });
    var t = e.nodeType === 9 ? e : e.ownerDocument;
    t === null || t[Ol] || (t[Ol] = !0, or("selectionchange", !1, t));
  }
}
function tc(e, t, n, s) {
  switch (Iu(t)) {
    case 1:
      var r = mh;
      break;
    case 4:
      r = vh;
      break;
    default:
      r = Oi;
  }
  n = r.bind(null, t, n, e), r = void 0, !Wr || t !== "touchstart" && t !== "touchmove" && t !== "wheel" || (r = !0), s ? r !== void 0 ? e.addEventListener(t, n, { capture: !0, passive: r }) : e.addEventListener(t, n, !0) : r !== void 0 ? e.addEventListener(t, n, { passive: r }) : e.addEventListener(t, n, !1);
}
function ur(e, t, n, s, r) {
  var i = s;
  if (!(t & 1) && !(t & 2) && s !== null) e: for (; ; ) {
    if (s === null) return;
    var a = s.tag;
    if (a === 3 || a === 4) {
      var u = s.stateNode.containerInfo;
      if (u === r || u.nodeType === 8 && u.parentNode === r) break;
      if (a === 4) for (a = s.return; a !== null; ) {
        var o = a.tag;
        if ((o === 3 || o === 4) && (o = a.stateNode.containerInfo, o === r || o.nodeType === 8 && o.parentNode === r)) return;
        a = a.return;
      }
      for (; u !== null; ) {
        if (a = Wt(u), a === null) return;
        if (o = a.tag, o === 5 || o === 6) {
          s = i = a;
          continue e;
        }
        u = u.parentNode;
      }
    }
    s = s.return;
  }
  Cu(function() {
    var d = i, m = zi(n), p = [];
    e: {
      var v = $u.get(e);
      if (v !== void 0) {
        var j = Ii, y = e;
        switch (e) {
          case "keypress":
            if (Zl(n) === 0) break e;
          case "keydown":
          case "keyup":
            j = Ph;
            break;
          case "focusin":
            y = "focus", j = nr;
            break;
          case "focusout":
            y = "blur", j = nr;
            break;
          case "beforeblur":
          case "afterblur":
            j = nr;
            break;
          case "click":
            if (n.button === 2) break e;
          case "auxclick":
          case "dblclick":
          case "mousedown":
          case "mousemove":
          case "mouseup":
          case "mouseout":
          case "mouseover":
          case "contextmenu":
            j = Qa;
            break;
          case "drag":
          case "dragend":
          case "dragenter":
          case "dragexit":
          case "dragleave":
          case "dragover":
          case "dragstart":
          case "drop":
            j = yh;
            break;
          case "touchcancel":
          case "touchend":
          case "touchmove":
          case "touchstart":
            j = Rh;
            break;
          case Gu:
          case Ju:
          case Zu:
            j = wh;
            break;
          case _u:
            j = Oh;
            break;
          case "scroll":
            j = gh;
            break;
          case "wheel":
            j = Ih;
            break;
          case "copy":
          case "cut":
          case "paste":
            j = Ch;
            break;
          case "gotpointercapture":
          case "lostpointercapture":
          case "pointercancel":
          case "pointerdown":
          case "pointermove":
          case "pointerout":
          case "pointerover":
          case "pointerup":
            j = Xa;
        }
        var C = (t & 4) !== 0, k = !C && e === "scroll", c = C ? v !== null ? v + "Capture" : null : v;
        C = [];
        for (var h = d, f; h !== null; ) {
          f = h;
          var x = f.stateNode;
          if (f.tag === 5 && x !== null && (f = x, c !== null && (x = al(h, c), x != null && C.push(pl(h, x, f)))), k) break;
          h = h.return;
        }
        0 < C.length && (v = new j(v, y, null, n, m), p.push({ event: v, listeners: C }));
      }
    }
    if (!(t & 7)) {
      e: {
        if (v = e === "mouseover" || e === "pointerover", j = e === "mouseout" || e === "pointerout", v && n !== Br && (y = n.relatedTarget || n.fromElement) && (Wt(y) || y[ct])) break e;
        if ((j || v) && (v = m.window === m ? m : (v = m.ownerDocument) ? v.defaultView || v.parentWindow : window, j ? (y = n.relatedTarget || n.toElement, j = d, y = y ? Wt(y) : null, y !== null && (k = en(y), y !== k || y.tag !== 5 && y.tag !== 6) && (y = null)) : (j = null, y = d), j !== y)) {
          if (C = Qa, x = "onMouseLeave", c = "onMouseEnter", h = "mouse", (e === "pointerout" || e === "pointerover") && (C = Xa, x = "onPointerLeave", c = "onPointerEnter", h = "pointer"), k = j == null ? v : un(j), f = y == null ? v : un(y), v = new C(x, h + "leave", j, n, m), v.target = k, v.relatedTarget = f, x = null, Wt(m) === d && (C = new C(c, h + "enter", y, n, m), C.target = f, C.relatedTarget = k, x = C), k = x, j && y) t: {
            for (C = j, c = y, h = 0, f = C; f; f = nn(f)) h++;
            for (f = 0, x = c; x; x = nn(x)) f++;
            for (; 0 < h - f; ) C = nn(C), h--;
            for (; 0 < f - h; ) c = nn(c), f--;
            for (; h--; ) {
              if (C === c || c !== null && C === c.alternate) break t;
              C = nn(C), c = nn(c);
            }
            C = null;
          }
          else C = null;
          j !== null && ro(p, v, j, C, !1), y !== null && k !== null && ro(p, k, y, C, !0);
        }
      }
      e: {
        if (v = d ? un(d) : window, j = v.nodeName && v.nodeName.toLowerCase(), j === "select" || j === "input" && v.type === "file") var N = Yh;
        else if (Za(v)) if (Hu) N = Gh;
        else {
          N = Kh;
          var g = Qh;
        }
        else (j = v.nodeName) && j.toLowerCase() === "input" && (v.type === "checkbox" || v.type === "radio") && (N = Xh);
        if (N && (N = N(e, d))) {
          qu(p, N, n, m);
          break e;
        }
        g && g(e, v, d), e === "focusout" && (g = v._wrapperState) && g.controlled && v.type === "number" && Fr(v, "number", v.value);
      }
      switch (g = d ? un(d) : window, e) {
        case "focusin":
          (Za(g) || g.contentEditable === "true") && (an = g, Kr = d, el = null);
          break;
        case "focusout":
          el = Kr = an = null;
          break;
        case "mousedown":
          Xr = !0;
          break;
        case "contextmenu":
        case "mouseup":
        case "dragend":
          Xr = !1, no(p, n, m);
          break;
        case "selectionchange":
          if (_h) break;
        case "keydown":
        case "keyup":
          no(p, n, m);
      }
      var M;
      if (Bi) e: {
        switch (e) {
          case "compositionstart":
            var S = "onCompositionStart";
            break e;
          case "compositionend":
            S = "onCompositionEnd";
            break e;
          case "compositionupdate":
            S = "onCompositionUpdate";
            break e;
        }
        S = void 0;
      }
      else rn ? Vu(e, n) && (S = "onCompositionEnd") : e === "keydown" && n.keyCode === 229 && (S = "onCompositionStart");
      S && (Bu && n.locale !== "ko" && (rn || S !== "onCompositionStart" ? S === "onCompositionEnd" && rn && (M = Uu()) : (wt = m, Di = "value" in wt ? wt.value : wt.textContent, rn = !0)), g = fs(d, S), 0 < g.length && (S = new Ka(S, e, null, n, m), p.push({ event: S, listeners: g }), M ? S.data = M : (M = Wu(n), M !== null && (S.data = M)))), (M = Bh ? Vh(e, n) : Wh(e, n)) && (d = fs(d, "onBeforeInput"), 0 < d.length && (m = new Ka("onBeforeInput", "beforeinput", null, n, m), p.push({ event: m, listeners: d }), m.data = M));
    }
    ec(p, t);
  });
}
function pl(e, t, n) {
  return { instance: e, listener: t, currentTarget: n };
}
function fs(e, t) {
  for (var n = t + "Capture", s = []; e !== null; ) {
    var r = e, i = r.stateNode;
    r.tag === 5 && i !== null && (r = i, i = al(e, n), i != null && s.unshift(pl(e, i, r)), i = al(e, t), i != null && s.push(pl(e, i, r))), e = e.return;
  }
  return s;
}
function nn(e) {
  if (e === null) return null;
  do
    e = e.return;
  while (e && e.tag !== 5);
  return e || null;
}
function ro(e, t, n, s, r) {
  for (var i = t._reactName, a = []; n !== null && n !== s; ) {
    var u = n, o = u.alternate, d = u.stateNode;
    if (o !== null && o === s) break;
    u.tag === 5 && d !== null && (u = d, r ? (o = al(n, i), o != null && a.unshift(pl(n, o, u))) : r || (o = al(n, i), o != null && a.push(pl(n, o, u)))), n = n.return;
  }
  a.length !== 0 && e.push({ event: t, listeners: a });
}
var nf = /\r\n?/g, lf = /\u0000|\uFFFD/g;
function io(e) {
  return (typeof e == "string" ? e : "" + e).replace(nf, `
`).replace(lf, "");
}
function Dl(e, t, n) {
  if (t = io(t), io(e) !== t && n) throw Error(z(425));
}
function ps() {
}
var Gr = null, Jr = null;
function Zr(e, t) {
  return e === "textarea" || e === "noscript" || typeof t.children == "string" || typeof t.children == "number" || typeof t.dangerouslySetInnerHTML == "object" && t.dangerouslySetInnerHTML !== null && t.dangerouslySetInnerHTML.__html != null;
}
var _r = typeof setTimeout == "function" ? setTimeout : void 0, sf = typeof clearTimeout == "function" ? clearTimeout : void 0, ao = typeof Promise == "function" ? Promise : void 0, rf = typeof queueMicrotask == "function" ? queueMicrotask : typeof ao < "u" ? function(e) {
  return ao.resolve(null).then(e).catch(af);
} : _r;
function af(e) {
  setTimeout(function() {
    throw e;
  });
}
function cr(e, t) {
  var n = t, s = 0;
  do {
    var r = n.nextSibling;
    if (e.removeChild(n), r && r.nodeType === 8) if (n = r.data, n === "/$") {
      if (s === 0) {
        e.removeChild(r), cl(t);
        return;
      }
      s--;
    } else n !== "$" && n !== "$?" && n !== "$!" || s++;
    n = r;
  } while (n);
  cl(t);
}
function Et(e) {
  for (; e != null; e = e.nextSibling) {
    var t = e.nodeType;
    if (t === 1 || t === 3) break;
    if (t === 8) {
      if (t = e.data, t === "$" || t === "$!" || t === "$?") break;
      if (t === "/$") return null;
    }
  }
  return e;
}
function oo(e) {
  e = e.previousSibling;
  for (var t = 0; e; ) {
    if (e.nodeType === 8) {
      var n = e.data;
      if (n === "$" || n === "$!" || n === "$?") {
        if (t === 0) return e;
        t--;
      } else n === "/$" && t++;
    }
    e = e.previousSibling;
  }
  return null;
}
var On = Math.random().toString(36).slice(2), _e = "__reactFiber$" + On, ml = "__reactProps$" + On, ct = "__reactContainer$" + On, $r = "__reactEvents$" + On, of = "__reactListeners$" + On, uf = "__reactHandles$" + On;
function Wt(e) {
  var t = e[_e];
  if (t) return t;
  for (var n = e.parentNode; n; ) {
    if (t = n[ct] || n[_e]) {
      if (n = t.alternate, t.child !== null || n !== null && n.child !== null) for (e = oo(e); e !== null; ) {
        if (n = e[_e]) return n;
        e = oo(e);
      }
      return t;
    }
    e = n, n = e.parentNode;
  }
  return null;
}
function Sl(e) {
  return e = e[_e] || e[ct], !e || e.tag !== 5 && e.tag !== 6 && e.tag !== 13 && e.tag !== 3 ? null : e;
}
function un(e) {
  if (e.tag === 5 || e.tag === 6) return e.stateNode;
  throw Error(z(33));
}
function Fs(e) {
  return e[ml] || null;
}
var ei = [], cn = -1;
function Ft(e) {
  return { current: e };
}
function J(e) {
  0 > cn || (e.current = ei[cn], ei[cn] = null, cn--);
}
function X(e, t) {
  cn++, ei[cn] = e.current, e.current = t;
}
var Tt = {}, ve = Ft(Tt), ke = Ft(!1), Xt = Tt;
function Sn(e, t) {
  var n = e.type.contextTypes;
  if (!n) return Tt;
  var s = e.stateNode;
  if (s && s.__reactInternalMemoizedUnmaskedChildContext === t) return s.__reactInternalMemoizedMaskedChildContext;
  var r = {}, i;
  for (i in n) r[i] = t[i];
  return s && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = t, e.__reactInternalMemoizedMaskedChildContext = r), r;
}
function Ce(e) {
  return e = e.childContextTypes, e != null;
}
function ms() {
  J(ke), J(ve);
}
function uo(e, t, n) {
  if (ve.current !== Tt) throw Error(z(168));
  X(ve, t), X(ke, n);
}
function nc(e, t, n) {
  var s = e.stateNode;
  if (t = t.childContextTypes, typeof s.getChildContext != "function") return n;
  s = s.getChildContext();
  for (var r in s) if (!(r in t)) throw Error(z(108, Qd(e) || "Unknown", r));
  return te({}, n, s);
}
function vs(e) {
  return e = (e = e.stateNode) && e.__reactInternalMemoizedMergedChildContext || Tt, Xt = ve.current, X(ve, e), X(ke, ke.current), !0;
}
function co(e, t, n) {
  var s = e.stateNode;
  if (!s) throw Error(z(169));
  n ? (e = nc(e, t, Xt), s.__reactInternalMemoizedMergedChildContext = e, J(ke), J(ve), X(ve, e)) : J(ke), X(ke, n);
}
var st = null, Os = !1, dr = !1;
function lc(e) {
  st === null ? st = [e] : st.push(e);
}
function cf(e) {
  Os = !0, lc(e);
}
function Ot() {
  if (!dr && st !== null) {
    dr = !0;
    var e = 0, t = Q;
    try {
      var n = st;
      for (Q = 1; e < n.length; e++) {
        var s = n[e];
        do
          s = s(!0);
        while (s !== null);
      }
      st = null, Os = !1;
    } catch (r) {
      throw st !== null && (st = st.slice(e + 1)), Mu(Ti, Ot), r;
    } finally {
      Q = t, dr = !1;
    }
  }
  return null;
}
var dn = [], hn = 0, gs = null, xs = 0, ze = [], Te = 0, Gt = null, it = 1, at = "";
function Bt(e, t) {
  dn[hn++] = xs, dn[hn++] = gs, gs = e, xs = t;
}
function sc(e, t, n) {
  ze[Te++] = it, ze[Te++] = at, ze[Te++] = Gt, Gt = e;
  var s = it;
  e = at;
  var r = 32 - He(s) - 1;
  s &= ~(1 << r), n += 1;
  var i = 32 - He(t) + r;
  if (30 < i) {
    var a = r - r % 5;
    i = (s & (1 << a) - 1).toString(32), s >>= a, r -= a, it = 1 << 32 - He(t) + r | n << r | s, at = i + e;
  } else it = 1 << i | n << r | s, at = e;
}
function Wi(e) {
  e.return !== null && (Bt(e, 1), sc(e, 1, 0));
}
function qi(e) {
  for (; e === gs; ) gs = dn[--hn], dn[hn] = null, xs = dn[--hn], dn[hn] = null;
  for (; e === Gt; ) Gt = ze[--Te], ze[Te] = null, at = ze[--Te], ze[Te] = null, it = ze[--Te], ze[Te] = null;
}
var Me = null, Ee = null, Z = !1, qe = null;
function rc(e, t) {
  var n = Re(5, null, null, 0);
  n.elementType = "DELETED", n.stateNode = t, n.return = e, t = e.deletions, t === null ? (e.deletions = [n], e.flags |= 16) : t.push(n);
}
function ho(e, t) {
  switch (e.tag) {
    case 5:
      var n = e.type;
      return t = t.nodeType !== 1 || n.toLowerCase() !== t.nodeName.toLowerCase() ? null : t, t !== null ? (e.stateNode = t, Me = e, Ee = Et(t.firstChild), !0) : !1;
    case 6:
      return t = e.pendingProps === "" || t.nodeType !== 3 ? null : t, t !== null ? (e.stateNode = t, Me = e, Ee = null, !0) : !1;
    case 13:
      return t = t.nodeType !== 8 ? null : t, t !== null ? (n = Gt !== null ? { id: it, overflow: at } : null, e.memoizedState = { dehydrated: t, treeContext: n, retryLane: 1073741824 }, n = Re(18, null, null, 0), n.stateNode = t, n.return = e, e.child = n, Me = e, Ee = null, !0) : !1;
    default:
      return !1;
  }
}
function ti(e) {
  return (e.mode & 1) !== 0 && (e.flags & 128) === 0;
}
function ni(e) {
  if (Z) {
    var t = Ee;
    if (t) {
      var n = t;
      if (!ho(e, t)) {
        if (ti(e)) throw Error(z(418));
        t = Et(n.nextSibling);
        var s = Me;
        t && ho(e, t) ? rc(s, n) : (e.flags = e.flags & -4097 | 2, Z = !1, Me = e);
      }
    } else {
      if (ti(e)) throw Error(z(418));
      e.flags = e.flags & -4097 | 2, Z = !1, Me = e;
    }
  }
}
function fo(e) {
  for (e = e.return; e !== null && e.tag !== 5 && e.tag !== 3 && e.tag !== 13; ) e = e.return;
  Me = e;
}
function Il(e) {
  if (e !== Me) return !1;
  if (!Z) return fo(e), Z = !0, !1;
  var t;
  if ((t = e.tag !== 3) && !(t = e.tag !== 5) && (t = e.type, t = t !== "head" && t !== "body" && !Zr(e.type, e.memoizedProps)), t && (t = Ee)) {
    if (ti(e)) throw ic(), Error(z(418));
    for (; t; ) rc(e, t), t = Et(t.nextSibling);
  }
  if (fo(e), e.tag === 13) {
    if (e = e.memoizedState, e = e !== null ? e.dehydrated : null, !e) throw Error(z(317));
    e: {
      for (e = e.nextSibling, t = 0; e; ) {
        if (e.nodeType === 8) {
          var n = e.data;
          if (n === "/$") {
            if (t === 0) {
              Ee = Et(e.nextSibling);
              break e;
            }
            t--;
          } else n !== "$" && n !== "$!" && n !== "$?" || t++;
        }
        e = e.nextSibling;
      }
      Ee = null;
    }
  } else Ee = Me ? Et(e.stateNode.nextSibling) : null;
  return !0;
}
function ic() {
  for (var e = Ee; e; ) e = Et(e.nextSibling);
}
function bn() {
  Ee = Me = null, Z = !1;
}
function Hi(e) {
  qe === null ? qe = [e] : qe.push(e);
}
var df = ft.ReactCurrentBatchConfig;
function qn(e, t, n) {
  if (e = n.ref, e !== null && typeof e != "function" && typeof e != "object") {
    if (n._owner) {
      if (n = n._owner, n) {
        if (n.tag !== 1) throw Error(z(309));
        var s = n.stateNode;
      }
      if (!s) throw Error(z(147, e));
      var r = s, i = "" + e;
      return t !== null && t.ref !== null && typeof t.ref == "function" && t.ref._stringRef === i ? t.ref : (t = function(a) {
        var u = r.refs;
        a === null ? delete u[i] : u[i] = a;
      }, t._stringRef = i, t);
    }
    if (typeof e != "string") throw Error(z(284));
    if (!n._owner) throw Error(z(290, e));
  }
  return e;
}
function Ul(e, t) {
  throw e = Object.prototype.toString.call(t), Error(z(31, e === "[object Object]" ? "object with keys {" + Object.keys(t).join(", ") + "}" : e));
}
function po(e) {
  var t = e._init;
  return t(e._payload);
}
function ac(e) {
  function t(c, h) {
    if (e) {
      var f = c.deletions;
      f === null ? (c.deletions = [h], c.flags |= 16) : f.push(h);
    }
  }
  function n(c, h) {
    if (!e) return null;
    for (; h !== null; ) t(c, h), h = h.sibling;
    return null;
  }
  function s(c, h) {
    for (c = /* @__PURE__ */ new Map(); h !== null; ) h.key !== null ? c.set(h.key, h) : c.set(h.index, h), h = h.sibling;
    return c;
  }
  function r(c, h) {
    return c = Pt(c, h), c.index = 0, c.sibling = null, c;
  }
  function i(c, h, f) {
    return c.index = f, e ? (f = c.alternate, f !== null ? (f = f.index, f < h ? (c.flags |= 2, h) : f) : (c.flags |= 2, h)) : (c.flags |= 1048576, h);
  }
  function a(c) {
    return e && c.alternate === null && (c.flags |= 2), c;
  }
  function u(c, h, f, x) {
    return h === null || h.tag !== 6 ? (h = xr(f, c.mode, x), h.return = c, h) : (h = r(h, f), h.return = c, h);
  }
  function o(c, h, f, x) {
    var N = f.type;
    return N === sn ? m(c, h, f.props.children, x, f.key) : h !== null && (h.elementType === N || typeof N == "object" && N !== null && N.$$typeof === gt && po(N) === h.type) ? (x = r(h, f.props), x.ref = qn(c, h, f), x.return = c, x) : (x = ss(f.type, f.key, f.props, null, c.mode, x), x.ref = qn(c, h, f), x.return = c, x);
  }
  function d(c, h, f, x) {
    return h === null || h.tag !== 4 || h.stateNode.containerInfo !== f.containerInfo || h.stateNode.implementation !== f.implementation ? (h = yr(f, c.mode, x), h.return = c, h) : (h = r(h, f.children || []), h.return = c, h);
  }
  function m(c, h, f, x, N) {
    return h === null || h.tag !== 7 ? (h = Qt(f, c.mode, x, N), h.return = c, h) : (h = r(h, f), h.return = c, h);
  }
  function p(c, h, f) {
    if (typeof h == "string" && h !== "" || typeof h == "number") return h = xr("" + h, c.mode, f), h.return = c, h;
    if (typeof h == "object" && h !== null) {
      switch (h.$$typeof) {
        case Ml:
          return f = ss(h.type, h.key, h.props, null, c.mode, f), f.ref = qn(c, null, h), f.return = c, f;
        case ln:
          return h = yr(h, c.mode, f), h.return = c, h;
        case gt:
          var x = h._init;
          return p(c, x(h._payload), f);
      }
      if (Kn(h) || In(h)) return h = Qt(h, c.mode, f, null), h.return = c, h;
      Ul(c, h);
    }
    return null;
  }
  function v(c, h, f, x) {
    var N = h !== null ? h.key : null;
    if (typeof f == "string" && f !== "" || typeof f == "number") return N !== null ? null : u(c, h, "" + f, x);
    if (typeof f == "object" && f !== null) {
      switch (f.$$typeof) {
        case Ml:
          return f.key === N ? o(c, h, f, x) : null;
        case ln:
          return f.key === N ? d(c, h, f, x) : null;
        case gt:
          return N = f._init, v(
            c,
            h,
            N(f._payload),
            x
          );
      }
      if (Kn(f) || In(f)) return N !== null ? null : m(c, h, f, x, null);
      Ul(c, f);
    }
    return null;
  }
  function j(c, h, f, x, N) {
    if (typeof x == "string" && x !== "" || typeof x == "number") return c = c.get(f) || null, u(h, c, "" + x, N);
    if (typeof x == "object" && x !== null) {
      switch (x.$$typeof) {
        case Ml:
          return c = c.get(x.key === null ? f : x.key) || null, o(h, c, x, N);
        case ln:
          return c = c.get(x.key === null ? f : x.key) || null, d(h, c, x, N);
        case gt:
          var g = x._init;
          return j(c, h, f, g(x._payload), N);
      }
      if (Kn(x) || In(x)) return c = c.get(f) || null, m(h, c, x, N, null);
      Ul(h, x);
    }
    return null;
  }
  function y(c, h, f, x) {
    for (var N = null, g = null, M = h, S = h = 0, A = null; M !== null && S < f.length; S++) {
      M.index > S ? (A = M, M = null) : A = M.sibling;
      var w = v(c, M, f[S], x);
      if (w === null) {
        M === null && (M = A);
        break;
      }
      e && M && w.alternate === null && t(c, M), h = i(w, h, S), g === null ? N = w : g.sibling = w, g = w, M = A;
    }
    if (S === f.length) return n(c, M), Z && Bt(c, S), N;
    if (M === null) {
      for (; S < f.length; S++) M = p(c, f[S], x), M !== null && (h = i(M, h, S), g === null ? N = M : g.sibling = M, g = M);
      return Z && Bt(c, S), N;
    }
    for (M = s(c, M); S < f.length; S++) A = j(M, c, S, f[S], x), A !== null && (e && A.alternate !== null && M.delete(A.key === null ? S : A.key), h = i(A, h, S), g === null ? N = A : g.sibling = A, g = A);
    return e && M.forEach(function(D) {
      return t(c, D);
    }), Z && Bt(c, S), N;
  }
  function C(c, h, f, x) {
    var N = In(f);
    if (typeof N != "function") throw Error(z(150));
    if (f = N.call(f), f == null) throw Error(z(151));
    for (var g = N = null, M = h, S = h = 0, A = null, w = f.next(); M !== null && !w.done; S++, w = f.next()) {
      M.index > S ? (A = M, M = null) : A = M.sibling;
      var D = v(c, M, w.value, x);
      if (D === null) {
        M === null && (M = A);
        break;
      }
      e && M && D.alternate === null && t(c, M), h = i(D, h, S), g === null ? N = D : g.sibling = D, g = D, M = A;
    }
    if (w.done) return n(
      c,
      M
    ), Z && Bt(c, S), N;
    if (M === null) {
      for (; !w.done; S++, w = f.next()) w = p(c, w.value, x), w !== null && (h = i(w, h, S), g === null ? N = w : g.sibling = w, g = w);
      return Z && Bt(c, S), N;
    }
    for (M = s(c, M); !w.done; S++, w = f.next()) w = j(M, c, S, w.value, x), w !== null && (e && w.alternate !== null && M.delete(w.key === null ? S : w.key), h = i(w, h, S), g === null ? N = w : g.sibling = w, g = w);
    return e && M.forEach(function(L) {
      return t(c, L);
    }), Z && Bt(c, S), N;
  }
  function k(c, h, f, x) {
    if (typeof f == "object" && f !== null && f.type === sn && f.key === null && (f = f.props.children), typeof f == "object" && f !== null) {
      switch (f.$$typeof) {
        case Ml:
          e: {
            for (var N = f.key, g = h; g !== null; ) {
              if (g.key === N) {
                if (N = f.type, N === sn) {
                  if (g.tag === 7) {
                    n(c, g.sibling), h = r(g, f.props.children), h.return = c, c = h;
                    break e;
                  }
                } else if (g.elementType === N || typeof N == "object" && N !== null && N.$$typeof === gt && po(N) === g.type) {
                  n(c, g.sibling), h = r(g, f.props), h.ref = qn(c, g, f), h.return = c, c = h;
                  break e;
                }
                n(c, g);
                break;
              } else t(c, g);
              g = g.sibling;
            }
            f.type === sn ? (h = Qt(f.props.children, c.mode, x, f.key), h.return = c, c = h) : (x = ss(f.type, f.key, f.props, null, c.mode, x), x.ref = qn(c, h, f), x.return = c, c = x);
          }
          return a(c);
        case ln:
          e: {
            for (g = f.key; h !== null; ) {
              if (h.key === g) if (h.tag === 4 && h.stateNode.containerInfo === f.containerInfo && h.stateNode.implementation === f.implementation) {
                n(c, h.sibling), h = r(h, f.children || []), h.return = c, c = h;
                break e;
              } else {
                n(c, h);
                break;
              }
              else t(c, h);
              h = h.sibling;
            }
            h = yr(f, c.mode, x), h.return = c, c = h;
          }
          return a(c);
        case gt:
          return g = f._init, k(c, h, g(f._payload), x);
      }
      if (Kn(f)) return y(c, h, f, x);
      if (In(f)) return C(c, h, f, x);
      Ul(c, f);
    }
    return typeof f == "string" && f !== "" || typeof f == "number" ? (f = "" + f, h !== null && h.tag === 6 ? (n(c, h.sibling), h = r(h, f), h.return = c, c = h) : (n(c, h), h = xr(f, c.mode, x), h.return = c, c = h), a(c)) : n(c, h);
  }
  return k;
}
var En = ac(!0), oc = ac(!1), ys = Ft(null), js = null, fn = null, Yi = null;
function Qi() {
  Yi = fn = js = null;
}
function Ki(e) {
  var t = ys.current;
  J(ys), e._currentValue = t;
}
function li(e, t, n) {
  for (; e !== null; ) {
    var s = e.alternate;
    if ((e.childLanes & t) !== t ? (e.childLanes |= t, s !== null && (s.childLanes |= t)) : s !== null && (s.childLanes & t) !== t && (s.childLanes |= t), e === n) break;
    e = e.return;
  }
}
function wn(e, t) {
  js = e, Yi = fn = null, e = e.dependencies, e !== null && e.firstContext !== null && (e.lanes & t && (we = !0), e.firstContext = null);
}
function Oe(e) {
  var t = e._currentValue;
  if (Yi !== e) if (e = { context: e, memoizedValue: t, next: null }, fn === null) {
    if (js === null) throw Error(z(308));
    fn = e, js.dependencies = { lanes: 0, firstContext: e };
  } else fn = fn.next = e;
  return t;
}
var qt = null;
function Xi(e) {
  qt === null ? qt = [e] : qt.push(e);
}
function uc(e, t, n, s) {
  var r = t.interleaved;
  return r === null ? (n.next = n, Xi(t)) : (n.next = r.next, r.next = n), t.interleaved = n, dt(e, s);
}
function dt(e, t) {
  e.lanes |= t;
  var n = e.alternate;
  for (n !== null && (n.lanes |= t), n = e, e = e.return; e !== null; ) e.childLanes |= t, n = e.alternate, n !== null && (n.childLanes |= t), n = e, e = e.return;
  return n.tag === 3 ? n.stateNode : null;
}
var xt = !1;
function Gi(e) {
  e.updateQueue = { baseState: e.memoizedState, firstBaseUpdate: null, lastBaseUpdate: null, shared: { pending: null, interleaved: null, lanes: 0 }, effects: null };
}
function cc(e, t) {
  e = e.updateQueue, t.updateQueue === e && (t.updateQueue = { baseState: e.baseState, firstBaseUpdate: e.firstBaseUpdate, lastBaseUpdate: e.lastBaseUpdate, shared: e.shared, effects: e.effects });
}
function ot(e, t) {
  return { eventTime: e, lane: t, tag: 0, payload: null, callback: null, next: null };
}
function Mt(e, t, n) {
  var s = e.updateQueue;
  if (s === null) return null;
  if (s = s.shared, Y & 2) {
    var r = s.pending;
    return r === null ? t.next = t : (t.next = r.next, r.next = t), s.pending = t, dt(e, n);
  }
  return r = s.interleaved, r === null ? (t.next = t, Xi(s)) : (t.next = r.next, r.next = t), s.interleaved = t, dt(e, n);
}
function _l(e, t, n) {
  if (t = t.updateQueue, t !== null && (t = t.shared, (n & 4194240) !== 0)) {
    var s = t.lanes;
    s &= e.pendingLanes, n |= s, t.lanes = n, Ri(e, n);
  }
}
function mo(e, t) {
  var n = e.updateQueue, s = e.alternate;
  if (s !== null && (s = s.updateQueue, n === s)) {
    var r = null, i = null;
    if (n = n.firstBaseUpdate, n !== null) {
      do {
        var a = { eventTime: n.eventTime, lane: n.lane, tag: n.tag, payload: n.payload, callback: n.callback, next: null };
        i === null ? r = i = a : i = i.next = a, n = n.next;
      } while (n !== null);
      i === null ? r = i = t : i = i.next = t;
    } else r = i = t;
    n = { baseState: s.baseState, firstBaseUpdate: r, lastBaseUpdate: i, shared: s.shared, effects: s.effects }, e.updateQueue = n;
    return;
  }
  e = n.lastBaseUpdate, e === null ? n.firstBaseUpdate = t : e.next = t, n.lastBaseUpdate = t;
}
function Ns(e, t, n, s) {
  var r = e.updateQueue;
  xt = !1;
  var i = r.firstBaseUpdate, a = r.lastBaseUpdate, u = r.shared.pending;
  if (u !== null) {
    r.shared.pending = null;
    var o = u, d = o.next;
    o.next = null, a === null ? i = d : a.next = d, a = o;
    var m = e.alternate;
    m !== null && (m = m.updateQueue, u = m.lastBaseUpdate, u !== a && (u === null ? m.firstBaseUpdate = d : u.next = d, m.lastBaseUpdate = o));
  }
  if (i !== null) {
    var p = r.baseState;
    a = 0, m = d = o = null, u = i;
    do {
      var v = u.lane, j = u.eventTime;
      if ((s & v) === v) {
        m !== null && (m = m.next = {
          eventTime: j,
          lane: 0,
          tag: u.tag,
          payload: u.payload,
          callback: u.callback,
          next: null
        });
        e: {
          var y = e, C = u;
          switch (v = t, j = n, C.tag) {
            case 1:
              if (y = C.payload, typeof y == "function") {
                p = y.call(j, p, v);
                break e;
              }
              p = y;
              break e;
            case 3:
              y.flags = y.flags & -65537 | 128;
            case 0:
              if (y = C.payload, v = typeof y == "function" ? y.call(j, p, v) : y, v == null) break e;
              p = te({}, p, v);
              break e;
            case 2:
              xt = !0;
          }
        }
        u.callback !== null && u.lane !== 0 && (e.flags |= 64, v = r.effects, v === null ? r.effects = [u] : v.push(u));
      } else j = { eventTime: j, lane: v, tag: u.tag, payload: u.payload, callback: u.callback, next: null }, m === null ? (d = m = j, o = p) : m = m.next = j, a |= v;
      if (u = u.next, u === null) {
        if (u = r.shared.pending, u === null) break;
        v = u, u = v.next, v.next = null, r.lastBaseUpdate = v, r.shared.pending = null;
      }
    } while (!0);
    if (m === null && (o = p), r.baseState = o, r.firstBaseUpdate = d, r.lastBaseUpdate = m, t = r.shared.interleaved, t !== null) {
      r = t;
      do
        a |= r.lane, r = r.next;
      while (r !== t);
    } else i === null && (r.shared.lanes = 0);
    Zt |= a, e.lanes = a, e.memoizedState = p;
  }
}
function vo(e, t, n) {
  if (e = t.effects, t.effects = null, e !== null) for (t = 0; t < e.length; t++) {
    var s = e[t], r = s.callback;
    if (r !== null) {
      if (s.callback = null, s = n, typeof r != "function") throw Error(z(191, r));
      r.call(s);
    }
  }
}
var bl = {}, tt = Ft(bl), vl = Ft(bl), gl = Ft(bl);
function Ht(e) {
  if (e === bl) throw Error(z(174));
  return e;
}
function Ji(e, t) {
  switch (X(gl, t), X(vl, e), X(tt, bl), e = t.nodeType, e) {
    case 9:
    case 11:
      t = (t = t.documentElement) ? t.namespaceURI : Dr(null, "");
      break;
    default:
      e = e === 8 ? t.parentNode : t, t = e.namespaceURI || null, e = e.tagName, t = Dr(t, e);
  }
  J(tt), X(tt, t);
}
function Mn() {
  J(tt), J(vl), J(gl);
}
function dc(e) {
  Ht(gl.current);
  var t = Ht(tt.current), n = Dr(t, e.type);
  t !== n && (X(vl, e), X(tt, n));
}
function Zi(e) {
  vl.current === e && (J(tt), J(vl));
}
var $ = Ft(0);
function ws(e) {
  for (var t = e; t !== null; ) {
    if (t.tag === 13) {
      var n = t.memoizedState;
      if (n !== null && (n = n.dehydrated, n === null || n.data === "$?" || n.data === "$!")) return t;
    } else if (t.tag === 19 && t.memoizedProps.revealOrder !== void 0) {
      if (t.flags & 128) return t;
    } else if (t.child !== null) {
      t.child.return = t, t = t.child;
      continue;
    }
    if (t === e) break;
    for (; t.sibling === null; ) {
      if (t.return === null || t.return === e) return null;
      t = t.return;
    }
    t.sibling.return = t.return, t = t.sibling;
  }
  return null;
}
var hr = [];
function _i() {
  for (var e = 0; e < hr.length; e++) hr[e]._workInProgressVersionPrimary = null;
  hr.length = 0;
}
var $l = ft.ReactCurrentDispatcher, fr = ft.ReactCurrentBatchConfig, Jt = 0, ee = null, re = null, oe = null, ks = !1, tl = !1, xl = 0, hf = 0;
function fe() {
  throw Error(z(321));
}
function $i(e, t) {
  if (t === null) return !1;
  for (var n = 0; n < t.length && n < e.length; n++) if (!Qe(e[n], t[n])) return !1;
  return !0;
}
function ea(e, t, n, s, r, i) {
  if (Jt = i, ee = t, t.memoizedState = null, t.updateQueue = null, t.lanes = 0, $l.current = e === null || e.memoizedState === null ? vf : gf, e = n(s, r), tl) {
    i = 0;
    do {
      if (tl = !1, xl = 0, 25 <= i) throw Error(z(301));
      i += 1, oe = re = null, t.updateQueue = null, $l.current = xf, e = n(s, r);
    } while (tl);
  }
  if ($l.current = Cs, t = re !== null && re.next !== null, Jt = 0, oe = re = ee = null, ks = !1, t) throw Error(z(300));
  return e;
}
function ta() {
  var e = xl !== 0;
  return xl = 0, e;
}
function Ze() {
  var e = { memoizedState: null, baseState: null, baseQueue: null, queue: null, next: null };
  return oe === null ? ee.memoizedState = oe = e : oe = oe.next = e, oe;
}
function De() {
  if (re === null) {
    var e = ee.alternate;
    e = e !== null ? e.memoizedState : null;
  } else e = re.next;
  var t = oe === null ? ee.memoizedState : oe.next;
  if (t !== null) oe = t, re = e;
  else {
    if (e === null) throw Error(z(310));
    re = e, e = { memoizedState: re.memoizedState, baseState: re.baseState, baseQueue: re.baseQueue, queue: re.queue, next: null }, oe === null ? ee.memoizedState = oe = e : oe = oe.next = e;
  }
  return oe;
}
function yl(e, t) {
  return typeof t == "function" ? t(e) : t;
}
function pr(e) {
  var t = De(), n = t.queue;
  if (n === null) throw Error(z(311));
  n.lastRenderedReducer = e;
  var s = re, r = s.baseQueue, i = n.pending;
  if (i !== null) {
    if (r !== null) {
      var a = r.next;
      r.next = i.next, i.next = a;
    }
    s.baseQueue = r = i, n.pending = null;
  }
  if (r !== null) {
    i = r.next, s = s.baseState;
    var u = a = null, o = null, d = i;
    do {
      var m = d.lane;
      if ((Jt & m) === m) o !== null && (o = o.next = { lane: 0, action: d.action, hasEagerState: d.hasEagerState, eagerState: d.eagerState, next: null }), s = d.hasEagerState ? d.eagerState : e(s, d.action);
      else {
        var p = {
          lane: m,
          action: d.action,
          hasEagerState: d.hasEagerState,
          eagerState: d.eagerState,
          next: null
        };
        o === null ? (u = o = p, a = s) : o = o.next = p, ee.lanes |= m, Zt |= m;
      }
      d = d.next;
    } while (d !== null && d !== i);
    o === null ? a = s : o.next = u, Qe(s, t.memoizedState) || (we = !0), t.memoizedState = s, t.baseState = a, t.baseQueue = o, n.lastRenderedState = s;
  }
  if (e = n.interleaved, e !== null) {
    r = e;
    do
      i = r.lane, ee.lanes |= i, Zt |= i, r = r.next;
    while (r !== e);
  } else r === null && (n.lanes = 0);
  return [t.memoizedState, n.dispatch];
}
function mr(e) {
  var t = De(), n = t.queue;
  if (n === null) throw Error(z(311));
  n.lastRenderedReducer = e;
  var s = n.dispatch, r = n.pending, i = t.memoizedState;
  if (r !== null) {
    n.pending = null;
    var a = r = r.next;
    do
      i = e(i, a.action), a = a.next;
    while (a !== r);
    Qe(i, t.memoizedState) || (we = !0), t.memoizedState = i, t.baseQueue === null && (t.baseState = i), n.lastRenderedState = i;
  }
  return [i, s];
}
function hc() {
}
function fc(e, t) {
  var n = ee, s = De(), r = t(), i = !Qe(s.memoizedState, r);
  if (i && (s.memoizedState = r, we = !0), s = s.queue, na(vc.bind(null, n, s, e), [e]), s.getSnapshot !== t || i || oe !== null && oe.memoizedState.tag & 1) {
    if (n.flags |= 2048, jl(9, mc.bind(null, n, s, r, t), void 0, null), ue === null) throw Error(z(349));
    Jt & 30 || pc(n, t, r);
  }
  return r;
}
function pc(e, t, n) {
  e.flags |= 16384, e = { getSnapshot: t, value: n }, t = ee.updateQueue, t === null ? (t = { lastEffect: null, stores: null }, ee.updateQueue = t, t.stores = [e]) : (n = t.stores, n === null ? t.stores = [e] : n.push(e));
}
function mc(e, t, n, s) {
  t.value = n, t.getSnapshot = s, gc(t) && xc(e);
}
function vc(e, t, n) {
  return n(function() {
    gc(t) && xc(e);
  });
}
function gc(e) {
  var t = e.getSnapshot;
  e = e.value;
  try {
    var n = t();
    return !Qe(e, n);
  } catch {
    return !0;
  }
}
function xc(e) {
  var t = dt(e, 1);
  t !== null && Ye(t, e, 1, -1);
}
function go(e) {
  var t = Ze();
  return typeof e == "function" && (e = e()), t.memoizedState = t.baseState = e, e = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: yl, lastRenderedState: e }, t.queue = e, e = e.dispatch = mf.bind(null, ee, e), [t.memoizedState, e];
}
function jl(e, t, n, s) {
  return e = { tag: e, create: t, destroy: n, deps: s, next: null }, t = ee.updateQueue, t === null ? (t = { lastEffect: null, stores: null }, ee.updateQueue = t, t.lastEffect = e.next = e) : (n = t.lastEffect, n === null ? t.lastEffect = e.next = e : (s = n.next, n.next = e, e.next = s, t.lastEffect = e)), e;
}
function yc() {
  return De().memoizedState;
}
function es(e, t, n, s) {
  var r = Ze();
  ee.flags |= e, r.memoizedState = jl(1 | t, n, void 0, s === void 0 ? null : s);
}
function Ds(e, t, n, s) {
  var r = De();
  s = s === void 0 ? null : s;
  var i = void 0;
  if (re !== null) {
    var a = re.memoizedState;
    if (i = a.destroy, s !== null && $i(s, a.deps)) {
      r.memoizedState = jl(t, n, i, s);
      return;
    }
  }
  ee.flags |= e, r.memoizedState = jl(1 | t, n, i, s);
}
function xo(e, t) {
  return es(8390656, 8, e, t);
}
function na(e, t) {
  return Ds(2048, 8, e, t);
}
function jc(e, t) {
  return Ds(4, 2, e, t);
}
function Nc(e, t) {
  return Ds(4, 4, e, t);
}
function wc(e, t) {
  if (typeof t == "function") return e = e(), t(e), function() {
    t(null);
  };
  if (t != null) return e = e(), t.current = e, function() {
    t.current = null;
  };
}
function kc(e, t, n) {
  return n = n != null ? n.concat([e]) : null, Ds(4, 4, wc.bind(null, t, e), n);
}
function la() {
}
function Cc(e, t) {
  var n = De();
  t = t === void 0 ? null : t;
  var s = n.memoizedState;
  return s !== null && t !== null && $i(t, s[1]) ? s[0] : (n.memoizedState = [e, t], e);
}
function Sc(e, t) {
  var n = De();
  t = t === void 0 ? null : t;
  var s = n.memoizedState;
  return s !== null && t !== null && $i(t, s[1]) ? s[0] : (e = e(), n.memoizedState = [e, t], e);
}
function bc(e, t, n) {
  return Jt & 21 ? (Qe(n, t) || (n = Pu(), ee.lanes |= n, Zt |= n, e.baseState = !0), t) : (e.baseState && (e.baseState = !1, we = !0), e.memoizedState = n);
}
function ff(e, t) {
  var n = Q;
  Q = n !== 0 && 4 > n ? n : 4, e(!0);
  var s = fr.transition;
  fr.transition = {};
  try {
    e(!1), t();
  } finally {
    Q = n, fr.transition = s;
  }
}
function Ec() {
  return De().memoizedState;
}
function pf(e, t, n) {
  var s = At(e);
  if (n = { lane: s, action: n, hasEagerState: !1, eagerState: null, next: null }, Mc(e)) Lc(t, n);
  else if (n = uc(e, t, n, s), n !== null) {
    var r = xe();
    Ye(n, e, s, r), Ac(n, t, s);
  }
}
function mf(e, t, n) {
  var s = At(e), r = { lane: s, action: n, hasEagerState: !1, eagerState: null, next: null };
  if (Mc(e)) Lc(t, r);
  else {
    var i = e.alternate;
    if (e.lanes === 0 && (i === null || i.lanes === 0) && (i = t.lastRenderedReducer, i !== null)) try {
      var a = t.lastRenderedState, u = i(a, n);
      if (r.hasEagerState = !0, r.eagerState = u, Qe(u, a)) {
        var o = t.interleaved;
        o === null ? (r.next = r, Xi(t)) : (r.next = o.next, o.next = r), t.interleaved = r;
        return;
      }
    } catch {
    } finally {
    }
    n = uc(e, t, r, s), n !== null && (r = xe(), Ye(n, e, s, r), Ac(n, t, s));
  }
}
function Mc(e) {
  var t = e.alternate;
  return e === ee || t !== null && t === ee;
}
function Lc(e, t) {
  tl = ks = !0;
  var n = e.pending;
  n === null ? t.next = t : (t.next = n.next, n.next = t), e.pending = t;
}
function Ac(e, t, n) {
  if (n & 4194240) {
    var s = t.lanes;
    s &= e.pendingLanes, n |= s, t.lanes = n, Ri(e, n);
  }
}
var Cs = { readContext: Oe, useCallback: fe, useContext: fe, useEffect: fe, useImperativeHandle: fe, useInsertionEffect: fe, useLayoutEffect: fe, useMemo: fe, useReducer: fe, useRef: fe, useState: fe, useDebugValue: fe, useDeferredValue: fe, useTransition: fe, useMutableSource: fe, useSyncExternalStore: fe, useId: fe, unstable_isNewReconciler: !1 }, vf = { readContext: Oe, useCallback: function(e, t) {
  return Ze().memoizedState = [e, t === void 0 ? null : t], e;
}, useContext: Oe, useEffect: xo, useImperativeHandle: function(e, t, n) {
  return n = n != null ? n.concat([e]) : null, es(
    4194308,
    4,
    wc.bind(null, t, e),
    n
  );
}, useLayoutEffect: function(e, t) {
  return es(4194308, 4, e, t);
}, useInsertionEffect: function(e, t) {
  return es(4, 2, e, t);
}, useMemo: function(e, t) {
  var n = Ze();
  return t = t === void 0 ? null : t, e = e(), n.memoizedState = [e, t], e;
}, useReducer: function(e, t, n) {
  var s = Ze();
  return t = n !== void 0 ? n(t) : t, s.memoizedState = s.baseState = t, e = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: e, lastRenderedState: t }, s.queue = e, e = e.dispatch = pf.bind(null, ee, e), [s.memoizedState, e];
}, useRef: function(e) {
  var t = Ze();
  return e = { current: e }, t.memoizedState = e;
}, useState: go, useDebugValue: la, useDeferredValue: function(e) {
  return Ze().memoizedState = e;
}, useTransition: function() {
  var e = go(!1), t = e[0];
  return e = ff.bind(null, e[1]), Ze().memoizedState = e, [t, e];
}, useMutableSource: function() {
}, useSyncExternalStore: function(e, t, n) {
  var s = ee, r = Ze();
  if (Z) {
    if (n === void 0) throw Error(z(407));
    n = n();
  } else {
    if (n = t(), ue === null) throw Error(z(349));
    Jt & 30 || pc(s, t, n);
  }
  r.memoizedState = n;
  var i = { value: n, getSnapshot: t };
  return r.queue = i, xo(vc.bind(
    null,
    s,
    i,
    e
  ), [e]), s.flags |= 2048, jl(9, mc.bind(null, s, i, n, t), void 0, null), n;
}, useId: function() {
  var e = Ze(), t = ue.identifierPrefix;
  if (Z) {
    var n = at, s = it;
    n = (s & ~(1 << 32 - He(s) - 1)).toString(32) + n, t = ":" + t + "R" + n, n = xl++, 0 < n && (t += "H" + n.toString(32)), t += ":";
  } else n = hf++, t = ":" + t + "r" + n.toString(32) + ":";
  return e.memoizedState = t;
}, unstable_isNewReconciler: !1 }, gf = {
  readContext: Oe,
  useCallback: Cc,
  useContext: Oe,
  useEffect: na,
  useImperativeHandle: kc,
  useInsertionEffect: jc,
  useLayoutEffect: Nc,
  useMemo: Sc,
  useReducer: pr,
  useRef: yc,
  useState: function() {
    return pr(yl);
  },
  useDebugValue: la,
  useDeferredValue: function(e) {
    var t = De();
    return bc(t, re.memoizedState, e);
  },
  useTransition: function() {
    var e = pr(yl)[0], t = De().memoizedState;
    return [e, t];
  },
  useMutableSource: hc,
  useSyncExternalStore: fc,
  useId: Ec,
  unstable_isNewReconciler: !1
}, xf = { readContext: Oe, useCallback: Cc, useContext: Oe, useEffect: na, useImperativeHandle: kc, useInsertionEffect: jc, useLayoutEffect: Nc, useMemo: Sc, useReducer: mr, useRef: yc, useState: function() {
  return mr(yl);
}, useDebugValue: la, useDeferredValue: function(e) {
  var t = De();
  return re === null ? t.memoizedState = e : bc(t, re.memoizedState, e);
}, useTransition: function() {
  var e = mr(yl)[0], t = De().memoizedState;
  return [e, t];
}, useMutableSource: hc, useSyncExternalStore: fc, useId: Ec, unstable_isNewReconciler: !1 };
function Ve(e, t) {
  if (e && e.defaultProps) {
    t = te({}, t), e = e.defaultProps;
    for (var n in e) t[n] === void 0 && (t[n] = e[n]);
    return t;
  }
  return t;
}
function si(e, t, n, s) {
  t = e.memoizedState, n = n(s, t), n = n == null ? t : te({}, t, n), e.memoizedState = n, e.lanes === 0 && (e.updateQueue.baseState = n);
}
var Is = { isMounted: function(e) {
  return (e = e._reactInternals) ? en(e) === e : !1;
}, enqueueSetState: function(e, t, n) {
  e = e._reactInternals;
  var s = xe(), r = At(e), i = ot(s, r);
  i.payload = t, n != null && (i.callback = n), t = Mt(e, i, r), t !== null && (Ye(t, e, r, s), _l(t, e, r));
}, enqueueReplaceState: function(e, t, n) {
  e = e._reactInternals;
  var s = xe(), r = At(e), i = ot(s, r);
  i.tag = 1, i.payload = t, n != null && (i.callback = n), t = Mt(e, i, r), t !== null && (Ye(t, e, r, s), _l(t, e, r));
}, enqueueForceUpdate: function(e, t) {
  e = e._reactInternals;
  var n = xe(), s = At(e), r = ot(n, s);
  r.tag = 2, t != null && (r.callback = t), t = Mt(e, r, s), t !== null && (Ye(t, e, s, n), _l(t, e, s));
} };
function yo(e, t, n, s, r, i, a) {
  return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(s, i, a) : t.prototype && t.prototype.isPureReactComponent ? !hl(n, s) || !hl(r, i) : !0;
}
function Pc(e, t, n) {
  var s = !1, r = Tt, i = t.contextType;
  return typeof i == "object" && i !== null ? i = Oe(i) : (r = Ce(t) ? Xt : ve.current, s = t.contextTypes, i = (s = s != null) ? Sn(e, r) : Tt), t = new t(n, i), e.memoizedState = t.state !== null && t.state !== void 0 ? t.state : null, t.updater = Is, e.stateNode = t, t._reactInternals = e, s && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = r, e.__reactInternalMemoizedMaskedChildContext = i), t;
}
function jo(e, t, n, s) {
  e = t.state, typeof t.componentWillReceiveProps == "function" && t.componentWillReceiveProps(n, s), typeof t.UNSAFE_componentWillReceiveProps == "function" && t.UNSAFE_componentWillReceiveProps(n, s), t.state !== e && Is.enqueueReplaceState(t, t.state, null);
}
function ri(e, t, n, s) {
  var r = e.stateNode;
  r.props = n, r.state = e.memoizedState, r.refs = {}, Gi(e);
  var i = t.contextType;
  typeof i == "object" && i !== null ? r.context = Oe(i) : (i = Ce(t) ? Xt : ve.current, r.context = Sn(e, i)), r.state = e.memoizedState, i = t.getDerivedStateFromProps, typeof i == "function" && (si(e, t, i, n), r.state = e.memoizedState), typeof t.getDerivedStateFromProps == "function" || typeof r.getSnapshotBeforeUpdate == "function" || typeof r.UNSAFE_componentWillMount != "function" && typeof r.componentWillMount != "function" || (t = r.state, typeof r.componentWillMount == "function" && r.componentWillMount(), typeof r.UNSAFE_componentWillMount == "function" && r.UNSAFE_componentWillMount(), t !== r.state && Is.enqueueReplaceState(r, r.state, null), Ns(e, n, r, s), r.state = e.memoizedState), typeof r.componentDidMount == "function" && (e.flags |= 4194308);
}
function Ln(e, t) {
  try {
    var n = "", s = t;
    do
      n += Yd(s), s = s.return;
    while (s);
    var r = n;
  } catch (i) {
    r = `
Error generating stack: ` + i.message + `
` + i.stack;
  }
  return { value: e, source: t, stack: r, digest: null };
}
function vr(e, t, n) {
  return { value: e, source: null, stack: n ?? null, digest: t ?? null };
}
function ii(e, t) {
  try {
    console.error(t.value);
  } catch (n) {
    setTimeout(function() {
      throw n;
    });
  }
}
var yf = typeof WeakMap == "function" ? WeakMap : Map;
function zc(e, t, n) {
  n = ot(-1, n), n.tag = 3, n.payload = { element: null };
  var s = t.value;
  return n.callback = function() {
    bs || (bs = !0, vi = s), ii(e, t);
  }, n;
}
function Tc(e, t, n) {
  n = ot(-1, n), n.tag = 3;
  var s = e.type.getDerivedStateFromError;
  if (typeof s == "function") {
    var r = t.value;
    n.payload = function() {
      return s(r);
    }, n.callback = function() {
      ii(e, t);
    };
  }
  var i = e.stateNode;
  return i !== null && typeof i.componentDidCatch == "function" && (n.callback = function() {
    ii(e, t), typeof s != "function" && (Lt === null ? Lt = /* @__PURE__ */ new Set([this]) : Lt.add(this));
    var a = t.stack;
    this.componentDidCatch(t.value, { componentStack: a !== null ? a : "" });
  }), n;
}
function No(e, t, n) {
  var s = e.pingCache;
  if (s === null) {
    s = e.pingCache = new yf();
    var r = /* @__PURE__ */ new Set();
    s.set(t, r);
  } else r = s.get(t), r === void 0 && (r = /* @__PURE__ */ new Set(), s.set(t, r));
  r.has(n) || (r.add(n), e = Tf.bind(null, e, t, n), t.then(e, e));
}
function wo(e) {
  do {
    var t;
    if ((t = e.tag === 13) && (t = e.memoizedState, t = t !== null ? t.dehydrated !== null : !0), t) return e;
    e = e.return;
  } while (e !== null);
  return null;
}
function ko(e, t, n, s, r) {
  return e.mode & 1 ? (e.flags |= 65536, e.lanes = r, e) : (e === t ? e.flags |= 65536 : (e.flags |= 128, n.flags |= 131072, n.flags &= -52805, n.tag === 1 && (n.alternate === null ? n.tag = 17 : (t = ot(-1, 1), t.tag = 2, Mt(n, t, 1))), n.lanes |= 1), e);
}
var jf = ft.ReactCurrentOwner, we = !1;
function ge(e, t, n, s) {
  t.child = e === null ? oc(t, null, n, s) : En(t, e.child, n, s);
}
function Co(e, t, n, s, r) {
  n = n.render;
  var i = t.ref;
  return wn(t, r), s = ea(e, t, n, s, i, r), n = ta(), e !== null && !we ? (t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~r, ht(e, t, r)) : (Z && n && Wi(t), t.flags |= 1, ge(e, t, s, r), t.child);
}
function So(e, t, n, s, r) {
  if (e === null) {
    var i = n.type;
    return typeof i == "function" && !da(i) && i.defaultProps === void 0 && n.compare === null && n.defaultProps === void 0 ? (t.tag = 15, t.type = i, Rc(e, t, i, s, r)) : (e = ss(n.type, null, s, t, t.mode, r), e.ref = t.ref, e.return = t, t.child = e);
  }
  if (i = e.child, !(e.lanes & r)) {
    var a = i.memoizedProps;
    if (n = n.compare, n = n !== null ? n : hl, n(a, s) && e.ref === t.ref) return ht(e, t, r);
  }
  return t.flags |= 1, e = Pt(i, s), e.ref = t.ref, e.return = t, t.child = e;
}
function Rc(e, t, n, s, r) {
  if (e !== null) {
    var i = e.memoizedProps;
    if (hl(i, s) && e.ref === t.ref) if (we = !1, t.pendingProps = s = i, (e.lanes & r) !== 0) e.flags & 131072 && (we = !0);
    else return t.lanes = e.lanes, ht(e, t, r);
  }
  return ai(e, t, n, s, r);
}
function Fc(e, t, n) {
  var s = t.pendingProps, r = s.children, i = e !== null ? e.memoizedState : null;
  if (s.mode === "hidden") if (!(t.mode & 1)) t.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, X(mn, be), be |= n;
  else {
    if (!(n & 1073741824)) return e = i !== null ? i.baseLanes | n : n, t.lanes = t.childLanes = 1073741824, t.memoizedState = { baseLanes: e, cachePool: null, transitions: null }, t.updateQueue = null, X(mn, be), be |= e, null;
    t.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, s = i !== null ? i.baseLanes : n, X(mn, be), be |= s;
  }
  else i !== null ? (s = i.baseLanes | n, t.memoizedState = null) : s = n, X(mn, be), be |= s;
  return ge(e, t, r, n), t.child;
}
function Oc(e, t) {
  var n = t.ref;
  (e === null && n !== null || e !== null && e.ref !== n) && (t.flags |= 512, t.flags |= 2097152);
}
function ai(e, t, n, s, r) {
  var i = Ce(n) ? Xt : ve.current;
  return i = Sn(t, i), wn(t, r), n = ea(e, t, n, s, i, r), s = ta(), e !== null && !we ? (t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~r, ht(e, t, r)) : (Z && s && Wi(t), t.flags |= 1, ge(e, t, n, r), t.child);
}
function bo(e, t, n, s, r) {
  if (Ce(n)) {
    var i = !0;
    vs(t);
  } else i = !1;
  if (wn(t, r), t.stateNode === null) ts(e, t), Pc(t, n, s), ri(t, n, s, r), s = !0;
  else if (e === null) {
    var a = t.stateNode, u = t.memoizedProps;
    a.props = u;
    var o = a.context, d = n.contextType;
    typeof d == "object" && d !== null ? d = Oe(d) : (d = Ce(n) ? Xt : ve.current, d = Sn(t, d));
    var m = n.getDerivedStateFromProps, p = typeof m == "function" || typeof a.getSnapshotBeforeUpdate == "function";
    p || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (u !== s || o !== d) && jo(t, a, s, d), xt = !1;
    var v = t.memoizedState;
    a.state = v, Ns(t, s, a, r), o = t.memoizedState, u !== s || v !== o || ke.current || xt ? (typeof m == "function" && (si(t, n, m, s), o = t.memoizedState), (u = xt || yo(t, n, u, s, v, o, d)) ? (p || typeof a.UNSAFE_componentWillMount != "function" && typeof a.componentWillMount != "function" || (typeof a.componentWillMount == "function" && a.componentWillMount(), typeof a.UNSAFE_componentWillMount == "function" && a.UNSAFE_componentWillMount()), typeof a.componentDidMount == "function" && (t.flags |= 4194308)) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), t.memoizedProps = s, t.memoizedState = o), a.props = s, a.state = o, a.context = d, s = u) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), s = !1);
  } else {
    a = t.stateNode, cc(e, t), u = t.memoizedProps, d = t.type === t.elementType ? u : Ve(t.type, u), a.props = d, p = t.pendingProps, v = a.context, o = n.contextType, typeof o == "object" && o !== null ? o = Oe(o) : (o = Ce(n) ? Xt : ve.current, o = Sn(t, o));
    var j = n.getDerivedStateFromProps;
    (m = typeof j == "function" || typeof a.getSnapshotBeforeUpdate == "function") || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (u !== p || v !== o) && jo(t, a, s, o), xt = !1, v = t.memoizedState, a.state = v, Ns(t, s, a, r);
    var y = t.memoizedState;
    u !== p || v !== y || ke.current || xt ? (typeof j == "function" && (si(t, n, j, s), y = t.memoizedState), (d = xt || yo(t, n, d, s, v, y, o) || !1) ? (m || typeof a.UNSAFE_componentWillUpdate != "function" && typeof a.componentWillUpdate != "function" || (typeof a.componentWillUpdate == "function" && a.componentWillUpdate(s, y, o), typeof a.UNSAFE_componentWillUpdate == "function" && a.UNSAFE_componentWillUpdate(s, y, o)), typeof a.componentDidUpdate == "function" && (t.flags |= 4), typeof a.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024)) : (typeof a.componentDidUpdate != "function" || u === e.memoizedProps && v === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || u === e.memoizedProps && v === e.memoizedState || (t.flags |= 1024), t.memoizedProps = s, t.memoizedState = y), a.props = s, a.state = y, a.context = o, s = d) : (typeof a.componentDidUpdate != "function" || u === e.memoizedProps && v === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || u === e.memoizedProps && v === e.memoizedState || (t.flags |= 1024), s = !1);
  }
  return oi(e, t, n, s, i, r);
}
function oi(e, t, n, s, r, i) {
  Oc(e, t);
  var a = (t.flags & 128) !== 0;
  if (!s && !a) return r && co(t, n, !1), ht(e, t, i);
  s = t.stateNode, jf.current = t;
  var u = a && typeof n.getDerivedStateFromError != "function" ? null : s.render();
  return t.flags |= 1, e !== null && a ? (t.child = En(t, e.child, null, i), t.child = En(t, null, u, i)) : ge(e, t, u, i), t.memoizedState = s.state, r && co(t, n, !0), t.child;
}
function Dc(e) {
  var t = e.stateNode;
  t.pendingContext ? uo(e, t.pendingContext, t.pendingContext !== t.context) : t.context && uo(e, t.context, !1), Ji(e, t.containerInfo);
}
function Eo(e, t, n, s, r) {
  return bn(), Hi(r), t.flags |= 256, ge(e, t, n, s), t.child;
}
var ui = { dehydrated: null, treeContext: null, retryLane: 0 };
function ci(e) {
  return { baseLanes: e, cachePool: null, transitions: null };
}
function Ic(e, t, n) {
  var s = t.pendingProps, r = $.current, i = !1, a = (t.flags & 128) !== 0, u;
  if ((u = a) || (u = e !== null && e.memoizedState === null ? !1 : (r & 2) !== 0), u ? (i = !0, t.flags &= -129) : (e === null || e.memoizedState !== null) && (r |= 1), X($, r & 1), e === null)
    return ni(t), e = t.memoizedState, e !== null && (e = e.dehydrated, e !== null) ? (t.mode & 1 ? e.data === "$!" ? t.lanes = 8 : t.lanes = 1073741824 : t.lanes = 1, null) : (a = s.children, e = s.fallback, i ? (s = t.mode, i = t.child, a = { mode: "hidden", children: a }, !(s & 1) && i !== null ? (i.childLanes = 0, i.pendingProps = a) : i = Vs(a, s, 0, null), e = Qt(e, s, n, null), i.return = t, e.return = t, i.sibling = e, t.child = i, t.child.memoizedState = ci(n), t.memoizedState = ui, e) : sa(t, a));
  if (r = e.memoizedState, r !== null && (u = r.dehydrated, u !== null)) return Nf(e, t, a, s, u, r, n);
  if (i) {
    i = s.fallback, a = t.mode, r = e.child, u = r.sibling;
    var o = { mode: "hidden", children: s.children };
    return !(a & 1) && t.child !== r ? (s = t.child, s.childLanes = 0, s.pendingProps = o, t.deletions = null) : (s = Pt(r, o), s.subtreeFlags = r.subtreeFlags & 14680064), u !== null ? i = Pt(u, i) : (i = Qt(i, a, n, null), i.flags |= 2), i.return = t, s.return = t, s.sibling = i, t.child = s, s = i, i = t.child, a = e.child.memoizedState, a = a === null ? ci(n) : { baseLanes: a.baseLanes | n, cachePool: null, transitions: a.transitions }, i.memoizedState = a, i.childLanes = e.childLanes & ~n, t.memoizedState = ui, s;
  }
  return i = e.child, e = i.sibling, s = Pt(i, { mode: "visible", children: s.children }), !(t.mode & 1) && (s.lanes = n), s.return = t, s.sibling = null, e !== null && (n = t.deletions, n === null ? (t.deletions = [e], t.flags |= 16) : n.push(e)), t.child = s, t.memoizedState = null, s;
}
function sa(e, t) {
  return t = Vs({ mode: "visible", children: t }, e.mode, 0, null), t.return = e, e.child = t;
}
function Bl(e, t, n, s) {
  return s !== null && Hi(s), En(t, e.child, null, n), e = sa(t, t.pendingProps.children), e.flags |= 2, t.memoizedState = null, e;
}
function Nf(e, t, n, s, r, i, a) {
  if (n)
    return t.flags & 256 ? (t.flags &= -257, s = vr(Error(z(422))), Bl(e, t, a, s)) : t.memoizedState !== null ? (t.child = e.child, t.flags |= 128, null) : (i = s.fallback, r = t.mode, s = Vs({ mode: "visible", children: s.children }, r, 0, null), i = Qt(i, r, a, null), i.flags |= 2, s.return = t, i.return = t, s.sibling = i, t.child = s, t.mode & 1 && En(t, e.child, null, a), t.child.memoizedState = ci(a), t.memoizedState = ui, i);
  if (!(t.mode & 1)) return Bl(e, t, a, null);
  if (r.data === "$!") {
    if (s = r.nextSibling && r.nextSibling.dataset, s) var u = s.dgst;
    return s = u, i = Error(z(419)), s = vr(i, s, void 0), Bl(e, t, a, s);
  }
  if (u = (a & e.childLanes) !== 0, we || u) {
    if (s = ue, s !== null) {
      switch (a & -a) {
        case 4:
          r = 2;
          break;
        case 16:
          r = 8;
          break;
        case 64:
        case 128:
        case 256:
        case 512:
        case 1024:
        case 2048:
        case 4096:
        case 8192:
        case 16384:
        case 32768:
        case 65536:
        case 131072:
        case 262144:
        case 524288:
        case 1048576:
        case 2097152:
        case 4194304:
        case 8388608:
        case 16777216:
        case 33554432:
        case 67108864:
          r = 32;
          break;
        case 536870912:
          r = 268435456;
          break;
        default:
          r = 0;
      }
      r = r & (s.suspendedLanes | a) ? 0 : r, r !== 0 && r !== i.retryLane && (i.retryLane = r, dt(e, r), Ye(s, e, r, -1));
    }
    return ca(), s = vr(Error(z(421))), Bl(e, t, a, s);
  }
  return r.data === "$?" ? (t.flags |= 128, t.child = e.child, t = Rf.bind(null, e), r._reactRetry = t, null) : (e = i.treeContext, Ee = Et(r.nextSibling), Me = t, Z = !0, qe = null, e !== null && (ze[Te++] = it, ze[Te++] = at, ze[Te++] = Gt, it = e.id, at = e.overflow, Gt = t), t = sa(t, s.children), t.flags |= 4096, t);
}
function Mo(e, t, n) {
  e.lanes |= t;
  var s = e.alternate;
  s !== null && (s.lanes |= t), li(e.return, t, n);
}
function gr(e, t, n, s, r) {
  var i = e.memoizedState;
  i === null ? e.memoizedState = { isBackwards: t, rendering: null, renderingStartTime: 0, last: s, tail: n, tailMode: r } : (i.isBackwards = t, i.rendering = null, i.renderingStartTime = 0, i.last = s, i.tail = n, i.tailMode = r);
}
function Uc(e, t, n) {
  var s = t.pendingProps, r = s.revealOrder, i = s.tail;
  if (ge(e, t, s.children, n), s = $.current, s & 2) s = s & 1 | 2, t.flags |= 128;
  else {
    if (e !== null && e.flags & 128) e: for (e = t.child; e !== null; ) {
      if (e.tag === 13) e.memoizedState !== null && Mo(e, n, t);
      else if (e.tag === 19) Mo(e, n, t);
      else if (e.child !== null) {
        e.child.return = e, e = e.child;
        continue;
      }
      if (e === t) break e;
      for (; e.sibling === null; ) {
        if (e.return === null || e.return === t) break e;
        e = e.return;
      }
      e.sibling.return = e.return, e = e.sibling;
    }
    s &= 1;
  }
  if (X($, s), !(t.mode & 1)) t.memoizedState = null;
  else switch (r) {
    case "forwards":
      for (n = t.child, r = null; n !== null; ) e = n.alternate, e !== null && ws(e) === null && (r = n), n = n.sibling;
      n = r, n === null ? (r = t.child, t.child = null) : (r = n.sibling, n.sibling = null), gr(t, !1, r, n, i);
      break;
    case "backwards":
      for (n = null, r = t.child, t.child = null; r !== null; ) {
        if (e = r.alternate, e !== null && ws(e) === null) {
          t.child = r;
          break;
        }
        e = r.sibling, r.sibling = n, n = r, r = e;
      }
      gr(t, !0, n, null, i);
      break;
    case "together":
      gr(t, !1, null, null, void 0);
      break;
    default:
      t.memoizedState = null;
  }
  return t.child;
}
function ts(e, t) {
  !(t.mode & 1) && e !== null && (e.alternate = null, t.alternate = null, t.flags |= 2);
}
function ht(e, t, n) {
  if (e !== null && (t.dependencies = e.dependencies), Zt |= t.lanes, !(n & t.childLanes)) return null;
  if (e !== null && t.child !== e.child) throw Error(z(153));
  if (t.child !== null) {
    for (e = t.child, n = Pt(e, e.pendingProps), t.child = n, n.return = t; e.sibling !== null; ) e = e.sibling, n = n.sibling = Pt(e, e.pendingProps), n.return = t;
    n.sibling = null;
  }
  return t.child;
}
function wf(e, t, n) {
  switch (t.tag) {
    case 3:
      Dc(t), bn();
      break;
    case 5:
      dc(t);
      break;
    case 1:
      Ce(t.type) && vs(t);
      break;
    case 4:
      Ji(t, t.stateNode.containerInfo);
      break;
    case 10:
      var s = t.type._context, r = t.memoizedProps.value;
      X(ys, s._currentValue), s._currentValue = r;
      break;
    case 13:
      if (s = t.memoizedState, s !== null)
        return s.dehydrated !== null ? (X($, $.current & 1), t.flags |= 128, null) : n & t.child.childLanes ? Ic(e, t, n) : (X($, $.current & 1), e = ht(e, t, n), e !== null ? e.sibling : null);
      X($, $.current & 1);
      break;
    case 19:
      if (s = (n & t.childLanes) !== 0, e.flags & 128) {
        if (s) return Uc(e, t, n);
        t.flags |= 128;
      }
      if (r = t.memoizedState, r !== null && (r.rendering = null, r.tail = null, r.lastEffect = null), X($, $.current), s) break;
      return null;
    case 22:
    case 23:
      return t.lanes = 0, Fc(e, t, n);
  }
  return ht(e, t, n);
}
var Bc, di, Vc, Wc;
Bc = function(e, t) {
  for (var n = t.child; n !== null; ) {
    if (n.tag === 5 || n.tag === 6) e.appendChild(n.stateNode);
    else if (n.tag !== 4 && n.child !== null) {
      n.child.return = n, n = n.child;
      continue;
    }
    if (n === t) break;
    for (; n.sibling === null; ) {
      if (n.return === null || n.return === t) return;
      n = n.return;
    }
    n.sibling.return = n.return, n = n.sibling;
  }
};
di = function() {
};
Vc = function(e, t, n, s) {
  var r = e.memoizedProps;
  if (r !== s) {
    e = t.stateNode, Ht(tt.current);
    var i = null;
    switch (n) {
      case "input":
        r = Tr(e, r), s = Tr(e, s), i = [];
        break;
      case "select":
        r = te({}, r, { value: void 0 }), s = te({}, s, { value: void 0 }), i = [];
        break;
      case "textarea":
        r = Or(e, r), s = Or(e, s), i = [];
        break;
      default:
        typeof r.onClick != "function" && typeof s.onClick == "function" && (e.onclick = ps);
    }
    Ir(n, s);
    var a;
    n = null;
    for (d in r) if (!s.hasOwnProperty(d) && r.hasOwnProperty(d) && r[d] != null) if (d === "style") {
      var u = r[d];
      for (a in u) u.hasOwnProperty(a) && (n || (n = {}), n[a] = "");
    } else d !== "dangerouslySetInnerHTML" && d !== "children" && d !== "suppressContentEditableWarning" && d !== "suppressHydrationWarning" && d !== "autoFocus" && (rl.hasOwnProperty(d) ? i || (i = []) : (i = i || []).push(d, null));
    for (d in s) {
      var o = s[d];
      if (u = r != null ? r[d] : void 0, s.hasOwnProperty(d) && o !== u && (o != null || u != null)) if (d === "style") if (u) {
        for (a in u) !u.hasOwnProperty(a) || o && o.hasOwnProperty(a) || (n || (n = {}), n[a] = "");
        for (a in o) o.hasOwnProperty(a) && u[a] !== o[a] && (n || (n = {}), n[a] = o[a]);
      } else n || (i || (i = []), i.push(
        d,
        n
      )), n = o;
      else d === "dangerouslySetInnerHTML" ? (o = o ? o.__html : void 0, u = u ? u.__html : void 0, o != null && u !== o && (i = i || []).push(d, o)) : d === "children" ? typeof o != "string" && typeof o != "number" || (i = i || []).push(d, "" + o) : d !== "suppressContentEditableWarning" && d !== "suppressHydrationWarning" && (rl.hasOwnProperty(d) ? (o != null && d === "onScroll" && G("scroll", e), i || u === o || (i = [])) : (i = i || []).push(d, o));
    }
    n && (i = i || []).push("style", n);
    var d = i;
    (t.updateQueue = d) && (t.flags |= 4);
  }
};
Wc = function(e, t, n, s) {
  n !== s && (t.flags |= 4);
};
function Hn(e, t) {
  if (!Z) switch (e.tailMode) {
    case "hidden":
      t = e.tail;
      for (var n = null; t !== null; ) t.alternate !== null && (n = t), t = t.sibling;
      n === null ? e.tail = null : n.sibling = null;
      break;
    case "collapsed":
      n = e.tail;
      for (var s = null; n !== null; ) n.alternate !== null && (s = n), n = n.sibling;
      s === null ? t || e.tail === null ? e.tail = null : e.tail.sibling = null : s.sibling = null;
  }
}
function pe(e) {
  var t = e.alternate !== null && e.alternate.child === e.child, n = 0, s = 0;
  if (t) for (var r = e.child; r !== null; ) n |= r.lanes | r.childLanes, s |= r.subtreeFlags & 14680064, s |= r.flags & 14680064, r.return = e, r = r.sibling;
  else for (r = e.child; r !== null; ) n |= r.lanes | r.childLanes, s |= r.subtreeFlags, s |= r.flags, r.return = e, r = r.sibling;
  return e.subtreeFlags |= s, e.childLanes = n, t;
}
function kf(e, t, n) {
  var s = t.pendingProps;
  switch (qi(t), t.tag) {
    case 2:
    case 16:
    case 15:
    case 0:
    case 11:
    case 7:
    case 8:
    case 12:
    case 9:
    case 14:
      return pe(t), null;
    case 1:
      return Ce(t.type) && ms(), pe(t), null;
    case 3:
      return s = t.stateNode, Mn(), J(ke), J(ve), _i(), s.pendingContext && (s.context = s.pendingContext, s.pendingContext = null), (e === null || e.child === null) && (Il(t) ? t.flags |= 4 : e === null || e.memoizedState.isDehydrated && !(t.flags & 256) || (t.flags |= 1024, qe !== null && (yi(qe), qe = null))), di(e, t), pe(t), null;
    case 5:
      Zi(t);
      var r = Ht(gl.current);
      if (n = t.type, e !== null && t.stateNode != null) Vc(e, t, n, s, r), e.ref !== t.ref && (t.flags |= 512, t.flags |= 2097152);
      else {
        if (!s) {
          if (t.stateNode === null) throw Error(z(166));
          return pe(t), null;
        }
        if (e = Ht(tt.current), Il(t)) {
          s = t.stateNode, n = t.type;
          var i = t.memoizedProps;
          switch (s[_e] = t, s[ml] = i, e = (t.mode & 1) !== 0, n) {
            case "dialog":
              G("cancel", s), G("close", s);
              break;
            case "iframe":
            case "object":
            case "embed":
              G("load", s);
              break;
            case "video":
            case "audio":
              for (r = 0; r < Gn.length; r++) G(Gn[r], s);
              break;
            case "source":
              G("error", s);
              break;
            case "img":
            case "image":
            case "link":
              G(
                "error",
                s
              ), G("load", s);
              break;
            case "details":
              G("toggle", s);
              break;
            case "input":
              Oa(s, i), G("invalid", s);
              break;
            case "select":
              s._wrapperState = { wasMultiple: !!i.multiple }, G("invalid", s);
              break;
            case "textarea":
              Ia(s, i), G("invalid", s);
          }
          Ir(n, i), r = null;
          for (var a in i) if (i.hasOwnProperty(a)) {
            var u = i[a];
            a === "children" ? typeof u == "string" ? s.textContent !== u && (i.suppressHydrationWarning !== !0 && Dl(s.textContent, u, e), r = ["children", u]) : typeof u == "number" && s.textContent !== "" + u && (i.suppressHydrationWarning !== !0 && Dl(
              s.textContent,
              u,
              e
            ), r = ["children", "" + u]) : rl.hasOwnProperty(a) && u != null && a === "onScroll" && G("scroll", s);
          }
          switch (n) {
            case "input":
              Ll(s), Da(s, i, !0);
              break;
            case "textarea":
              Ll(s), Ua(s);
              break;
            case "select":
            case "option":
              break;
            default:
              typeof i.onClick == "function" && (s.onclick = ps);
          }
          s = r, t.updateQueue = s, s !== null && (t.flags |= 4);
        } else {
          a = r.nodeType === 9 ? r : r.ownerDocument, e === "http://www.w3.org/1999/xhtml" && (e = vu(n)), e === "http://www.w3.org/1999/xhtml" ? n === "script" ? (e = a.createElement("div"), e.innerHTML = "<script><\/script>", e = e.removeChild(e.firstChild)) : typeof s.is == "string" ? e = a.createElement(n, { is: s.is }) : (e = a.createElement(n), n === "select" && (a = e, s.multiple ? a.multiple = !0 : s.size && (a.size = s.size))) : e = a.createElementNS(e, n), e[_e] = t, e[ml] = s, Bc(e, t, !1, !1), t.stateNode = e;
          e: {
            switch (a = Ur(n, s), n) {
              case "dialog":
                G("cancel", e), G("close", e), r = s;
                break;
              case "iframe":
              case "object":
              case "embed":
                G("load", e), r = s;
                break;
              case "video":
              case "audio":
                for (r = 0; r < Gn.length; r++) G(Gn[r], e);
                r = s;
                break;
              case "source":
                G("error", e), r = s;
                break;
              case "img":
              case "image":
              case "link":
                G(
                  "error",
                  e
                ), G("load", e), r = s;
                break;
              case "details":
                G("toggle", e), r = s;
                break;
              case "input":
                Oa(e, s), r = Tr(e, s), G("invalid", e);
                break;
              case "option":
                r = s;
                break;
              case "select":
                e._wrapperState = { wasMultiple: !!s.multiple }, r = te({}, s, { value: void 0 }), G("invalid", e);
                break;
              case "textarea":
                Ia(e, s), r = Or(e, s), G("invalid", e);
                break;
              default:
                r = s;
            }
            Ir(n, r), u = r;
            for (i in u) if (u.hasOwnProperty(i)) {
              var o = u[i];
              i === "style" ? yu(e, o) : i === "dangerouslySetInnerHTML" ? (o = o ? o.__html : void 0, o != null && gu(e, o)) : i === "children" ? typeof o == "string" ? (n !== "textarea" || o !== "") && il(e, o) : typeof o == "number" && il(e, "" + o) : i !== "suppressContentEditableWarning" && i !== "suppressHydrationWarning" && i !== "autoFocus" && (rl.hasOwnProperty(i) ? o != null && i === "onScroll" && G("scroll", e) : o != null && Mi(e, i, o, a));
            }
            switch (n) {
              case "input":
                Ll(e), Da(e, s, !1);
                break;
              case "textarea":
                Ll(e), Ua(e);
                break;
              case "option":
                s.value != null && e.setAttribute("value", "" + zt(s.value));
                break;
              case "select":
                e.multiple = !!s.multiple, i = s.value, i != null ? xn(e, !!s.multiple, i, !1) : s.defaultValue != null && xn(
                  e,
                  !!s.multiple,
                  s.defaultValue,
                  !0
                );
                break;
              default:
                typeof r.onClick == "function" && (e.onclick = ps);
            }
            switch (n) {
              case "button":
              case "input":
              case "select":
              case "textarea":
                s = !!s.autoFocus;
                break e;
              case "img":
                s = !0;
                break e;
              default:
                s = !1;
            }
          }
          s && (t.flags |= 4);
        }
        t.ref !== null && (t.flags |= 512, t.flags |= 2097152);
      }
      return pe(t), null;
    case 6:
      if (e && t.stateNode != null) Wc(e, t, e.memoizedProps, s);
      else {
        if (typeof s != "string" && t.stateNode === null) throw Error(z(166));
        if (n = Ht(gl.current), Ht(tt.current), Il(t)) {
          if (s = t.stateNode, n = t.memoizedProps, s[_e] = t, (i = s.nodeValue !== n) && (e = Me, e !== null)) switch (e.tag) {
            case 3:
              Dl(s.nodeValue, n, (e.mode & 1) !== 0);
              break;
            case 5:
              e.memoizedProps.suppressHydrationWarning !== !0 && Dl(s.nodeValue, n, (e.mode & 1) !== 0);
          }
          i && (t.flags |= 4);
        } else s = (n.nodeType === 9 ? n : n.ownerDocument).createTextNode(s), s[_e] = t, t.stateNode = s;
      }
      return pe(t), null;
    case 13:
      if (J($), s = t.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
        if (Z && Ee !== null && t.mode & 1 && !(t.flags & 128)) ic(), bn(), t.flags |= 98560, i = !1;
        else if (i = Il(t), s !== null && s.dehydrated !== null) {
          if (e === null) {
            if (!i) throw Error(z(318));
            if (i = t.memoizedState, i = i !== null ? i.dehydrated : null, !i) throw Error(z(317));
            i[_e] = t;
          } else bn(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
          pe(t), i = !1;
        } else qe !== null && (yi(qe), qe = null), i = !0;
        if (!i) return t.flags & 65536 ? t : null;
      }
      return t.flags & 128 ? (t.lanes = n, t) : (s = s !== null, s !== (e !== null && e.memoizedState !== null) && s && (t.child.flags |= 8192, t.mode & 1 && (e === null || $.current & 1 ? ie === 0 && (ie = 3) : ca())), t.updateQueue !== null && (t.flags |= 4), pe(t), null);
    case 4:
      return Mn(), di(e, t), e === null && fl(t.stateNode.containerInfo), pe(t), null;
    case 10:
      return Ki(t.type._context), pe(t), null;
    case 17:
      return Ce(t.type) && ms(), pe(t), null;
    case 19:
      if (J($), i = t.memoizedState, i === null) return pe(t), null;
      if (s = (t.flags & 128) !== 0, a = i.rendering, a === null) if (s) Hn(i, !1);
      else {
        if (ie !== 0 || e !== null && e.flags & 128) for (e = t.child; e !== null; ) {
          if (a = ws(e), a !== null) {
            for (t.flags |= 128, Hn(i, !1), s = a.updateQueue, s !== null && (t.updateQueue = s, t.flags |= 4), t.subtreeFlags = 0, s = n, n = t.child; n !== null; ) i = n, e = s, i.flags &= 14680066, a = i.alternate, a === null ? (i.childLanes = 0, i.lanes = e, i.child = null, i.subtreeFlags = 0, i.memoizedProps = null, i.memoizedState = null, i.updateQueue = null, i.dependencies = null, i.stateNode = null) : (i.childLanes = a.childLanes, i.lanes = a.lanes, i.child = a.child, i.subtreeFlags = 0, i.deletions = null, i.memoizedProps = a.memoizedProps, i.memoizedState = a.memoizedState, i.updateQueue = a.updateQueue, i.type = a.type, e = a.dependencies, i.dependencies = e === null ? null : { lanes: e.lanes, firstContext: e.firstContext }), n = n.sibling;
            return X($, $.current & 1 | 2), t.child;
          }
          e = e.sibling;
        }
        i.tail !== null && le() > An && (t.flags |= 128, s = !0, Hn(i, !1), t.lanes = 4194304);
      }
      else {
        if (!s) if (e = ws(a), e !== null) {
          if (t.flags |= 128, s = !0, n = e.updateQueue, n !== null && (t.updateQueue = n, t.flags |= 4), Hn(i, !0), i.tail === null && i.tailMode === "hidden" && !a.alternate && !Z) return pe(t), null;
        } else 2 * le() - i.renderingStartTime > An && n !== 1073741824 && (t.flags |= 128, s = !0, Hn(i, !1), t.lanes = 4194304);
        i.isBackwards ? (a.sibling = t.child, t.child = a) : (n = i.last, n !== null ? n.sibling = a : t.child = a, i.last = a);
      }
      return i.tail !== null ? (t = i.tail, i.rendering = t, i.tail = t.sibling, i.renderingStartTime = le(), t.sibling = null, n = $.current, X($, s ? n & 1 | 2 : n & 1), t) : (pe(t), null);
    case 22:
    case 23:
      return ua(), s = t.memoizedState !== null, e !== null && e.memoizedState !== null !== s && (t.flags |= 8192), s && t.mode & 1 ? be & 1073741824 && (pe(t), t.subtreeFlags & 6 && (t.flags |= 8192)) : pe(t), null;
    case 24:
      return null;
    case 25:
      return null;
  }
  throw Error(z(156, t.tag));
}
function Cf(e, t) {
  switch (qi(t), t.tag) {
    case 1:
      return Ce(t.type) && ms(), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
    case 3:
      return Mn(), J(ke), J(ve), _i(), e = t.flags, e & 65536 && !(e & 128) ? (t.flags = e & -65537 | 128, t) : null;
    case 5:
      return Zi(t), null;
    case 13:
      if (J($), e = t.memoizedState, e !== null && e.dehydrated !== null) {
        if (t.alternate === null) throw Error(z(340));
        bn();
      }
      return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
    case 19:
      return J($), null;
    case 4:
      return Mn(), null;
    case 10:
      return Ki(t.type._context), null;
    case 22:
    case 23:
      return ua(), null;
    case 24:
      return null;
    default:
      return null;
  }
}
var Vl = !1, me = !1, Sf = typeof WeakSet == "function" ? WeakSet : Set, I = null;
function pn(e, t) {
  var n = e.ref;
  if (n !== null) if (typeof n == "function") try {
    n(null);
  } catch (s) {
    ne(e, t, s);
  }
  else n.current = null;
}
function hi(e, t, n) {
  try {
    n();
  } catch (s) {
    ne(e, t, s);
  }
}
var Lo = !1;
function bf(e, t) {
  if (Gr = ds, e = Ku(), Vi(e)) {
    if ("selectionStart" in e) var n = { start: e.selectionStart, end: e.selectionEnd };
    else e: {
      n = (n = e.ownerDocument) && n.defaultView || window;
      var s = n.getSelection && n.getSelection();
      if (s && s.rangeCount !== 0) {
        n = s.anchorNode;
        var r = s.anchorOffset, i = s.focusNode;
        s = s.focusOffset;
        try {
          n.nodeType, i.nodeType;
        } catch {
          n = null;
          break e;
        }
        var a = 0, u = -1, o = -1, d = 0, m = 0, p = e, v = null;
        t: for (; ; ) {
          for (var j; p !== n || r !== 0 && p.nodeType !== 3 || (u = a + r), p !== i || s !== 0 && p.nodeType !== 3 || (o = a + s), p.nodeType === 3 && (a += p.nodeValue.length), (j = p.firstChild) !== null; )
            v = p, p = j;
          for (; ; ) {
            if (p === e) break t;
            if (v === n && ++d === r && (u = a), v === i && ++m === s && (o = a), (j = p.nextSibling) !== null) break;
            p = v, v = p.parentNode;
          }
          p = j;
        }
        n = u === -1 || o === -1 ? null : { start: u, end: o };
      } else n = null;
    }
    n = n || { start: 0, end: 0 };
  } else n = null;
  for (Jr = { focusedElem: e, selectionRange: n }, ds = !1, I = t; I !== null; ) if (t = I, e = t.child, (t.subtreeFlags & 1028) !== 0 && e !== null) e.return = t, I = e;
  else for (; I !== null; ) {
    t = I;
    try {
      var y = t.alternate;
      if (t.flags & 1024) switch (t.tag) {
        case 0:
        case 11:
        case 15:
          break;
        case 1:
          if (y !== null) {
            var C = y.memoizedProps, k = y.memoizedState, c = t.stateNode, h = c.getSnapshotBeforeUpdate(t.elementType === t.type ? C : Ve(t.type, C), k);
            c.__reactInternalSnapshotBeforeUpdate = h;
          }
          break;
        case 3:
          var f = t.stateNode.containerInfo;
          f.nodeType === 1 ? f.textContent = "" : f.nodeType === 9 && f.documentElement && f.removeChild(f.documentElement);
          break;
        case 5:
        case 6:
        case 4:
        case 17:
          break;
        default:
          throw Error(z(163));
      }
    } catch (x) {
      ne(t, t.return, x);
    }
    if (e = t.sibling, e !== null) {
      e.return = t.return, I = e;
      break;
    }
    I = t.return;
  }
  return y = Lo, Lo = !1, y;
}
function nl(e, t, n) {
  var s = t.updateQueue;
  if (s = s !== null ? s.lastEffect : null, s !== null) {
    var r = s = s.next;
    do {
      if ((r.tag & e) === e) {
        var i = r.destroy;
        r.destroy = void 0, i !== void 0 && hi(t, n, i);
      }
      r = r.next;
    } while (r !== s);
  }
}
function Us(e, t) {
  if (t = t.updateQueue, t = t !== null ? t.lastEffect : null, t !== null) {
    var n = t = t.next;
    do {
      if ((n.tag & e) === e) {
        var s = n.create;
        n.destroy = s();
      }
      n = n.next;
    } while (n !== t);
  }
}
function fi(e) {
  var t = e.ref;
  if (t !== null) {
    var n = e.stateNode;
    switch (e.tag) {
      case 5:
        e = n;
        break;
      default:
        e = n;
    }
    typeof t == "function" ? t(e) : t.current = e;
  }
}
function qc(e) {
  var t = e.alternate;
  t !== null && (e.alternate = null, qc(t)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (t = e.stateNode, t !== null && (delete t[_e], delete t[ml], delete t[$r], delete t[of], delete t[uf])), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
}
function Hc(e) {
  return e.tag === 5 || e.tag === 3 || e.tag === 4;
}
function Ao(e) {
  e: for (; ; ) {
    for (; e.sibling === null; ) {
      if (e.return === null || Hc(e.return)) return null;
      e = e.return;
    }
    for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18; ) {
      if (e.flags & 2 || e.child === null || e.tag === 4) continue e;
      e.child.return = e, e = e.child;
    }
    if (!(e.flags & 2)) return e.stateNode;
  }
}
function pi(e, t, n) {
  var s = e.tag;
  if (s === 5 || s === 6) e = e.stateNode, t ? n.nodeType === 8 ? n.parentNode.insertBefore(e, t) : n.insertBefore(e, t) : (n.nodeType === 8 ? (t = n.parentNode, t.insertBefore(e, n)) : (t = n, t.appendChild(e)), n = n._reactRootContainer, n != null || t.onclick !== null || (t.onclick = ps));
  else if (s !== 4 && (e = e.child, e !== null)) for (pi(e, t, n), e = e.sibling; e !== null; ) pi(e, t, n), e = e.sibling;
}
function mi(e, t, n) {
  var s = e.tag;
  if (s === 5 || s === 6) e = e.stateNode, t ? n.insertBefore(e, t) : n.appendChild(e);
  else if (s !== 4 && (e = e.child, e !== null)) for (mi(e, t, n), e = e.sibling; e !== null; ) mi(e, t, n), e = e.sibling;
}
var ce = null, We = !1;
function mt(e, t, n) {
  for (n = n.child; n !== null; ) Yc(e, t, n), n = n.sibling;
}
function Yc(e, t, n) {
  if (et && typeof et.onCommitFiberUnmount == "function") try {
    et.onCommitFiberUnmount(Ps, n);
  } catch {
  }
  switch (n.tag) {
    case 5:
      me || pn(n, t);
    case 6:
      var s = ce, r = We;
      ce = null, mt(e, t, n), ce = s, We = r, ce !== null && (We ? (e = ce, n = n.stateNode, e.nodeType === 8 ? e.parentNode.removeChild(n) : e.removeChild(n)) : ce.removeChild(n.stateNode));
      break;
    case 18:
      ce !== null && (We ? (e = ce, n = n.stateNode, e.nodeType === 8 ? cr(e.parentNode, n) : e.nodeType === 1 && cr(e, n), cl(e)) : cr(ce, n.stateNode));
      break;
    case 4:
      s = ce, r = We, ce = n.stateNode.containerInfo, We = !0, mt(e, t, n), ce = s, We = r;
      break;
    case 0:
    case 11:
    case 14:
    case 15:
      if (!me && (s = n.updateQueue, s !== null && (s = s.lastEffect, s !== null))) {
        r = s = s.next;
        do {
          var i = r, a = i.destroy;
          i = i.tag, a !== void 0 && (i & 2 || i & 4) && hi(n, t, a), r = r.next;
        } while (r !== s);
      }
      mt(e, t, n);
      break;
    case 1:
      if (!me && (pn(n, t), s = n.stateNode, typeof s.componentWillUnmount == "function")) try {
        s.props = n.memoizedProps, s.state = n.memoizedState, s.componentWillUnmount();
      } catch (u) {
        ne(n, t, u);
      }
      mt(e, t, n);
      break;
    case 21:
      mt(e, t, n);
      break;
    case 22:
      n.mode & 1 ? (me = (s = me) || n.memoizedState !== null, mt(e, t, n), me = s) : mt(e, t, n);
      break;
    default:
      mt(e, t, n);
  }
}
function Po(e) {
  var t = e.updateQueue;
  if (t !== null) {
    e.updateQueue = null;
    var n = e.stateNode;
    n === null && (n = e.stateNode = new Sf()), t.forEach(function(s) {
      var r = Ff.bind(null, e, s);
      n.has(s) || (n.add(s), s.then(r, r));
    });
  }
}
function Be(e, t) {
  var n = t.deletions;
  if (n !== null) for (var s = 0; s < n.length; s++) {
    var r = n[s];
    try {
      var i = e, a = t, u = a;
      e: for (; u !== null; ) {
        switch (u.tag) {
          case 5:
            ce = u.stateNode, We = !1;
            break e;
          case 3:
            ce = u.stateNode.containerInfo, We = !0;
            break e;
          case 4:
            ce = u.stateNode.containerInfo, We = !0;
            break e;
        }
        u = u.return;
      }
      if (ce === null) throw Error(z(160));
      Yc(i, a, r), ce = null, We = !1;
      var o = r.alternate;
      o !== null && (o.return = null), r.return = null;
    } catch (d) {
      ne(r, t, d);
    }
  }
  if (t.subtreeFlags & 12854) for (t = t.child; t !== null; ) Qc(t, e), t = t.sibling;
}
function Qc(e, t) {
  var n = e.alternate, s = e.flags;
  switch (e.tag) {
    case 0:
    case 11:
    case 14:
    case 15:
      if (Be(t, e), Je(e), s & 4) {
        try {
          nl(3, e, e.return), Us(3, e);
        } catch (C) {
          ne(e, e.return, C);
        }
        try {
          nl(5, e, e.return);
        } catch (C) {
          ne(e, e.return, C);
        }
      }
      break;
    case 1:
      Be(t, e), Je(e), s & 512 && n !== null && pn(n, n.return);
      break;
    case 5:
      if (Be(t, e), Je(e), s & 512 && n !== null && pn(n, n.return), e.flags & 32) {
        var r = e.stateNode;
        try {
          il(r, "");
        } catch (C) {
          ne(e, e.return, C);
        }
      }
      if (s & 4 && (r = e.stateNode, r != null)) {
        var i = e.memoizedProps, a = n !== null ? n.memoizedProps : i, u = e.type, o = e.updateQueue;
        if (e.updateQueue = null, o !== null) try {
          u === "input" && i.type === "radio" && i.name != null && pu(r, i), Ur(u, a);
          var d = Ur(u, i);
          for (a = 0; a < o.length; a += 2) {
            var m = o[a], p = o[a + 1];
            m === "style" ? yu(r, p) : m === "dangerouslySetInnerHTML" ? gu(r, p) : m === "children" ? il(r, p) : Mi(r, m, p, d);
          }
          switch (u) {
            case "input":
              Rr(r, i);
              break;
            case "textarea":
              mu(r, i);
              break;
            case "select":
              var v = r._wrapperState.wasMultiple;
              r._wrapperState.wasMultiple = !!i.multiple;
              var j = i.value;
              j != null ? xn(r, !!i.multiple, j, !1) : v !== !!i.multiple && (i.defaultValue != null ? xn(
                r,
                !!i.multiple,
                i.defaultValue,
                !0
              ) : xn(r, !!i.multiple, i.multiple ? [] : "", !1));
          }
          r[ml] = i;
        } catch (C) {
          ne(e, e.return, C);
        }
      }
      break;
    case 6:
      if (Be(t, e), Je(e), s & 4) {
        if (e.stateNode === null) throw Error(z(162));
        r = e.stateNode, i = e.memoizedProps;
        try {
          r.nodeValue = i;
        } catch (C) {
          ne(e, e.return, C);
        }
      }
      break;
    case 3:
      if (Be(t, e), Je(e), s & 4 && n !== null && n.memoizedState.isDehydrated) try {
        cl(t.containerInfo);
      } catch (C) {
        ne(e, e.return, C);
      }
      break;
    case 4:
      Be(t, e), Je(e);
      break;
    case 13:
      Be(t, e), Je(e), r = e.child, r.flags & 8192 && (i = r.memoizedState !== null, r.stateNode.isHidden = i, !i || r.alternate !== null && r.alternate.memoizedState !== null || (aa = le())), s & 4 && Po(e);
      break;
    case 22:
      if (m = n !== null && n.memoizedState !== null, e.mode & 1 ? (me = (d = me) || m, Be(t, e), me = d) : Be(t, e), Je(e), s & 8192) {
        if (d = e.memoizedState !== null, (e.stateNode.isHidden = d) && !m && e.mode & 1) for (I = e, m = e.child; m !== null; ) {
          for (p = I = m; I !== null; ) {
            switch (v = I, j = v.child, v.tag) {
              case 0:
              case 11:
              case 14:
              case 15:
                nl(4, v, v.return);
                break;
              case 1:
                pn(v, v.return);
                var y = v.stateNode;
                if (typeof y.componentWillUnmount == "function") {
                  s = v, n = v.return;
                  try {
                    t = s, y.props = t.memoizedProps, y.state = t.memoizedState, y.componentWillUnmount();
                  } catch (C) {
                    ne(s, n, C);
                  }
                }
                break;
              case 5:
                pn(v, v.return);
                break;
              case 22:
                if (v.memoizedState !== null) {
                  To(p);
                  continue;
                }
            }
            j !== null ? (j.return = v, I = j) : To(p);
          }
          m = m.sibling;
        }
        e: for (m = null, p = e; ; ) {
          if (p.tag === 5) {
            if (m === null) {
              m = p;
              try {
                r = p.stateNode, d ? (i = r.style, typeof i.setProperty == "function" ? i.setProperty("display", "none", "important") : i.display = "none") : (u = p.stateNode, o = p.memoizedProps.style, a = o != null && o.hasOwnProperty("display") ? o.display : null, u.style.display = xu("display", a));
              } catch (C) {
                ne(e, e.return, C);
              }
            }
          } else if (p.tag === 6) {
            if (m === null) try {
              p.stateNode.nodeValue = d ? "" : p.memoizedProps;
            } catch (C) {
              ne(e, e.return, C);
            }
          } else if ((p.tag !== 22 && p.tag !== 23 || p.memoizedState === null || p === e) && p.child !== null) {
            p.child.return = p, p = p.child;
            continue;
          }
          if (p === e) break e;
          for (; p.sibling === null; ) {
            if (p.return === null || p.return === e) break e;
            m === p && (m = null), p = p.return;
          }
          m === p && (m = null), p.sibling.return = p.return, p = p.sibling;
        }
      }
      break;
    case 19:
      Be(t, e), Je(e), s & 4 && Po(e);
      break;
    case 21:
      break;
    default:
      Be(
        t,
        e
      ), Je(e);
  }
}
function Je(e) {
  var t = e.flags;
  if (t & 2) {
    try {
      e: {
        for (var n = e.return; n !== null; ) {
          if (Hc(n)) {
            var s = n;
            break e;
          }
          n = n.return;
        }
        throw Error(z(160));
      }
      switch (s.tag) {
        case 5:
          var r = s.stateNode;
          s.flags & 32 && (il(r, ""), s.flags &= -33);
          var i = Ao(e);
          mi(e, i, r);
          break;
        case 3:
        case 4:
          var a = s.stateNode.containerInfo, u = Ao(e);
          pi(e, u, a);
          break;
        default:
          throw Error(z(161));
      }
    } catch (o) {
      ne(e, e.return, o);
    }
    e.flags &= -3;
  }
  t & 4096 && (e.flags &= -4097);
}
function Ef(e, t, n) {
  I = e, Kc(e);
}
function Kc(e, t, n) {
  for (var s = (e.mode & 1) !== 0; I !== null; ) {
    var r = I, i = r.child;
    if (r.tag === 22 && s) {
      var a = r.memoizedState !== null || Vl;
      if (!a) {
        var u = r.alternate, o = u !== null && u.memoizedState !== null || me;
        u = Vl;
        var d = me;
        if (Vl = a, (me = o) && !d) for (I = r; I !== null; ) a = I, o = a.child, a.tag === 22 && a.memoizedState !== null ? Ro(r) : o !== null ? (o.return = a, I = o) : Ro(r);
        for (; i !== null; ) I = i, Kc(i), i = i.sibling;
        I = r, Vl = u, me = d;
      }
      zo(e);
    } else r.subtreeFlags & 8772 && i !== null ? (i.return = r, I = i) : zo(e);
  }
}
function zo(e) {
  for (; I !== null; ) {
    var t = I;
    if (t.flags & 8772) {
      var n = t.alternate;
      try {
        if (t.flags & 8772) switch (t.tag) {
          case 0:
          case 11:
          case 15:
            me || Us(5, t);
            break;
          case 1:
            var s = t.stateNode;
            if (t.flags & 4 && !me) if (n === null) s.componentDidMount();
            else {
              var r = t.elementType === t.type ? n.memoizedProps : Ve(t.type, n.memoizedProps);
              s.componentDidUpdate(r, n.memoizedState, s.__reactInternalSnapshotBeforeUpdate);
            }
            var i = t.updateQueue;
            i !== null && vo(t, i, s);
            break;
          case 3:
            var a = t.updateQueue;
            if (a !== null) {
              if (n = null, t.child !== null) switch (t.child.tag) {
                case 5:
                  n = t.child.stateNode;
                  break;
                case 1:
                  n = t.child.stateNode;
              }
              vo(t, a, n);
            }
            break;
          case 5:
            var u = t.stateNode;
            if (n === null && t.flags & 4) {
              n = u;
              var o = t.memoizedProps;
              switch (t.type) {
                case "button":
                case "input":
                case "select":
                case "textarea":
                  o.autoFocus && n.focus();
                  break;
                case "img":
                  o.src && (n.src = o.src);
              }
            }
            break;
          case 6:
            break;
          case 4:
            break;
          case 12:
            break;
          case 13:
            if (t.memoizedState === null) {
              var d = t.alternate;
              if (d !== null) {
                var m = d.memoizedState;
                if (m !== null) {
                  var p = m.dehydrated;
                  p !== null && cl(p);
                }
              }
            }
            break;
          case 19:
          case 17:
          case 21:
          case 22:
          case 23:
          case 25:
            break;
          default:
            throw Error(z(163));
        }
        me || t.flags & 512 && fi(t);
      } catch (v) {
        ne(t, t.return, v);
      }
    }
    if (t === e) {
      I = null;
      break;
    }
    if (n = t.sibling, n !== null) {
      n.return = t.return, I = n;
      break;
    }
    I = t.return;
  }
}
function To(e) {
  for (; I !== null; ) {
    var t = I;
    if (t === e) {
      I = null;
      break;
    }
    var n = t.sibling;
    if (n !== null) {
      n.return = t.return, I = n;
      break;
    }
    I = t.return;
  }
}
function Ro(e) {
  for (; I !== null; ) {
    var t = I;
    try {
      switch (t.tag) {
        case 0:
        case 11:
        case 15:
          var n = t.return;
          try {
            Us(4, t);
          } catch (o) {
            ne(t, n, o);
          }
          break;
        case 1:
          var s = t.stateNode;
          if (typeof s.componentDidMount == "function") {
            var r = t.return;
            try {
              s.componentDidMount();
            } catch (o) {
              ne(t, r, o);
            }
          }
          var i = t.return;
          try {
            fi(t);
          } catch (o) {
            ne(t, i, o);
          }
          break;
        case 5:
          var a = t.return;
          try {
            fi(t);
          } catch (o) {
            ne(t, a, o);
          }
      }
    } catch (o) {
      ne(t, t.return, o);
    }
    if (t === e) {
      I = null;
      break;
    }
    var u = t.sibling;
    if (u !== null) {
      u.return = t.return, I = u;
      break;
    }
    I = t.return;
  }
}
var Mf = Math.ceil, Ss = ft.ReactCurrentDispatcher, ra = ft.ReactCurrentOwner, Fe = ft.ReactCurrentBatchConfig, Y = 0, ue = null, se = null, de = 0, be = 0, mn = Ft(0), ie = 0, Nl = null, Zt = 0, Bs = 0, ia = 0, ll = null, Ne = null, aa = 0, An = 1 / 0, lt = null, bs = !1, vi = null, Lt = null, Wl = !1, kt = null, Es = 0, sl = 0, gi = null, ns = -1, ls = 0;
function xe() {
  return Y & 6 ? le() : ns !== -1 ? ns : ns = le();
}
function At(e) {
  return e.mode & 1 ? Y & 2 && de !== 0 ? de & -de : df.transition !== null ? (ls === 0 && (ls = Pu()), ls) : (e = Q, e !== 0 || (e = window.event, e = e === void 0 ? 16 : Iu(e.type)), e) : 1;
}
function Ye(e, t, n, s) {
  if (50 < sl) throw sl = 0, gi = null, Error(z(185));
  kl(e, n, s), (!(Y & 2) || e !== ue) && (e === ue && (!(Y & 2) && (Bs |= n), ie === 4 && Nt(e, de)), Se(e, s), n === 1 && Y === 0 && !(t.mode & 1) && (An = le() + 500, Os && Ot()));
}
function Se(e, t) {
  var n = e.callbackNode;
  ch(e, t);
  var s = cs(e, e === ue ? de : 0);
  if (s === 0) n !== null && Wa(n), e.callbackNode = null, e.callbackPriority = 0;
  else if (t = s & -s, e.callbackPriority !== t) {
    if (n != null && Wa(n), t === 1) e.tag === 0 ? cf(Fo.bind(null, e)) : lc(Fo.bind(null, e)), rf(function() {
      !(Y & 6) && Ot();
    }), n = null;
    else {
      switch (zu(s)) {
        case 1:
          n = Ti;
          break;
        case 4:
          n = Lu;
          break;
        case 16:
          n = us;
          break;
        case 536870912:
          n = Au;
          break;
        default:
          n = us;
      }
      n = td(n, Xc.bind(null, e));
    }
    e.callbackPriority = t, e.callbackNode = n;
  }
}
function Xc(e, t) {
  if (ns = -1, ls = 0, Y & 6) throw Error(z(327));
  var n = e.callbackNode;
  if (kn() && e.callbackNode !== n) return null;
  var s = cs(e, e === ue ? de : 0);
  if (s === 0) return null;
  if (s & 30 || s & e.expiredLanes || t) t = Ms(e, s);
  else {
    t = s;
    var r = Y;
    Y |= 2;
    var i = Jc();
    (ue !== e || de !== t) && (lt = null, An = le() + 500, Yt(e, t));
    do
      try {
        Pf();
        break;
      } catch (u) {
        Gc(e, u);
      }
    while (!0);
    Qi(), Ss.current = i, Y = r, se !== null ? t = 0 : (ue = null, de = 0, t = ie);
  }
  if (t !== 0) {
    if (t === 2 && (r = Hr(e), r !== 0 && (s = r, t = xi(e, r))), t === 1) throw n = Nl, Yt(e, 0), Nt(e, s), Se(e, le()), n;
    if (t === 6) Nt(e, s);
    else {
      if (r = e.current.alternate, !(s & 30) && !Lf(r) && (t = Ms(e, s), t === 2 && (i = Hr(e), i !== 0 && (s = i, t = xi(e, i))), t === 1)) throw n = Nl, Yt(e, 0), Nt(e, s), Se(e, le()), n;
      switch (e.finishedWork = r, e.finishedLanes = s, t) {
        case 0:
        case 1:
          throw Error(z(345));
        case 2:
          Vt(e, Ne, lt);
          break;
        case 3:
          if (Nt(e, s), (s & 130023424) === s && (t = aa + 500 - le(), 10 < t)) {
            if (cs(e, 0) !== 0) break;
            if (r = e.suspendedLanes, (r & s) !== s) {
              xe(), e.pingedLanes |= e.suspendedLanes & r;
              break;
            }
            e.timeoutHandle = _r(Vt.bind(null, e, Ne, lt), t);
            break;
          }
          Vt(e, Ne, lt);
          break;
        case 4:
          if (Nt(e, s), (s & 4194240) === s) break;
          for (t = e.eventTimes, r = -1; 0 < s; ) {
            var a = 31 - He(s);
            i = 1 << a, a = t[a], a > r && (r = a), s &= ~i;
          }
          if (s = r, s = le() - s, s = (120 > s ? 120 : 480 > s ? 480 : 1080 > s ? 1080 : 1920 > s ? 1920 : 3e3 > s ? 3e3 : 4320 > s ? 4320 : 1960 * Mf(s / 1960)) - s, 10 < s) {
            e.timeoutHandle = _r(Vt.bind(null, e, Ne, lt), s);
            break;
          }
          Vt(e, Ne, lt);
          break;
        case 5:
          Vt(e, Ne, lt);
          break;
        default:
          throw Error(z(329));
      }
    }
  }
  return Se(e, le()), e.callbackNode === n ? Xc.bind(null, e) : null;
}
function xi(e, t) {
  var n = ll;
  return e.current.memoizedState.isDehydrated && (Yt(e, t).flags |= 256), e = Ms(e, t), e !== 2 && (t = Ne, Ne = n, t !== null && yi(t)), e;
}
function yi(e) {
  Ne === null ? Ne = e : Ne.push.apply(Ne, e);
}
function Lf(e) {
  for (var t = e; ; ) {
    if (t.flags & 16384) {
      var n = t.updateQueue;
      if (n !== null && (n = n.stores, n !== null)) for (var s = 0; s < n.length; s++) {
        var r = n[s], i = r.getSnapshot;
        r = r.value;
        try {
          if (!Qe(i(), r)) return !1;
        } catch {
          return !1;
        }
      }
    }
    if (n = t.child, t.subtreeFlags & 16384 && n !== null) n.return = t, t = n;
    else {
      if (t === e) break;
      for (; t.sibling === null; ) {
        if (t.return === null || t.return === e) return !0;
        t = t.return;
      }
      t.sibling.return = t.return, t = t.sibling;
    }
  }
  return !0;
}
function Nt(e, t) {
  for (t &= ~ia, t &= ~Bs, e.suspendedLanes |= t, e.pingedLanes &= ~t, e = e.expirationTimes; 0 < t; ) {
    var n = 31 - He(t), s = 1 << n;
    e[n] = -1, t &= ~s;
  }
}
function Fo(e) {
  if (Y & 6) throw Error(z(327));
  kn();
  var t = cs(e, 0);
  if (!(t & 1)) return Se(e, le()), null;
  var n = Ms(e, t);
  if (e.tag !== 0 && n === 2) {
    var s = Hr(e);
    s !== 0 && (t = s, n = xi(e, s));
  }
  if (n === 1) throw n = Nl, Yt(e, 0), Nt(e, t), Se(e, le()), n;
  if (n === 6) throw Error(z(345));
  return e.finishedWork = e.current.alternate, e.finishedLanes = t, Vt(e, Ne, lt), Se(e, le()), null;
}
function oa(e, t) {
  var n = Y;
  Y |= 1;
  try {
    return e(t);
  } finally {
    Y = n, Y === 0 && (An = le() + 500, Os && Ot());
  }
}
function _t(e) {
  kt !== null && kt.tag === 0 && !(Y & 6) && kn();
  var t = Y;
  Y |= 1;
  var n = Fe.transition, s = Q;
  try {
    if (Fe.transition = null, Q = 1, e) return e();
  } finally {
    Q = s, Fe.transition = n, Y = t, !(Y & 6) && Ot();
  }
}
function ua() {
  be = mn.current, J(mn);
}
function Yt(e, t) {
  e.finishedWork = null, e.finishedLanes = 0;
  var n = e.timeoutHandle;
  if (n !== -1 && (e.timeoutHandle = -1, sf(n)), se !== null) for (n = se.return; n !== null; ) {
    var s = n;
    switch (qi(s), s.tag) {
      case 1:
        s = s.type.childContextTypes, s != null && ms();
        break;
      case 3:
        Mn(), J(ke), J(ve), _i();
        break;
      case 5:
        Zi(s);
        break;
      case 4:
        Mn();
        break;
      case 13:
        J($);
        break;
      case 19:
        J($);
        break;
      case 10:
        Ki(s.type._context);
        break;
      case 22:
      case 23:
        ua();
    }
    n = n.return;
  }
  if (ue = e, se = e = Pt(e.current, null), de = be = t, ie = 0, Nl = null, ia = Bs = Zt = 0, Ne = ll = null, qt !== null) {
    for (t = 0; t < qt.length; t++) if (n = qt[t], s = n.interleaved, s !== null) {
      n.interleaved = null;
      var r = s.next, i = n.pending;
      if (i !== null) {
        var a = i.next;
        i.next = r, s.next = a;
      }
      n.pending = s;
    }
    qt = null;
  }
  return e;
}
function Gc(e, t) {
  do {
    var n = se;
    try {
      if (Qi(), $l.current = Cs, ks) {
        for (var s = ee.memoizedState; s !== null; ) {
          var r = s.queue;
          r !== null && (r.pending = null), s = s.next;
        }
        ks = !1;
      }
      if (Jt = 0, oe = re = ee = null, tl = !1, xl = 0, ra.current = null, n === null || n.return === null) {
        ie = 1, Nl = t, se = null;
        break;
      }
      e: {
        var i = e, a = n.return, u = n, o = t;
        if (t = de, u.flags |= 32768, o !== null && typeof o == "object" && typeof o.then == "function") {
          var d = o, m = u, p = m.tag;
          if (!(m.mode & 1) && (p === 0 || p === 11 || p === 15)) {
            var v = m.alternate;
            v ? (m.updateQueue = v.updateQueue, m.memoizedState = v.memoizedState, m.lanes = v.lanes) : (m.updateQueue = null, m.memoizedState = null);
          }
          var j = wo(a);
          if (j !== null) {
            j.flags &= -257, ko(j, a, u, i, t), j.mode & 1 && No(i, d, t), t = j, o = d;
            var y = t.updateQueue;
            if (y === null) {
              var C = /* @__PURE__ */ new Set();
              C.add(o), t.updateQueue = C;
            } else y.add(o);
            break e;
          } else {
            if (!(t & 1)) {
              No(i, d, t), ca();
              break e;
            }
            o = Error(z(426));
          }
        } else if (Z && u.mode & 1) {
          var k = wo(a);
          if (k !== null) {
            !(k.flags & 65536) && (k.flags |= 256), ko(k, a, u, i, t), Hi(Ln(o, u));
            break e;
          }
        }
        i = o = Ln(o, u), ie !== 4 && (ie = 2), ll === null ? ll = [i] : ll.push(i), i = a;
        do {
          switch (i.tag) {
            case 3:
              i.flags |= 65536, t &= -t, i.lanes |= t;
              var c = zc(i, o, t);
              mo(i, c);
              break e;
            case 1:
              u = o;
              var h = i.type, f = i.stateNode;
              if (!(i.flags & 128) && (typeof h.getDerivedStateFromError == "function" || f !== null && typeof f.componentDidCatch == "function" && (Lt === null || !Lt.has(f)))) {
                i.flags |= 65536, t &= -t, i.lanes |= t;
                var x = Tc(i, u, t);
                mo(i, x);
                break e;
              }
          }
          i = i.return;
        } while (i !== null);
      }
      _c(n);
    } catch (N) {
      t = N, se === n && n !== null && (se = n = n.return);
      continue;
    }
    break;
  } while (!0);
}
function Jc() {
  var e = Ss.current;
  return Ss.current = Cs, e === null ? Cs : e;
}
function ca() {
  (ie === 0 || ie === 3 || ie === 2) && (ie = 4), ue === null || !(Zt & 268435455) && !(Bs & 268435455) || Nt(ue, de);
}
function Ms(e, t) {
  var n = Y;
  Y |= 2;
  var s = Jc();
  (ue !== e || de !== t) && (lt = null, Yt(e, t));
  do
    try {
      Af();
      break;
    } catch (r) {
      Gc(e, r);
    }
  while (!0);
  if (Qi(), Y = n, Ss.current = s, se !== null) throw Error(z(261));
  return ue = null, de = 0, ie;
}
function Af() {
  for (; se !== null; ) Zc(se);
}
function Pf() {
  for (; se !== null && !th(); ) Zc(se);
}
function Zc(e) {
  var t = ed(e.alternate, e, be);
  e.memoizedProps = e.pendingProps, t === null ? _c(e) : se = t, ra.current = null;
}
function _c(e) {
  var t = e;
  do {
    var n = t.alternate;
    if (e = t.return, t.flags & 32768) {
      if (n = Cf(n, t), n !== null) {
        n.flags &= 32767, se = n;
        return;
      }
      if (e !== null) e.flags |= 32768, e.subtreeFlags = 0, e.deletions = null;
      else {
        ie = 6, se = null;
        return;
      }
    } else if (n = kf(n, t, be), n !== null) {
      se = n;
      return;
    }
    if (t = t.sibling, t !== null) {
      se = t;
      return;
    }
    se = t = e;
  } while (t !== null);
  ie === 0 && (ie = 5);
}
function Vt(e, t, n) {
  var s = Q, r = Fe.transition;
  try {
    Fe.transition = null, Q = 1, zf(e, t, n, s);
  } finally {
    Fe.transition = r, Q = s;
  }
  return null;
}
function zf(e, t, n, s) {
  do
    kn();
  while (kt !== null);
  if (Y & 6) throw Error(z(327));
  n = e.finishedWork;
  var r = e.finishedLanes;
  if (n === null) return null;
  if (e.finishedWork = null, e.finishedLanes = 0, n === e.current) throw Error(z(177));
  e.callbackNode = null, e.callbackPriority = 0;
  var i = n.lanes | n.childLanes;
  if (dh(e, i), e === ue && (se = ue = null, de = 0), !(n.subtreeFlags & 2064) && !(n.flags & 2064) || Wl || (Wl = !0, td(us, function() {
    return kn(), null;
  })), i = (n.flags & 15990) !== 0, n.subtreeFlags & 15990 || i) {
    i = Fe.transition, Fe.transition = null;
    var a = Q;
    Q = 1;
    var u = Y;
    Y |= 4, ra.current = null, bf(e, n), Qc(n, e), Zh(Jr), ds = !!Gr, Jr = Gr = null, e.current = n, Ef(n), nh(), Y = u, Q = a, Fe.transition = i;
  } else e.current = n;
  if (Wl && (Wl = !1, kt = e, Es = r), i = e.pendingLanes, i === 0 && (Lt = null), rh(n.stateNode), Se(e, le()), t !== null) for (s = e.onRecoverableError, n = 0; n < t.length; n++) r = t[n], s(r.value, { componentStack: r.stack, digest: r.digest });
  if (bs) throw bs = !1, e = vi, vi = null, e;
  return Es & 1 && e.tag !== 0 && kn(), i = e.pendingLanes, i & 1 ? e === gi ? sl++ : (sl = 0, gi = e) : sl = 0, Ot(), null;
}
function kn() {
  if (kt !== null) {
    var e = zu(Es), t = Fe.transition, n = Q;
    try {
      if (Fe.transition = null, Q = 16 > e ? 16 : e, kt === null) var s = !1;
      else {
        if (e = kt, kt = null, Es = 0, Y & 6) throw Error(z(331));
        var r = Y;
        for (Y |= 4, I = e.current; I !== null; ) {
          var i = I, a = i.child;
          if (I.flags & 16) {
            var u = i.deletions;
            if (u !== null) {
              for (var o = 0; o < u.length; o++) {
                var d = u[o];
                for (I = d; I !== null; ) {
                  var m = I;
                  switch (m.tag) {
                    case 0:
                    case 11:
                    case 15:
                      nl(8, m, i);
                  }
                  var p = m.child;
                  if (p !== null) p.return = m, I = p;
                  else for (; I !== null; ) {
                    m = I;
                    var v = m.sibling, j = m.return;
                    if (qc(m), m === d) {
                      I = null;
                      break;
                    }
                    if (v !== null) {
                      v.return = j, I = v;
                      break;
                    }
                    I = j;
                  }
                }
              }
              var y = i.alternate;
              if (y !== null) {
                var C = y.child;
                if (C !== null) {
                  y.child = null;
                  do {
                    var k = C.sibling;
                    C.sibling = null, C = k;
                  } while (C !== null);
                }
              }
              I = i;
            }
          }
          if (i.subtreeFlags & 2064 && a !== null) a.return = i, I = a;
          else e: for (; I !== null; ) {
            if (i = I, i.flags & 2048) switch (i.tag) {
              case 0:
              case 11:
              case 15:
                nl(9, i, i.return);
            }
            var c = i.sibling;
            if (c !== null) {
              c.return = i.return, I = c;
              break e;
            }
            I = i.return;
          }
        }
        var h = e.current;
        for (I = h; I !== null; ) {
          a = I;
          var f = a.child;
          if (a.subtreeFlags & 2064 && f !== null) f.return = a, I = f;
          else e: for (a = h; I !== null; ) {
            if (u = I, u.flags & 2048) try {
              switch (u.tag) {
                case 0:
                case 11:
                case 15:
                  Us(9, u);
              }
            } catch (N) {
              ne(u, u.return, N);
            }
            if (u === a) {
              I = null;
              break e;
            }
            var x = u.sibling;
            if (x !== null) {
              x.return = u.return, I = x;
              break e;
            }
            I = u.return;
          }
        }
        if (Y = r, Ot(), et && typeof et.onPostCommitFiberRoot == "function") try {
          et.onPostCommitFiberRoot(Ps, e);
        } catch {
        }
        s = !0;
      }
      return s;
    } finally {
      Q = n, Fe.transition = t;
    }
  }
  return !1;
}
function Oo(e, t, n) {
  t = Ln(n, t), t = zc(e, t, 1), e = Mt(e, t, 1), t = xe(), e !== null && (kl(e, 1, t), Se(e, t));
}
function ne(e, t, n) {
  if (e.tag === 3) Oo(e, e, n);
  else for (; t !== null; ) {
    if (t.tag === 3) {
      Oo(t, e, n);
      break;
    } else if (t.tag === 1) {
      var s = t.stateNode;
      if (typeof t.type.getDerivedStateFromError == "function" || typeof s.componentDidCatch == "function" && (Lt === null || !Lt.has(s))) {
        e = Ln(n, e), e = Tc(t, e, 1), t = Mt(t, e, 1), e = xe(), t !== null && (kl(t, 1, e), Se(t, e));
        break;
      }
    }
    t = t.return;
  }
}
function Tf(e, t, n) {
  var s = e.pingCache;
  s !== null && s.delete(t), t = xe(), e.pingedLanes |= e.suspendedLanes & n, ue === e && (de & n) === n && (ie === 4 || ie === 3 && (de & 130023424) === de && 500 > le() - aa ? Yt(e, 0) : ia |= n), Se(e, t);
}
function $c(e, t) {
  t === 0 && (e.mode & 1 ? (t = zl, zl <<= 1, !(zl & 130023424) && (zl = 4194304)) : t = 1);
  var n = xe();
  e = dt(e, t), e !== null && (kl(e, t, n), Se(e, n));
}
function Rf(e) {
  var t = e.memoizedState, n = 0;
  t !== null && (n = t.retryLane), $c(e, n);
}
function Ff(e, t) {
  var n = 0;
  switch (e.tag) {
    case 13:
      var s = e.stateNode, r = e.memoizedState;
      r !== null && (n = r.retryLane);
      break;
    case 19:
      s = e.stateNode;
      break;
    default:
      throw Error(z(314));
  }
  s !== null && s.delete(t), $c(e, n);
}
var ed;
ed = function(e, t, n) {
  if (e !== null) if (e.memoizedProps !== t.pendingProps || ke.current) we = !0;
  else {
    if (!(e.lanes & n) && !(t.flags & 128)) return we = !1, wf(e, t, n);
    we = !!(e.flags & 131072);
  }
  else we = !1, Z && t.flags & 1048576 && sc(t, xs, t.index);
  switch (t.lanes = 0, t.tag) {
    case 2:
      var s = t.type;
      ts(e, t), e = t.pendingProps;
      var r = Sn(t, ve.current);
      wn(t, n), r = ea(null, t, s, e, r, n);
      var i = ta();
      return t.flags |= 1, typeof r == "object" && r !== null && typeof r.render == "function" && r.$$typeof === void 0 ? (t.tag = 1, t.memoizedState = null, t.updateQueue = null, Ce(s) ? (i = !0, vs(t)) : i = !1, t.memoizedState = r.state !== null && r.state !== void 0 ? r.state : null, Gi(t), r.updater = Is, t.stateNode = r, r._reactInternals = t, ri(t, s, e, n), t = oi(null, t, s, !0, i, n)) : (t.tag = 0, Z && i && Wi(t), ge(null, t, r, n), t = t.child), t;
    case 16:
      s = t.elementType;
      e: {
        switch (ts(e, t), e = t.pendingProps, r = s._init, s = r(s._payload), t.type = s, r = t.tag = Df(s), e = Ve(s, e), r) {
          case 0:
            t = ai(null, t, s, e, n);
            break e;
          case 1:
            t = bo(null, t, s, e, n);
            break e;
          case 11:
            t = Co(null, t, s, e, n);
            break e;
          case 14:
            t = So(null, t, s, Ve(s.type, e), n);
            break e;
        }
        throw Error(z(
          306,
          s,
          ""
        ));
      }
      return t;
    case 0:
      return s = t.type, r = t.pendingProps, r = t.elementType === s ? r : Ve(s, r), ai(e, t, s, r, n);
    case 1:
      return s = t.type, r = t.pendingProps, r = t.elementType === s ? r : Ve(s, r), bo(e, t, s, r, n);
    case 3:
      e: {
        if (Dc(t), e === null) throw Error(z(387));
        s = t.pendingProps, i = t.memoizedState, r = i.element, cc(e, t), Ns(t, s, null, n);
        var a = t.memoizedState;
        if (s = a.element, i.isDehydrated) if (i = { element: s, isDehydrated: !1, cache: a.cache, pendingSuspenseBoundaries: a.pendingSuspenseBoundaries, transitions: a.transitions }, t.updateQueue.baseState = i, t.memoizedState = i, t.flags & 256) {
          r = Ln(Error(z(423)), t), t = Eo(e, t, s, n, r);
          break e;
        } else if (s !== r) {
          r = Ln(Error(z(424)), t), t = Eo(e, t, s, n, r);
          break e;
        } else for (Ee = Et(t.stateNode.containerInfo.firstChild), Me = t, Z = !0, qe = null, n = oc(t, null, s, n), t.child = n; n; ) n.flags = n.flags & -3 | 4096, n = n.sibling;
        else {
          if (bn(), s === r) {
            t = ht(e, t, n);
            break e;
          }
          ge(e, t, s, n);
        }
        t = t.child;
      }
      return t;
    case 5:
      return dc(t), e === null && ni(t), s = t.type, r = t.pendingProps, i = e !== null ? e.memoizedProps : null, a = r.children, Zr(s, r) ? a = null : i !== null && Zr(s, i) && (t.flags |= 32), Oc(e, t), ge(e, t, a, n), t.child;
    case 6:
      return e === null && ni(t), null;
    case 13:
      return Ic(e, t, n);
    case 4:
      return Ji(t, t.stateNode.containerInfo), s = t.pendingProps, e === null ? t.child = En(t, null, s, n) : ge(e, t, s, n), t.child;
    case 11:
      return s = t.type, r = t.pendingProps, r = t.elementType === s ? r : Ve(s, r), Co(e, t, s, r, n);
    case 7:
      return ge(e, t, t.pendingProps, n), t.child;
    case 8:
      return ge(e, t, t.pendingProps.children, n), t.child;
    case 12:
      return ge(e, t, t.pendingProps.children, n), t.child;
    case 10:
      e: {
        if (s = t.type._context, r = t.pendingProps, i = t.memoizedProps, a = r.value, X(ys, s._currentValue), s._currentValue = a, i !== null) if (Qe(i.value, a)) {
          if (i.children === r.children && !ke.current) {
            t = ht(e, t, n);
            break e;
          }
        } else for (i = t.child, i !== null && (i.return = t); i !== null; ) {
          var u = i.dependencies;
          if (u !== null) {
            a = i.child;
            for (var o = u.firstContext; o !== null; ) {
              if (o.context === s) {
                if (i.tag === 1) {
                  o = ot(-1, n & -n), o.tag = 2;
                  var d = i.updateQueue;
                  if (d !== null) {
                    d = d.shared;
                    var m = d.pending;
                    m === null ? o.next = o : (o.next = m.next, m.next = o), d.pending = o;
                  }
                }
                i.lanes |= n, o = i.alternate, o !== null && (o.lanes |= n), li(
                  i.return,
                  n,
                  t
                ), u.lanes |= n;
                break;
              }
              o = o.next;
            }
          } else if (i.tag === 10) a = i.type === t.type ? null : i.child;
          else if (i.tag === 18) {
            if (a = i.return, a === null) throw Error(z(341));
            a.lanes |= n, u = a.alternate, u !== null && (u.lanes |= n), li(a, n, t), a = i.sibling;
          } else a = i.child;
          if (a !== null) a.return = i;
          else for (a = i; a !== null; ) {
            if (a === t) {
              a = null;
              break;
            }
            if (i = a.sibling, i !== null) {
              i.return = a.return, a = i;
              break;
            }
            a = a.return;
          }
          i = a;
        }
        ge(e, t, r.children, n), t = t.child;
      }
      return t;
    case 9:
      return r = t.type, s = t.pendingProps.children, wn(t, n), r = Oe(r), s = s(r), t.flags |= 1, ge(e, t, s, n), t.child;
    case 14:
      return s = t.type, r = Ve(s, t.pendingProps), r = Ve(s.type, r), So(e, t, s, r, n);
    case 15:
      return Rc(e, t, t.type, t.pendingProps, n);
    case 17:
      return s = t.type, r = t.pendingProps, r = t.elementType === s ? r : Ve(s, r), ts(e, t), t.tag = 1, Ce(s) ? (e = !0, vs(t)) : e = !1, wn(t, n), Pc(t, s, r), ri(t, s, r, n), oi(null, t, s, !0, e, n);
    case 19:
      return Uc(e, t, n);
    case 22:
      return Fc(e, t, n);
  }
  throw Error(z(156, t.tag));
};
function td(e, t) {
  return Mu(e, t);
}
function Of(e, t, n, s) {
  this.tag = e, this.key = n, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.ref = null, this.pendingProps = t, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = s, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
}
function Re(e, t, n, s) {
  return new Of(e, t, n, s);
}
function da(e) {
  return e = e.prototype, !(!e || !e.isReactComponent);
}
function Df(e) {
  if (typeof e == "function") return da(e) ? 1 : 0;
  if (e != null) {
    if (e = e.$$typeof, e === Ai) return 11;
    if (e === Pi) return 14;
  }
  return 2;
}
function Pt(e, t) {
  var n = e.alternate;
  return n === null ? (n = Re(e.tag, t, e.key, e.mode), n.elementType = e.elementType, n.type = e.type, n.stateNode = e.stateNode, n.alternate = e, e.alternate = n) : (n.pendingProps = t, n.type = e.type, n.flags = 0, n.subtreeFlags = 0, n.deletions = null), n.flags = e.flags & 14680064, n.childLanes = e.childLanes, n.lanes = e.lanes, n.child = e.child, n.memoizedProps = e.memoizedProps, n.memoizedState = e.memoizedState, n.updateQueue = e.updateQueue, t = e.dependencies, n.dependencies = t === null ? null : { lanes: t.lanes, firstContext: t.firstContext }, n.sibling = e.sibling, n.index = e.index, n.ref = e.ref, n;
}
function ss(e, t, n, s, r, i) {
  var a = 2;
  if (s = e, typeof e == "function") da(e) && (a = 1);
  else if (typeof e == "string") a = 5;
  else e: switch (e) {
    case sn:
      return Qt(n.children, r, i, t);
    case Li:
      a = 8, r |= 8;
      break;
    case Lr:
      return e = Re(12, n, t, r | 2), e.elementType = Lr, e.lanes = i, e;
    case Ar:
      return e = Re(13, n, t, r), e.elementType = Ar, e.lanes = i, e;
    case Pr:
      return e = Re(19, n, t, r), e.elementType = Pr, e.lanes = i, e;
    case du:
      return Vs(n, r, i, t);
    default:
      if (typeof e == "object" && e !== null) switch (e.$$typeof) {
        case uu:
          a = 10;
          break e;
        case cu:
          a = 9;
          break e;
        case Ai:
          a = 11;
          break e;
        case Pi:
          a = 14;
          break e;
        case gt:
          a = 16, s = null;
          break e;
      }
      throw Error(z(130, e == null ? e : typeof e, ""));
  }
  return t = Re(a, n, t, r), t.elementType = e, t.type = s, t.lanes = i, t;
}
function Qt(e, t, n, s) {
  return e = Re(7, e, s, t), e.lanes = n, e;
}
function Vs(e, t, n, s) {
  return e = Re(22, e, s, t), e.elementType = du, e.lanes = n, e.stateNode = { isHidden: !1 }, e;
}
function xr(e, t, n) {
  return e = Re(6, e, null, t), e.lanes = n, e;
}
function yr(e, t, n) {
  return t = Re(4, e.children !== null ? e.children : [], e.key, t), t.lanes = n, t.stateNode = { containerInfo: e.containerInfo, pendingChildren: null, implementation: e.implementation }, t;
}
function If(e, t, n, s, r) {
  this.tag = t, this.containerInfo = e, this.finishedWork = this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.pendingContext = this.context = null, this.callbackPriority = 0, this.eventTimes = $s(0), this.expirationTimes = $s(-1), this.entangledLanes = this.finishedLanes = this.mutableReadLanes = this.expiredLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = $s(0), this.identifierPrefix = s, this.onRecoverableError = r, this.mutableSourceEagerHydrationData = null;
}
function ha(e, t, n, s, r, i, a, u, o) {
  return e = new If(e, t, n, u, o), t === 1 ? (t = 1, i === !0 && (t |= 8)) : t = 0, i = Re(3, null, null, t), e.current = i, i.stateNode = e, i.memoizedState = { element: s, isDehydrated: n, cache: null, transitions: null, pendingSuspenseBoundaries: null }, Gi(i), e;
}
function Uf(e, t, n) {
  var s = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
  return { $$typeof: ln, key: s == null ? null : "" + s, children: e, containerInfo: t, implementation: n };
}
function nd(e) {
  if (!e) return Tt;
  e = e._reactInternals;
  e: {
    if (en(e) !== e || e.tag !== 1) throw Error(z(170));
    var t = e;
    do {
      switch (t.tag) {
        case 3:
          t = t.stateNode.context;
          break e;
        case 1:
          if (Ce(t.type)) {
            t = t.stateNode.__reactInternalMemoizedMergedChildContext;
            break e;
          }
      }
      t = t.return;
    } while (t !== null);
    throw Error(z(171));
  }
  if (e.tag === 1) {
    var n = e.type;
    if (Ce(n)) return nc(e, n, t);
  }
  return t;
}
function ld(e, t, n, s, r, i, a, u, o) {
  return e = ha(n, s, !0, e, r, i, a, u, o), e.context = nd(null), n = e.current, s = xe(), r = At(n), i = ot(s, r), i.callback = t ?? null, Mt(n, i, r), e.current.lanes = r, kl(e, r, s), Se(e, s), e;
}
function Ws(e, t, n, s) {
  var r = t.current, i = xe(), a = At(r);
  return n = nd(n), t.context === null ? t.context = n : t.pendingContext = n, t = ot(i, a), t.payload = { element: e }, s = s === void 0 ? null : s, s !== null && (t.callback = s), e = Mt(r, t, a), e !== null && (Ye(e, r, a, i), _l(e, r, a)), a;
}
function Ls(e) {
  if (e = e.current, !e.child) return null;
  switch (e.child.tag) {
    case 5:
      return e.child.stateNode;
    default:
      return e.child.stateNode;
  }
}
function Do(e, t) {
  if (e = e.memoizedState, e !== null && e.dehydrated !== null) {
    var n = e.retryLane;
    e.retryLane = n !== 0 && n < t ? n : t;
  }
}
function fa(e, t) {
  Do(e, t), (e = e.alternate) && Do(e, t);
}
function Bf() {
  return null;
}
var sd = typeof reportError == "function" ? reportError : function(e) {
  console.error(e);
};
function pa(e) {
  this._internalRoot = e;
}
qs.prototype.render = pa.prototype.render = function(e) {
  var t = this._internalRoot;
  if (t === null) throw Error(z(409));
  Ws(e, t, null, null);
};
qs.prototype.unmount = pa.prototype.unmount = function() {
  var e = this._internalRoot;
  if (e !== null) {
    this._internalRoot = null;
    var t = e.containerInfo;
    _t(function() {
      Ws(null, e, null, null);
    }), t[ct] = null;
  }
};
function qs(e) {
  this._internalRoot = e;
}
qs.prototype.unstable_scheduleHydration = function(e) {
  if (e) {
    var t = Fu();
    e = { blockedOn: null, target: e, priority: t };
    for (var n = 0; n < jt.length && t !== 0 && t < jt[n].priority; n++) ;
    jt.splice(n, 0, e), n === 0 && Du(e);
  }
};
function ma(e) {
  return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11);
}
function Hs(e) {
  return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11 && (e.nodeType !== 8 || e.nodeValue !== " react-mount-point-unstable "));
}
function Io() {
}
function Vf(e, t, n, s, r) {
  if (r) {
    if (typeof s == "function") {
      var i = s;
      s = function() {
        var d = Ls(a);
        i.call(d);
      };
    }
    var a = ld(t, s, e, 0, null, !1, !1, "", Io);
    return e._reactRootContainer = a, e[ct] = a.current, fl(e.nodeType === 8 ? e.parentNode : e), _t(), a;
  }
  for (; r = e.lastChild; ) e.removeChild(r);
  if (typeof s == "function") {
    var u = s;
    s = function() {
      var d = Ls(o);
      u.call(d);
    };
  }
  var o = ha(e, 0, !1, null, null, !1, !1, "", Io);
  return e._reactRootContainer = o, e[ct] = o.current, fl(e.nodeType === 8 ? e.parentNode : e), _t(function() {
    Ws(t, o, n, s);
  }), o;
}
function Ys(e, t, n, s, r) {
  var i = n._reactRootContainer;
  if (i) {
    var a = i;
    if (typeof r == "function") {
      var u = r;
      r = function() {
        var o = Ls(a);
        u.call(o);
      };
    }
    Ws(t, a, e, r);
  } else a = Vf(n, t, e, r, s);
  return Ls(a);
}
Tu = function(e) {
  switch (e.tag) {
    case 3:
      var t = e.stateNode;
      if (t.current.memoizedState.isDehydrated) {
        var n = Xn(t.pendingLanes);
        n !== 0 && (Ri(t, n | 1), Se(t, le()), !(Y & 6) && (An = le() + 500, Ot()));
      }
      break;
    case 13:
      _t(function() {
        var s = dt(e, 1);
        if (s !== null) {
          var r = xe();
          Ye(s, e, 1, r);
        }
      }), fa(e, 1);
  }
};
Fi = function(e) {
  if (e.tag === 13) {
    var t = dt(e, 134217728);
    if (t !== null) {
      var n = xe();
      Ye(t, e, 134217728, n);
    }
    fa(e, 134217728);
  }
};
Ru = function(e) {
  if (e.tag === 13) {
    var t = At(e), n = dt(e, t);
    if (n !== null) {
      var s = xe();
      Ye(n, e, t, s);
    }
    fa(e, t);
  }
};
Fu = function() {
  return Q;
};
Ou = function(e, t) {
  var n = Q;
  try {
    return Q = e, t();
  } finally {
    Q = n;
  }
};
Vr = function(e, t, n) {
  switch (t) {
    case "input":
      if (Rr(e, n), t = n.name, n.type === "radio" && t != null) {
        for (n = e; n.parentNode; ) n = n.parentNode;
        for (n = n.querySelectorAll("input[name=" + JSON.stringify("" + t) + '][type="radio"]'), t = 0; t < n.length; t++) {
          var s = n[t];
          if (s !== e && s.form === e.form) {
            var r = Fs(s);
            if (!r) throw Error(z(90));
            fu(s), Rr(s, r);
          }
        }
      }
      break;
    case "textarea":
      mu(e, n);
      break;
    case "select":
      t = n.value, t != null && xn(e, !!n.multiple, t, !1);
  }
};
wu = oa;
ku = _t;
var Wf = { usingClientEntryPoint: !1, Events: [Sl, un, Fs, ju, Nu, oa] }, Yn = { findFiberByHostInstance: Wt, bundleType: 0, version: "18.3.1", rendererPackageName: "react-dom" }, qf = { bundleType: Yn.bundleType, version: Yn.version, rendererPackageName: Yn.rendererPackageName, rendererConfig: Yn.rendererConfig, overrideHookState: null, overrideHookStateDeletePath: null, overrideHookStateRenamePath: null, overrideProps: null, overridePropsDeletePath: null, overridePropsRenamePath: null, setErrorHandler: null, setSuspenseHandler: null, scheduleUpdate: null, currentDispatcherRef: ft.ReactCurrentDispatcher, findHostInstanceByFiber: function(e) {
  return e = bu(e), e === null ? null : e.stateNode;
}, findFiberByHostInstance: Yn.findFiberByHostInstance || Bf, findHostInstancesForRefresh: null, scheduleRefresh: null, scheduleRoot: null, setRefreshHandler: null, getCurrentFiber: null, reconcilerVersion: "18.3.1-next-f1338f8080-20240426" };
if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
  var ql = __REACT_DEVTOOLS_GLOBAL_HOOK__;
  if (!ql.isDisabled && ql.supportsFiber) try {
    Ps = ql.inject(qf), et = ql;
  } catch {
  }
}
Ae.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = Wf;
Ae.createPortal = function(e, t) {
  var n = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
  if (!ma(t)) throw Error(z(200));
  return Uf(e, t, null, n);
};
Ae.createRoot = function(e, t) {
  if (!ma(e)) throw Error(z(299));
  var n = !1, s = "", r = sd;
  return t != null && (t.unstable_strictMode === !0 && (n = !0), t.identifierPrefix !== void 0 && (s = t.identifierPrefix), t.onRecoverableError !== void 0 && (r = t.onRecoverableError)), t = ha(e, 1, !1, null, null, n, !1, s, r), e[ct] = t.current, fl(e.nodeType === 8 ? e.parentNode : e), new pa(t);
};
Ae.findDOMNode = function(e) {
  if (e == null) return null;
  if (e.nodeType === 1) return e;
  var t = e._reactInternals;
  if (t === void 0)
    throw typeof e.render == "function" ? Error(z(188)) : (e = Object.keys(e).join(","), Error(z(268, e)));
  return e = bu(t), e = e === null ? null : e.stateNode, e;
};
Ae.flushSync = function(e) {
  return _t(e);
};
Ae.hydrate = function(e, t, n) {
  if (!Hs(t)) throw Error(z(200));
  return Ys(null, e, t, !0, n);
};
Ae.hydrateRoot = function(e, t, n) {
  if (!ma(e)) throw Error(z(405));
  var s = n != null && n.hydratedSources || null, r = !1, i = "", a = sd;
  if (n != null && (n.unstable_strictMode === !0 && (r = !0), n.identifierPrefix !== void 0 && (i = n.identifierPrefix), n.onRecoverableError !== void 0 && (a = n.onRecoverableError)), t = ld(t, null, e, 1, n ?? null, r, !1, i, a), e[ct] = t.current, fl(e), s) for (e = 0; e < s.length; e++) n = s[e], r = n._getVersion, r = r(n._source), t.mutableSourceEagerHydrationData == null ? t.mutableSourceEagerHydrationData = [n, r] : t.mutableSourceEagerHydrationData.push(
    n,
    r
  );
  return new qs(t);
};
Ae.render = function(e, t, n) {
  if (!Hs(t)) throw Error(z(200));
  return Ys(null, e, t, !1, n);
};
Ae.unmountComponentAtNode = function(e) {
  if (!Hs(e)) throw Error(z(40));
  return e._reactRootContainer ? (_t(function() {
    Ys(null, null, e, !1, function() {
      e._reactRootContainer = null, e[ct] = null;
    });
  }), !0) : !1;
};
Ae.unstable_batchedUpdates = oa;
Ae.unstable_renderSubtreeIntoContainer = function(e, t, n, s) {
  if (!Hs(n)) throw Error(z(200));
  if (e == null || e._reactInternals === void 0) throw Error(z(38));
  return Ys(e, t, n, !1, s);
};
Ae.version = "18.3.1-next-f1338f8080-20240426";
function rd() {
  if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function"))
    try {
      __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(rd);
    } catch (e) {
      console.error(e);
    }
}
rd(), ru.exports = Ae;
var Hf = ru.exports, id, Uo = Hf;
id = Uo.createRoot, Uo.hydrateRoot;
function O(e, t = "number") {
  if (e == null || Number.isNaN(e)) return "—";
  if (t === "percent") return `${(e * 100).toFixed(1)}%`;
  const n = Math.abs(e);
  let s;
  return n >= 1e9 ? s = `${(e / 1e9).toFixed(1)}B` : n >= 1e6 ? s = `${(e / 1e6).toFixed(1)}M` : n >= 1e3 ? s = `${(e / 1e3).toFixed(1)}K` : n >= 100 || Number.isInteger(e) ? s = Math.round(e).toLocaleString() : s = e.toFixed(2), t === "currency" ? e < 0 ? `-$${s.replace("-", "")}` : `$${s}` : s;
}
function Kt(e, t = 1) {
  if (e == null || Number.isNaN(e)) return "—";
  const n = (e * 100).toFixed(t);
  return `${e > 0 ? "+" : ""}${n}%`;
}
function ad(e, t = !1) {
  return e == null || Math.abs(e) < 5e-4 ? "flat" : e > 0 !== t ? "up" : "down";
}
const $e = (e = "") => e.split(".").pop().replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (t) => t.toUpperCase()), Pn = {
  executives: "Executives",
  managers: "Managers",
  daily_operations: "Operations",
  weekly_business_review: "Weekly business review"
}, ji = {
  comparable_time_series: "Comparable time series",
  enterprise_scope_authorized: "Enterprise scope authorized",
  manager_scope_authorized: "Manager scope authorized",
  operating_scope_authorized: "Operating scope authorized",
  stable_segment_hierarchy: "Stable segment hierarchy",
  period_complete: "Complete period",
  fresh_data: "Fresh data (≤ 2 days)",
  event_time: "Event time",
  comparable_intraday_series: "Intraday series",
  target: "Target / baseline",
  forecast_versioned: "Snowflake ML forecast",
  reconciled_driver_bridge: "Reconciled driver bridge",
  action_tracking: "Decision tracking",
  plan_versioned: "Versioned plan",
  risk_metadata_current: "Risk register"
};
let Bo = 0;
const va = (e) => {
  const t = P.useRef(null);
  return t.current || (Bo += 1, t.current = `${e}${Bo}`), t.current;
};
function tn(e = 720) {
  const t = P.useRef(null), [n, s] = P.useState(e);
  return P.useLayoutEffect(() => {
    const r = t.current;
    if (!r) return;
    const i = () => {
      const u = Math.round(r.clientWidth);
      u > 50 && s(u);
    };
    i();
    const a = typeof ResizeObserver < "u" ? new ResizeObserver(i) : null;
    return a && a.observe(r), () => a && a.disconnect();
  }, []), [t, n];
}
function Ke(e) {
  const [t, n] = P.useState(null), s = (a, u) => {
    const o = e.current;
    if (!o) return;
    const d = o.getBoundingClientRect(), m = a.clientX - d.left, p = a.clientY - d.top;
    n({ x: m, y: p, content: u, flip: m > d.width * 0.62 });
  }, r = () => n(null);
  return [t ? /* @__PURE__ */ l.jsx("div", { className: `tip ${t.flip ? "flip" : ""}`, style: { left: t.x, top: t.y }, children: t.content }) : null, s, r];
}
function Ie({ title: e, rows: t = [] }) {
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    e && /* @__PURE__ */ l.jsx("div", { className: "tip-title", children: e }),
    t.filter(Boolean).map(([n, s, r], i) => /* @__PURE__ */ l.jsxs("div", { className: "tip-row", children: [
      /* @__PURE__ */ l.jsx("span", { children: n }),
      /* @__PURE__ */ l.jsx("b", { className: r || "", children: s })
    ] }, i))
  ] });
}
function zn(e, t, n = 4) {
  e === t && (t = e + 1);
  const s = t - e, r = s / n, i = 10 ** Math.floor(Math.log10(r)), a = [1, 2, 2.5, 5, 10].map((m) => m * i).find((m) => s / m <= n) || r, u = Math.floor(e / a) * a, o = Math.ceil(t / a) * a, d = [];
  for (let m = u; m <= o + a / 2; m += a) d.push(m);
  return d;
}
function od(e, { force0: t = !1 } = {}) {
  const n = Math.min(...e), s = Math.max(...e);
  if (t || n <= 0 || s <= 0) return { lo: Math.min(0, n), hi: Math.max(s, n === s ? n + 1e-9 : s), zoomed: !1 };
  if ((s - n) / s > 0.4) return { lo: 0, hi: s, zoomed: !1 };
  const r = Math.max((s - n) * 0.25, s * 5e-3);
  return { lo: Math.max(0, n - r), hi: s + r, zoomed: !0 };
}
function ud({ x: e, y: t }) {
  return /* @__PURE__ */ l.jsxs("g", { className: "axis-break", children: [
    /* @__PURE__ */ l.jsx("title", { children: "Axis zoomed to the data range (does not start at 0)" }),
    /* @__PURE__ */ l.jsx("rect", { x: e - 7, y: t - 7, width: "14", height: "9" }),
    /* @__PURE__ */ l.jsx("path", { d: `M${e - 7},${t - 2} l3.5,-3 l3.5,3 l3.5,-3 l3.5,3 M${e - 7},${t + 2} l3.5,-3 l3.5,3 l3.5,-3 l3.5,3` })
  ] });
}
const Tn = (e) => e == null ? "—" : `${e > 0 ? "+" : ""}${(e * 100).toFixed(1)}%`;
function cd({ points: e = [], forecast: t = [], kind: n, height: s = 240, baselineLabel: r, seriesLabel: i = "Actual" }) {
  var _;
  const [a, u] = P.useState(null), o = P.useRef(null), [d, m] = tn(), [p, v, j] = Ke(d), y = va("lg"), C = [...e.map((E) => ({ ...E, t: "a" })), ...t.map((E) => ({ ...E, t: "f" }))], k = [];
  if (e.forEach((E) => {
    E.value != null && k.push(E.value), E.baseline != null && k.push(E.baseline);
  }), t.forEach((E) => {
    k.push(E.lower, E.upper, E.forecast);
  }), !k.length) return /* @__PURE__ */ l.jsx("div", { ref: d, children: /* @__PURE__ */ l.jsx(Dt, { text: "No data points in this window." }) });
  const c = od(k), h = zn(c.lo, c.hi), f = h[0], x = h[h.length - 1], N = { l: 56, r: 12, t: 12, b: 28 }, g = m - N.l - N.r, M = s - N.t - N.b, S = C.length, A = (E) => N.l + (S <= 1 ? g / 2 : E * g / (S - 1)), w = (E) => N.t + M - (E - f) / (x - f || 1) * M, D = (E, T, b = 0) => E.map((B, W) => B[T] == null ? null : `${A(W + b)},${w(B[T])}`).filter(Boolean).map((B, W) => (W ? "L" : "M") + B).join(" "), L = e.length, V = t.length ? [
    ...t.map((E, T) => `${A(T + L)},${w(E.upper)}`),
    ...t.slice().reverse().map((E, T) => `${A(L + t.length - 1 - T)},${w(E.lower)}`)
  ] : [], q = Math.max(1, Math.ceil(S / Math.max(3, Math.floor(m / 90)))), F = (E) => {
    const T = o.current.getBoundingClientRect(), b = (E.clientX - T.left) / T.width * m, B = Math.max(0, Math.min(S - 1, Math.round((b - N.l) / g * (S - 1))));
    u(B);
    const W = C[B], ae = B > 0 && C[B - 1].t === "a" ? C[B - 1].value : null;
    v(E, W.t === "a" ? /* @__PURE__ */ l.jsx(Ie, { title: W.label, rows: [
      [i, O(W.value, n)],
      W.baseline != null && [r || "Baseline", O(W.baseline, n)],
      W.baseline != null && ["vs baseline", Tn(W.baseline ? (W.value - W.baseline) / Math.abs(W.baseline) : null)],
      ae != null && W.value != null && ["vs previous", Tn(ae ? (W.value - ae) / Math.abs(ae) : null)]
    ] }) : /* @__PURE__ */ l.jsx(Ie, { title: `${W.label} · forecast`, rows: [
      ["Forecast", O(W.forecast, n)],
      ["80% range", `${O(W.lower, n)} – ${O(W.upper, n)}`]
    ] }));
  }, U = a != null ? C[a] : null;
  return /* @__PURE__ */ l.jsxs("div", { className: "chart", ref: d, children: [
    /* @__PURE__ */ l.jsxs(
      "svg",
      {
        ref: o,
        viewBox: `0 0 ${m} ${s}`,
        role: "img",
        onMouseMove: F,
        onMouseLeave: () => {
          u(null), j();
        },
        children: [
          h.map((E) => /* @__PURE__ */ l.jsxs("g", { children: [
            /* @__PURE__ */ l.jsx("line", { x1: N.l, x2: m - N.r, y1: w(E), y2: w(E), className: "grid" }),
            /* @__PURE__ */ l.jsx("text", { x: N.l - 8, y: w(E) + 4, className: "tick", textAnchor: "end", children: O(E, n) })
          ] }, E)),
          C.map((E, T) => (T % q === 0 && S - 1 - T >= q / 2 || T === S - 1) && /* @__PURE__ */ l.jsx("text", { x: A(T), y: s - 8, className: "tick", textAnchor: T === S - 1 ? "end" : T === 0 ? "start" : "middle", children: Yf(E.label) }, T)),
          c.zoomed && /* @__PURE__ */ l.jsx(ud, { x: N.l, y: N.t + M - 3 }),
          V.length > 0 && /* @__PURE__ */ l.jsx("polygon", { points: V.join(" "), className: "band" }),
          e.some((E) => E.baseline != null) && /* @__PURE__ */ l.jsx("path", { d: D(e, "baseline"), className: "line baseline" }),
          /* @__PURE__ */ l.jsx("defs", { children: /* @__PURE__ */ l.jsxs("linearGradient", { id: y, x1: "0", x2: "0", y1: "0", y2: "1", children: [
            /* @__PURE__ */ l.jsx("stop", { offset: "0%", stopColor: "var(--area, #29B5E8)", stopOpacity: "0.28" }),
            /* @__PURE__ */ l.jsx("stop", { offset: "100%", stopColor: "var(--area, #29B5E8)", stopOpacity: "0" })
          ] }) }),
          (() => {
            const E = e.map((T, b) => T.value == null ? null : [A(b), w(T.value)]).filter(Boolean);
            return E.length > 1 ? /* @__PURE__ */ l.jsx("path", { d: `M${E[0][0]},${N.t + M} ${E.map((T) => `L${T[0]},${T[1]}`).join(" ")} L${E[E.length - 1][0]},${N.t + M} Z`, fill: `url(#${y})` }) : null;
          })(),
          /* @__PURE__ */ l.jsx("path", { d: D(e, "value"), className: "line actual" }),
          (() => {
            var T;
            const E = e.map((b) => b.value).lastIndexOf((T = e.filter((b) => b.value != null).slice(-1)[0]) == null ? void 0 : T.value);
            return E >= 0 && a == null ? /* @__PURE__ */ l.jsx("circle", { cx: A(E), cy: w(e[E].value), r: "4.5", className: "dot end" }) : null;
          })(),
          t.length > 0 && /* @__PURE__ */ l.jsx("path", { d: `M${A(L - 1)},${w(((_ = e[e.length - 1]) == null ? void 0 : _.value) ?? t[0].forecast)} ` + t.map((E, T) => `L${A(T + L)},${w(E.forecast)}`).join(" "), className: "line forecast" }),
          U && /* @__PURE__ */ l.jsx("line", { x1: A(a), x2: A(a), y1: N.t, y2: N.t + M, className: "cursor" }),
          U && U.t === "a" && U.value != null && /* @__PURE__ */ l.jsx("circle", { cx: A(a), cy: w(U.value), r: "4", className: "dot" }),
          U && U.t === "f" && /* @__PURE__ */ l.jsx("circle", { cx: A(a), cy: w(U.forecast), r: "4", className: "dot f" })
        ]
      }
    ),
    p,
    /* @__PURE__ */ l.jsxs("div", { className: "legend", children: [
      /* @__PURE__ */ l.jsxs("span", { children: [
        /* @__PURE__ */ l.jsx("i", { className: "sw actual" }),
        i
      ] }),
      e.some((E) => E.baseline != null) && /* @__PURE__ */ l.jsxs("span", { children: [
        /* @__PURE__ */ l.jsx("i", { className: "sw baseline" }),
        r || "Baseline"
      ] }),
      t.length > 0 && /* @__PURE__ */ l.jsxs("span", { children: [
        /* @__PURE__ */ l.jsx("i", { className: "sw forecast" }),
        "Forecast (80% band)"
      ] })
    ] })
  ] });
}
function Yf(e = "") {
  return e.replace("Wk of ", "").replace(/ 20(\d\d)$/, " '$1");
}
function Qf({ values: e = [], labels: t = [], kind: n, height: s = 44 }) {
  const [r, i] = P.useState(null), [a, u] = tn(220), [o, d, m] = Ke(a), p = va("sg"), v = e.filter((x) => x != null);
  if (v.length < 2) return null;
  const j = Math.min(...v), y = Math.max(...v), C = (x) => 3 + x / (e.length - 1) * (u - 6), k = (x) => s - 4 - (x - j) / (y - j || 1) * (s - 8), c = e.map((x, N) => x == null ? null : `${C(N)},${k(x)}`).filter(Boolean).join(" "), h = e.length - 1, f = (x) => {
    const N = x.currentTarget.getBoundingClientRect(), g = Math.max(0, Math.min(h, Math.round((x.clientX - N.left) / N.width * h)));
    i(g), d(x, /* @__PURE__ */ l.jsx(Ie, { title: t[g] || "", rows: [["Value", O(e[g], n)]] }));
  };
  return /* @__PURE__ */ l.jsxs("div", { className: "spark-wrap", ref: a, children: [
    /* @__PURE__ */ l.jsxs(
      "svg",
      {
        className: "spark",
        viewBox: `0 0 ${u} ${s}`,
        onMouseMove: f,
        onMouseLeave: () => {
          i(null), m();
        },
        children: [
          /* @__PURE__ */ l.jsx("defs", { children: /* @__PURE__ */ l.jsxs("linearGradient", { id: p, x1: "0", x2: "0", y1: "0", y2: "1", children: [
            /* @__PURE__ */ l.jsx("stop", { offset: "0%", stopColor: "var(--area, #29B5E8)", stopOpacity: "0.30" }),
            /* @__PURE__ */ l.jsx("stop", { offset: "100%", stopColor: "var(--area, #29B5E8)", stopOpacity: "0" })
          ] }) }),
          (() => {
            const x = e.map((N, g) => N == null ? null : g).filter((N) => N != null);
            return /* @__PURE__ */ l.jsx("path", { d: `M${C(x[0])},${s} ${x.map((N) => `L${C(N)},${k(e[N])}`).join(" ")} L${C(x[x.length - 1])},${s} Z`, fill: `url(#${p})`, stroke: "none" });
          })(),
          /* @__PURE__ */ l.jsx("polyline", { points: c }),
          e[h] != null && /* @__PURE__ */ l.jsx("circle", { cx: C(h), cy: k(e[h]), r: "3", className: "spark-now" }),
          r != null && e[r] != null && /* @__PURE__ */ l.jsx("circle", { cx: C(r), cy: k(e[r]), r: "3", className: "spark-hover" })
        ]
      }
    ),
    o
  ] });
}
function Kf({ rows: e = [], kind: t, max: n = 12, onSelect: s, currentLabel: r, priorLabel: i, inverse: a = !1 }) {
  const u = (y) => y == null || y === 0 ? "" : y > 0 !== a ? "up" : "down", o = P.useRef(null), [d, m, p] = Ke(o), v = e.slice(0, n), j = Math.max(...v.map((y) => Math.max(y.current || 0, y.prior || 0)), 1e-12);
  return /* @__PURE__ */ l.jsxs("div", { className: "bars chart", ref: o, onMouseLeave: p, children: [
    v.map((y) => /* @__PURE__ */ l.jsxs(
      "button",
      {
        type: "button",
        className: "bar-row",
        onClick: () => s && s(y),
        onMouseMove: (C) => m(C, /* @__PURE__ */ l.jsx(Ie, { title: y.segment, rows: [
          [r || "Current", O(y.current, t)],
          y.prior != null && [i || "Prior", O(y.prior, t)],
          y.change != null && ["Change", Tn(y.change), u(y.change)],
          y.share != null && ["Share of total", `${(y.share * 100).toFixed(1)}%`],
          s && ["", "Click to ask the agent why"]
        ] })),
        children: [
          /* @__PURE__ */ l.jsx("span", { className: "bar-label", children: y.segment }),
          /* @__PURE__ */ l.jsxs("span", { className: "bar-track", children: [
            /* @__PURE__ */ l.jsx("i", { className: "bar-fill", style: { width: `${Math.max(0, (y.current || 0) / j) * 100}%` } }),
            y.prior != null && /* @__PURE__ */ l.jsx("i", { className: "bar-prior", style: { left: `${Math.max(0, y.prior / j) * 100}%` } })
          ] }),
          /* @__PURE__ */ l.jsx("span", { className: "bar-value", children: O(y.current, t) }),
          /* @__PURE__ */ l.jsx("span", { className: `bar-delta ${u(y.change)}`, children: y.change == null ? "" : `${y.change > 0 ? "▲" : "▼"} ${(Math.abs(y.change) * 100).toFixed(0)}%` })
        ]
      },
      y.segment
    )),
    d
  ] });
}
function Xf({ start: e, end: t, steps: n = [], kind: s, startLabel: r, endLabel: i, height: a = 250 }) {
  const [u, o] = tn(), [d, m, p] = Ke(u), v = [
    { name: r, v: e, type: "total" },
    ...n.map((w) => ({ name: w.segment, v: w.delta, type: w.delta >= 0 ? "up" : "down" })),
    { name: i, v: t, type: "total" }
  ];
  let j = 0;
  const y = v.map((w) => {
    if (w.type === "total")
      return j = w.v, { ...w, a: 0, b: w.v };
    const D = j;
    return j += w.v, { ...w, a: D, b: j };
  }), C = y.flatMap((w) => w.type === "total" ? [w.b] : [w.a, w.b]), k = od(C), c = zn(k.lo, k.hi, 4), h = c[0], f = c[c.length - 1];
  k.zoomed && y.forEach((w) => {
    w.type === "total" && (w.a = h);
  });
  const x = { l: 56, r: 8, t: 16, b: 46 }, N = o - x.l - x.r, g = a - x.t - x.b, M = N / y.length, S = (w) => x.t + g - (w - h) / (f - h || 1) * g, A = e || 0;
  return /* @__PURE__ */ l.jsxs("div", { className: "chart", ref: u, children: [
    /* @__PURE__ */ l.jsxs("svg", { viewBox: `0 0 ${o} ${a}`, role: "img", onMouseLeave: p, children: [
      c.map((w) => /* @__PURE__ */ l.jsxs("g", { children: [
        /* @__PURE__ */ l.jsx("line", { x1: x.l, x2: o - x.r, y1: S(w), y2: S(w), className: "grid" }),
        /* @__PURE__ */ l.jsx("text", { x: x.l - 8, y: S(w) + 4, className: "tick", textAnchor: "end", children: O(w, s) })
      ] }, w)),
      y.map((w, D) => /* @__PURE__ */ l.jsxs("g", { onMouseMove: (L) => m(L, /* @__PURE__ */ l.jsx(Ie, { title: w.name, rows: w.type === "total" ? [["Total", O(w.v, s)]] : [
        ["Contribution", `${w.v >= 0 ? "+" : "−"}${O(Math.abs(w.v), s)}`, w.v >= 0 ? "up" : "down"],
        ["Running total", O(w.b, s)],
        A ? ["% of starting total", Tn(w.v / Math.abs(A))] : null
      ] })), children: [
        /* @__PURE__ */ l.jsx(
          "rect",
          {
            x: x.l + D * M + M * 0.15,
            width: M * 0.7,
            y: S(Math.max(w.a, w.b)),
            height: Math.max(1, Math.abs(S(w.a) - S(w.b))),
            rx: "4",
            className: `wf ${w.type}`
          }
        ),
        /* @__PURE__ */ l.jsx("text", { x: x.l + D * M + M / 2, y: S(Math.max(w.a, w.b)) - 4, className: "tick val", textAnchor: "middle", children: w.type === "total" ? O(w.v, s) : `${w.v >= 0 ? "+" : "−"}${O(Math.abs(w.v), s)}` }),
        /* @__PURE__ */ l.jsx("text", { x: x.l + D * M + M / 2, y: a - 26, className: "tick", textAnchor: "middle", children: String(w.name).slice(0, 12) })
      ] }, D)),
      k.zoomed && /* @__PURE__ */ l.jsx(ud, { x: x.l, y: x.t + g - 3 })
    ] }),
    d
  ] });
}
const yt = ["var(--h1, #EEF6FC)", "var(--h2, #D2E7F6)", "var(--h3, #A9D1EE)", "var(--h4, #78B4E0)", "var(--h5, #4693CF)", "var(--h6, #1F72B3)", "var(--h7, #0D548C)"];
function Gf(e) {
  const t = [...e].sort((y, C) => y - C), n = t.length, s = yt.length - 1;
  if (!n) return { step: () => 0, breaks: [], cut: null };
  const r = (y, C) => y[Math.min(y.length - 1, Math.max(0, Math.floor(C * y.length)))], i = r(t, 0.75) - r(t, 0.25), a = r(t, 0.75) + 3 * i, u = n >= 8 && i > 0 ? t.filter((y) => y <= a) : t, o = u.length < n ? a : null, d = o == null ? yt.length : s, m = [...new Set(u)];
  let p, v;
  if (m.length <= d)
    p = (y) => Math.round(m.indexOf(y) / Math.max(1, m.length - 1) * (d - 1)), v = m.map((y) => [y, y]);
  else {
    const y = Array.from({ length: d - 1 }, (C, k) => r(u, (k + 1) / d));
    p = (C) => {
      let k = 0;
      for (; k < y.length && C >= y[k]; ) k += 1;
      return k;
    }, v = Array.from({ length: d }, (C, k) => [k === 0 ? u[0] : y[k - 1], k === d - 1 ? u[u.length - 1] : y[k]]);
  }
  return { step: (y) => o != null && y > o ? s : p(y), breaks: v, cut: o, max: t[n - 1] };
}
function dd({ rows: e = [], cols: t = [], values: n = [], kind: s, rowLabel: r, colLabel: i }) {
  const a = P.useRef(null), [u, o, d] = Ke(a), m = n.flat().filter((c) => c != null), { step: p, breaks: v, cut: j, max: y } = Gf(m), C = m.reduce((c, h) => c + h, 0), k = s !== "percent";
  return /* @__PURE__ */ l.jsxs("div", { className: "heat-wrap chart", ref: a, onMouseLeave: d, children: [
    /* @__PURE__ */ l.jsxs("table", { className: "heat", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsxs("th", { children: [
          r,
          " \\ ",
          i
        ] }),
        t.map((c) => /* @__PURE__ */ l.jsx("th", { children: c }, c))
      ] }) }),
      /* @__PURE__ */ l.jsx("tbody", { children: e.map((c, h) => /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", { children: c }),
        t.map((f, x) => {
          var M;
          const N = (M = n[h]) == null ? void 0 : M[x], g = N == null ? -1 : p(N);
          return /* @__PURE__ */ l.jsx(
            "td",
            {
              className: j != null && N > j ? "outlier" : "",
              style: { background: g < 0 ? "var(--heat-empty, #f6f8fb)" : yt[g], color: g >= 5 ? "var(--heat-ink-hi, #fff)" : "var(--heat-ink, #0f1d2e)" },
              onMouseMove: (S) => o(S, /* @__PURE__ */ l.jsx(Ie, { title: `${c} · ${f}`, rows: [
                ["Value", O(N, s)],
                N != null && (j != null && N > j ? ["Outlier", `far above the rest (> ${O(j, s)})`] : ["Shade", `${O(v[g][0], s)}–${O(v[g][1], s)}`]),
                k && C && N != null ? ["Share of table", `${(N / C * 100).toFixed(1)}%`] : null
              ] })),
              children: O(N, s)
            },
            f
          );
        })
      ] }, c)) })
    ] }),
    v.length > 1 && /* @__PURE__ */ l.jsxs("div", { className: "heat-legend", "aria-label": "Colour scale", children: [
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "Lower" }),
      v.map(([c, h], f) => /* @__PURE__ */ l.jsxs("span", { className: "hl-step", title: `${O(c, s)} – ${O(h, s)}`, children: [
        /* @__PURE__ */ l.jsx("i", { style: { background: yt[Math.round(f / Math.max(1, v.length - 1) * (j != null ? yt.length - 2 : yt.length - 1))] } }),
        /* @__PURE__ */ l.jsx("em", { children: O(c, s) })
      ] }, f)),
      j != null && /* @__PURE__ */ l.jsxs("span", { className: "hl-step out", title: `Outliers: above ${O(j, s)}`, children: [
        /* @__PURE__ */ l.jsx("i", { style: { background: yt[yt.length - 1] } }),
        /* @__PURE__ */ l.jsxs("em", { children: [
          "outlier ≤ ",
          O(y, s)
        ] })
      ] }),
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "Higher" })
    ] }),
    u
  ] });
}
function Jf({ points: e = [], kind: t }) {
  var c;
  const [n, s] = P.useState(null), r = P.useRef(null), [i, a, u] = Ke(r), o = e.map((h) => h.value).filter((h) => h != null);
  if (o.length < 2) return /* @__PURE__ */ l.jsx(Dt, { text: "Not enough points" });
  const d = 220, m = 70, p = Math.min(...o), v = Math.max(...o), j = (h) => h / (e.length - 1) * d, y = (h) => m - 6 - (h - p) / (v - p || 1) * (m - 12), C = e.map((h, f) => h.value == null ? null : `${j(f)},${y(h.value)}`).filter(Boolean), k = (h) => {
    const f = h.currentTarget.getBoundingClientRect(), x = Math.max(0, Math.min(e.length - 1, Math.round((h.clientX - f.left) / f.width * (e.length - 1))));
    s(x), a(h, /* @__PURE__ */ l.jsx(Ie, { title: e[x].label, rows: [["Value", O(e[x].value, t)]] }));
  };
  return /* @__PURE__ */ l.jsxs("div", { className: "chart", ref: r, children: [
    /* @__PURE__ */ l.jsxs("svg", { viewBox: `0 0 ${d} ${m}`, className: "mini", onMouseMove: k, onMouseLeave: () => {
      s(null), u();
    }, children: [
      /* @__PURE__ */ l.jsx("polyline", { points: C.join(" ") }),
      n != null && ((c = e[n]) == null ? void 0 : c.value) != null && /* @__PURE__ */ l.jsx("circle", { cx: j(n), cy: y(e[n].value), r: "3", className: "spark-hover" })
    ] }),
    i
  ] });
}
function Dt({ text: e }) {
  return /* @__PURE__ */ l.jsx("div", { className: "empty", children: e });
}
const Hl = ["var(--c1, #11629E)", "var(--c2, #29B5E8)", "var(--c3, #E8830C)", "var(--c4, #11A39A)", "var(--c5, #7D44CF)", "var(--c6, #D45B90)"], Vo = "var(--c-other, #A9B4C2)", jr = 6;
function Zf(e) {
  const t = (m) => /^other\b/i.test(String(m.label)), n = e.filter((m) => !t(m)), s = e.filter(t);
  if (n.length + (s.length ? 1 : 0) <= jr && s.length <= 1)
    return e.map((m) => ({ ...m, other: t(m) }));
  const r = n.slice(0, jr - 1), i = [...n.slice(jr - 1), ...s], a = (m) => i.reduce((p, v) => v[m] == null ? p : p + v[m], 0), u = i.filter((m) => !t(m)).map((m) => m.label), o = s.reduce((m, p) => {
    var v;
    return m + (Number((v = String(p.label).match(/\((\d+)\)/)) == null ? void 0 : v[1]) || 0);
  }, 0), d = u.length + o;
  return [
    ...r.map((m) => ({ ...m, other: !1 })),
    {
      label: `Other (${d})`,
      value: a("value"),
      share: i.some((m) => m.share != null) ? a("share") : null,
      other: !0,
      members: u,
      hidden: o
    }
  ];
}
function _f({ slices: e = [], kind: t, total: n, centerLabel: s }) {
  const r = Zf(e), [i, a] = P.useState(null), [u, o] = tn(400), [d, m, p] = Ke(u), v = 78, j = 54, y = 90;
  let C = -Math.PI / 2;
  const k = r.map((f, x) => {
    const N = C + (f.share || 0) * Math.PI * 2, g = N - C > Math.PI ? 1 : 0, M = (w, D) => `${y + D * Math.cos(w)},${y + D * Math.sin(w)}`, A = (f.share || 0) >= 0.9999 ? `M${y - v},${y} A${v},${v} 0 1 1 ${y + v},${y} A${v},${v} 0 1 1 ${y - v},${y} M${y - j},${y} A${j},${j} 0 1 0 ${y + j},${y} A${j},${j} 0 1 0 ${y - j},${y} Z` : `M${M(C, v)} A${v},${v} 0 ${g} 1 ${M(N, v)} L${M(N, j)} A${j},${j} 0 ${g} 0 ${M(C, j)} Z`;
    return C = N, { d: A, color: f.other ? Vo : Hl[x % Hl.length], s: f, i: x };
  }), c = i != null ? r[i] : null, h = (f) => {
    var x;
    return /* @__PURE__ */ l.jsx(Ie, { title: f.label, rows: [
      ["Value", O(f.value, t)],
      ["Share", `${((f.share || 0) * 100).toFixed(1)}%`],
      (x = f.members) != null && x.length ? ["Includes", f.members.slice(0, 4).join(", ") + (f.members.length + (f.hidden || 0) > 4 ? ` +${f.members.length + (f.hidden || 0) - 4} more` : "")] : null
    ] });
  };
  return /* @__PURE__ */ l.jsxs("div", { className: `donut-wrap chart ${o < 420 ? "stack" : ""}`, ref: u, onMouseLeave: () => {
    a(null), p();
  }, children: [
    /* @__PURE__ */ l.jsxs("svg", { viewBox: "0 0 180 180", className: "donut", children: [
      k.map((f) => /* @__PURE__ */ l.jsx(
        "path",
        {
          d: f.d,
          fill: f.color,
          fillRule: "evenodd",
          stroke: "#fff",
          strokeWidth: "2",
          opacity: i == null || i === f.i ? 1 : 0.35,
          onMouseMove: (x) => {
            a(f.i), m(x, h(f.s));
          }
        },
        f.i
      )),
      /* @__PURE__ */ l.jsx("text", { x: "90", y: "86", textAnchor: "middle", className: "donut-val", children: c ? `${((c.share || 0) * 100).toFixed(0)}%` : O(n, t) }),
      /* @__PURE__ */ l.jsx("text", { x: "90", y: "104", textAnchor: "middle", className: "tick", children: c ? String(c.label).slice(0, 16) : s })
    ] }),
    /* @__PURE__ */ l.jsx("div", { className: "donut-legend", children: r.map((f, x) => /* @__PURE__ */ l.jsxs("div", { className: "dl", onMouseMove: (N) => {
      a(x), m(N, h(f));
    }, children: [
      /* @__PURE__ */ l.jsx("i", { style: { background: f.other ? Vo : Hl[x % Hl.length] } }),
      /* @__PURE__ */ l.jsx("span", { children: f.label }),
      /* @__PURE__ */ l.jsx("b", { children: f.share == null ? "" : `${(f.share * 100).toFixed(1)}%` }),
      /* @__PURE__ */ l.jsx("em", { children: O(f.value, t) })
    ] }, f.label)) }),
    d
  ] });
}
function $f({ rows: e = [], kind: t, height: n = 250 }) {
  const [s, r] = tn(), [i, a] = P.useState(null), [u, o, d] = Ke(s);
  if (!e.length) return /* @__PURE__ */ l.jsx("div", { ref: s, children: /* @__PURE__ */ l.jsx(Dt, { text: "No data." }) });
  const m = { l: 56, r: 40, t: 12, b: 50 }, p = r - m.l - m.r, v = n - m.t - m.b, j = Math.max(...e.map((N) => N.value), 1e-12), y = zn(0, j, 4), C = y[y.length - 1], k = p / e.length, c = (N) => m.t + v - N / C * v, h = (N) => m.t + v - N * v, f = e.map((N, g) => `${g ? "L" : "M"}${m.l + g * k + k / 2},${h(N.cum_share || 0)}`).join(" "), x = Math.max(1, Math.ceil(e.length / Math.max(3, Math.floor(p / 60))));
  return /* @__PURE__ */ l.jsxs("div", { className: "chart", ref: s, children: [
    /* @__PURE__ */ l.jsxs("svg", { viewBox: `0 0 ${r} ${n}`, role: "img", onMouseLeave: () => {
      a(null), d();
    }, children: [
      y.map((N) => /* @__PURE__ */ l.jsxs("g", { children: [
        /* @__PURE__ */ l.jsx("line", { x1: m.l, x2: r - m.r, y1: c(N), y2: c(N), className: "grid" }),
        /* @__PURE__ */ l.jsx("text", { x: m.l - 8, y: c(N) + 4, className: "tick", textAnchor: "end", children: O(N, t) })
      ] }, N)),
      /* @__PURE__ */ l.jsx("line", { x1: m.l, x2: r - m.r, y1: h(0.8), y2: h(0.8), className: "line baseline" }),
      /* @__PURE__ */ l.jsx("text", { x: r - m.r + 4, y: h(0.8) + 4, className: "tick", children: "80%" }),
      /* @__PURE__ */ l.jsx("text", { x: r - m.r + 4, y: h(1) + 4, className: "tick", children: "100%" }),
      e.map((N, g) => /* @__PURE__ */ l.jsxs("g", { onMouseMove: (M) => {
        a(g), o(M, /* @__PURE__ */ l.jsx(Ie, { title: `#${g + 1} ${N.label}`, rows: [
          ["Value", O(N.value, t)],
          ["Cumulative share", `${((N.cum_share || 0) * 100).toFixed(1)}%`]
        ] }));
      }, children: [
        /* @__PURE__ */ l.jsx(
          "rect",
          {
            x: m.l + g * k + k * 0.12,
            width: k * 0.76,
            y: c(Math.max(0, N.value)),
            height: Math.max(1, m.t + v - c(Math.max(0, N.value))),
            rx: "3",
            className: `wf total ${i === g ? "hl" : ""}`
          }
        ),
        g % x === 0 && /* @__PURE__ */ l.jsx(
          "text",
          {
            x: m.l + g * k + k / 2,
            y: n - 34,
            className: "tick",
            textAnchor: "end",
            transform: `rotate(-35 ${m.l + g * k + k / 2} ${n - 34})`,
            children: String(N.label).slice(0, 14)
          }
        )
      ] }, g)),
      /* @__PURE__ */ l.jsx("path", { d: f, className: "line forecast" })
    ] }),
    u,
    /* @__PURE__ */ l.jsxs("div", { className: "legend", children: [
      /* @__PURE__ */ l.jsxs("span", { children: [
        /* @__PURE__ */ l.jsx("i", { className: "sw actual" }),
        "Value"
      ] }),
      /* @__PURE__ */ l.jsxs("span", { children: [
        /* @__PURE__ */ l.jsx("i", { className: "sw forecast" }),
        "Cumulative share"
      ] })
    ] })
  ] });
}
function ep(e, t, n, s) {
  if (e.length > 24) return [];
  const r = 6.1, i = 12, a = 6, u = e.map((v) => ({ cx: t(v.x), cy: n(v.y) })), o = [], d = (v, j) => v.x0 < j.x1 && j.x0 < v.x1 && v.y0 < j.y1 && j.y0 < v.y1, m = e.map((v, j) => j).sort((v, j) => Math.abs(e[j].y) - Math.abs(e[v].y)), p = [];
  return m.forEach((v) => {
    const j = String(e[v].label).slice(0, 16), y = j.length * r, { cx: C, cy: k } = u[v], h = [
      { x: C + 8, y: k + 4, anchor: "start", b: { x0: C + 7, x1: C + 9 + y, y0: k - 7, y1: k + 5 } },
      { x: C - 8, y: k + 4, anchor: "end", b: { x0: C - 9 - y, x1: C - 7, y0: k - 7, y1: k + 5 } },
      { x: C, y: k - 9, anchor: "middle", b: { x0: C - y / 2, x1: C + y / 2, y0: k - 9 - i + 2, y1: k - 7 } },
      { x: C, y: k + 17, anchor: "middle", b: { x0: C - y / 2, x1: C + y / 2, y0: k + 7, y1: k + 7 + i } }
    ].find((f) => f.b.x0 >= s.l && f.b.x1 <= s.r + 4 && f.b.y0 >= s.t - 2 && f.b.y1 <= s.b + 2 && !o.some((x) => d(x, f.b)) && !u.some((x, N) => N !== v && d(f.b, { x0: x.cx - a, x1: x.cx + a, y0: x.cy - a, y1: x.cy + a })));
    h && (o.push(h.b), p.push({ i: v, text: j, x: h.x, y: h.y, anchor: h.anchor }));
  }), p;
}
function tp({ points: e = [], xKind: t, yKind: n, xLabel: s, yLabel: r, height: i = 260 }) {
  const [a, u] = tn(), [o, d] = P.useState(null), [m, p, v] = Ke(a);
  if (!e.length) return /* @__PURE__ */ l.jsx("div", { ref: a, children: /* @__PURE__ */ l.jsx(Dt, { text: "No data." }) });
  const j = { l: 60, r: 14, t: 12, b: 40 }, y = u - j.l - j.r, C = i - j.t - j.b, k = (L) => {
    const V = Math.min(...L), q = Math.max(...L), F = (q - V || Math.abs(q) || 1) * 0.12;
    return [V - F, q + F];
  }, [c, h] = k(e.map((L) => L.x)), [f, x] = k(e.map((L) => L.y)), N = zn(c, h, 4), g = zn(f, x, 4), M = (L) => j.l + (L - N[0]) / (N[N.length - 1] - N[0] || 1) * y, S = (L) => j.t + C - (L - g[0]) / (g[g.length - 1] - g[0] || 1) * C, A = (L) => {
    const V = [...L].sort((q, F) => q - F);
    return V[Math.floor(V.length / 2)];
  }, w = A(e.map((L) => L.x)), D = A(e.map((L) => L.y));
  return /* @__PURE__ */ l.jsxs("div", { className: "chart", ref: a, children: [
    /* @__PURE__ */ l.jsxs("svg", { viewBox: `0 0 ${u} ${i}`, role: "img", onMouseLeave: () => {
      d(null), v();
    }, children: [
      g.map((L) => /* @__PURE__ */ l.jsxs("g", { children: [
        /* @__PURE__ */ l.jsx("line", { x1: j.l, x2: u - j.r, y1: S(L), y2: S(L), className: "grid" }),
        /* @__PURE__ */ l.jsx("text", { x: j.l - 8, y: S(L) + 4, className: "tick", textAnchor: "end", children: O(L, n) })
      ] }, `y${L}`)),
      N.map((L) => /* @__PURE__ */ l.jsx("text", { x: M(L), y: i - 22, className: "tick", textAnchor: "middle", children: O(L, t) }, `x${L}`)),
      /* @__PURE__ */ l.jsx("line", { x1: M(w), x2: M(w), y1: j.t, y2: j.t + C, className: "line baseline" }),
      /* @__PURE__ */ l.jsx("line", { x1: j.l, x2: u - j.r, y1: S(D), y2: S(D), className: "line baseline" }),
      e.map((L, V) => /* @__PURE__ */ l.jsx(
        "circle",
        {
          cx: M(L.x),
          cy: S(L.y),
          r: o === V ? 7 : 5,
          className: `pt ${L.y < 0 ? "neg" : ""}`,
          onMouseMove: (q) => {
            d(V), p(q, /* @__PURE__ */ l.jsx(Ie, { title: L.label, rows: [[s, O(L.x, t)], [r, O(L.y, n)]] }));
          }
        },
        V
      )),
      ep(e, M, S, { l: j.l, r: u - j.r, t: j.t, b: j.t + C }).map((L) => /* @__PURE__ */ l.jsx("text", { x: L.x, y: L.y, className: "tick pt-label", textAnchor: L.anchor, children: L.text }, `l${L.i}`)),
      /* @__PURE__ */ l.jsxs("text", { x: u - j.r, y: i - 6, className: "tick", textAnchor: "end", children: [
        s,
        " →"
      ] })
    ] }),
    m,
    /* @__PURE__ */ l.jsx("div", { className: "legend", children: /* @__PURE__ */ l.jsxs("span", { className: "muted small", children: [
      "↑ ",
      r,
      " · dashed lines = medians"
    ] }) })
  ] });
}
function np({ rows: e = [], kind: t, labels: n = [], inverse: s = !1 }) {
  const r = (p) => p == null || p === 0 ? "" : p > 0 !== s ? "up" : "down", i = P.useRef(null), [a, u, o] = Ke(i), d = Math.max(...e.flatMap((p) => [p.current || 0, p.prior || 0, p.yoy || 0]), 1e-12), m = ["current", "prior", "yoy"];
  return /* @__PURE__ */ l.jsxs("div", { className: "gbars chart", ref: i, onMouseLeave: o, children: [
    /* @__PURE__ */ l.jsx("div", { className: "legend", children: n.map((p, v) => /* @__PURE__ */ l.jsxs("span", { children: [
      /* @__PURE__ */ l.jsx("i", { className: `sw g${v}` }),
      p
    ] }, p)) }),
    e.map((p) => /* @__PURE__ */ l.jsxs("div", { className: "gbar", onMouseMove: (v) => u(v, /* @__PURE__ */ l.jsx(Ie, { title: p.segment, rows: [
      [n[0], O(p.current, t)],
      [n[1], O(p.prior, t)],
      [n[2], O(p.yoy, t)],
      ["vs previous", Tn(p.change), r(p.change)],
      ["vs last year", Tn(p.yoy_change), r(p.yoy_change)]
    ] })), children: [
      /* @__PURE__ */ l.jsx("span", { className: "bar-label", children: p.segment }),
      /* @__PURE__ */ l.jsx("div", { className: "gstack", children: m.map((v, j) => /* @__PURE__ */ l.jsxs("div", { className: "gline", children: [
        /* @__PURE__ */ l.jsx("i", { className: `g${j}`, style: { width: `${Math.max(0, (p[v] || 0) / d) * 100}%` } }),
        j === 0 && /* @__PURE__ */ l.jsx("em", { children: O(p[v], t) })
      ] }, v)) }),
      /* @__PURE__ */ l.jsx("span", { className: `bar-delta ${r(p.yoy_change)}`, children: p.yoy_change == null ? "" : `${p.yoy_change > 0 ? "▲" : "▼"} ${(Math.abs(p.yoy_change) * 100).toFixed(0)}% YoY` })
    ] }, p.segment)),
    a
  ] });
}
const vt = {
  actual: { stroke: "var(--line-main, #1872C4)", width: 2.6, dash: "" },
  plan: { stroke: "#0b2440", width: 1.6, dash: "3 4" },
  ref: { stroke: "#A9B4C2", width: 1.8, dash: "" },
  forecast: { stroke: "#7D44CF", width: 2.2, dash: "6 4" }
};
function lp({ labels: e = [], series: t = [], band: n, kind: s, nowIndex: r, nowLabel: i = "now", height: a = 250 }) {
  const [u, o] = tn(), [d, m] = P.useState(null), [p, v, j] = Ke(u), y = va("sc"), C = t.flatMap((F) => F.values.filter((U) => U != null));
  if (n && C.push(...n.lower.filter((F) => F != null), ...n.upper.filter((F) => F != null)), !C.length || !e.length) return /* @__PURE__ */ l.jsx("div", { ref: u, children: /* @__PURE__ */ l.jsx(Dt, { text: "No data points yet." }) });
  const k = zn(Math.min(0, ...C), Math.max(...C), 4), c = k[0], h = k[k.length - 1], f = { l: 58, r: 14, t: 14, b: 28 }, x = o - f.l - f.r, N = a - f.t - f.b, g = e.length, M = (F) => f.l + (g <= 1 ? x / 2 : F * x / (g - 1)), S = (F) => f.t + N - (F - c) / (h - c || 1) * N, A = (F) => {
    let U = "", _ = !1;
    return F.forEach((E, T) => {
      if (E == null) {
        _ = !1;
        return;
      }
      U += `${_ ? "L" : "M"}${M(T)},${S(E)} `, _ = !0;
    }), U;
  }, w = t.find((F) => F.style === "actual"), D = w ? w.values.map((F, U) => F == null ? null : [M(U), S(F)]).filter(Boolean) : [], L = n ? (() => {
    const F = n.upper.map((U, _) => U == null || n.lower[_] == null ? null : _).filter((U) => U != null);
    return F.length > 1 ? [...F.map((U) => `${M(U)},${S(n.upper[U])}`), ...F.slice().reverse().map((U) => `${M(U)},${S(n.lower[U])}`)].join(" ") : null;
  })() : null, V = Math.max(1, Math.ceil(g / Math.max(3, Math.floor(x / 64)))), q = (F) => {
    const U = F.currentTarget.getBoundingClientRect(), _ = (F.clientX - U.left) / U.width * o, E = Math.max(0, Math.min(g - 1, Math.round((_ - f.l) / x * (g - 1))));
    m(E);
    const T = t.filter((b) => b.values[E] != null).map((b) => [b.label, O(b.values[E], s)]);
    if (w && w.values[E] != null) {
      const b = t.find((B) => B.style === "plan" && B.values[E] != null);
      if (b && b.values[E]) {
        const B = (w.values[E] - b.values[E]) / Math.abs(b.values[E]);
        T.push([`vs ${b.label.toLowerCase()}`, `${B > 0 ? "+" : ""}${(B * 100).toFixed(1)}%`, B >= 0 ? "up" : "down"]);
      }
    }
    n && n.lower[E] != null && E !== r && T.push(["80% range", `${O(n.lower[E], s)} – ${O(n.upper[E], s)}`]), v(F, /* @__PURE__ */ l.jsx(Ie, { title: e[E], rows: T }));
  };
  return /* @__PURE__ */ l.jsxs("div", { className: "chart", ref: u, children: [
    /* @__PURE__ */ l.jsxs("svg", { viewBox: `0 0 ${o} ${a}`, role: "img", onMouseMove: q, onMouseLeave: () => {
      m(null), j();
    }, children: [
      k.map((F) => /* @__PURE__ */ l.jsxs("g", { children: [
        /* @__PURE__ */ l.jsx("line", { x1: f.l, x2: o - f.r, y1: S(F), y2: S(F), className: "grid" }),
        /* @__PURE__ */ l.jsx("text", { x: f.l - 8, y: S(F) + 4, className: "tick", textAnchor: "end", children: O(F, s) })
      ] }, F)),
      e.map((F, U) => (U % V === 0 && g - 1 - U >= V / 2 || U === g - 1) && /* @__PURE__ */ l.jsx("text", { x: M(U), y: a - 8, className: "tick", textAnchor: U === g - 1 ? "end" : U === 0 ? "start" : "middle", children: F }, U)),
      L && /* @__PURE__ */ l.jsx("polygon", { points: L, className: "band" }),
      /* @__PURE__ */ l.jsx("defs", { children: /* @__PURE__ */ l.jsxs("linearGradient", { id: y, x1: "0", x2: "0", y1: "0", y2: "1", children: [
        /* @__PURE__ */ l.jsx("stop", { offset: "0%", stopColor: "var(--area, #29B5E8)", stopOpacity: "0.26" }),
        /* @__PURE__ */ l.jsx("stop", { offset: "100%", stopColor: "var(--area, #29B5E8)", stopOpacity: "0" })
      ] }) }),
      D.length > 1 && /* @__PURE__ */ l.jsx("path", { d: `M${D[0][0]},${f.t + N} ${D.map((F) => `L${F[0]},${F[1]}`).join(" ")} L${D[D.length - 1][0]},${f.t + N} Z`, fill: `url(#${y})` }),
      t.filter((F) => F.style !== "actual").map((F) => {
        const U = vt[F.style] || vt.ref;
        return /* @__PURE__ */ l.jsx("path", { d: A(F.values), fill: "none", stroke: U.stroke, strokeWidth: U.width, strokeDasharray: U.dash }, F.key);
      }),
      w && /* @__PURE__ */ l.jsx("path", { d: A(w.values), fill: "none", stroke: vt.actual.stroke, strokeWidth: vt.actual.width, strokeLinejoin: "round" }),
      r != null && r < g - 1 && /* @__PURE__ */ l.jsxs("g", { className: "now-guide", children: [
        /* @__PURE__ */ l.jsx("line", { x1: M(r), x2: M(r), y1: f.t, y2: f.t + N }),
        /* @__PURE__ */ l.jsx(
          "text",
          {
            x: M(r) + (M(r) > o - 110 ? -4 : 4),
            y: f.t + 10,
            className: "tick now",
            textAnchor: M(r) > o - 110 ? "end" : "start",
            children: i
          }
        )
      ] }),
      w && r != null && w.values[r] != null && d == null && /* @__PURE__ */ l.jsx("circle", { cx: M(r), cy: S(w.values[r]), r: "4.5", className: "dot end" }),
      d != null && /* @__PURE__ */ l.jsx("line", { x1: M(d), x2: M(d), y1: f.t, y2: f.t + N, className: "cursor" }),
      d != null && t.map((F) => F.values[d] != null && /* @__PURE__ */ l.jsx("circle", { cx: M(d), cy: S(F.values[d]), r: "3.5", fill: (vt[F.style] || vt.ref).stroke, stroke: "#fff", strokeWidth: "1.5" }, F.key))
    ] }),
    p,
    /* @__PURE__ */ l.jsx("div", { className: "legend slegend", children: t.map((F) => {
      const U = vt[F.style] || vt.ref;
      return /* @__PURE__ */ l.jsxs("span", { children: [
        /* @__PURE__ */ l.jsx("svg", { width: "22", height: "8", children: /* @__PURE__ */ l.jsx("line", { x1: "0", x2: "22", y1: "4", y2: "4", stroke: U.stroke, strokeWidth: "2.4", strokeDasharray: U.dash }) }),
        F.label
      ] }, F.key);
    }) })
  ] });
}
function sp({ value: e, target: t, good: n }) {
  if (e == null || !Number.isFinite(e)) return null;
  const s = t != null && Number.isFinite(t) ? t : null, r = (j) => Math.max(0, Math.min(100, j)), i = Math.min(0, e, s ?? 0), u = (Math.max(0, e, s ?? 0) - i) * 1.12 || 1, o = (j) => r((j - i) / u * 100), d = o(0), m = o(e), p = Math.min(d, m), v = Math.abs(m - d);
  return /* @__PURE__ */ l.jsxs("div", { className: "bullet", title: s != null ? `Bar = actual, tick = target (${s.toLocaleString()})` : "", children: [
    i < 0 && /* @__PURE__ */ l.jsx("b", { className: "zero", style: { left: `${d}%` } }),
    /* @__PURE__ */ l.jsx("i", { className: n === !1 ? "off" : "", style: { left: `${p}%`, width: `${v}%` } }),
    s != null && /* @__PURE__ */ l.jsx("s", { style: { left: `calc(${o(s)}% - 1px)` } })
  ] });
}
const Qs = /RETURN|STOCKOUT|DELIVERY_DAYS|TRANSIT|CLICK_TO_SHIP|DISCOUNT|LOST|COST|COGS|WEEKS_OF_SUPPLY/i;
function Wo({ data: e, ctx: t, spec: n }) {
  const s = (n == null ? void 0 : n.show_trend) !== !1;
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsx("div", { className: "kpis", children: e.items.map((r, i) => {
      var o;
      const a = (o = t == null ? void 0 : t.defs) == null ? void 0 : o[r.metric], u = Qs.test(r.metric);
      return /* @__PURE__ */ l.jsxs("div", { className: `kpi ${i === 0 ? "primary" : ""}`, children: [
        /* @__PURE__ */ l.jsxs("div", { className: "kpi-label", title: a || "", children: [
          r.label,
          a ? /* @__PURE__ */ l.jsx("span", { className: "def", children: "ⓘ" }) : null
        ] }),
        /* @__PURE__ */ l.jsx("div", { className: "kpi-value", children: O(r.current, r.kind) }),
        /* @__PURE__ */ l.jsx("div", { className: "kpi-period", children: e.current_label }),
        /* @__PURE__ */ l.jsxs("div", { className: "kpi-delta", children: [
          /* @__PURE__ */ l.jsxs("span", { className: `delta ${ad(r.delta, u)}`, children: [
            gn(r.delta),
            " ",
            r.kind === "percent" && r.delta_pt != null ? `${r.delta_pt >= 0 ? "+" : "−"}${(Math.abs(r.delta_pt) * 100).toFixed(1)} pt` : Kt(r.delta)
          ] }),
          /* @__PURE__ */ l.jsxs("em", { children: [
            r.delta_label,
            r.base != null ? ` (${O(r.base, r.kind)})` : ""
          ] })
        ] }),
        s && /* @__PURE__ */ l.jsx(Qf, { values: r.spark, labels: e.spark_labels, kind: r.kind })
      ] }, r.metric);
    }) }),
    s && /* @__PURE__ */ l.jsxs("div", { className: "kpi-foot", children: [
      "Lines show the ",
      (e.spark_caption || "").toLowerCase(),
      " · hover a line for each value · green/red already accounts for metrics where lower is better"
    ] })
  ] });
}
function rp({ data: e }) {
  return /* @__PURE__ */ l.jsx(
    cd,
    {
      points: e.points,
      kind: e.kind,
      baselineLabel: e.baseline_label,
      seriesLabel: e.metric_label
    }
  );
}
function ip({ data: e }) {
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsx(cd, { points: e.history, forecast: e.forecast, kind: e.kind, seriesLabel: e.metric_label }),
    /* @__PURE__ */ l.jsxs("div", { className: "prov", children: [
      "⚙ ",
      e.provenance
    ] })
  ] });
}
function Nr({ data: e, ctx: t, spec: n }) {
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsxs("div", { className: "sub", children: [
      e.dimension_label,
      " · ",
      e.current_label,
      " (marker = ",
      e.prior_label,
      ")"
    ] }),
    /* @__PURE__ */ l.jsx(
      Kf,
      {
        inverse: Qs.test((n == null ? void 0 : n.metric_id) || ""),
        rows: e.rows,
        kind: e.kind,
        currentLabel: e.current_label,
        priorLabel: e.prior_label,
        onSelect: (s) => t.ask(`Why did ${e.metric_label} for ${e.dimension_label} ${s.segment} change in ${e.current_label} vs ${e.prior_label}?`)
      }
    )
  ] });
}
function ap({ data: e }) {
  var t, n;
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsx(
      Xf,
      {
        start: e.start,
        end: e.end,
        steps: e.steps,
        kind: e.kind,
        startLabel: e.start_label,
        endLabel: e.end_label
      }
    ),
    /* @__PURE__ */ l.jsxs("div", { className: `recon ${e.reconciled ? "ok" : "bad"}`, children: [
      e.reconciled ? "✓ Reconciled: start + contributions = end" : "✗ Does not reconcile",
      " · ",
      e.dimension_label,
      " contribution, additive metric"
    ] }),
    ((t = e.insights) == null ? void 0 : t.length) > 0 && /* @__PURE__ */ l.jsxs("div", { className: "insights", children: [
      /* @__PURE__ */ l.jsx("div", { className: "insights-title", children: "Key drivers · Snowflake ML Top Insights" }),
      e.insights.map((s, r) => /* @__PURE__ */ l.jsxs("div", { className: "insight", children: [
        /* @__PURE__ */ l.jsx("span", { children: s.contributor.join(" & ") }),
        /* @__PURE__ */ l.jsxs("b", { className: s.contribution >= 0 ? "up" : "down", children: [
          s.contribution >= 0 ? "+" : "−",
          O(Math.abs(s.contribution), e.kind)
        ] })
      ] }, r))
    ] }),
    e.insights_pending && /* @__PURE__ */ l.jsx("div", { className: "prov", children: "⚙ Snowflake ML Top Insights is analysing drivers…" }),
    !((n = e.insights) != null && n.length) && e.insights_error && /* @__PURE__ */ l.jsxs("details", { children: [
      /* @__PURE__ */ l.jsx("summary", { className: "prov muted", children: "Top Insights unavailable — showing the reconciled bridge (details)" }),
      /* @__PURE__ */ l.jsx("pre", { className: "err-pre", children: e.insights_error })
    ] })
  ] });
}
function wr({ data: e, ctx: t, spec: n }) {
  var i;
  if (!e.rows.length) return /* @__PURE__ */ l.jsx(Dt, { text: "No segment deviates materially from its own history." });
  const s = Qs.test(e.metric || (n == null ? void 0 : n.metric_id) || ""), r = (a) => a === 0 ? "" : a > 0 !== s ? "up" : "down";
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    e.none_flagged && /* @__PURE__ */ l.jsxs("div", { className: "exc-calm", children: [
      "No ",
      ((i = e.dimension_label) == null ? void 0 : i.toLowerCase()) || "segment",
      " is outside its normal range (|z| ≥ 2). Closest movers to watch:"
    ] }),
    /* @__PURE__ */ l.jsx("div", { className: "exc", children: e.rows.map((a) => /* @__PURE__ */ l.jsxs("div", { className: "exc-row", children: [
      /* @__PURE__ */ l.jsx("span", { className: "exc-seg", children: a.segment }),
      /* @__PURE__ */ l.jsx("span", { className: `sev ${a.severity.toLowerCase()}`, children: a.severity }),
      /* @__PURE__ */ l.jsx("span", { className: "nums", children: a.lower != null ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
        O(a.current, e.kind),
        " vs expected ",
        O(a.expected, e.kind),
        " ·",
        " ",
        /* @__PURE__ */ l.jsx("b", { className: r(a.z), children: Kt(a.deviation, 0) }),
        " ",
        /* @__PURE__ */ l.jsxs("span", { className: "muted", children: [
          "(normal range ",
          O(a.lower, e.kind),
          "–",
          O(a.upper, e.kind),
          ")"
        ] })
      ] }) : /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
        O(a.current, e.kind),
        " vs norm ",
        O(a.expected, e.kind),
        " ·",
        " ",
        /* @__PURE__ */ l.jsx("b", { className: r(a.z), children: Kt(a.deviation, 0) }),
        " (z ",
        a.z.toFixed(1),
        ")"
      ] }) }),
      /* @__PURE__ */ l.jsxs("span", { className: "acts", children: [
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => t.ask(`Why is ${e.metric_label} for ${a.segment} ${a.direction} its normal level in the latest period?`), children: "Ask agent" }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => t.decide({
          title: `Investigate ${a.segment} ${e.metric_label.toLowerCase()} (${Kt(a.deviation, 0)} vs norm)`,
          detail: `${a.segment} ${e.metric_label} ${O(a.current, e.kind)} vs norm ${O(a.expected, e.kind)} (z ${a.z.toFixed(1)}).`,
          evidence: { component: n.component_id, ...a }
        }), children: "Log decision" })
      ] })
    ] }, a.segment)) }),
    /* @__PURE__ */ l.jsxs("div", { className: "prov", children: [
      e.ml && /* @__PURE__ */ l.jsx("span", { className: "ml-badge", title: e.provenance || "", children: "Snowflake ML · ANOMALY_DETECTION" }),
      e.insights_pending && /* @__PURE__ */ l.jsx("span", { className: "ml-badge wait", children: "Training Snowflake ML anomaly model…" }),
      e.method
    ] })
  ] });
}
function op({ data: e, ctx: t }) {
  var n;
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsx("div", { className: "table-actions", children: /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", onClick: () => t.decide({}), children: "+ New decision" }) }),
    (n = e.rows) != null && n.length ? /* @__PURE__ */ l.jsxs("table", { className: "table", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", { children: "Decision" }),
        /* @__PURE__ */ l.jsx("th", { children: "Owner" }),
        /* @__PURE__ */ l.jsx("th", { children: "Due" }),
        /* @__PURE__ */ l.jsx("th", { children: "Status" }),
        /* @__PURE__ */ l.jsx("th", { children: "Logged" })
      ] }) }),
      /* @__PURE__ */ l.jsx("tbody", { children: e.rows.map((s) => /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsxs("td", { children: [
          /* @__PURE__ */ l.jsx("b", { children: s.title }),
          /* @__PURE__ */ l.jsx("div", { className: "muted small", children: s.detail })
        ] }),
        /* @__PURE__ */ l.jsx("td", { children: s.owner || "—" }),
        /* @__PURE__ */ l.jsx("td", { children: s.due_date || "—" }),
        /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("select", { value: s.status, onChange: (r) => t.send("decision_status", { decision_id: s.decision_id, status: r.target.value }), children: ["Open", "In progress", "Done"].map((r) => /* @__PURE__ */ l.jsx("option", { children: r }, r)) }) }),
        /* @__PURE__ */ l.jsxs("td", { className: "muted small", children: [
          s.created_by,
          /* @__PURE__ */ l.jsx("br", {}),
          s.created_at
        ] })
      ] }, s.decision_id)) })
    ] }) : /* @__PURE__ */ l.jsx(Dt, { text: "No decisions logged yet. Log one from an exception, an agent answer, or here." })
  ] });
}
function qo({ data: e }) {
  return /* @__PURE__ */ l.jsxs("div", { className: "scroll", children: [
    /* @__PURE__ */ l.jsx("div", { className: "sub", children: e.period_label }),
    /* @__PURE__ */ l.jsxs("table", { className: "table", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsx("tr", { children: e.columns.map((t) => /* @__PURE__ */ l.jsx("th", { children: t.label }, t.id)) }) }),
      /* @__PURE__ */ l.jsx("tbody", { children: e.rows.map((t, n) => /* @__PURE__ */ l.jsx("tr", { children: e.columns.map((s) => /* @__PURE__ */ l.jsx("td", { children: s.type === "dim" ? t[s.id] : O(t[s.id], s.kind) }, s.id)) }, n)) })
    ] })
  ] });
}
function up({ data: e }) {
  return /* @__PURE__ */ l.jsx("div", { className: "multiples", children: e.panels.map((t) => {
    const n = t.points.map((r) => r.value).filter((r) => r != null), s = n.length > 1 ? (n[n.length - 1] - n[0]) / Math.abs(n[0] || 1) : null;
    return /* @__PURE__ */ l.jsxs("div", { className: "multiple", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "multiple-head", children: [
        /* @__PURE__ */ l.jsx("b", { children: t.segment }),
        /* @__PURE__ */ l.jsx("span", { className: `delta ${ad(s)}`, children: Kt(s, 0) })
      ] }),
      /* @__PURE__ */ l.jsx(Jf, { points: t.points, kind: e.kind }),
      /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
        O(n[n.length - 1], e.kind),
        " latest"
      ] })
    ] }, t.segment);
  }) });
}
function Ho({ data: e }) {
  return /* @__PURE__ */ l.jsx(
    dd,
    {
      rows: e.rows,
      cols: e.cols,
      values: e.values,
      kind: e.kind,
      rowLabel: e.row_label,
      colLabel: e.col_label
    }
  );
}
function cp({ data: e }) {
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsxs("div", { className: "sub", children: [
      e.dimension_label,
      " · ",
      e.period_label
    ] }),
    /* @__PURE__ */ l.jsx(_f, { slices: e.slices, kind: e.kind, total: e.total, centerLabel: e.metric_label })
  ] });
}
function dp({ data: e }) {
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsxs("div", { className: "sub", children: [
      e.dimension_label,
      " · ",
      e.period_label,
      e.n80 ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
        " · ",
        /* @__PURE__ */ l.jsxs("b", { children: [
          e.n80,
          " of ",
          e.total_count
        ] }),
        " make up 80%"
      ] }) : null
    ] }),
    /* @__PURE__ */ l.jsx($f, { rows: e.rows, kind: e.kind })
  ] });
}
function hp({ data: e, ctx: t }) {
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsxs("div", { className: "sub", children: [
      "Each point = one ",
      e.dimension_label,
      " · ",
      e.period_label
    ] }),
    /* @__PURE__ */ l.jsx(tp, { points: e.points, xKind: e.x_kind, yKind: e.y_kind, xLabel: e.x_label, yLabel: e.y_label })
  ] });
}
function fp({ data: e, spec: t }) {
  return /* @__PURE__ */ l.jsx(np, { rows: e.rows, kind: e.kind, labels: e.labels, inverse: Qs.test((t == null ? void 0 : t.metric_id) || "") });
}
const rt = (e, t) => e == null ? "—" : t === "percent" ? `${e > 0 ? "+" : ""}${(e * 100).toFixed(1)} pt` : Kt(e), vn = { good: "up", ok: "flat", warn: "warn", bad: "down" }, gn = (e) => e == null || Math.abs(e) < 5e-4 ? "▬" : e > 0 ? "▲" : "▼", kr = (e) => e.value == null || e.target == null ? null : e.value - e.target, Yo = (e, t) => e == null ? "—" : t === "percent" ? `${e > 0 ? "+" : ""}${(e * 100).toFixed(1)} pt` : `${e > 0 ? "+" : ""}${O(e, t)}`, hd = [["bullet", "Bullet bars (actual vs target)"], ["variance", "Variance with arrows"], ["table", "Variance table"]];
function pp({ data: e, ctx: t, spec: n }) {
  const s = (n == null ? void 0 : n.display) || "bullet", q = (n == null ? void 0 : n.show_trend) === !0;
  return s === "table" ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsxs("table", { className: "table kplan-table", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", { children: "Metric" }),
        /* @__PURE__ */ l.jsx("th", { className: "num", children: e.period_label }),
        /* @__PURE__ */ l.jsx("th", { className: "num", children: "Target" }),
        /* @__PURE__ */ l.jsx("th", { className: "num", children: "Variance" }),
        /* @__PURE__ */ l.jsx("th", { className: "num", children: "Variance %" }),
        /* @__PURE__ */ l.jsx("th", { className: "num", children: e.month_label })
      ] }) }),
      /* @__PURE__ */ l.jsx("tbody", { children: e.items.map((r) => {
        var i;
        return /* @__PURE__ */ l.jsxs("tr", { children: [
          /* @__PURE__ */ l.jsx("td", { title: ((i = t == null ? void 0 : t.defs) == null ? void 0 : i[r.metric]) || "", children: r.label }),
          /* @__PURE__ */ l.jsx("td", { className: "num", children: /* @__PURE__ */ l.jsx("b", { children: O(r.value, r.kind) }) }),
          /* @__PURE__ */ l.jsxs("td", { className: "num", children: [
            O(r.target, r.kind),
            " ",
            /* @__PURE__ */ l.jsx("span", { className: "muted small", children: r.target_label === "plan" ? "plan" : "LY" })
          ] }),
          /* @__PURE__ */ l.jsxs("td", { className: `num delta ${vn[r.status]}`, children: [
            gn(kr(r)),
            " ",
            Yo(kr(r), r.kind)
          ] }),
          /* @__PURE__ */ l.jsx("td", { className: `num delta ${vn[r.status]}`, children: r.kind === "percent" ? "" : rt(r.delta, r.kind) }),
          /* @__PURE__ */ l.jsx("td", { className: "num", children: O(r.month, r.kind) })
        ] }, r.metric);
      }) })
    ] }),
    /* @__PURE__ */ l.jsx("div", { className: "kpi-foot", children: "Target = plan where the metric has one, otherwise last year · ▲▼ colour already accounts for metrics where lower is better" })
  ] }) : /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsx("div", { className: "kplan", children: e.items.map((r) => {
      var i;
      return /* @__PURE__ */ l.jsxs("div", { className: `kplan-card st-${r.status}`, children: [
        /* @__PURE__ */ l.jsx("div", { className: "kpi-label", title: ((i = t == null ? void 0 : t.defs) == null ? void 0 : i[r.metric]) || "", children: r.label }),
        s === "variance" ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
          /* @__PURE__ */ l.jsx("div", { className: "kplan-row", children: /* @__PURE__ */ l.jsx("span", { className: "kpi-value", children: O(r.value, r.kind) }) }),
          /* @__PURE__ */ l.jsxs("div", { className: `kplan-var ${vn[r.status]}`, children: [
            /* @__PURE__ */ l.jsx("span", { className: "arr", children: gn(r.delta) }),
            /* @__PURE__ */ l.jsx("b", { children: rt(r.delta, r.kind) }),
            r.kind !== "percent" && /* @__PURE__ */ l.jsx("span", { children: Yo(kr(r), r.kind) }),
            /* @__PURE__ */ l.jsxs("em", { children: [
              "vs ",
              r.target_label,
              " (",
              O(r.target, r.kind),
              ")"
            ] })
          ] })
        ] }) : /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
          /* @__PURE__ */ l.jsxs("div", { className: "kplan-row", children: [
            /* @__PURE__ */ l.jsx("span", { className: "kpi-value", children: O(r.value, r.kind) }),
            /* @__PURE__ */ l.jsxs("span", { className: `delta ${vn[r.status]}`, children: [
              gn(r.delta),
              " ",
              rt(r.delta, r.kind)
            ] }),
            /* @__PURE__ */ l.jsxs("em", { children: [
              "vs ",
              r.target_label
            ] })
          ] }),
          /* @__PURE__ */ l.jsx(sp, { value: r.value, target: r.target, good: r.status === "bad" ? !1 : void 0 })
        ] }),
        q && /* @__PURE__ */ l.jsx(Qf, { values: r.spark, labels: e.spark_labels, kind: r.kind }),
        /* @__PURE__ */ l.jsxs("div", { className: "kplan-foot", children: [
          s !== "variance" && /* @__PURE__ */ l.jsxs("span", { children: [
            r.target_label === "plan" ? "Plan" : "Last year",
            " ",
            O(r.target, r.kind)
          ] }),
          r.target_label === "plan" && r.py != null && /* @__PURE__ */ l.jsxs("span", { children: [
            "LY ",
            gn(r.delta_py),
            " ",
            rt(r.delta_py, r.kind)
          ] }),
          r.month != null && /* @__PURE__ */ l.jsxs("span", { children: [
            e.month_label,
            ": ",
            O(r.month, r.kind),
            r.month_delta != null ? ` (${rt(r.month_delta, r.kind)})` : ""
          ] })
        ] })
      ] }, r.metric);
    }) }),
    /* @__PURE__ */ l.jsxs("div", { className: "kpi-foot", children: [
      e.period_label,
      " · ",
      s === "bullet" ? `bar = actual, tick = ${e.has_plan ? "plan (last year where a metric has no plan)" : "last year"} · ` : "",
      "colour and ▲▼ already account for metrics where lower is better"
    ] })
  ] });
}
function Qo({ data: e }) {
  var s, r;
  const t = (s = e.series) == null ? void 0 : s.some((i) => i.style === "forecast"), n = e.mode === "hour" ? `now · ${((r = e.labels) == null ? void 0 : r[e.now_index]) || ""}` : e.mode === "ytd" ? "latest month" : "today";
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    e.mode === "hour" && e.pace != null && /* @__PURE__ */ l.jsxs("div", { className: "pace-head", children: [
      /* @__PURE__ */ l.jsx("b", { className: e.pace >= 0 ? "up" : "down", children: Kt(e.pace) }),
      " vs the same time last week",
      e.projected != null && /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
        " · on this pace the day closes near ",
        /* @__PURE__ */ l.jsx("b", { children: O(e.projected, e.kind) })
      ] })
    ] }),
    /* @__PURE__ */ l.jsx(
      lp,
      {
        labels: e.labels,
        series: e.series,
        band: e.band,
        kind: e.kind,
        nowIndex: e.now_index,
        nowLabel: n
      }
    ),
    /* @__PURE__ */ l.jsxs("div", { className: "prov", children: [
      t && /* @__PURE__ */ l.jsx("span", { className: "ml-badge", title: e.provenance || "", children: "Snowflake ML · FORECAST" }),
      e.insights_pending && /* @__PURE__ */ l.jsx("span", { className: "ml-badge wait", children: "Training Snowflake ML forecast to year end…" }),
      e.caption
    ] })
  ] });
}
function mp({ data: e, ctx: t }) {
  return /* @__PURE__ */ l.jsx(l.Fragment, { children: /* @__PURE__ */ l.jsx("div", { className: "status-row", children: e.items.map((n) => {
    var s;
    return /* @__PURE__ */ l.jsxs("div", { className: `status-card st-${n.status}`, children: [
      /* @__PURE__ */ l.jsxs("div", { className: "kpi-label", title: ((s = t == null ? void 0 : t.defs) == null ? void 0 : s[n.metric]) || "", children: [
        n.label,
        n.timed ? "" : " (today)"
      ] }),
      /* @__PURE__ */ l.jsx("div", { className: "status-val", children: O(n.current, n.kind) }),
      /* @__PURE__ */ l.jsxs("div", { className: "kpi-delta", children: [
        /* @__PURE__ */ l.jsxs("span", { className: `delta ${vn[n.status]}`, children: [
          gn(n.delta),
          " ",
          rt(n.delta, n.kind)
        ] }),
        /* @__PURE__ */ l.jsxs("em", { children: [
          e.compare_label,
          n.base != null ? ` (${O(n.base, n.kind)})` : ""
        ] })
      ] }),
      n.avg != null && /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
        "4-week normal ",
        O(n.avg, n.kind)
      ] })
    ] }, n.metric);
  }) }) });
}
function vp({ data: e }) {
  return /* @__PURE__ */ l.jsx(dd, { rows: e.rows, cols: e.cols, values: e.values, kind: e.kind, rowLabel: e.row_label, colLabel: e.col_label });
}
function gp({ data: e, ctx: t, spec: n }) {
  var s, r;
  return (s = e.rows) != null && s.length ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    e.none_flagged && /* @__PURE__ */ l.jsx("div", { className: "exc-calm", children: "Nothing is outside its normal range today. Closest movers to watch:" }),
    /* @__PURE__ */ l.jsxs("table", { className: "table worklist", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", {}),
        /* @__PURE__ */ l.jsx("th", { children: "What" }),
        /* @__PURE__ */ l.jsx("th", { children: "Where" }),
        /* @__PURE__ */ l.jsx("th", { className: "num", children: "Today" }),
        /* @__PURE__ */ l.jsxs("th", { className: "num", children: [
          "Normal ",
          (r = e.today_label) == null ? void 0 : r.slice(0, 3)
        ] }),
        /* @__PURE__ */ l.jsx("th", { className: "num", children: "Change" }),
        /* @__PURE__ */ l.jsx("th", {})
      ] }) }),
      /* @__PURE__ */ l.jsx("tbody", { children: e.rows.map((i, a) => /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("span", { className: `sevdot ${i.severity.toLowerCase()}`, title: `${i.severity} · z ${i.z.toFixed(1)}` }) }),
        /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("b", { children: i.metric_label }) }),
        /* @__PURE__ */ l.jsxs("td", { children: [
          i.segment,
          " ",
          /* @__PURE__ */ l.jsx("span", { className: "muted small", children: i.dimension_label })
        ] }),
        /* @__PURE__ */ l.jsx("td", { className: "num", children: O(i.current, i.kind) }),
        /* @__PURE__ */ l.jsx("td", { className: "num muted", children: O(i.normal, i.kind) }),
        /* @__PURE__ */ l.jsx("td", { className: "num", children: /* @__PURE__ */ l.jsx("b", { className: "down", children: rt(i.deviation, i.kind) }) }),
        /* @__PURE__ */ l.jsxs("td", { className: "acts", children: [
          /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => {
            var u;
            return t.ask(`Why is ${i.metric_label} for ${i.segment} (${i.dimension_label}) ${i.deviation > 0 ? "above" : "below"} a normal ${(u = e.today_label) == null ? void 0 : u.slice(0, 3)} today, and what should we do now?`);
          }, children: "Ask agent" }),
          /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => t.decide({
            title: `Act on ${i.segment} ${i.metric_label.toLowerCase()} today (${rt(i.deviation, i.kind)})`,
            detail: `${i.segment} (${i.dimension_label}) ${i.metric_label} ${O(i.current, i.kind)} today vs normal ${O(i.normal, i.kind)}.`,
            evidence: { component: n.component_id, ...i }
          }), children: "Log decision" })
        ] })
      ] }, a)) })
    ] }),
    /* @__PURE__ */ l.jsx("div", { className: "prov", children: e.method })
  ] }) : /* @__PURE__ */ l.jsx(Dt, { text: "Nothing is off today compared with a normal day." });
}
function xp({ data: e, ctx: t }) {
  const n = e.columns, s = (r, i, a) => /* @__PURE__ */ l.jsxs("td", { className: `sc-cell st-${r.status}`, title: r.base != null ? `${i.compare === "plan" ? "Plan" : i.compare}: ${O(r.base, i.kind)}` : "", children: [
    /* @__PURE__ */ l.jsx("span", { className: "sc-val", children: O(r.value, i.kind) }),
    /* @__PURE__ */ l.jsx("span", { className: `sc-d ${vn[r.status]}`, children: rt(r.delta, i.kind) })
  ] }, a);
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsxs("table", { className: "table scorecard", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", { children: e.dimension_label }),
        n.map((r) => /* @__PURE__ */ l.jsxs("th", { className: "num", children: [
          r.label,
          /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
            "vs ",
            r.compare
          ] })
        ] }, r.metric))
      ] }) }),
      /* @__PURE__ */ l.jsxs("tbody", { children: [
        e.rows.map((r) => /* @__PURE__ */ l.jsxs(
          "tr",
          {
            className: "sc-row",
            title: `Filter the dashboard to ${r.segment}`,
            onClick: () => t.drill && t.drill(e.dimension, r.segment),
            children: [
              /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("b", { children: r.segment }) }),
              r.cells.map((i, a) => s(i, n[a], a))
            ]
          },
          r.segment
        )),
        /* @__PURE__ */ l.jsxs("tr", { className: "sc-total", children: [
          /* @__PURE__ */ l.jsx("td", { children: "Total" }),
          e.total.cells.map((r, i) => s(r, n[i], i))
        ] })
      ] })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "kpi-foot", children: [
      e.period_label,
      " · green ahead, amber slightly behind, red ≥10% (or ≥2 pt) behind · click a row to drill into it"
    ] })
  ] });
}
/* ---- Chart drop A (15 Oct): bars + line, treemap, progress gauge, P&L table. Colours come from theme tokens. ---- */
function aaInk(c) {
  const m = /#([0-9a-f]{6})/i.exec(c || "");
  if (!m) return "#fff";
  const n = parseInt(m[1], 16), r = (n >> 16) / 255, g = (n >> 8 & 255) / 255, b = (n & 255) / 255;
  const L = (v) => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  return 0.2126 * L(r) + 0.7152 * L(g) + 0.0722 * L(b) > 0.42 ? "#1d1a17" : "#ffffff";
}
function useAaPalette(ref) {
  const [p, setP] = P.useState(null);
  P.useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const cs = getComputedStyle(el), out = {};
    [...Hl, Vo].forEach((v) => {
      const m = /var\((--[\w-]+),\s*([^)]+)\)/.exec(v);
      out[v] = m ? (cs.getPropertyValue(m[1]).trim() || m[2].trim()) : v;
    });
    const key = JSON.stringify(out);
    setP((prev) => prev && JSON.stringify(prev) === key ? prev : out);
  });
  return p;
}
function CmbX({ data: e }) {
  const [s, r] = tn(), [hv, setHv] = P.useState(null), [u, o, d] = Ke(s);
  const pts = e.points || [];
  if (!pts.length) return /* @__PURE__ */ l.jsx("div", { ref: s, children: /* @__PURE__ */ l.jsx(Dt, { text: "No data." }) });
  const n = 280, m = { l: 58, r: 62, t: 24, b: 34 }, W = Math.max(60, r - m.l - m.r), H = n - m.t - m.b, k = W / pts.length;
  const bv = pts.map((p) => p.bar).filter((v) => v != null), lv = pts.map((p) => p.line).filter((v) => v != null);
  const yb = zn(Math.min(0, ...bv), Math.max(1e-12, ...bv), 4), b0 = yb[0], b1 = yb[yb.length - 1];
  const lz = lv.length ? od(lv) : { lo: 0, hi: 1 }, yl = zn(lz.lo, lz.hi, 4), l0 = yl[0], l1 = yl[yl.length - 1];
  const X = (i) => m.l + i * k + k / 2, YB = (v) => m.t + H - (v - b0) / (b1 - b0 || 1) * H, YL = (v) => m.t + H - (v - l0) / (l1 - l0 || 1) * H;
  const path = pts.map((p, i) => p.line == null ? null : [X(i), YL(p.line)]).filter(Boolean).map(([x, y], i) => `${i ? "L" : "M"}${x},${y}`).join(" ");
  const step = Math.max(1, Math.ceil(pts.length / Math.max(3, Math.floor(W / 70)))), last = pts.length - 1, lastLine = [...pts].reverse().find((p) => p.line != null);
  const chg = (a, b, kd) => a == null || b == null ? null : kd === "percent" ? a - b : b ? (a - b) / Math.abs(b) : null;
  return /* @__PURE__ */ l.jsxs("div", { className: "chart cmb", ref: s, children: [
    /* @__PURE__ */ l.jsxs("svg", { viewBox: `0 0 ${r} ${n}`, role: "img", "aria-label": `${e.bar_label} bars and ${e.line_label} line`, onMouseLeave: () => { setHv(null), d(); }, children: [
      yb.map((v) => /* @__PURE__ */ l.jsxs("g", { children: [
        /* @__PURE__ */ l.jsx("line", { x1: m.l, x2: r - m.r, y1: YB(v), y2: YB(v), className: "grid" }),
        /* @__PURE__ */ l.jsx("text", { x: m.l - 8, y: YB(v) + 4, className: "tick", textAnchor: "end", children: O(v, e.bar_kind) })
      ] }, "b" + v)),
      yl.map((v) => /* @__PURE__ */ l.jsx("text", { x: r - m.r + 8, y: YL(v) + 4, className: "tick cmb-r", children: O(v, e.line_kind) }, "l" + v)),
      pts.map((p, i) => /* @__PURE__ */ l.jsxs("g", { onMouseMove: (ev) => {
        setHv(i), o(ev, /* @__PURE__ */ l.jsx(Ie, { title: p.label, rows: [
          [e.bar_label, O(p.bar, e.bar_kind)],
          i > 0 && chg(p.bar, pts[i - 1].bar, e.bar_kind) != null ? ["  vs " + pts[i - 1].label, rt(chg(p.bar, pts[i - 1].bar, e.bar_kind), e.bar_kind)] : null,
          [e.line_label, O(p.line, e.line_kind)],
          i > 0 && chg(p.line, pts[i - 1].line, e.line_kind) != null ? ["  vs " + pts[i - 1].label, rt(chg(p.line, pts[i - 1].line, e.line_kind), e.line_kind)] : null
        ] }));
      }, children: [
        /* @__PURE__ */ l.jsx("rect", { x: m.l + i * k, y: m.t, width: k, height: H, className: `cmb-hit ${hv === i ? "on" : ""}` }),
        p.bar != null && /* @__PURE__ */ l.jsx("rect", { x: X(i) - k * 0.31, width: k * 0.62, y: Math.min(YB(p.bar), YB(0)), height: Math.max(1, Math.abs(YB(0) - YB(p.bar))), rx: 3, className: `cmb-bar ${i === last ? "now" : ""} ${hv === i ? "hl" : ""}` }),
        i % step === 0 || i === last ? /* @__PURE__ */ l.jsx("text", { x: X(i), y: n - 12, className: `tick ${i === last ? "strong" : ""}`, textAnchor: "middle", children: String(p.label).replace(/^Wk of /, "").slice(0, 12) }) : null
      ] }, i)),
      /* @__PURE__ */ l.jsx("path", { d: path, className: "cmb-line" }),
      pts.map((p, i) => p.line == null ? null : /* @__PURE__ */ l.jsx("circle", { cx: X(i), cy: YL(p.line), r: i === last || hv === i ? 4.5 : 2.5, className: "cmb-dot" }, "d" + i)),
      (() => {
        const bt = pts[last].bar != null ? Math.min(YB(pts[last].bar), YB(0)) - 7 : null, li = pts.lastIndexOf(lastLine || {}), ly0 = lastLine ? YL(lastLine.line) - 10 : null;
        const ly = ly0 != null && bt != null && li === last && Math.abs(ly0 - bt) < 15 ? (ly0 < bt ? Math.min(ly0, bt - 15) : YL(lastLine.line) + 18) : ly0;
        return /* @__PURE__ */ l.jsxs("g", { pointerEvents: "none", children: [
          bt != null && /* @__PURE__ */ l.jsx("text", { x: X(last), y: Math.max(m.t - 6, bt), className: "cmb-lbl", textAnchor: "middle", children: O(pts[last].bar, e.bar_kind) }),
          lastLine && /* @__PURE__ */ l.jsx("text", { x: X(li) - 9, y: Math.max(m.t - 6, ly), className: "cmb-lbl line halo", textAnchor: "end", children: O(lastLine.line, e.line_kind) })
        ] });
      })()
    ] }),
    u,
    /* @__PURE__ */ l.jsxs("div", { className: "legend", children: [
      /* @__PURE__ */ l.jsxs("span", { children: [/* @__PURE__ */ l.jsx("i", { className: "sw cmb-sw-bar" }), e.bar_label, " (bars, left axis)"] }),
      /* @__PURE__ */ l.jsxs("span", { children: [/* @__PURE__ */ l.jsx("i", { className: "sw cmb-sw-line" }), e.line_label, " (line, right axis)"] })
    ] })
  ] });
}
function aaSquarify(items, x0, y0, w0, h0) {
  const out = [], total = items.reduce((a, b) => a + b.v, 0);
  if (!total || w0 <= 0 || h0 <= 0) return out;
  const sc = w0 * h0 / total;
  let rx = x0, ry = y0, rw = w0, rh = h0, row = [];
  const rest = items.slice();
  const worst = (rw2, side) => {
    const s = rw2.reduce((a, b) => a + b.v * sc, 0), mx = Math.max(...rw2.map((q) => q.v * sc)), mn = Math.min(...rw2.map((q) => q.v * sc));
    return Math.max(side * side * mx / (s * s), s * s / (side * side * mn));
  };
  const lay = () => {
    const s = row.reduce((a, b) => a + b.v * sc, 0);
    if (rw >= rh) {
      const cw = s / rh;
      let cy = ry;
      row.forEach((q) => { const ch = q.v * sc / cw; out.push({ ...q, x: rx, y: cy, w: cw, h: ch }); cy += ch; });
      rx += cw, rw -= cw;
    } else {
      const ch = s / rw;
      let cx = rx;
      row.forEach((q) => { const cw = q.v * sc / ch; out.push({ ...q, x: cx, y: ry, w: cw, h: ch }); cx += cw; });
      ry += ch, rh -= ch;
    }
    row = [];
  };
  while (rest.length) {
    const side = Math.min(rw, rh), c = rest[0];
    if (!row.length || worst([...row, c], side) <= worst(row, side)) row.push(c), rest.shift();
    else lay();
  }
  row.length && lay();
  return out;
}
function TmX({ data: e }) {
  const [s, r] = tn(), [u, o, d] = Ke(s), pal = useAaPalette(s), [hv, setHv] = P.useState(null);
  const gs = (e.groups || []).filter((g) => g.value > 0);
  if (!gs.length) return /* @__PURE__ */ l.jsx("div", { ref: s, children: /* @__PURE__ */ l.jsx(Dt, { text: "No positive values to draw." }) });
  const n = 300, nested = gs.some((g) => (g.children || []).length), colorOf = (g, i) => g.other ? Vo : Hl[i % Hl.length];
  const boxes = aaSquarify(gs.map((g, i) => ({ v: g.value, g, i })), 0, 0, r, n);
  const pct = (v) => v == null ? "" : `${(v * 100).toFixed(v < 0.1 ? 1 : 0)}%`;
  const tip = (ev, title, it) => o(ev, /* @__PURE__ */ l.jsx(Ie, { title, rows: [
    ["Value", O(it.value, e.kind)],
    ["Share of total", pct(it.share)],
    it.change != null ? ["vs " + e.prior_label, rt(it.change, "number"), it.change > 0 ? "up" : "down"] : ["vs " + e.prior_label, "no prior value"]
  ] }));
  const label = (q, it, fill, big) => {
    if (q.w < 54 || q.h < 30) return null;
    const ink = aaInk(pal && pal[fill]), max = Math.max(3, Math.floor((q.w - 12) / (big ? 7.6 : 6.6)));
    const nm = String(it.label), txt = nm.length > max ? nm.slice(0, max - 1) + "…" : nm;
    return /* @__PURE__ */ l.jsxs("g", { className: "tm-txt", style: { fill: ink }, pointerEvents: "none", children: [
      /* @__PURE__ */ l.jsx("text", { x: q.x + 8, y: q.y + 18, className: big ? "tm-name big" : "tm-name", children: txt }),
      q.h >= 46 && /* @__PURE__ */ l.jsxs("text", { x: q.x + 8, y: q.y + 35, className: "tm-val", children: [O(it.value, e.kind), q.w >= 110 && it.change != null ? `  ·  ${it.change > 0 ? "▲" : "▼"}${Math.abs(it.change * 100).toFixed(0)}%` : ""] }),
      q.h >= 62 && q.w >= 80 && /* @__PURE__ */ l.jsxs("text", { x: q.x + 8, y: q.y + 50, className: "tm-share", children: [pct(it.share), " of total"] })
    ] });
  };
  return /* @__PURE__ */ l.jsxs("div", { className: "chart tm", ref: s, children: [
    /* @__PURE__ */ l.jsx("svg", { viewBox: `0 0 ${r} ${n}`, role: "img", "aria-label": `${e.metric_label} treemap by ${e.dimension_label}`, onMouseLeave: () => { setHv(null), d(); }, children: boxes.map((b) => {
      const fill = colorOf(b.g, b.i), kids = (b.g.children || []).filter((c) => c.value > 0), head = nested && kids.length && b.h > 44 && b.w > 70 ? 22 : 0;
      const inner = kids.length && nested ? aaSquarify(kids.map((c, j) => ({ v: c.value, c, j })), b.x + 2, b.y + head + 2, b.w - 4, b.h - head - 4) : [];
      return /* @__PURE__ */ l.jsxs("g", { children: [
        /* @__PURE__ */ l.jsx("rect", { x: b.x, y: b.y, width: Math.max(0, b.w), height: Math.max(0, b.h), className: `tm-box ${hv === "g" + b.i ? "hl" : ""}`, style: { fill }, onMouseMove: (ev) => { setHv("g" + b.i), tip(ev, b.g.label, b.g); } }),
        inner.length ? inner.map((q) => /* @__PURE__ */ l.jsxs("g", { children: [
          /* @__PURE__ */ l.jsx("rect", { x: q.x, y: q.y, width: Math.max(0, q.w), height: Math.max(0, q.h), className: `tm-leaf ${hv === b.i + ":" + q.j ? "hl" : ""}`, style: { fill, fillOpacity: Math.max(0.42, 1 - q.j * 0.09) }, onMouseMove: (ev) => { setHv(b.i + ":" + q.j), tip(ev, `${b.g.label} · ${q.c.label}`, q.c); } }),
          label(q, q.c, fill, !1)
        ] }, q.j)) : null,
        head ? /* @__PURE__ */ l.jsx("text", { x: b.x + 8, y: b.y + 16, className: "tm-name big", pointerEvents: "none", style: { fill: aaInk(pal && pal[fill]) }, children: `${b.g.label} · ${O(b.g.value, e.kind)} · ${pct(b.g.share)}` }) : null,
        !inner.length ? label(b, b.g, fill, !0) : null
      ] }, b.i);
    }) }),
    u,
    /* @__PURE__ */ l.jsxs("div", { className: "kpi-foot", children: [
      "Box size = ", e.metric_label, " in ", e.period_label, e.dimension2_label ? ` · ${e.dimension_label} › ${e.dimension2_label}` : ` · by ${e.dimension_label}`,
      " · ▲▼ vs ", e.prior_label,
      e.excluded_count ? ` · ${e.excluded_count} zero or negative value(s) not drawn (${O(e.excluded, e.kind)})` : ""
    ] })
  ] });
}
function GgX({ data: e }) {
  if (e.progress == null) return /* @__PURE__ */ l.jsx(Dt, { text: "No target to measure progress against." });
  const cx = 160, cy = 150, R = 118, pt = (f) => [cx - R * Math.cos(Math.PI * f), cy - R * Math.sin(Math.PI * f)];
  const arc = (f) => { const [x, y] = pt(Math.max(0.0001, Math.min(1, f))); return `M${cx - R},${cy} A${R},${R} 0 0 1 ${x},${y}`; };
  const good = e.pace == null ? null : e.pace >= 1 !== !!e.inverse, ex = e.expected_share != null ? pt(Math.min(1, e.expected_share)) : null;
  const exI = e.expected_share != null ? [cx - (R - 20) * Math.cos(Math.PI * Math.min(1, e.expected_share)), cy - (R - 20) * Math.sin(Math.PI * Math.min(1, e.expected_share))] : null;
  const exO = e.expected_share != null ? [cx - (R + 20) * Math.cos(Math.PI * Math.min(1, e.expected_share)), cy - (R + 20) * Math.sin(Math.PI * Math.min(1, e.expected_share))] : null;
  const tl = e.target_label === "plan" ? "plan" : "last year", full = e.target_label === "plan" ? "full-year plan" : "last year's full year";
  return /* @__PURE__ */ l.jsxs("div", { className: "gg", children: [
    /* @__PURE__ */ l.jsxs("svg", { viewBox: "0 0 320 178", role: "img", "aria-label": `${e.metric_label} ${(e.progress * 100).toFixed(0)}% of ${full}`, children: [
      /* @__PURE__ */ l.jsx("path", { d: arc(1), className: "gg-track" }),
      /* @__PURE__ */ l.jsx("path", { d: arc(e.progress), className: `gg-fill ${good === !1 ? "behind" : ""}` }),
      ex && /* @__PURE__ */ l.jsxs("g", { className: "gg-mark", children: [
        /* @__PURE__ */ l.jsx("line", { x1: exI[0], y1: exI[1], x2: exO[0], y2: exO[1] }),
        /* @__PURE__ */ l.jsx("title", { children: `${tl === "plan" ? "Plan" : "Last year"} by this point: ${O(e.expected, e.kind)} (${(e.expected_share * 100).toFixed(0)}% of the year's ${tl})` })
      ] }),
      /* @__PURE__ */ l.jsx("text", { x: cx, y: cy - 30, textAnchor: "middle", className: "gg-big", children: `${(e.progress * 100).toFixed(0)}%` }),
      /* @__PURE__ */ l.jsx("text", { x: cx, y: cy - 8, textAnchor: "middle", className: "gg-sub", children: `of ${full} · ${O(e.target, e.kind)}` }),
      /* @__PURE__ */ l.jsx("text", { x: cx - R, y: cy + 20, textAnchor: "middle", className: "tick", children: "0" }),
      /* @__PURE__ */ l.jsx("text", { x: cx + R, y: cy + 20, textAnchor: "middle", className: "tick", children: O(e.target, e.kind) })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "gg-stats", children: [
      /* @__PURE__ */ l.jsxs("div", { children: [/* @__PURE__ */ l.jsx("span", { children: "Year to date" }), /* @__PURE__ */ l.jsx("b", { children: O(e.actual, e.kind) }), /* @__PURE__ */ l.jsx("em", { children: e.period_label })] }),
      /* @__PURE__ */ l.jsxs("div", { children: [/* @__PURE__ */ l.jsx("span", { children: `vs ${tl} by now` }), /* @__PURE__ */ l.jsx("b", { className: good == null ? "" : good ? "up" : "down", children: e.pace == null ? "—" : `${e.pace >= 1 ? "▲" : "▼"} ${(Math.abs(e.pace - 1) * 100).toFixed(1)}%` }), /* @__PURE__ */ l.jsx("em", { children: e.expected == null ? "" : `${tl} by now ${O(e.expected, e.kind)}` })] }),
      /* @__PURE__ */ l.jsxs("div", { children: [/* @__PURE__ */ l.jsx("span", { children: "At this pace" }), /* @__PURE__ */ l.jsx("b", { children: O(e.projected, e.kind) }), /* @__PURE__ */ l.jsx("em", { children: e.months_left ? `${e.months_left} month${e.months_left === 1 ? "" : "s"} left` : `${e.days_left} day${e.days_left === 1 ? "" : "s"} left` })] })
    ] }),
    /* @__PURE__ */ l.jsx("div", { className: "kpi-foot", children: `Tick = where ${tl === "plan" ? "the plan" : "last year"} was by this point · projection = ${full} × pace so far` })
  ] });
}
function PnX({ data: e }) {
  const cols = e.columns || [], rows = e.rows || [];
  if (!rows.length) return /* @__PURE__ */ l.jsx(Dt, { text: "No data." });
  const tint = (c, kind) => {
    if (!c || c.good == null || c.change == null) return {};
    const mag = Math.min(1, Math.abs(c.change) * (kind === "percent" ? 12 : 2.2)), pc = Math.round(7 + mag * 23);
    return { background: `color-mix(in srgb, var(${c.good ? "--ok" : "--bad"}) ${pc}%, transparent)` };
  };
  const cell = (c, r, cls, key) => /* @__PURE__ */ l.jsxs("td", { className: `num ${cls || ""}`, style: tint(c, r.kind), title: c.base == null ? "" : `${e.base_label}: ${O(c.base, r.kind)}`, children: [
    /* @__PURE__ */ l.jsx("div", { className: "pn-v", children: O(c.value, r.kind) }),
    /* @__PURE__ */ l.jsx("div", { className: `pn-d ${c.good == null ? "" : c.good ? "up" : "down"}`, children: c.change == null ? "—" : `${gn(r.inverse ? -c.change : c.change) === "▬" ? "" : c.change > 0 ? "▲ " : "▼ "}${rt(c.change, r.kind)}` })
  ] }, key);
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsx("div", { className: "pn-wrap", children: /* @__PURE__ */ l.jsxs("table", { className: "table pnl", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", { children: e.period_label }),
        cols.map((c) => /* @__PURE__ */ l.jsx("th", { className: "num", children: c }, c)),
        /* @__PURE__ */ l.jsx("th", { className: "num pn-tot", children: "Total" })
      ] }) }),
      /* @__PURE__ */ l.jsx("tbody", { children: rows.map((r) => /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", { scope: "row", className: "pn-m", children: r.label }),
        r.cells.map((c, i) => cell(c, r, "", i)),
        cell(r.total, r, "pn-tot", "t")
      ] }, r.metric)) })
    ] }) }),
    /* @__PURE__ */ l.jsxs("div", { className: "kpi-foot", children: [
      "Each cell vs ", e.base_label, " · % change, or points for rates · shading = better / worse (accounts for metrics where lower is better)",
      e.truncated ? ` · largest ${cols.length} ${e.dimension_label.toLowerCase()} values shown; Total covers all` : ""
    ] })
  ] });
}
/* ---- Company themes (15 Oct): theme variables on the dashboard + the Company theme panel ---- */
function ThemeVars({ theme: t }) {
  const ref = P.useRef(null);
  P.useLayoutEffect(() => {
    const el = ref.current, main = el && el.closest(".main");
    if (!main) return;
    const vars = t && t.kind === "custom" ? t.vars || {} : {}, keys = ["--bg", "--card", "--ink", "--line", "--muted"];
    keys.forEach((k) => vars[k] ? main.style.setProperty("--t" + k.slice(1), vars[k]) : main.style.removeProperty("--t" + k.slice(1)));
    return () => keys.forEach((k) => main.style.removeProperty("--t" + k.slice(1)));
  }, [t && t.id, t && JSON.stringify(t.vars || {})]);
  return /* @__PURE__ */ l.jsx("span", { ref, hidden: !0 });
}
const THM_ROLES = [["primary", "Primary brand colour", !0], ["accent", "Accent / secondary"], ["background", "Page background"], ["surface", "Cards"], ["text", "Text"], ["positive", "Positive (good)"], ["negative", "Negative (bad)"], ["warning", "Warning"]];
const THM_ICON = { pass: "✓", fixed: "↺", fail: "!" };
function ThmSw({ tokens: k = {}, big: b }) {
  const cs = [k.primary, k.c1, k.c2, k.c3, k.c4, k.c5, k.c6].filter((c, i, z) => c && z.indexOf(c) === i);
  return /* @__PURE__ */ l.jsxs("span", { className: `thm-sw ${b ? "big" : ""}`, style: { background: k.bg || "#f5f8fc", borderColor: k.line || "#e3e9f2" }, children: [
    /* @__PURE__ */ l.jsx("i", { style: { background: k.card || "#fff", color: k.ink || "#0b2440" }, children: "Aa" }),
    cs.map((c, i) => /* @__PURE__ */ l.jsx("b", { style: { background: c } }, i))
  ] });
}
const THM_BUILTIN_SW = {
  classic: { bg: "#f5f8fc", card: "#ffffff", ink: "#0b2440", line: "#e3e9f2", primary: "#11567f", c1: "#11629E", c2: "#29B5E8", c3: "#E8830C", c4: "#11A39A", c5: "#7D44CF", c6: "#D45B90" },
  editorial: { bg: "#f3eee6", card: "#fffcf7", ink: "#2a2420", line: "#e6ddd0", primary: "#2a2420", c1: "#3a2f2a", c2: "#c9a882", c3: "#b5653f", c4: "#8fa98a", c5: "#6f7d91", c6: "#d8c4a2" },
  command: { bg: "#14100e", card: "#1d1815", ink: "#f1e9df", line: "#2f2723", primary: "#d9a066", c1: "#d9a066", c2: "#8c6a4f", c3: "#c86b45", c4: "#86a17f", c5: "#7487a3", c6: "#c2ad8e" }
};
function ThmPreview({ tokens: k }) {
  const st = {};
  Object.entries(k || {}).forEach(([n, v]) => st["--" + n] = v);
  const bars = [0.92, 0.74, 0.6, 0.48, 0.36, 0.27];
  return /* @__PURE__ */ l.jsxs("div", { className: "thm-prev", style: st, children: [
    /* @__PURE__ */ l.jsxs("div", { className: "thm-band", children: [/* @__PURE__ */ l.jsx("span", { children: "✦ WHAT CHANGED AND WHY" }), /* @__PURE__ */ l.jsx("b", { children: "Sales up 12% on last month, led by the West" })] }),
    /* @__PURE__ */ l.jsxs("div", { className: "thm-row", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "thm-card", children: [/* @__PURE__ */ l.jsx("small", { children: "NET SALES" }), /* @__PURE__ */ l.jsx("strong", { children: "$4.2M" }), /* @__PURE__ */ l.jsx("em", { className: "up", children: "▲ +12.4%" }), /* @__PURE__ */ l.jsx("em", { className: "down", children: "▼ -3.1% margin" })] }),
      /* @__PURE__ */ l.jsxs("div", { className: "thm-card grow", children: [/* @__PURE__ */ l.jsx("small", { children: "BY REGION" }), /* @__PURE__ */ l.jsx("div", { className: "thm-bars", children: bars.map((w, i) => /* @__PURE__ */ l.jsx("i", { style: { width: `${w * 100}%`, background: `var(--c${i + 1})` } }, i)) })] }),
      /* @__PURE__ */ l.jsxs("div", { className: "thm-card", children: [/* @__PURE__ */ l.jsx("small", { children: "HEAT" }), /* @__PURE__ */ l.jsx("div", { className: "thm-heat", children: [1, 2, 3, 4, 5, 6, 7].map((i) => /* @__PURE__ */ l.jsx("i", { style: { background: `var(--h${i})` } }, i)) }), /* @__PURE__ */ l.jsx("button", { type: "button", className: "thm-btn", children: "Publish" })] })
    ] }),
    /* @__PURE__ */ l.jsx("p", { className: "thm-muted", children: "Secondary text and captions look like this." })
  ] });
}
function ThmForm({ data: e, send: t, pending: n }) {
  const dr = e.theme_draft, [tab, setTab] = P.useState("form"), [nm, setNm] = P.useState(""), [inp, setInp] = P.useState({ primary: "#11567f", chart: [] }), [def, setDef] = P.useState(!1), [err, setErr] = P.useState("");
  P.useEffect(() => {
    dr && (setInp({ ...dr.inputs, chart: [...(dr.inputs.chart || [])] }), dr.name && setNm((x) => x || dr.name.replace(/\.(json|css|svg|png|jpe?g|txt)$/i, "")));
  }, [dr && JSON.stringify(dr.inputs)]);
  const set = (k, v) => setInp((x) => ({ ...x, [k]: v })), setC = (i, v) => setInp((x) => {
    const c = [...(x.chart || [])];
    return c[i] = v, { ...x, chart: c.filter(Boolean) };
  });
  const check = () => t("theme_preview", { source: "form", inputs: inp, name: nm, theme_id: dr && dr.theme_id }, "Checking the colours…");
  const upload = (kind, f) => {
    if (!f) return;
    if (f.size > 15e5) return setErr("That file is larger than 1.5 MB.");
    setErr("");
    const rd = new FileReader();
    rd.onload = () => t("theme_preview", { source: kind, file: { name: f.name, b64: String(rd.result).split(",").pop() }, name: nm }, kind === "logo" ? "Reading the logo colours…" : "Reading the brand file…");
    rd.readAsDataURL(f);
  };
  const hexIn = (k, v, onCh, req) => /* @__PURE__ */ l.jsxs("span", { className: "thm-hex", children: [
    /* @__PURE__ */ l.jsx("input", { type: "color", value: /^#[0-9a-f]{6}$/i.test(v || "") ? v : "#ffffff", onChange: (x) => onCh(x.target.value), "aria-label": k }),
    /* @__PURE__ */ l.jsx("input", { type: "text", value: v || "", placeholder: req ? "#RRGGBB" : "auto", onChange: (x) => onCh(x.target.value.trim()), maxLength: 7 })
  ] });
  return /* @__PURE__ */ l.jsxs("div", { className: "thm-new", children: [
    /* @__PURE__ */ l.jsx("h4", { children: dr && dr.theme_id ? "Edit company theme" : "Add a company theme" }),
    /* @__PURE__ */ l.jsx("div", { className: "idea-tabs", children: [["form", "Brand colours"], ["tokens", "Upload brand file"], ["logo", "From the logo"]].map(([k, v]) => /* @__PURE__ */ l.jsx("button", { type: "button", className: `seg ${tab === k ? "on" : ""}`, onClick: () => setTab(k), children: v }, k)) }),
    tab === "tokens" && /* @__PURE__ */ l.jsxs("div", { className: "thm-up", children: [
      /* @__PURE__ */ l.jsx("p", { className: "muted small", children: "A design-token file from the brand or design team: JSON (any nesting, e.g. color.brand.primary.value) or CSS variables (--brand-primary: #0b5394). Only colour values are read." }),
      /* @__PURE__ */ l.jsx("input", { type: "file", accept: ".json,.css,.txt,application/json,text/css,text/plain", onChange: (x) => upload("tokens", x.target.files && x.target.files[0]) })
    ] }),
    tab === "logo" && /* @__PURE__ */ l.jsxs("div", { className: "thm-up", children: [
      /* @__PURE__ */ l.jsx("p", { className: "muted small", children: "PNG, JPG or SVG. The main brand colours are pulled out; you confirm or change them below before saving." }),
      /* @__PURE__ */ l.jsx("input", { type: "file", accept: ".png,.jpg,.jpeg,.svg,image/png,image/jpeg,image/svg+xml", onChange: (x) => upload("logo", x.target.files && x.target.files[0]) })
    ] }),
    err && /* @__PURE__ */ l.jsx("div", { className: "alert error small", children: err }),
    (tab === "form" || dr) && /* @__PURE__ */ l.jsxs("div", { className: "thm-grid", children: [
      /* @__PURE__ */ l.jsxs("label", { className: "thm-name", children: ["Theme name", /* @__PURE__ */ l.jsx("input", { type: "text", value: nm, placeholder: "e.g. Harborline brand", onChange: (x) => setNm(x.target.value), maxLength: 80 })] }),
      THM_ROLES.map(([k, lab, req]) => /* @__PURE__ */ l.jsxs("label", { children: [lab, req ? " *" : "", hexIn(k, inp[k], (v) => set(k, v), req)] }, k)),
      /* @__PURE__ */ l.jsxs("div", { className: "thm-chart", children: [/* @__PURE__ */ l.jsx("span", { children: "Chart colours (up to 6; empty = derived from the brand)" }), /* @__PURE__ */ l.jsx("div", { children: [0, 1, 2, 3, 4, 5].map((i) => /* @__PURE__ */ l.jsx("span", { children: hexIn("chart " + (i + 1), (inp.chart || [])[i], (v) => setC(i, v)) }, i)) })] })
    ] }),
    (tab === "form" || dr) && /* @__PURE__ */ l.jsx("div", { className: "thm-actions", children: /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small ghost", disabled: !inp.primary || n, onClick: check, children: dr ? "Re-check colours" : "Check colours & preview" }) }),
    dr && /* @__PURE__ */ l.jsxs("div", { className: "thm-result", children: [
      /* @__PURE__ */ l.jsx(ThmPreview, { tokens: dr.tokens }),
      /* @__PURE__ */ l.jsxs("div", { className: "thm-checks", children: [
        /* @__PURE__ */ l.jsx("b", { className: `thm-st ${dr.status}`, children: dr.status === "pass" ? "✓ All checks pass" : dr.status === "fixed" ? "↺ Passes after small adjustments" : "! Some checks fail" }),
        /* @__PURE__ */ l.jsx("ul", { children: dr.checks.map((c, i) => /* @__PURE__ */ l.jsxs("li", { className: c.status, children: [
          /* @__PURE__ */ l.jsx("span", { className: "thm-ci", children: THM_ICON[c.status] || "·" }),
          /* @__PURE__ */ l.jsx("em", { children: c.id }),
          " ", c.label, c.status !== "pass" && c.from && c.to && c.from !== c.to ? /* @__PURE__ */ l.jsxs("span", { className: "thm-ft", children: [/* @__PURE__ */ l.jsx("i", { style: { background: c.from } }), "→", /* @__PURE__ */ l.jsx("i", { style: { background: c.to } })] }) : null,
          /* @__PURE__ */ l.jsx("small", { children: c.detail })
        ] }, i)) }),
        /* @__PURE__ */ l.jsx("p", { className: "muted small", children: "Contrast follows WCAG 2.1 AA: text 4.5:1, chart marks 3:1. Adjusted colours keep their hue; change the brand input above and re-check if you prefer another fix." })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "thm-save", children: [
        /* @__PURE__ */ l.jsxs("label", { className: "tmenu-check", children: [/* @__PURE__ */ l.jsx("input", { type: "checkbox", checked: def, onChange: (x) => setDef(x.target.checked) }), " Make it the company default"] }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => t("theme_cancel", {}, "…", !0), children: "Cancel" }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", disabled: !nm.trim() || n, title: dr.status === "fail" ? "Some checks fail: you can still save, the report is kept with the theme" : "", onClick: () => t("theme_save", { name: nm, inputs: inp, source: dr.source, theme_id: dr.theme_id, make_default: def }, "Saving the theme…"), children: "Save theme" })
      ] })
    ] })
  ] });
}
function ThmPanel({ data: e, send: t, pending: n }) {
  const cur = e.theme || {}, defId = (e.theme_default || {}).setting_value || "classic", onDash = !!(e.spec && e.step === "workspace" && !e.viewer_mode);
  const all = [...(e.theme_builtin || []).map((b) => ({ id: b.id, name: b.name, tokens: THM_BUILTIN_SW[b.id], builtin: !0 })), ...(e.themes || []).map((x) => ({ id: "t:" + x.theme_id, name: x.name, tokens: x.tokens, raw: x }))];
  const defName = (all.find((x) => x.id === defId) || {}).name || "Classic";
  const dashId = (e.view || {}).theme || (e.spec || {}).theme || "";
  return /* @__PURE__ */ l.jsxs("div", { className: "thm", children: [
    /* @__PURE__ */ l.jsxs("p", { className: "muted small", children: ["Dashboards follow the company theme. Classic is used until one is set. Every theme is checked for readable text and distinct chart colours before it is saved, and every change is recorded (AA_THEMES)."] }),
    /* @__PURE__ */ l.jsxs("div", { className: "thm-now", children: [
      /* @__PURE__ */ l.jsxs("div", { children: [/* @__PURE__ */ l.jsx("small", { children: "Company default" }), /* @__PURE__ */ l.jsx("b", { children: defName }), (e.theme_default || {}).set_by ? /* @__PURE__ */ l.jsx("em", { children: `set by ${e.theme_default.set_by} · ${e.theme_default.set_at}` }) : null] }),
      onDash && /* @__PURE__ */ l.jsxs("label", { children: [/* @__PURE__ */ l.jsx("small", { children: "This dashboard" }), /* @__PURE__ */ l.jsxs("select", { value: dashId, onChange: (x) => t("theme_apply", { theme_id: x.target.value }, "Applying theme…", !0), children: [
        /* @__PURE__ */ l.jsx("option", { value: "", children: `Company default (${defName})` }),
        all.map((x) => /* @__PURE__ */ l.jsx("option", { value: x.id, children: x.name }, x.id))
      ] }), /* @__PURE__ */ l.jsx("em", { children: "Kept with the dashboard and with each published version." })] })
    ] }),
    /* @__PURE__ */ l.jsx("div", { className: "thm-list", children: all.map((x) => /* @__PURE__ */ l.jsxs("div", { className: `thm-item ${x.id === defId ? "is-def" : ""}`, children: [
      /* @__PURE__ */ l.jsx(ThmSw, { tokens: x.tokens || {} }),
      /* @__PURE__ */ l.jsxs("div", { className: "thm-meta", children: [
        /* @__PURE__ */ l.jsxs("b", { children: [x.name, x.id === defId ? /* @__PURE__ */ l.jsx("span", { className: "thm-tag", children: "Company default" }) : null, cur.id === x.id && onDash ? /* @__PURE__ */ l.jsx("span", { className: "thm-tag on", children: "On this dashboard" }) : null] }),
        /* @__PURE__ */ l.jsx("small", { children: x.builtin ? "Built in" : `${x.raw.status === "pass" ? "✓ checks pass" : x.raw.status === "fixed" ? "↺ adjusted to pass" : "! check issues"} · ${x.raw.source} · ${x.raw.created_by || ""} ${x.raw.created_at || ""}` })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "thm-btns", children: [
        x.id !== defId && /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => t("theme_default", { theme_id: x.id }, "Setting the company default…"), children: "Make default" }),
        !x.builtin && /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => t("theme_preview", { source: "form", inputs: x.raw.inputs, name: x.name, theme_id: x.raw.theme_id }, "Opening the theme…"), children: "Edit" }),
        !x.builtin && /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small danger-txt", onClick: () => t("theme_delete", { theme_id: x.raw.theme_id }, "Removing…"), children: "Remove" })
      ] })
    ] }, x.id)) }),
    /* @__PURE__ */ l.jsx(ThmForm, { data: e, send: t, pending: n })
  ] });
}
const yp = {
  combo_chart: CmbX,
  treemap: TmX,
  gauge: GgX,
  pnl_table: PnX,
  kpi_grid: Wo,
  kpi_card: Wo,
  trend_chart: rp,
  forecast_band: ip,
  ranked_bar: Nr,
  target_bar: Nr,
  capacity_chart: Nr,
  small_multiples: up,
  driver_bridge: ap,
  exception_table: wr,
  exception_queue: wr,
  risk_table: wr,
  action_table: op,
  evidence_table: qo,
  segment_matrix: Ho,
  detail_table: qo,
  heatmap: Ho,
  share_donut: cp,
  pareto: dp,
  scatter: hp,
  period_compare: fp,
  kpi_plan: pp,
  ytd_trajectory: Qo,
  pace_chart: Qo,
  status_tiles: mp,
  hour_heatmap: vp,
  worklist: gp,
  scorecard: xp
}, jp = {
  combo_chart: 7,
  treemap: 6,
  gauge: 5,
  pnl_table: 12,
  kpi_grid: 12,
  kpi_card: 4,
  trend_chart: 7,
  forecast_band: 8,
  small_multiples: 12,
  driver_bridge: 7,
  ranked_bar: 5,
  target_bar: 5,
  capacity_chart: 5,
  exception_table: 5,
  risk_table: 5,
  exception_queue: 12,
  action_table: 12,
  evidence_table: 12,
  segment_matrix: 12,
  detail_table: 12,
  heatmap: 12,
  share_donut: 4,
  pareto: 6,
  scatter: 6,
  period_compare: 6,
  kpi_plan: 12,
  ytd_trajectory: 7,
  pace_chart: 7,
  status_tiles: 12,
  hour_heatmap: 5,
  worklist: 12,
  scorecard: 8
};
function fd(e) {
  const t = [];
  let n = [], s = 0;
  const r = () => {
    n.length && (n[n.length - 1].span += 12 - s, t.push(...n)), n = [], s = 0;
  };
  return e.forEach((i) => {
    const a = Math.max(3, Math.min(12, i.width || jp[i.type] || 6));
    s + a > 12 && r(), n.push({ ...i, span: a }), s += a;
  }), r(), t;
}
const Np = [
  { id: "executives", label: "Executive" },
  { id: "managers", label: "Manager" },
  { id: "daily_operations", label: "Operations" },
  { id: "weekly_business_review", label: "Weekly review" }
], Ut = { executives: "Executive", managers: "Manager", weekly_business_review: "Weekly review", daily_operations: "Operations" }, Cr = (e) => e === "weekly_business_review" || e === "daily_operations" ? "operations" : e, wp = [
  { id: "executives", label: "Executive" },
  { id: "managers", label: "Manager" },
  { id: "daily_operations", label: "Operations" },
  { id: "weekly_business_review", label: "Weekly review" }
], Ko = [
  "Board pack on revenue and margin vs last year, by region…",
  "Which segments and categories need attention this month?",
  "Live operations today: pace by hour and what is going wrong…",
  "Where are we losing profit, and what is driving it?"
];
function kp({ kind: e }) {
  const t = { width: 20, height: 20, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" };
  return e === "executives" ? /* @__PURE__ */ l.jsxs("svg", { ...t, children: [
    /* @__PURE__ */ l.jsx("path", { d: "M3 17l6-6 4 4 8-8" }),
    /* @__PURE__ */ l.jsx("path", { d: "M15 7h6v6" })
  ] }) : e === "managers" ? /* @__PURE__ */ l.jsxs("svg", { ...t, children: [
    /* @__PURE__ */ l.jsx("rect", { x: "3", y: "3", width: "7", height: "7", rx: "1.5" }),
    /* @__PURE__ */ l.jsx("rect", { x: "14", y: "3", width: "7", height: "7", rx: "1.5" }),
    /* @__PURE__ */ l.jsx("rect", { x: "3", y: "14", width: "7", height: "7", rx: "1.5" }),
    /* @__PURE__ */ l.jsx("rect", { x: "14", y: "14", width: "7", height: "7", rx: "1.5" })
  ] }) : /* @__PURE__ */ l.jsx("svg", { ...t, children: /* @__PURE__ */ l.jsx("path", { d: "M3 12h4l3-8 4 16 3-8h4" }) });
}
function Sr({ size: e = 30 }) {
  return /* @__PURE__ */ l.jsxs("svg", { width: e, height: e, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.7", strokeLinejoin: "round", children: [
    /* @__PURE__ */ l.jsx("path", { d: "M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z" }),
    /* @__PURE__ */ l.jsx("path", { d: "M19 3v4M17 5h4" })
  ] });
}
function Cp({ data: e, send: t, pending: n, onBuilder: s }) {
  var U, _, E, T;
  const [r, i] = P.useState(""), [a, u] = P.useState(null), [o, d] = P.useState(""), [m, p] = P.useState(""), v = (e.featured || []).length > 0, [j, y] = P.useState("featured"), [C, k] = P.useState(0), [O, R] = P.useState(0), [Q, Z] = P.useState(!1), c = P.useRef({}), h = P.useRef(null), f = e.suggestions || [], x = e.building, N = (n == null ? void 0 : n.type) === "route_prompt", g = (n == null ? void 0 : n.type) === "compose_layout" || x && !e.error, M = N || g;
  P.useEffect(() => {
    const b = setInterval(() => k((B) => (B + 1) % Ko.length), 3500);
    return () => clearInterval(b);
  }, []), P.useEffect(() => {
    n || (!f.length && !c.current.base ? (c.current.base = !0, t("home_suggestions", {}, "Profiling your data…", !0)) : e.suggestions_by === "catalog" && !c.current.ai && (c.current.ai = !0, t("home_suggestions_ai", {}, "Cortex is proposing dashboards…", !0)));
  }, [f.length, e.suggestions_by, n]), P.useEffect(() => {
    const b = x ? `${x.goal}:${e.revision}` : "";
    x && !n && !e.error && c.current.compose !== b && (c.current.compose = b, t("compose_layout", { goal: x.goal }, "Cortex is designing your dashboard…", !0));
  }, [x, n, e.revision]), P.useEffect(() => {
    if (!M)
      return R(0);
    R(0);
    const b = setInterval(() => R((B) => Math.min(B + 1, x ? 4 : 2)), 1400);
    return () => clearInterval(b);
  }, [M, n == null ? void 0 : n.id, e.revision]);
  const S = () => {
    var B;
    if (M || !r.trim()) return;
    const b = r.trim();
    if ((B = a == null ? void 0 : a.s) != null && B.semantic_view) {
      const W = b !== a.text;
      t("route_prompt", {
        suggestion: { ...a.s, goal: b, metrics: W ? [] : a.s.metrics || [] },
        prompt: b,
        audience: o || a.s.audience
      }, "Preparing the governed data…", !0);
    } else t("route_prompt", o ? { prompt: b, audience: o } : { prompt: b }, "Finding the right governed data…", !0);
  }, A = (b, B, W) => {
    i(B), d(b.audience || ""), p(""), u({ s: b, text: B, label: W }), window.scrollTo && window.scrollTo({ top: 0, behavior: "smooth" }), setTimeout(() => {
      const ae = h.current;
      ae && (ae.focus(), ae.setSelectionRange(B.length, B.length));
    }, 50);
  }, w = e.prompts || [], J = m ? m === "all" ? "" : m : o, L = (J ? w.filter((b) => b.audience === J) : w).slice(0, 6), V = f.filter((b) => (!J || b.audience === J) && (!v || j === "all" || b.featured)), q = e.features || {}, F = [["Cortex AI", q.complete], ["ML Forecast", q.forecast], ["Top Insights", q.top_insights], ["Cortex Agents", q.agents]];
  if (M) {
    const b = (x == null ? void 0 : x.prompt) || r || ((a == null ? void 0 : a.text) || (n == null ? void 0 : n.label)) || "Building your governed analytics workspace", B = !!x, W = B ? Math.max(2, Math.min(4, O + 2)) : Math.min(2, O), ae = (x == null ? void 0 : x.domain) || ((a == null ? void 0 : a.s) == null ? void 0 : a.s.semantic_view) || "governed data", nt = B ? "Generating governed dashboard" : (n == null ? void 0 : n.label) || "Finding governed data", it = B ? "Designing your analytics workspace" : W > 1 ? "Profiling governed data" : "Understanding your request";
    return /* @__PURE__ */ l.jsxs("section", { className: "home view gen-view aa-generation-page", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "gen-panel", children: [
        /* @__PURE__ */ l.jsx("div", { className: "gen-orb", children: /* @__PURE__ */ l.jsx(Sr, { size: 34 }) }),
        /* @__PURE__ */ l.jsx("div", { className: "gen-kicker", children: nt }),
        /* @__PURE__ */ l.jsx("h1", { children: it }),
        /* @__PURE__ */ l.jsx("p", { className: "gen-prompt", children: b }),
        /* @__PURE__ */ l.jsxs("div", { className: "gen-meta", children: [
          /* @__PURE__ */ l.jsxs("span", { children: [
            "Live Snowflake run",
            n != null && n.label ? ` · ${n.label}` : ""
          ] }),
          /* @__PURE__ */ l.jsxs("b", { children: [
            "Step ",
            Math.max(1, W),
            " of 4"
          ] })
        ] }),
        /* @__PURE__ */ l.jsxs("div", { className: "gen-rail", children: [
          /* @__PURE__ */ l.jsx("i", { className: `p${W}` })
        ] }),
        /* @__PURE__ */ l.jsxs("ol", { className: "gen-steps", children: [
          /* @__PURE__ */ l.jsxs("li", { className: W > 0 ? "done" : "now", children: [
            /* @__PURE__ */ l.jsx("span", {}),
            /* @__PURE__ */ l.jsxs("div", { children: [
              /* @__PURE__ */ l.jsx("b", { children: "Choose governed data" }),
              /* @__PURE__ */ l.jsx("small", { children: B ? `${Ut[x.audience] || "Auto-routed"} dashboard on ${ae}` : "Matching the request to available semantic views" })
            ] })
          ] }),
          /* @__PURE__ */ l.jsxs("li", { className: W > 1 ? "done" : W === 1 ? "now" : "wait", children: [
            /* @__PURE__ */ l.jsx("span", {}),
            /* @__PURE__ */ l.jsxs("div", { children: [
              /* @__PURE__ */ l.jsx("b", { children: "Profile metrics and dimensions" }),
              /* @__PURE__ */ l.jsx("small", { children: B ? `${x.metrics || "Available"} metrics + ${x.dimensions || "available"} dimensions verified` : "Checking history, freshness, joins and permissions" })
            ] })
          ] }),
          /* @__PURE__ */ l.jsxs("li", { className: W > 2 ? "done" : W === 2 ? "now" : "wait", children: [
            /* @__PURE__ */ l.jsx("span", {}),
            /* @__PURE__ */ l.jsxs("div", { children: [
              /* @__PURE__ */ l.jsx("b", { children: "Draft pages and charts" }),
              /* @__PURE__ */ l.jsx("small", { children: B ? "Cortex is arranging KPI, trend and detail tiles" : "Preparing the dashboard plan for Cortex layout" })
            ] })
          ] }),
          /* @__PURE__ */ l.jsxs("li", { className: W > 3 ? "now" : "wait", children: [
            /* @__PURE__ */ l.jsx("span", {}),
            /* @__PURE__ */ l.jsxs("div", { children: [
              /* @__PURE__ */ l.jsx("b", { children: "Prepare review" }),
              /* @__PURE__ */ l.jsx("small", { children: "Opening the review workspace as soon as Snowflake returns" })
            ] })
          ] })
        ] }),
        /* @__PURE__ */ l.jsxs("div", { className: "gen-buffer", children: [
          /* @__PURE__ */ l.jsx("i", {}),
          /* @__PURE__ */ l.jsx("span", { children: W > 3 ? "Finalizing validated outline..." : W > 1 ? "Analyzing governed fields..." : "Routing request..." })
        ] })
      ] })
    ] });
  }
  return /* @__PURE__ */ l.jsxs("section", { className: `home view ${o ? "" : "home-clean"}`, children: [
    /* @__PURE__ */ l.jsxs("div", { className: "home-hero", children: [
      /* @__PURE__ */ l.jsx("div", { className: "orb", children: /* @__PURE__ */ l.jsx(Sr, {}) }),
      /* @__PURE__ */ l.jsx("div", { className: "home-kicker", children: "Analytics workspace / Build" }),
      /* @__PURE__ */ l.jsxs("h1", { children: [
        /* @__PURE__ */ l.jsx("span", { children: "Ask your data." }),
        /* @__PURE__ */ l.jsx("span", { children: "Build governed dashboards." })
      ] }),
      /* @__PURE__ */ l.jsx("p", { children: "Turn governed Snowflake data into executive, manager, and operations dashboards without leaving Snowflake." }),
      /* @__PURE__ */ l.jsxs("div", { className: "home-engine", children: [
        /* @__PURE__ */ l.jsx("div", { className: "engine-kicker", children: "Conversational dashboard engine" }),
        /* @__PURE__ */ l.jsx("h2", { children: "Plan with your data. Build for your audience." }),
        /* @__PURE__ */ l.jsx("p", { children: "Discover metrics, choose the story, then shape every page." })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: `prompt-bar ${M ? "busy-bar" : ""}`, children: [
        a && /* @__PURE__ */ l.jsxs("div", { className: "picked", children: [
          "Editing: ",
          /* @__PURE__ */ l.jsx("b", { children: a.label }),
          " · change any words, then press send",
          /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => {
            u(null), i("");
          }, children: "Clear" })
        ] }),
        /* @__PURE__ */ l.jsx(
          "textarea",
          {
            ref: h,
            rows: a ? 3 : 2,
            value: r,
            placeholder: Ko[C],
            disabled: M,
            onChange: (b) => {
              i(b.target.value), b.target.value.trim() || u(null);
            },
            onKeyDown: (b) => {
              b.key === "Enter" && !b.shiftKey && (b.preventDefault(), S());
            }
          }
        ),
        /* @__PURE__ */ l.jsxs("div", { className: "prompt-foot", children: [
          /* @__PURE__ */ l.jsxs("div", { className: "aud-pick", children: [
            /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "For" }),
            wp.map((b) => /* @__PURE__ */ l.jsx("button", { type: "button", className: `seg ${o === b.id ? "on" : ""}`, onClick: () => {
              d(o === b.id ? "" : b.id), p("");
            }, children: b.label }, b.id))
          ] }),
          /* @__PURE__ */ l.jsx("button", { type: "button", className: "send", disabled: M || !r.trim(), onClick: S, "aria-label": "Build dashboard", children: M ? /* @__PURE__ */ l.jsx("span", { className: "spinner" }) : /* @__PURE__ */ l.jsx("svg", { width: "18", height: "18", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2.2", strokeLinecap: "round", children: /* @__PURE__ */ l.jsx("path", { d: "M12 19V5M5 12l7-7 7 7" }) }) })
        ] })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "home-context", children: [
        /* @__PURE__ */ l.jsxs("span", { className: "context-main", children: [
          /* @__PURE__ */ l.jsx("i", {}),
          v && e.featured[0] ? e.featured[0].label : "Governed Snowflake data"
        ] }),
        /* @__PURE__ */ l.jsx("span", { children: v && e.featured[0] ? `${e.featured[0].metrics} governed metrics` : "Curated metrics" }),
        /* @__PURE__ */ l.jsx("span", { children: v && e.featured[0] ? `${e.featured[0].dimensions} dimensions` : "Semantic context" }),
        /* @__PURE__ */ l.jsx("span", { children: "Designed for Snowflake" }),
        /* @__PURE__ */ l.jsx("span", { children: "One workflow" })
      ] }),
      false && /* @__PURE__ */ l.jsxs("div", { className: "home-workflow", children: [
        ["01", "Ask", "Describe the business question"].map(([b, B, W]) => /* @__PURE__ */ l.jsxs("span", { children: [
          /* @__PURE__ */ l.jsx("b", { children: b }),
          /* @__PURE__ */ l.jsx("strong", { children: B }),
          /* @__PURE__ */ l.jsx("em", { children: W })
        ] }, b)),
        ["02", "Choose audience", "Executive, manager or operations"].map(([b, B, W]) => /* @__PURE__ */ l.jsxs("span", { children: [
          /* @__PURE__ */ l.jsx("b", { children: b }),
          /* @__PURE__ */ l.jsx("strong", { children: B }),
          /* @__PURE__ */ l.jsx("em", { children: W })
        ] }, b)),
        ["03", "Cortex drafts", "Metrics, pages and charts"].map(([b, B, W]) => /* @__PURE__ */ l.jsxs("span", { children: [
          /* @__PURE__ */ l.jsx("b", { children: b }),
          /* @__PURE__ */ l.jsx("strong", { children: B }),
          /* @__PURE__ */ l.jsx("em", { children: W })
        ] }, b)),
        ["04", "Review", "Publish with governed data"].map(([b, B, W]) => /* @__PURE__ */ l.jsxs("span", { children: [
          /* @__PURE__ */ l.jsx("b", { children: b }),
          /* @__PURE__ */ l.jsx("strong", { children: B }),
          /* @__PURE__ */ l.jsx("em", { children: W })
        ] }, b))
      ] }),
      false && L.length > 0 && /* @__PURE__ */ l.jsxs("div", { className: "rec-section", children: [
        /* @__PURE__ */ l.jsxs("div", { className: "rec-head", children: [
          /* @__PURE__ */ l.jsx("h3", { children: "Recommended prompts" }),
          /* @__PURE__ */ l.jsx("span", { children: o ? `${Ut[o]} focus` : "Mixed from your governed data" })
        ] }),
        /* @__PURE__ */ l.jsx("div", { className: "rec-grid", children: L.map((b, B) => /* @__PURE__ */ l.jsxs(
          "button",
          {
            type: "button",
            className: `rec-card ${Cr(b.audience)}`,
            style: { "--i": B },
            disabled: M,
            title: "Puts this request in the box to edit; nothing is built until you press send",
            onClick: () => A({ semantic_view: b.semantic_view, audience: b.audience, metrics: b.metrics, title: b.text }, b.text, `${Ut[b.audience]} request`),
            children: [
              /* @__PURE__ */ l.jsxs("span", { className: "rec-icon", children: [
                /* @__PURE__ */ l.jsx(kp, { kind: Cr(b.audience) })
              ] }),
              /* @__PURE__ */ l.jsx("b", { children: b.text }),
              /* @__PURE__ */ l.jsx("span", { className: "rec-meta", children: ((b.themes || []).slice(0, 2).join(" + ") || Ut[b.audience]) + (b.semantic_view ? ` from ${String(b.semantic_view).split(".").slice(-1)[0]}` : "") }),
              /* @__PURE__ */ l.jsxs("span", { className: "rec-foot", children: [
                /* @__PURE__ */ l.jsx("em", { children: Ut[b.audience] }),
                (b.metrics || []).slice(0, 2).map((W) => /* @__PURE__ */ l.jsx("small", { children: W }, W))
              ] })
            ]
          },
          `${b.text}-${B}`
        )) })
      ] }),
      false && /* @__PURE__ */ l.jsxs("div", { className: "ai-ready", children: [
        F.map(([b, B]) => /* @__PURE__ */ l.jsxs("span", { className: B ? "ok" : "off", children: [
          /* @__PURE__ */ l.jsx("i", {}),
          b
        ] }, b)),
        e.catalog_size ? /* @__PURE__ */ l.jsxs("span", { className: "muted", children: [
          "· ",
          e.catalog_size,
          " governed datasets profiled"
        ] }) : null
      ] })
    ] }),
    o && /* @__PURE__ */ l.jsxs("div", { className: "featured-bar", children: [
      v && e.featured.map((b) => /* @__PURE__ */ l.jsxs("span", { className: "featured-ds", title: b.fqn, children: [
        /* @__PURE__ */ l.jsx("i", { className: "live-dot" }),
        " ",
        /* @__PURE__ */ l.jsx("b", { children: b.label }),
        " · ",
        b.adhoc ? `${b.metrics} measures from facts` : `${b.metrics} governed metrics`,
        " · ",
        b.dimensions,
        " dimensions",
        b.adhoc ? "" : " · updating live"
      ] }, b.fqn)),
      s && /* @__PURE__ */ l.jsx("button", { type: "button", className: "link connect-link", onClick: s, children: "＋ Connect a Snowflake table" })
    ] }),
    o && ((_ = e.catalog_skipped) == null ? void 0 : _.length) > 0 && /* @__PURE__ */ l.jsxs("details", { className: "skipped-views", children: [
      /* @__PURE__ */ l.jsxs("summary", { children: [
        e.catalog_skipped.length,
        " semantic view",
        e.catalog_skipped.length > 1 ? "s" : "",
        " found but not used for ideas"
      ] }),
      /* @__PURE__ */ l.jsx("ul", { children: e.catalog_skipped.map((b) => /* @__PURE__ */ l.jsxs("li", { children: [
        /* @__PURE__ */ l.jsx("b", { title: b.fqn, children: b.name }),
        ": ",
        b.reason,
        "."
      ] }, b.fqn)) })
    ] }),
    false && M && /* @__PURE__ */ l.jsxs("div", { className: "build-card", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "build-title", children: [
        /* @__PURE__ */ l.jsx(Sr, { size: 18 }),
        " Building: ",
        /* @__PURE__ */ l.jsx("i", { children: (x == null ? void 0 : x.prompt) || r })
      ] }),
      /* @__PURE__ */ l.jsxs("ol", { className: "build-steps", children: [
        /* @__PURE__ */ l.jsxs("li", { className: x ? "done" : "now", children: [
          /* @__PURE__ */ l.jsx("b", { children: "Understand the request & choose governed data" }),
          x && /* @__PURE__ */ l.jsxs("span", { children: [
            Ut[x.audience],
            " dashboard on ",
            /* @__PURE__ */ l.jsx("b", { children: x.domain }),
            x.reason ? ` — ${x.reason}` : "",
            " ",
            /* @__PURE__ */ l.jsxs("em", { children: [
              "(",
              x.by,
              ")"
            ] })
          ] })
        ] }),
        /* @__PURE__ */ l.jsxs("li", { className: x ? "done" : "", children: [
          /* @__PURE__ */ l.jsx("b", { children: "Profile the data" }),
          x && /* @__PURE__ */ l.jsxs("span", { children: [
            x.metrics,
            " metrics · ",
            x.dimensions,
            " dimensions · history, cardinality and capabilities proven"
          ] })
        ] }),
        /* @__PURE__ */ l.jsx("li", { className: x ? "now" : "", children: /* @__PURE__ */ l.jsx("b", { children: "Cortex drafts pages & charts, validator checks every tile" }) }),
        /* @__PURE__ */ l.jsx("li", { children: /* @__PURE__ */ l.jsx("b", { children: "You review metrics & outline, then build" }) })
      ] })
    ] }),
    o && /* @__PURE__ */ l.jsxs("div", { className: "idea-head", children: [
      /* @__PURE__ */ l.jsx("h3", { children: "Recommended" }),
      /* @__PURE__ */ l.jsxs("label", { className: "idea-filter", children: [
        /* @__PURE__ */ l.jsx("span", { children: "Prompt set" }),
        /* @__PURE__ */ l.jsxs("select", { value: m || o || "all", onChange: (b) => p(b.target.value), children: [
          /* @__PURE__ */ l.jsx("option", { value: "all", children: "Mixed prompts" }),
          wp.map((b) => /* @__PURE__ */ l.jsx("option", { value: b.id, children: b.label }, b.id))
        ] })
      ] }),
      Q && v && /* @__PURE__ */ l.jsxs("div", { className: "idea-tabs", children: [
        /* @__PURE__ */ l.jsxs("button", { type: "button", className: `seg ${j === "featured" ? "on" : ""}`, onClick: () => y("featured"), children: [
          "● ",
          e.featured.length > 1 ? "Featured data" : e.featured[0].label
        ] }),
        /* @__PURE__ */ l.jsxs("button", { type: "button", className: `seg ${j === "all" ? "on" : ""}`, onClick: () => y("all"), children: [
          "All data",
          f.length ? ` (${f.length})` : ""
        ] })
      ] }),
      false && /* @__PURE__ */ l.jsx("div", { className: "idea-tabs idea-audience-tabs", children: Np.map((b) => /* @__PURE__ */ l.jsx("button", { type: "button", className: `seg ${m === b.id ? "on" : ""}`, onClick: () => p(m === b.id ? "" : b.id), children: b.label }, b.id)) }),
      /* @__PURE__ */ l.jsx("span", { className: `idea-src ${Q ? "show-source" : "action-only"}`, children: !Q ? /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", title: "Ask Cortex for a fresh set of ideas", onClick: () => {
        Z(!0), t("home_suggestions_ai", { fresh: !0 }, "Cortex is writing new ideas...", !0);
      }, children: "New ideas" }) : (n == null ? void 0 : n.type) === "home_suggestions_ai" && e.suggestions_by === "cortex" ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
        /* @__PURE__ */ l.jsx("span", { className: "spinner dark sm" }),
        " Cortex is writing new ideas…"
      ] }) : e.suggestions_by === "cortex" ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
        /* @__PURE__ */ l.jsx(Sr, { size: 13 }),
        " Suggested by Cortex",
        e.suggestions_at ? ` · saved ${e.suggestions_at}` : "",
        /* @__PURE__ */ l.jsx(
          "button",
          {
            type: "button",
            className: "link",
            title: "Ask Cortex for a fresh set of ideas (added on top; earlier ideas stay below)",
            onClick: () => t("home_suggestions_ai", { fresh: !0 }, "Cortex is writing new ideas…", !0),
            children: "↻ New ideas"
          }
        )
      ] }) : e.suggestions_by === "catalog" ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
        /* @__PURE__ */ l.jsx("span", { className: "spinner dark sm" }),
        " Cortex is tailoring ideas…"
      ] }) : f.length ? "From your data catalog" : null })
    ] }),
    o && L.length > 0 && /* @__PURE__ */ l.jsxs("div", { className: "prompt-recs", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "prompt-recs-head", children: [
        /* @__PURE__ */ l.jsx("span", { children: "Starter prompts" }),
        /* @__PURE__ */ l.jsx("em", { children: J ? `${Ut[J]} prompt set` : "Mixed prompt set" })
      ] }),
      /* @__PURE__ */ l.jsx("div", { className: "prompt-rec-grid", children: L.map((b, B) => /* @__PURE__ */ l.jsxs("button", { type: "button", className: `prompt-rec ${Cr(b.audience)}`, style: { "--i": B }, disabled: M, onClick: () => A({ semantic_view: b.semantic_view, audience: b.audience, metrics: b.metrics, title: b.text }, b.text, `${Ut[b.audience]} request`), children: [
        /* @__PURE__ */ l.jsx("span", { children: Ut[b.audience] }),
        /* @__PURE__ */ l.jsx("b", { children: b.text }),
        /* @__PURE__ */ l.jsx("small", { children: ((b.themes || []).slice(0, 2).join(" + ") || "Governed prompt") + (b.semantic_view ? ` from ${String(b.semantic_view).split(".").slice(-1)[0]}` : "") })
      ] }, `${b.text}-${B}`)) })
    ] }),
    o && f.length > 0 && !V.length && /* @__PURE__ */ l.jsxs("div", { className: "empty", children: [
      "No ideas for this filter yet. ",
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => {
        p("all"), y("all");
      }, children: "Show mixed ideas" })
    ] }),
    o && (f.length ? /* @__PURE__ */ l.jsx("div", { className: "ideas", children: V.map((b, B) => /* @__PURE__ */ l.jsxs(
      "button",
      {
        type: "button",
        className: `idea ${Cr(b.audience)}`,
        style: { "--i": B },
        disabled: M,
        title: "Puts this idea in the box to edit; nothing is built until you press send",
        onClick: () => A(b, b.goal || b.title, `${Ut[b.audience]} idea "${b.title}"`),
        children: [
          /* @__PURE__ */ l.jsxs("div", { className: "idea-top", children: [
            /* @__PURE__ */ l.jsx("span", { className: "idea-icon", children: /* @__PURE__ */ l.jsx(kp, { kind: Cr(b.audience) }) }),
            /* @__PURE__ */ l.jsxs("span", { className: "idea-aud", children: [
              b.featured && /* @__PURE__ */ l.jsx("em", { className: "live-tag", children: "● Live" }),
              Ut[b.audience],
              b.earlier && /* @__PURE__ */ l.jsx("em", { className: "idea-earlier", title: `Suggested earlier (saved ${b.earlier})`, children: "· Earlier" })
            ] })
          ] }),
          b.theme_label && /* @__PURE__ */ l.jsx("span", { className: "idea-theme", children: b.theme_label }),
          /* @__PURE__ */ l.jsx("b", { children: b.title }),
          /* @__PURE__ */ l.jsx("span", { className: "idea-detail", children: b.detail }),
          /* @__PURE__ */ l.jsxs("span", { className: "idea-foot", children: [
            (b.metrics || []).slice(0, 3).map((W) => /* @__PURE__ */ l.jsx("em", { children: W }, W)),
            /* @__PURE__ */ l.jsx("small", { children: b.domain })
          ] })
        ]
      },
      `${b.title}-${B}`
    )) }) : /* @__PURE__ */ l.jsx("div", { className: "ideas", children: [0, 1, 2, 3, 4, 5].map((b) => /* @__PURE__ */ l.jsxs("div", { className: "idea skeleton", children: [
      /* @__PURE__ */ l.jsx("i", {}),
      /* @__PURE__ */ l.jsx("b", {}),
      /* @__PURE__ */ l.jsx("span", {}),
      /* @__PURE__ */ l.jsx("span", {})
    ] }, b)) })),
    o && ((E = e.published) == null ? void 0 : E.length) > 0 && /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
      /* @__PURE__ */ l.jsx("h3", { className: "sec-title", children: "Published dashboards" }),
      /* @__PURE__ */ l.jsx("div", { className: "recent", children: e.published.slice(0, 8).map((b) => /* @__PURE__ */ l.jsxs("button", { type: "button", className: "recent-card pub", disabled: M, onClick: () => t("open_published", { dashboard_id: b.dashboard_id }), children: [
        /* @__PURE__ */ l.jsxs("b", { children: [
          "📊 ",
          b.name
        ] }),
        /* @__PURE__ */ l.jsxs("small", { children: [
          "v",
          b.version,
          " · ",
          Ut[b.audience] || b.audience,
          " · ",
          b.published_by || "",
          " · ",
          b.published_at
        ] })
      ] }, b.dashboard_id)) })
    ] }),
    o && ((T = e.dashboards) == null ? void 0 : T.length) > 0 && /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
      /* @__PURE__ */ l.jsx("h3", { className: "sec-title", children: "Your drafts" }),
      /* @__PURE__ */ l.jsx("div", { className: "recent", children: e.dashboards.slice(0, 6).map((b) => /* @__PURE__ */ l.jsxs("button", { type: "button", className: "recent-card", disabled: M, onClick: () => t("open_dashboard", { dashboard_id: b.dashboard_id }), children: [
        /* @__PURE__ */ l.jsx("b", { children: b.name }),
        /* @__PURE__ */ l.jsxs("small", { children: [
          Ut[b.audience] || b.audience,
          " · v",
          b.version,
          " · ",
          b.created_at
        ] })
      ] }, b.dashboard_id)) })
    ] }),
    o && /* @__PURE__ */ l.jsx("div", { className: "home-foot", children: /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => t("go", { step: "source" }, "Opening…"), children: "Browse governed data sources (advanced) →" }) })
  ] });
}
const Ni = ["Sales", "Profitability", "Customers", "Fulfilment", "Returns", "Inventory", "Plan"];
function Sp({ type: e }) {
  const t = { width: 22, height: 16, viewBox: "0 0 22 16", fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round" };
  switch (e) {
    case "kpi_grid":
    case "kpi_card":
    case "kpi_plan":
    case "status_tiles":
      return /* @__PURE__ */ l.jsxs("svg", { ...t, children: [
        /* @__PURE__ */ l.jsx("rect", { x: "1", y: "3", width: "5.5", height: "10", rx: "1.5" }),
        /* @__PURE__ */ l.jsx("rect", { x: "8.25", y: "3", width: "5.5", height: "10", rx: "1.5" }),
        /* @__PURE__ */ l.jsx("rect", { x: "15.5", y: "3", width: "5.5", height: "10", rx: "1.5" })
      ] });
    case "trend_chart":
    case "small_multiples":
    case "pace_chart":
      return /* @__PURE__ */ l.jsx("svg", { ...t, children: /* @__PURE__ */ l.jsx("path", { d: "M1 12l5-5 4 3 5-6 6 4" }) });
    case "forecast_band":
    case "ytd_trajectory":
      return /* @__PURE__ */ l.jsxs("svg", { ...t, children: [
        /* @__PURE__ */ l.jsx("path", { d: "M1 12l5-5 4 3 4-4" }),
        /* @__PURE__ */ l.jsx("path", { d: "M14 6l7-2", strokeDasharray: "2 2" })
      ] });
    case "share_donut":
      return /* @__PURE__ */ l.jsxs("svg", { ...t, children: [
        /* @__PURE__ */ l.jsx("circle", { cx: "11", cy: "8", r: "6" }),
        /* @__PURE__ */ l.jsx("circle", { cx: "11", cy: "8", r: "2.5" })
      ] });
    case "scatter":
      return /* @__PURE__ */ l.jsxs("svg", { ...t, children: [
        /* @__PURE__ */ l.jsx("circle", { cx: "4", cy: "11", r: "1.4" }),
        /* @__PURE__ */ l.jsx("circle", { cx: "9", cy: "7", r: "1.4" }),
        /* @__PURE__ */ l.jsx("circle", { cx: "14", cy: "9", r: "1.4" }),
        /* @__PURE__ */ l.jsx("circle", { cx: "18", cy: "4", r: "1.4" })
      ] });
    case "heatmap":
    case "segment_matrix":
    case "hour_heatmap":
    case "scorecard":
      return /* @__PURE__ */ l.jsxs("svg", { ...t, children: [
        /* @__PURE__ */ l.jsx("rect", { x: "2", y: "2", width: "5", height: "5" }),
        /* @__PURE__ */ l.jsx("rect", { x: "8.5", y: "2", width: "5", height: "5" }),
        /* @__PURE__ */ l.jsx("rect", { x: "15", y: "2", width: "5", height: "5" }),
        /* @__PURE__ */ l.jsx("rect", { x: "2", y: "9", width: "5", height: "5" }),
        /* @__PURE__ */ l.jsx("rect", { x: "8.5", y: "9", width: "5", height: "5" }),
        /* @__PURE__ */ l.jsx("rect", { x: "15", y: "9", width: "5", height: "5" })
      ] });
    case "detail_table":
    case "evidence_table":
    case "action_table":
      return /* @__PURE__ */ l.jsx("svg", { ...t, children: /* @__PURE__ */ l.jsx("path", { d: "M2 3h18M2 8h18M2 13h18" }) });
    case "driver_bridge":
      return /* @__PURE__ */ l.jsx("svg", { ...t, children: /* @__PURE__ */ l.jsx("path", { d: "M2 14V6M7 6V3M12 3v5M17 8v6" }) });
    case "exception_table":
    case "worklist":
      return /* @__PURE__ */ l.jsxs("svg", { ...t, children: [
        /* @__PURE__ */ l.jsx("path", { d: "M11 2l9 12H2z" }),
        /* @__PURE__ */ l.jsx("path", { d: "M11 7v3" })
      ] });
    default:
      return /* @__PURE__ */ l.jsx("svg", { ...t, children: /* @__PURE__ */ l.jsx("path", { d: "M2 14h4V6H2zM9 14h4V2H9zM16 14h4V9h-4z" }) });
  }
}
function br(e) {
  return [e.metric_id, e.metric2_id, ...e.metrics || []].filter(Boolean);
}
function Skx({ type: e, mini: m, n: NK }) {
  const H = m ? 26 : 64, vb = "0 0 120 48", A = "#29b5e8", D = "#11567f", F = "#d7e7f5", G = "#eef4fa", S = { vectorEffect: "non-scaling-stroke" };
  const svg = (kids, keep) => /* @__PURE__ */ l.jsx("svg", { className: "skx", viewBox: vb, preserveAspectRatio: keep ? "xMidYMid meet" : "none", style: { height: H }, "aria-hidden": "true", children: kids });
  const line = (pts, c, dash) => /* @__PURE__ */ l.jsx("polyline", { points: pts, fill: "none", stroke: c, strokeWidth: 2, strokeDasharray: dash || "none", ...S });
  switch (e) {
    case "kpi_grid": case "kpi_card": case "kpi_plan": case "status_tiles":
      const KN = Math.max(1, Math.min(6, NK || 4)), KW = 120 / KN;
      return svg([...Array(KN).keys()].map((i) => /* @__PURE__ */ l.jsxs("g", { children: [
        /* @__PURE__ */ l.jsx("rect", { x: 2 + i * KW, y: 6, width: KW - 4, height: 36, rx: 3, fill: G, stroke: F }),
        /* @__PURE__ */ l.jsx("rect", { x: 6 + i * KW, y: 12, width: Math.min(12, KW / 2), height: 3, fill: "#9db4ca" }),
        /* @__PURE__ */ l.jsx("rect", { x: 6 + i * KW, y: 19, width: KW * 0.6, height: 8, rx: 1, fill: D }),
        /* @__PURE__ */ l.jsx("rect", { x: 6 + i * KW, y: 33, width: KW * (0.6 - (i % 3) * 0.06), height: 3, fill: e === "kpi_plan" ? A : "#9fd8a5" })
      ] }, i)));
    case "trend_chart": case "pace_chart":
      return svg([line("2,36 16,30 30,33 44,24 58,27 72,18 86,21 100,12 118,15", D), line("2,40 16,37 30,38 44,33 58,35 72,29 86,31 100,26 118,27", "#9db4ca", "4 3")]);
    case "forecast_band": case "ytd_trajectory":
      return svg([/* @__PURE__ */ l.jsx("polygon", { points: "80,22 118,8 118,26 80,24", fill: F }), line("2,44 20,40 40,34 60,29 80,23", D), line("80,23 118,17", A, "4 3"), line("2,44 118,12", "#9db4ca", "2 3")]);
    case "ranked_bar": case "target_bar": case "capacity_chart":
      return svg([96, 80, 66, 50, 38, 26].map((w, i) => /* @__PURE__ */ l.jsx("rect", { x: 2, y: 3 + i * 7.5, width: w, height: 5, rx: 1, fill: i ? F : A }, i)));
    case "period_compare":
      return svg([0, 1, 2, 3].map((g) => [0, 1, 2].map((k) => /* @__PURE__ */ l.jsx("rect", { x: 6 + g * 29 + k * 7, y: 46 - [30, 26, 22][k] + g * 3, width: 6, height: [30, 26, 22][k] - g * 3, fill: [D, A, F][k] }, g + "-" + k))).flat());
    case "share_donut":
      return svg([/* @__PURE__ */ l.jsx("circle", { cx: 60, cy: 24, r: 16, fill: "none", stroke: F, strokeWidth: 9 }), /* @__PURE__ */ l.jsx("circle", { cx: 60, cy: 24, r: 16, fill: "none", stroke: A, strokeWidth: 9, strokeDasharray: "45 100", transform: "rotate(-90 60 24)" }), /* @__PURE__ */ l.jsx("circle", { cx: 60, cy: 24, r: 16, fill: "none", stroke: D, strokeWidth: 9, strokeDasharray: "25 100", strokeDashoffset: -45, transform: "rotate(-90 60 24)" })], !0);
    case "pareto":
      return svg([...[40, 30, 22, 15, 10, 7, 5, 4].map((h, i) => /* @__PURE__ */ l.jsx("rect", { x: 4 + i * 14, y: 46 - h, width: 11, height: h, fill: i < 3 ? A : F }, i)), line("9,30 23,18 37,11 51,7 65,5 79,4 93,3 107,3", D)]);
    case "driver_bridge":
      return svg([/* @__PURE__ */ l.jsx("rect", { x: 4, y: 14, width: 14, height: 32, fill: "#9db4ca" }), /* @__PURE__ */ l.jsx("rect", { x: 24, y: 6, width: 14, height: 8, fill: "#4caf7a" }), /* @__PURE__ */ l.jsx("rect", { x: 44, y: 6, width: 14, height: 6, fill: "#e06c6c" }), /* @__PURE__ */ l.jsx("rect", { x: 64, y: 3, width: 14, height: 9, fill: "#4caf7a" }), /* @__PURE__ */ l.jsx("rect", { x: 84, y: 3, width: 14, height: 4, fill: "#e06c6c" }), /* @__PURE__ */ l.jsx("rect", { x: 104, y: 7, width: 14, height: 39, fill: D })]);
    case "scatter":
      return svg([[10, 38], [22, 30], [30, 34], [41, 24], [52, 27], [60, 18], [71, 21], [83, 12], [94, 16], [108, 8]].map(([x, y], i) => /* @__PURE__ */ l.jsx("circle", { cx: x, cy: y, r: 2.6, fill: i === 7 ? A : D }, i)), !0);
    case "heatmap": case "hour_heatmap": case "segment_matrix":
      return svg([0, 1, 2, 3].map((r) => [...Array(10)].map((_, c) => /* @__PURE__ */ l.jsx("rect", { x: 2 + c * 11.6, y: 2 + r * 11.5, width: 10.6, height: 10.5, fill: A, opacity: 0.15 + ((r * 3 + c * 7) % 9) / 11 }, r + "-" + c))).flat());
    case "small_multiples":
      return svg([0, 1, 2, 3, 4, 5].map((i) => /* @__PURE__ */ l.jsx("g", { children: [/* @__PURE__ */ l.jsx("rect", { x: 2 + (i % 3) * 39.3, y: 2 + Math.floor(i / 3) * 23, width: 37, height: 21, fill: G }), line(`${5 + (i % 3) * 39.3},${18 + Math.floor(i / 3) * 23} ${15 + (i % 3) * 39.3},${12 + Math.floor(i / 3) * 23 + (i % 2) * 3} ${25 + (i % 3) * 39.3},${14 + Math.floor(i / 3) * 23} ${36 + (i % 3) * 39.3},${8 + Math.floor(i / 3) * 23 + (i % 3) * 2}`, D)] }, i)));
    case "combo_chart":
      return svg([...[22, 28, 18, 30, 26, 34, 38].map((h, i) => /* @__PURE__ */ l.jsx("rect", { x: 6 + i * 16, y: 46 - h, width: 11, height: h, fill: i === 6 ? D : F }, i)), line("11,24 27,20 43,26 59,16 75,19 91,12 107,9", A)]);
    case "treemap":
      return svg([[2, 2, 62, 44, D], [66, 2, 52, 26, A], [66, 30, 30, 16, F], [98, 30, 20, 16, "#9db4ca"]].map(([x, y, w, h, c], i) => /* @__PURE__ */ l.jsx("rect", { x, y, width: w, height: h, rx: 2, fill: c }, i)));
    case "gauge":
      return svg([/* @__PURE__ */ l.jsx("path", { d: "M24,42 A36,36 0 0 1 96,42", fill: "none", stroke: F, strokeWidth: 9 }), /* @__PURE__ */ l.jsx("path", { d: "M24,42 A36,36 0 0 1 84,16", fill: "none", stroke: D, strokeWidth: 9 })], !0);
    case "pnl_table":
      return svg([0, 1, 2, 3, 4].map((r) => /* @__PURE__ */ l.jsx("g", { children: [/* @__PURE__ */ l.jsx("rect", { x: 2, y: 3 + r * 9, width: 26, height: 5, fill: "#9db4ca" }), ...[0, 1, 2, 3, 4].map((c) => /* @__PURE__ */ l.jsx("rect", { x: 34 + c * 17, y: 2 + r * 9, width: 15, height: 7, fill: ["#cfeedd", "#f6d6d6", "#e4f5ec", "#fbe7e7", G][(r * 2 + c) % 5] }, c))] }, r)));
    case "scorecard":
      return svg([0, 1, 2, 3, 4].map((r) => /* @__PURE__ */ l.jsx("g", { children: [/* @__PURE__ */ l.jsx("rect", { x: 2, y: 3 + r * 9, width: 30, height: 4, fill: "#9db4ca" }), ...[0, 1, 2, 3].map((c) => /* @__PURE__ */ l.jsx("circle", { cx: 50 + c * 18, cy: 5 + r * 9, r: 3, fill: ["#4caf7a", "#e8b33f", "#e06c6c", "#4caf7a"][(r + c) % 4] }, c))] }, r)));
    case "exception_table": case "worklist": case "exception_queue": case "risk_table":
      return svg([0, 1, 2, 3, 4].map((r) => /* @__PURE__ */ l.jsx("g", { children: [/* @__PURE__ */ l.jsx("circle", { cx: 6, cy: 6 + r * 9, r: 3, fill: r < 2 ? "#e06c6c" : r < 3 ? "#e8b33f" : "#c9d6e3" }), /* @__PURE__ */ l.jsx("rect", { x: 14, y: 4 + r * 9, width: 60 - r * 5, height: 4, fill: "#9db4ca" }), /* @__PURE__ */ l.jsx("rect", { x: 92, y: 4 + r * 9, width: 24, height: 4, fill: F })] }, r)));
    default:
      return svg([0, 1, 2, 3, 4].map((r) => /* @__PURE__ */ l.jsx("g", { children: [/* @__PURE__ */ l.jsx("rect", { x: 2, y: 3 + r * 9, width: 116, height: 7, fill: r ? (r % 2 ? "#fff" : G) : F })] }, r)));
  }
}
function Cmx({ send: t, preview: e, selected: s }) {
  const [o, a] = P.useState(!!e), [x, y] = P.useState(""), [nm, sn] = P.useState(""), [b, sb] = P.useState(!1);
  P.useEffect(() => {
    sb(!1), e && a(!0);
  }, [e]);
  const go = () => {
    x.trim() && (sb(!0), t("metric_define", { text: x, name: nm, selected: [...s] }, "Cortex is checking your metric..."));
  };
  if (!o)
    return /* @__PURE__ */ l.jsxs("div", { className: "cm-open", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => a(!0), children: "+ Define a metric" }),
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "Not in the list? Describe it and Cortex builds it from these metrics." })
    ] });
  return /* @__PURE__ */ l.jsxs("div", { className: "cm-box", children: [
    /* @__PURE__ */ l.jsx("h4", { children: "Define a custom metric" }),
    /* @__PURE__ */ l.jsx("p", { className: "muted small", children: "Plain English or a formula over the metrics of this view, e.g. “return rate = returned units divided by units sold” or ORDERS.PROFIT / ORDERS.SALES. Filters and new columns are not possible here." }),
    /* @__PURE__ */ l.jsx("textarea", { rows: 2, value: x, placeholder: "Describe the metric or type a formula", onChange: (c) => y(c.target.value) }),
    /* @__PURE__ */ l.jsx("input", { className: "cm-name", value: nm, placeholder: "Name (optional), e.g. RETURN_RATE", onChange: (c) => sn(c.target.value) }),
    /* @__PURE__ */ l.jsxs("div", { className: "cm-actions", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn primary", disabled: b || !x.trim(), onClick: go, children: b ? "Checking..." : "Check with Cortex" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => {
        a(!1), e && t("metric_cancel", {}, "", !0);
      }, children: "Cancel" })
    ] }),
    e && e.error && /* @__PURE__ */ l.jsx("div", { className: "cm-error", children: e.error }),
    e && !e.error && /* @__PURE__ */ l.jsxs("div", { className: "cm-preview", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "cm-title", children: [/* @__PURE__ */ l.jsx("b", { children: e.label }), /* @__PURE__ */ l.jsx("em", { className: "draft-tag cm-tag", children: "custom" })] }),
      /* @__PURE__ */ l.jsx("div", { className: "cm-formula", children: "= " + e.display }),
      e.description && /* @__PURE__ */ l.jsx("p", { className: "small", children: e.description }),
      /* @__PURE__ */ l.jsxs("div", { className: "cm-value", children: [
        e.period + ": ",
        /* @__PURE__ */ l.jsx("b", { children: e.value }),
        e.bases && e.bases.length > 0 && /* @__PURE__ */ l.jsx("span", { className: "muted small", children: " (" + e.bases.map((c) => c.label + " " + c.value).join(" · ") + ")" })
      ] }),
      /* @__PURE__ */ l.jsx("small", { className: "muted", children: (e.origin === "cortex" ? "✦ " : "") + e.provenance }),
      e.governed && /* @__PURE__ */ l.jsxs("details", { className: "cm-gov", children: [/* @__PURE__ */ l.jsx("summary", { children: "Make it governed (for the data owner)" }), /* @__PURE__ */ l.jsx("pre", { children: e.governed })] }),
      /* @__PURE__ */ l.jsxs("div", { className: "cm-actions", children: [
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn primary", disabled: b, onClick: () => {
          sb(!0), y(""), sn(""), a(!1), t("metric_save", { selected: [...s] }, "Saving metric...");
        }, children: "Save and add" }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => t("metric_cancel", {}, "", !0), children: "Discard" })
      ] })
    ] })
  ] });
}
function bp({ cards: e, selected: t, onToggle: n, onClose: s, send: SND, preview: PV }) {
  const [r, i] = P.useState("All"), [a, u] = P.useState(""), o = a.trim().toLowerCase(), d = e.filter((p) => (r === "All" || p.theme === r) && (!o || `${p.label} ${p.definition}`.toLowerCase().includes(o))), m = ["All", ...Ni.filter((p) => e.some((v) => v.theme === p))];
  return /* @__PURE__ */ l.jsx("div", { className: "modal-back", onClick: s, children: /* @__PURE__ */ l.jsxs("div", { className: "modal picker", onClick: (p) => p.stopPropagation(), children: [
    /* @__PURE__ */ l.jsxs("div", { className: "picker-head", children: [
      /* @__PURE__ */ l.jsxs("div", { children: [
        /* @__PURE__ */ l.jsx("h3", { children: "Add or remove metrics" }),
        /* @__PURE__ */ l.jsxs("span", { className: "muted small", children: [
          e.length,
          " ",
          e.some((p) => p.origin === "cortex" || p.origin === "adhoc") ? "metrics drafted from the facts of" : "governed metrics in",
          " this semantic view · ",
          t.size,
          " on the dashboard"
        ] })
      ] }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "x", onClick: s, children: "×" })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "picker-tools", children: [
      /* @__PURE__ */ l.jsx("input", { autoFocus: !0, className: "search", placeholder: "Search metrics, e.g. shipping, stock, margin", value: a, onChange: (p) => u(p.target.value) }),
      /* @__PURE__ */ l.jsx("div", { className: "idea-tabs", children: m.map((p) => /* @__PURE__ */ l.jsx("button", { type: "button", className: `seg ${r === p ? "on" : ""}`, onClick: () => i(p), children: p }, p)) })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "picker-list", children: [
      d.map((p) => /* @__PURE__ */ l.jsxs("label", { className: `prow ${t.has(p.id) ? "on" : ""}`, children: [
        /* @__PURE__ */ l.jsx("input", { type: "checkbox", checked: t.has(p.id), onChange: () => n(p.id) }),
        /* @__PURE__ */ l.jsxs("span", { className: "prow-main", children: [
          /* @__PURE__ */ l.jsxs("b", { children: [
            p.label,
            p.recommended && /* @__PURE__ */ l.jsx("em", { className: "rec-dot", title: "Recommended by Cortex", children: "✦" }),
            p.origin === "custom" && /* @__PURE__ */ l.jsx("em", { className: "draft-tag cm-tag", title: p.why || "Custom metric (not governed)", children: "custom" })
          ] }),
          p.definition && /* @__PURE__ */ l.jsx("span", { children: p.definition }),
          p.why && /* @__PURE__ */ l.jsxs("span", { className: "prow-why", children: [
            "✦ ",
            p.why
          ] })
        ] }),
        /* @__PURE__ */ l.jsx("span", { className: "prow-theme", children: p.theme }),
        p.formula && /* @__PURE__ */ l.jsx("span", { className: "prow-f", title: p.formula, children: "ƒ" })
      ] }, p.id)),
      !d.length && /* @__PURE__ */ l.jsxs("div", { className: "empty", children: [
        'No metric matches "',
        a,
        '".'
      ] })
    ] }),
    SND && /* @__PURE__ */ l.jsx(Cmx, { send: SND, preview: PV, selected: t }),
    /* @__PURE__ */ l.jsx("div", { className: "modal-foot", children: /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", onClick: s, children: "Done" }) })
  ] }) });
}
function pd({ md: e, send: t }) {
  var s, r;
  const n = e.origin === "cortex";
  return /* @__PURE__ */ l.jsxs("section", { className: "rv2-block draft-banner", children: [
    /* @__PURE__ */ l.jsxs("div", { className: "db-head", children: [
      /* @__PURE__ */ l.jsxs("div", { children: [
        /* @__PURE__ */ l.jsxs("b", { children: [
          (s = e.view) == null ? void 0 : s.split(".").pop(),
          e.table ? ` · ${e.table}` : "",
          " defines no metrics, so ",
          n ? "Cortex" : "the app",
          " drafted ",
          e.count,
          " from its ",
          e.facts,
          " facts."
        ] }),
        /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
          n ? `Snowflake profiled ${e.profiled_facts || 0} facts (counts, distinct values, ranges) through the semantic view; Cortex chose an aggregation for each fact, added ratios and wrote definitions; the validator checked every one. Hover a metric for why.` : "Cortex was unavailable, so rules chose the aggregations from the data profile. Try re-drafting with Cortex.",
          e.saved_at ? ` Saved ${e.saved_at}${e.saved_by ? ` by ${e.saved_by}` : ""}, shared by everyone using this view.` : ""
        ] })
      ] }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small ghost-ai", onClick: () => t("metrics_redraft", {}, "Profiling the facts and drafting metrics with Cortex…"), children: "✦ Re-draft with Cortex" })
    ] }),
    ((r = e.notes) == null ? void 0 : r.length) > 0 && /* @__PURE__ */ l.jsxs("details", { children: [
      /* @__PURE__ */ l.jsxs("summary", { className: "prov", children: [
        "Validator: ",
        e.notes.length,
        " change",
        e.notes.length > 1 ? "s" : "",
        " to the draft"
      ] }),
      /* @__PURE__ */ l.jsx("ul", { className: "small sb-notes", children: e.notes.map((i, a) => /* @__PURE__ */ l.jsxs("li", { children: [
        /* @__PURE__ */ l.jsx("span", { className: `tag ${i.action === "dropped" ? "no" : "warn"}`, children: i.action }),
        " ",
        i.item,
        ": ",
        i.why
      ] }, a)) })
    ] }),
    /* @__PURE__ */ l.jsxs("details", { children: [
      /* @__PURE__ */ l.jsx("summary", { className: "prov", children: "Make them governed: METRICS clause for the view owner" }),
      /* @__PURE__ */ l.jsx("p", { className: "muted small", children: "The app queries these as ad-hoc metrics. To make them part of the semantic view, the owner adds this clause to its definition (CREATE OR REPLACE SEMANTIC VIEW … )." }),
      /* @__PURE__ */ l.jsx("pre", { className: "sql-log", children: e.ddl })
    ] })
  ] });
}
function Ep({ data: e, send: t, ctx: CTX }) {
  const n = e.draft, s = n.spec, r = n.cards || [], i = P.useMemo(() => Object.fromEntries(r.map((S) => [S.id, S])), [n]), a = () => {
    var S;
    return new Set((S = n.selected) != null && S.length ? n.selected : r.filter((A) => A.recommended).map((A) => A.id));
  }, u = () => s.pages.map((S) => ({ page_id: S.page_id, label: S.label, purpose: S.purpose, tiles: S.components.map((A) => A.component_id) })), [o, d] = P.useState(a), [m, p] = P.useState(u), [v, j] = P.useState(!1);
  P.useEffect(() => {
    d(a()), p(u());
  }, [n]);
  const y = P.useMemo(() => Object.fromEntries(s.pages.flatMap((S) => S.components.map((A) => [`${S.page_id}/${A.component_id}`, A]))), [n]), [B, W] = P.useState(!1), [ae, nt] = P.useState(0), C = (S) => d((A) => {
    const w = new Set(A);
    return w.has(S) ? w.delete(S) : w.add(S), w;
  }), k = (S) => S.metrics && S.metrics.length ? S.metrics.some((A) => o.has(A)) : br(S).every((A) => o.has(A)), c = m.map((S) => ({ ...S, comps: S.tiles.map((A) => y[`${S.page_id}/${A}`]).filter(Boolean) })), h = c.reduce((S, A) => S + A.comps.filter(k).length, 0), f = new Set(Object.values(y).flatMap(br)), x = [...o].filter((S) => !f.has(S)), N = [...o].map((S) => i[S]).filter(Boolean).sort((S, A) => Ni.indexOf(S.theme) - Ni.indexOf(A.theme)), g = (S, A) => p((w) => w.map((D, L) => L !== S ? D : { ...D, tiles: D.tiles.filter((V) => V !== A) })), M = (S) => {
    var A;
    return ((A = i[S]) == null ? void 0 : A.label) || (S || "").split(".").pop().replace(/_/g, " ").toLowerCase();
  }, E = () => {
    W(!0), t("build_draft", { metrics: [...o], outline: m.map((S) => ({ page_id: S.page_id, label: S.label, tiles: S.tiles })) }, "Building dashboard workspace...", !0);
  };
  P.useEffect(() => {
    if (!B)
      return nt(0);
    nt(0);
    const S = setInterval(() => nt((A) => Math.min(A + 1, 3)), 1350);
    return () => clearInterval(S);
  }, [B, n]), P.useEffect(() => {
    e.error && W(!1);
  }, [e.error]);
  if (B) {
    const S = Math.max(1, Math.min(4, ae + 1)), A = (w) => S > w ? "done" : S === w ? "now" : "wait", D = s.display_name || "your governed dashboard", L = `${o.size} metrics - ${m.length} pages - ${h} tiles`, V = S > 3 ? "Opening Step 3 dashboard..." : S > 2 ? "Rendering dashboard tiles..." : S > 1 ? "Running governed Snowflake queries..." : "Locking reviewed draft...";
    return /* @__PURE__ */ l.jsxs("section", { className: "view gen-view aa-generation-page review-build-page", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "gen-panel", children: [
        /* @__PURE__ */ l.jsx("div", { className: "gen-orb", children: /* @__PURE__ */ l.jsx(Sr, { size: 34 }) }),
        /* @__PURE__ */ l.jsx("div", { className: "gen-kicker", children: "BUILDING GOVERNED DASHBOARD" }),
        /* @__PURE__ */ l.jsx("h1", { children: "Building your dashboard" }),
        /* @__PURE__ */ l.jsx("p", { className: "gen-prompt", children: D }),
        /* @__PURE__ */ l.jsxs("div", { className: "gen-meta", children: [
          /* @__PURE__ */ l.jsx("span", { children: "Review approved" }),
          /* @__PURE__ */ l.jsx("span", { children: L }),
          /* @__PURE__ */ l.jsxs("b", { children: [
            "Step ",
            S,
            " of 4"
          ] })
        ] }),
        /* @__PURE__ */ l.jsx("div", { className: "gen-rail", children: /* @__PURE__ */ l.jsx("i", { className: `p${S}` }) }),
        /* @__PURE__ */ l.jsxs("ol", { className: "gen-steps", children: [
          /* @__PURE__ */ l.jsxs("li", { className: A(1), children: [
            /* @__PURE__ */ l.jsx("span", {}),
            /* @__PURE__ */ l.jsxs("div", { children: [
              /* @__PURE__ */ l.jsx("b", { children: "Lock reviewed plan" }),
              /* @__PURE__ */ l.jsx("small", { children: "Using the Step 2 metrics, pages and tile outline" })
            ] })
          ] }),
          /* @__PURE__ */ l.jsxs("li", { className: A(2), children: [
            /* @__PURE__ */ l.jsx("span", {}),
            /* @__PURE__ */ l.jsxs("div", { children: [
              /* @__PURE__ */ l.jsx("b", { children: "Run governed queries" }),
              /* @__PURE__ */ l.jsx("small", { children: "Applying semantic view filters, dates and joins" })
            ] })
          ] }),
          /* @__PURE__ */ l.jsxs("li", { className: A(3), children: [
            /* @__PURE__ */ l.jsx("span", {}),
            /* @__PURE__ */ l.jsxs("div", { children: [
              /* @__PURE__ */ l.jsx("b", { children: "Render dashboard workspace" }),
              /* @__PURE__ */ l.jsx("small", { children: "Composing KPI cards, drivers and decision sections" })
            ] })
          ] }),
          /* @__PURE__ */ l.jsxs("li", { className: A(4), children: [
            /* @__PURE__ */ l.jsx("span", {}),
            /* @__PURE__ */ l.jsxs("div", { children: [
              /* @__PURE__ */ l.jsx("b", { children: "Open Step 3" }),
              /* @__PURE__ */ l.jsx("small", { children: "Publishing the draft into the dashboard workspace" })
            ] })
          ] })
        ] }),
        /* @__PURE__ */ l.jsxs("div", { className: "gen-buffer", children: [
          /* @__PURE__ */ l.jsx("i", {}),
          /* @__PURE__ */ l.jsx("span", { children: V })
        ] })
      ] })
    ] });
  }
  return /* @__PURE__ */ l.jsxs("section", { className: "view review2", children: [
    /* @__PURE__ */ l.jsxs("header", { className: "rv2-head", children: [
      /* @__PURE__ */ l.jsxs("div", { children: [
        /* @__PURE__ */ l.jsx("div", { className: "eyebrow", children: "Step 2 of 3 · Review the draft" }),
        /* @__PURE__ */ l.jsx("h1", { children: s.display_name }),
        /* @__PURE__ */ l.jsx("p", { className: "muted", children: s.description })
      ] }),
      /* @__PURE__ */ l.jsx("div", { className: "rv2-meta", children: /* @__PURE__ */ l.jsx("span", { className: "pill ai", children: s.origin === "persona" ? `Reviewed layout · ✦ ${s.slot_origin === "cortex" ? "metrics chosen by Cortex" : "default metrics"}` : "✦ Drafted by Cortex" }) })
    ] }),
    e.metric_draft && /* @__PURE__ */ l.jsx(pd, { md: e.metric_draft, send: t }),
    /* @__PURE__ */ l.jsxs("section", { className: "rv2-block", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "rv2-title", children: [
        /* @__PURE__ */ l.jsxs("h3", { children: [
          "Metrics ",
          /* @__PURE__ */ l.jsx("span", { className: "count", children: o.size })
        ] }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => j(!0), children: "+ Add or remove metrics" })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "mchips", children: [
        N.map((S) => /* @__PURE__ */ l.jsxs("span", { className: "mchip", title: S.definition || "", children: [
          S.recommended && /* @__PURE__ */ l.jsx("em", { className: "rec-dot", title: "Recommended by Cortex", children: "✦" }),
          S.label,
          S.origin === "cortex" && /* @__PURE__ */ l.jsx("em", { className: "draft-tag", title: S.why || "Drafted by Cortex from the facts", children: "drafted" }),
          S.origin === "custom" && /* @__PURE__ */ l.jsx("em", { className: "draft-tag cm-tag", title: (S.why || "Custom metric") + (S.formula ? " \u00b7 = " + S.formula : ""), children: "custom" }),
          /* @__PURE__ */ l.jsx("button", { type: "button", "aria-label": `Remove ${S.label}`, onClick: () => C(S.id), children: "×" })
        ] }, S.id)),
        !N.length && /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "No metrics selected — add at least one." })
      ] }),
      x.length > 0 && /* @__PURE__ */ l.jsxs("div", { className: "rv2-note", children: [
        "New metrics (",
        x.map(M).join(", "),
        ") will appear as headline cards on page 1."
      ] })
    ] }),
    (s.layout_options || []).length > 1 && /* @__PURE__ */ l.jsxs("section", { className: "rv2-block lo-block", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "rv2-title", children: [
        /* @__PURE__ */ l.jsx("h3", { children: "Layout" }),
        /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "Reviewed layouts for this audience, filled with the same metrics. Switching makes no AI call." })
      ] }),
      /* @__PURE__ */ l.jsx("div", { className: "lo-grid", children: s.layout_options.map((LO) => /* @__PURE__ */ l.jsxs("button", { type: "button", className: `lo-card ${LO.id === s.layout_variant ? "on" : ""}`, onClick: () => LO.id !== s.layout_variant && t("switch_layout", { variant: LO.id, metrics: [...o] }, "Switching layout..."), children: [
        /* @__PURE__ */ l.jsxs("div", { className: "lo-top", children: [/* @__PURE__ */ l.jsx("b", { children: LO.title }), LO.id === s.layout_variant ? /* @__PURE__ */ l.jsx("em", { className: "lo-cur", children: "Current" }) : /* @__PURE__ */ l.jsx("span", { className: "lo-pages", children: `${LO.pages} page${LO.pages > 1 ? "s" : ""}` })] }),
        /* @__PURE__ */ l.jsx("div", { className: "lo-mini", children: LO.tiles.map((TT, ix) => /* @__PURE__ */ l.jsx("span", { className: "lo-t", style: { gridColumn: `span ${Math.max(2, Math.min(12, TT.span || 6))}` }, children: /* @__PURE__ */ l.jsx(Skx, { type: TT.type, mini: !0, n: TT.n }) }, ix)) }),
        /* @__PURE__ */ l.jsx("span", { className: "lo-sum", children: LO.summary })
      ] }, LO.id)) })
    ] }),
    /* @__PURE__ */ l.jsxs("section", { className: "rv2-block", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "rv2-title", children: [
        /* @__PURE__ */ l.jsxs("h3", { children: [
          "Layout preview ",
          /* @__PURE__ */ l.jsxs("span", { className: "count", children: [
            m.length,
            m.length === 1 ? " page · " : " pages · ",
            h,
            h === 1 ? " tile" : " tiles"
          ] })
        ] }),
        /* @__PURE__ */ l.jsxs("span", { className: "wf-tools", children: [
          /* @__PURE__ */ l.jsx("span", { className: "muted small", children: n.preview ? "Page 1 shows real data (forecasts and ML load after build) · × removes a tile" : "Sketches show each chart's shape · × removes a tile · rename pages inline" }),
          /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn ghost small", onClick: () => t("preview_draft", { metrics: [...o], outline: m.map((PG) => ({ page_id: PG.page_id, label: PG.label, tiles: PG.tiles })) }, "Running page 1 with real data..."), children: n.preview ? "Refresh data preview" : "Preview page 1 with data" })
        ] })
      ] }),
      /* @__PURE__ */ l.jsx("div", { className: "wf-pages", children: c.map((S, A) => /* @__PURE__ */ l.jsxs("div", { className: "wf-page", children: [
        /* @__PURE__ */ l.jsxs("div", { className: "wf-page-head", children: [
          /* @__PURE__ */ l.jsx("span", { className: "ol-num", children: A + 1 }),
          /* @__PURE__ */ l.jsx("input", { value: S.label, onChange: (w) => p((D) => D.map((L, V) => V === A ? { ...L, label: w.target.value } : L)) }),
          /* @__PURE__ */ l.jsxs("span", { className: "wf-acts", children: [
            /* @__PURE__ */ l.jsx("button", { type: "button", title: "Move left", disabled: A === 0, onClick: () => p((w) => {
              const D = [...w];
              return [D[A - 1], D[A]] = [D[A], D[A - 1]], D;
            }), children: "‹" }),
            /* @__PURE__ */ l.jsx("button", { type: "button", title: "Move right", disabled: A === m.length - 1, onClick: () => p((w) => {
              const D = [...w];
              return [D[A + 1], D[A]] = [D[A], D[A + 1]], D;
            }), children: "›" }),
            /* @__PURE__ */ l.jsx("button", { type: "button", title: "Remove page", disabled: m.length < 2, onClick: () => p((w) => w.filter((D, L) => L !== A)), children: "×" })
          ] })
        ] }),
        /* @__PURE__ */ l.jsx("div", { className: "wf-q", children: S.purpose }),
        /* @__PURE__ */ l.jsxs("div", { className: "wf-grid", children: [
          fd(S.comps).map((w) => {
            var q, F;
            const D = k(w), L = br(w).map(M), V = w.dimension ? w.dimension.split(".").pop().replace(/_/g, " ").toLowerCase() : "";
            return /* @__PURE__ */ l.jsxs(
              "div",
              {
                className: `wf-tile ${D ? "" : "gone"} ${w.type === "kpi_grid" ? "kpi" : ""}`,
                style: { gridColumn: `span ${w.span}` },
                title: `${w.title}
${((F = (q = e.tile_types) == null ? void 0 : q[w.type]) == null ? void 0 : F.label) || w.type}: ${L.join(", ")}${V ? ` by ${V}` : ""}${D ? "" : `
Will be removed: its metric is not selected`}`,
                children: (() => {
                  var Q, R2;
                  const PVd = n.preview, LR = PVd && PVd.page_id === S.page_id ? PVd.results[`${S.page_id}/${w.component_id}`] : null, LV = LR && LR.status === "ready" && yp[w.type], TL = ((R2 = (Q = e.tile_types) == null ? void 0 : Q[w.type]) == null ? void 0 : R2.label) || w.type.replace(/_/g, " ");
                  return [
                    /* @__PURE__ */ l.jsxs("div", { className: "wf-head", children: [
                      /* @__PURE__ */ l.jsx("span", { className: "wf-name", children: [w.focus ? /* @__PURE__ */ l.jsx("em", { className: "wf-ask", children: "Your question" }) : null, w.title] }),
                      /* @__PURE__ */ l.jsx("span", { className: "wf-type", children: TL })
                    ] }, "h"),
                    LV ? /* @__PURE__ */ l.jsx("div", { className: "wf-live", children: /* @__PURE__ */ l.jsx(LV, { data: LR.data, ctx: CTX || {}, spec: { ...((PVd.comps || {})[w.component_id] || w), span: w.span } }) }, "l")
                      : /* @__PURE__ */ l.jsx("div", { className: "wf-sketch", children: /* @__PURE__ */ l.jsx(Skx, { type: w.type, n: (w.metrics || []).length }) }, "s"),
                    !LV && /* @__PURE__ */ l.jsxs("div", { className: "wf-foot", children: [
                      (w.title || "").toLowerCase().includes(String(L[0] || "~").toLowerCase()) ? null : /* @__PURE__ */ l.jsx("span", { children: L.join(", ") + (V ? ` by ${V}` : "") }),
                      w.question ? /* @__PURE__ */ l.jsx("span", { className: "wf-qq", children: w.question }) : null
                    ] }, "f"),
                    /* @__PURE__ */ l.jsx("button", { type: "button", className: "wf-x", "aria-label": "Remove tile", onClick: () => g(A, w.component_id), children: "×" }, "x")
                  ];
                })()
              },
              w.component_id
            );
          }),
          !S.comps.length && /* @__PURE__ */ l.jsx("div", { className: "wf-empty", children: "Empty page" })
        ] })
      ] }, S.page_id)) })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "review-bar", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost", onClick: () => t("go", { step: "home" }, "Opening…"), children: "← Back" }),
      /* @__PURE__ */ l.jsxs("span", { className: "muted small", children: [
        o.size,
        " metrics · ",
        m.length,
        m.length === 1 ? " page · " : " pages · ",
        h,
        h === 1 ? " tile" : " tiles"
      ] }),
      /* @__PURE__ */ l.jsxs("span", { className: "review-actions", children: [
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn ghost-ai", onClick: () => t("redraft", { metrics: [...o], added: x }, "Cortex is redesigning around your metrics…"), children: "✦ Redesign" }),
        /* @__PURE__ */ l.jsx(
          "button",
          {
            type: "button",
            className: "btn",
            disabled: !h && !x.length,
            onClick: E,
            children: "Build dashboard →"
          }
        )
      ] })
    ] }),
    v && /* @__PURE__ */ l.jsx(bp, { cards: r, selected: o, onToggle: C, onClose: () => j(!1), send: t, preview: n.metric_preview })
  ] });
}
const rs = [
  "trend_chart",
  "forecast_band",
  "ranked_bar",
  "period_compare",
  "share_donut",
  "pareto",
  "scatter",
  "heatmap",
  "small_multiples",
  "driver_bridge",
  "exception_table",
  "treemap"
], Mp = [["", "Audience default"], ["month", "Monthly"], ["week", "Weekly"], ["day", "Daily"], ["quarter", "Quarterly"]], Lp = [["prior", "Previous period"], ["yoy", "Same period last year"], ["plan", "Plan / target"]];
function Ap({ data: e, send: t, pageId: n }) {
  var u;
  const s = e.view || {}, r = ((u = e.profile) == null ? void 0 : u.calendar) || {}, i = (o) => t("set_view", { ...o, page_id: n }, "Re-running governed queries…"), a = s.filters || {};
  return /* @__PURE__ */ l.jsxs("div", { className: "viewbar", children: [
    /* @__PURE__ */ l.jsxs("div", { className: "vb-chips", role: "group", "aria-label": "Period", children: [
      /* @__PURE__ */ l.jsx("span", { className: "vb-lbl", children: "Period" }),
      [["", "Auto"], ["day", "Day"], ["week", "Week"], ["month", "Month"], ["quarter", "Quarter"]].map(([o, d]) => /* @__PURE__ */ l.jsx("button", { type: "button", className: (s.grain || "") === o ? "on" : "", onClick: () => (s.grain || "") !== o && i({ grain: o || null }), children: d }, o || "auto"))
    ] }),
    /* @__PURE__ */ l.jsxs("span", { className: "vb-now", title: `Latest complete ${r.grain}; data through ${r.max_date}`, children: [
      "Showing ",
      /* @__PURE__ */ l.jsx("b", { children: r.current_label })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "vb-chips", role: "group", "aria-label": "Compare to", children: [
      /* @__PURE__ */ l.jsx("span", { className: "vb-lbl", children: "Compare" }),
      [["prior", "Prior period"], ["yoy", "Last year"], ["plan", "Plan"]].map(([o, d]) => /* @__PURE__ */ l.jsx("button", { type: "button", className: (s.compare || "prior") === o ? "on" : "", onClick: () => (s.compare || "prior") !== o && i({ compare: o }), children: d }, o))
    ] }),
    (e.filter_dims || []).map((o) => {
      var d;
      return /* @__PURE__ */ l.jsxs("label", { className: "vb-item", children: [
        /* @__PURE__ */ l.jsx("span", { children: o.label }),
        /* @__PURE__ */ l.jsxs(
          "select",
          {
            value: (a[o.id] || [])[0] || "",
            onChange: (m) => i({ filters: { ...a, [o.id]: m.target.value ? [m.target.value] : [] } }),
            children: [
              /* @__PURE__ */ l.jsx("option", { value: "", children: "All" }),
              (((d = e.filter_options) == null ? void 0 : d[o.id]) || []).map((m) => /* @__PURE__ */ l.jsx("option", { value: m, children: m }, m))
            ]
          }
        )
      ] }, o.id);
    }),
    Object.entries(a).filter(([o, d]) => (d == null ? void 0 : d.length) && !(e.filter_dims || []).some((m) => m.id === o)).map(([o, d]) => /* @__PURE__ */ l.jsxs("span", { className: "fchip", children: [
      $e(o),
      ": ",
      /* @__PURE__ */ l.jsx("b", { children: d.join(", ") }),
      /* @__PURE__ */ l.jsx("button", { type: "button", title: "Remove", onClick: () => {
        const m = { ...a };
        delete m[o], i({ filters: m });
      }, children: "×" })
    ] }, o)),
    Object.keys(a).length > 0 && /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => i({ filters: {} }), children: "Clear filters" }),
    /* @__PURE__ */ l.jsxs("span", { className: "vb-live", children: [
      /* @__PURE__ */ l.jsx("i", {}),
      " Live · data through ",
      r.max_date
    ] })
  ] });
}
const Pp = 5 * 60 * 1e3;
function zp({ persona: e, data: t, onRefresh: n, auto: s, setAuto: r, refreshedAt: i }) {
  var u;
  const a = ((u = t.profile) == null ? void 0 : u.calendar) || {};
  return e === "daily_operations" ? /* @__PURE__ */ l.jsxs("div", { className: "pstrip live", children: [
    /* @__PURE__ */ l.jsxs("span", { children: [
      /* @__PURE__ */ l.jsx("i", { className: "pulse" }),
      " ",
      /* @__PURE__ */ l.jsx("b", { children: "Live" }),
      " · today ",
      a.max_date,
      " · compared with the same weekday last week, same hours"
    ] }),
    /* @__PURE__ */ l.jsxs("span", { className: "pstrip-r", children: [
      "Refreshed ",
      i,
      /* @__PURE__ */ l.jsxs("label", { className: "auto", children: [
        /* @__PURE__ */ l.jsx("input", { type: "checkbox", checked: s, onChange: (o) => r(o.target.checked) }),
        " auto-refresh every 5 min"
      ] }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: n, children: "Refresh now" })
    ] })
  ] }) : e === "executives" ? null : false ? /* @__PURE__ */ l.jsxs("div", { className: "pstrip", children: [
    /* @__PURE__ */ l.jsxs("span", { children: [
      /* @__PURE__ */ l.jsx("b", { children: "" }),
      " · year to date through ",
      a.current_label,
      " · against plan, and last year where there is no plan"
    ] }),
    /* @__PURE__ */ l.jsxs("span", { className: "pstrip-r", children: [
      "Data as of ",
      a.max_date
    ] })
  ] }) : e === "managers" ? /* @__PURE__ */ l.jsxs("div", { className: "pstrip", children: [
    /* @__PURE__ */ l.jsxs("span", { children: [
      /* @__PURE__ */ l.jsx("b", { children: "Weekly scorecard" }),
      " · ",
      a.current_label,
      " vs plan (or the prior week) · click a scorecard row to drill in"
    ] }),
    /* @__PURE__ */ l.jsxs("span", { className: "pstrip-r", children: [
      "Data as of ",
      a.max_date
    ] })
  ] }) : null;
}
function md(e) {
  var o, d, m;
  const t = ((o = e.model) == null ? void 0 : o.metric_dims) || {}, n = ((d = e.model) == null ? void 0 : d.metrics) || [], s = (((m = e.model) == null ? void 0 : m.dimensions) || []).filter((p) => !p.is_time), r = e.distinct || {};
  return { okDims: (p, v, j = "dim") => {
    var k, c;
    const y = (p || []).filter((h) => h && t[h]), C = (c = (k = e.tile_types) == null ? void 0 : k[v]) == null ? void 0 : c[j === "dim2" ? "dim2_range" : "dim_range"];
    return s.filter((h) => y.every((f) => t[f].includes(h.id)) && (!C || r[h.id] == null || r[h.id] >= C[0] && r[h.id] <= C[1]));
  }, okMetrics: (p, v) => {
    var C, k;
    const j = (p || []).filter(Boolean), y = (k = (C = e.tile_types) == null ? void 0 : C[v]) == null ? void 0 : k.additive;
    return n.filter((c) => (!t[c.id] || j.every((h) => t[c.id].includes(h))) && (!y || c.additive));
  }, allMetrics: n, allDims: s, label: (p, v) => {
    var j;
    return ((j = p.find((y) => y.id === v)) == null ? void 0 : j.label) || (v || "").split(".").pop().replace(/_/g, " ").toLowerCase();
  }, distinct: r };
}
function Yl(e, t, n) {
  return !t || e.some((s) => s.id === t) ? e : [n.find((s) => s.id === t) || { id: t, label: t }, ...e];
}
function Tp({ c: e, page: t, data: n, send: s, onClose: r }) {
  var c, h, f, x, N;
  const i = md(n), a = e.dimension || ((c = e.role_bindings) == null ? void 0 : c.segment) || ((h = e.role_bindings) == null ? void 0 : h.region) || "", u = (g) => {
    s("tile_update", { page_id: t.page_id, component_id: e.component_id, patch: g }, "Validating & re-querying…"), r();
  }, o = e.metrics || [(f = n.bindings) == null ? void 0 : f.primary_metric, ...((x = n.bindings) == null ? void 0 : x.supporting_metrics) || []].filter(Boolean), d = (((N = n.spec) == null ? void 0 : N.governance) || []).filter((g) => g.tile === e.title).slice(-2), m = (g) => {
    var M;
    return ((M = i.distinct) == null ? void 0 : M[g]) != null ? ` (${i.distinct[g]})` : "";
  }, p = ["kpi_grid", "kpi_card"].includes(e.type), v = Yl(i.okMetrics([a, e.dimension2], e.type), e.metric_id, i.allMetrics), j = Yl(i.okMetrics([a], e.type).filter((g) => g.id !== e.metric_id), e.metric2_id, i.allMetrics), y = Yl(i.okDims([e.metric_id, e.metric2_id], e.type), a, i.allDims), C = Yl(i.okDims([e.metric_id], e.type, "dim2").filter((g) => g.id !== a), e.dimension2, i.allDims), k = i.allDims.length - i.okDims([e.metric_id, e.metric2_id], e.type).length;
  return /* @__PURE__ */ l.jsxs("div", { className: "tmenu", onMouseLeave: r, children: [
    rs.includes(e.type) && /* @__PURE__ */ l.jsxs("label", { children: [
      "Chart type",
      /* @__PURE__ */ l.jsx("select", { value: e.type, onChange: (g) => u({ type: g.target.value }), children: rs.map((g) => {
        var M, S;
        return /* @__PURE__ */ l.jsx("option", { value: g, children: ((S = (M = n.tile_types) == null ? void 0 : M[g]) == null ? void 0 : S.label) || g }, g);
      }) })
    ] }),
    e.metric_id && !p && /* @__PURE__ */ l.jsxs("label", { children: [
      e.type === "scatter" ? "Metric (x axis)" : "Metric",
      /* @__PURE__ */ l.jsx("select", { value: e.metric_id, onChange: (g) => u({ metric_id: g.target.value }), children: v.map((g) => /* @__PURE__ */ l.jsx("option", { value: g.id, children: g.label }, g.id)) })
    ] }),
    e.type === "combo_chart" && /* @__PURE__ */ l.jsxs("label", { children: [
      "Line metric",
      /* @__PURE__ */ l.jsx("select", { value: e.metric2_id || "", onChange: (g) => u({ metric2_id: g.target.value }), children: Yl(i.allMetrics.filter((g) => g.id !== e.metric_id), e.metric2_id, i.allMetrics).map((g) => /* @__PURE__ */ l.jsx("option", { value: g.id, children: g.label }, g.id)) })
    ] }),
    e.type === "treemap" && /* @__PURE__ */ l.jsxs("label", { children: [
      "Inside each box",
      /* @__PURE__ */ l.jsxs("select", { value: e.dimension2 || "", onChange: (g) => u({ dimension2: g.target.value || null }), children: [/* @__PURE__ */ l.jsx("option", { value: "", children: "Nothing (one level)" }), ...C.map((g) => /* @__PURE__ */ l.jsxs("option", { value: g.id, children: [g.label, m(g.id)] }, g.id))] })
    ] }),
    e.type === "scatter" && /* @__PURE__ */ l.jsxs("label", { children: [
      "Metric (y axis)",
      /* @__PURE__ */ l.jsx("select", { value: e.metric2_id || "", onChange: (g) => u({ metric2_id: g.target.value }), children: j.map((g) => /* @__PURE__ */ l.jsx("option", { value: g.id, children: g.label }, g.id)) })
    ] }),
    a && rs.includes(e.type) && !["trend_chart", "forecast_band"].includes(e.type) && /* @__PURE__ */ l.jsxs("label", { children: [
      e.type === "heatmap" ? "Rows" : e.type === "scatter" ? "One point per" : e.type === "treemap" ? "Boxes" : "Break down by",
      /* @__PURE__ */ l.jsx("select", { value: a, onChange: (g) => u({ dimension: g.target.value }), children: y.map((g) => /* @__PURE__ */ l.jsxs("option", { value: g.id, children: [
        g.label,
        m(g.id)
      ] }, g.id)) })
    ] }),
    e.type === "heatmap" && /* @__PURE__ */ l.jsxs("label", { children: [
      "Columns",
      /* @__PURE__ */ l.jsx("select", { value: e.dimension2 || "", onChange: (g) => u({ dimension2: g.target.value }), children: C.map((g) => /* @__PURE__ */ l.jsxs("option", { value: g.id, children: [
        g.label,
        m(g.id)
      ] }, g.id)) })
    ] }),
    k > 0 && !p && a && /* @__PURE__ */ l.jsxs("div", { className: "muted small tmenu-note", children: [
      k,
      " breakdown",
      k > 1 ? "s" : "",
      " hidden: not related to this metric in the semantic view, or too many/few values for this chart."
    ] }),
    e.type === "pnl_table" && /* @__PURE__ */ l.jsxs("label", { children: [
      "Columns",
      /* @__PURE__ */ l.jsx("select", { value: e.dimension || "", onChange: (g) => u({ dimension: g.target.value }), children: Yl(i.okDims(e.metrics || [], e.type), e.dimension, i.allDims).map((g) => /* @__PURE__ */ l.jsxs("option", { value: g.id, children: [g.label, m(g.id)] }, g.id)) })
    ] }),
    ["kpi_grid", "kpi_card", "detail_table", "evidence_table", "pnl_table"].includes(e.type) && /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
      /* @__PURE__ */ l.jsxs("label", { children: [
        "Add metric",
        /* @__PURE__ */ l.jsxs("select", { value: "", onChange: (g) => g.target.value && u({ metrics: [...o, g.target.value], type: e.type === "kpi_card" ? "kpi_grid" : e.type === "evidence_table" ? "detail_table" : e.type }), children: [
          /* @__PURE__ */ l.jsx("option", { value: "", children: "Choose…" }),
          i.okMetrics(e.type === "detail_table" ? e.dimensions || [] : e.type === "pnl_table" ? [e.dimension] : [], e.type).filter((g) => !o.includes(g.id)).map((g) => /* @__PURE__ */ l.jsx("option", { value: g.id, children: g.label }, g.id))
        ] })
      ] }),
      o.length > 1 && /* @__PURE__ */ l.jsxs("label", { children: [
        "Remove metric",
        /* @__PURE__ */ l.jsxs("select", { value: "", onChange: (g) => g.target.value && u({ metrics: o.filter((M) => M !== g.target.value), type: e.type === "kpi_card" ? "kpi_grid" : e.type === "evidence_table" ? "detail_table" : e.type }), children: [
          /* @__PURE__ */ l.jsx("option", { value: "", children: "Choose…" }),
          o.map((g) => /* @__PURE__ */ l.jsx("option", { value: g, children: i.label(i.allMetrics, g) }, g))
        ] })
      ] })
    ] }),
    e.type === "kpi_plan" && /* @__PURE__ */ l.jsxs("label", { children: [
      "Show as",
      /* @__PURE__ */ l.jsx("select", { value: e.display || "bullet", onChange: (g) => u({ display: g.target.value }), children: hd.map(([g, M]) => /* @__PURE__ */ l.jsx("option", { value: g, children: M }, g)) })
    ] }),
    p && /* @__PURE__ */ l.jsxs("label", { className: "tmenu-check", children: [
      /* @__PURE__ */ l.jsx(
        "input",
        {
          type: "checkbox",
          checked: e.show_trend !== !1,
          onChange: (g) => u({ show_trend: g.target.checked })
        }
      ),
      " Trend line under each card"
    ] }),
    /* @__PURE__ */ l.jsxs("label", { children: [
      "Width",
      /* @__PURE__ */ l.jsx("select", { value: e.width || e.span, onChange: (g) => u({ width: Number(g.target.value) }), children: (p || ["heatmap", "detail_table"].includes(e.type) ? [6, 7, 8, 9, 12] : [3, 4, 5, 6, 7, 8, 9, 12]).map((g) => /* @__PURE__ */ l.jsx("option", { value: g, children: g === 12 ? "Full width" : `${g}/12` }, g)) })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "tmenu-row", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => {
        s("tile_move", { page_id: t.page_id, component_id: e.component_id, dir: -1 }, "Moving…"), r();
      }, children: "← Move" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => {
        s("tile_move", { page_id: t.page_id, component_id: e.component_id, dir: 1 }, "Moving…"), r();
      }, children: "Move →" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small danger-txt", onClick: () => {
        s("tile_remove", { page_id: t.page_id, component_id: e.component_id }, "Removing…"), r();
      }, children: "Remove" })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "tmenu-why", children: [
      /* @__PURE__ */ l.jsx("b", { children: "Why this chart?" }),
      /* @__PURE__ */ l.jsx("div", { children: e.question || "Answers the page question for this metric." }),
      d.map((g, M) => /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
        "Validator: ",
        g.action,
        " — ",
        g.reason
      ] }, M))
    ] })
  ] });
}
function Rp({ page: e, data: t, send: n, onClose: s }) {
  var S, A;
  const r = md(t), [i, a] = P.useState("describe"), [u, o] = P.useState(""), [d, m] = P.useState("ranked_bar"), [p, v] = P.useState(((S = t.bindings) == null ? void 0 : S.primary_metric) || ""), [j, y] = P.useState(""), [C, k] = P.useState(((A = t.bindings) == null ? void 0 : A.segment_dimension) || ""), [c, h] = P.useState(""), f = !["trend_chart", "forecast_band", "kpi_grid", "kpi_plan", "status_tiles", "ytd_trajectory", "pace_chart", "hour_heatmap", "combo_chart", "gauge"].includes(d), x = r.okMetrics([], d), N = r.okDims([p, d === "scatter" ? j : null], d), g = r.okMetrics([], d).filter((w) => w.id !== p), M = r.okDims([p], d, "dim2").filter((w) => w.id !== C);
  return P.useEffect(() => {
    x.length && !x.some((w) => w.id === p) && v(x[0].id);
  }, [d]), P.useEffect(() => {
    f && N.length && !N.some((w) => w.id === C) && k(N[0].id);
  }, [d, p, j]), P.useEffect(() => {
    (d === "scatter" || d === "combo_chart") && (!j || j === p || d === "combo_chart") && g.length && y((d === "combo_chart" && g.find((w) => /RATIO|RATE|PCT|PERCENT|MARGIN|SHARE/i.test(w.id.split(".").pop())) || g[0]).id);
  }, [d, p]), P.useEffect(() => {
    d === "heatmap" && (!c || c === C) && M.length && h(M[0].id);
  }, [d, p, C]), /* @__PURE__ */ l.jsxs("div", { className: "addtile", children: [
    /* @__PURE__ */ l.jsxs("div", { className: "idea-tabs", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: `seg ${i === "describe" ? "on" : ""}`, onClick: () => a("describe"), children: "✦ Describe it" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: `seg ${i === "pick" ? "on" : ""}`, onClick: () => a("pick"), children: "Pick chart & fields" })
    ] }),
    i === "describe" ? /* @__PURE__ */ l.jsxs("div", { className: "addtile-row", children: [
      /* @__PURE__ */ l.jsx(
        "input",
        {
          autoFocus: !0,
          placeholder: "e.g. free shipping % by region vs last year",
          value: u,
          onChange: (w) => o(w.target.value),
          onKeyDown: (w) => {
            w.key === "Enter" && u.trim() && (n("tile_add", { page_id: e.page_id, instruction: u }, "Cortex is designing the tile…"), s());
          }
        }
      ),
      /* @__PURE__ */ l.jsx(
        "button",
        {
          type: "button",
          className: "btn small ghost-ai",
          disabled: !u.trim(),
          onClick: () => {
            n("tile_add", { page_id: e.page_id, instruction: u }, "Cortex is designing the tile…"), s();
          },
          children: "Add"
        }
      )
    ] }) : /* @__PURE__ */ l.jsxs("div", { className: "addtile-row wrap", children: [
      /* @__PURE__ */ l.jsx("select", { value: d, onChange: (w) => m(w.target.value), children: ["kpi_grid", ...rs, "combo_chart", "gauge", "pnl_table", "detail_table", "kpi_plan", "ytd_trajectory", "scorecard", "status_tiles", "pace_chart", "hour_heatmap", "worklist"].filter((w) => {
        var D;
        return (D = t.tile_types) == null ? void 0 : D[w];
      }).map((w) => {
        var D, L;
        return /* @__PURE__ */ l.jsx("option", { value: w, children: ((L = (D = t.tile_types) == null ? void 0 : D[w]) == null ? void 0 : L.label) || w }, w);
      }) }),
      /* @__PURE__ */ l.jsx("select", { value: p, onChange: (w) => v(w.target.value), children: x.map((w) => /* @__PURE__ */ l.jsx("option", { value: w.id, children: w.label }, w.id)) }),
      (d === "scatter" || d === "combo_chart") && /* @__PURE__ */ l.jsx("select", { value: j, onChange: (w) => y(w.target.value), children: g.map((w) => /* @__PURE__ */ l.jsxs("option", { value: w.id, children: [
        d === "combo_chart" ? "line: " : "vs ",
        w.label
      ] }, w.id)) }),
      f && /* @__PURE__ */ l.jsx("select", { value: C, onChange: (w) => k(w.target.value), children: N.map((w) => /* @__PURE__ */ l.jsxs("option", { value: w.id, children: [
        "by ",
        w.label
      ] }, w.id)) }),
      d === "heatmap" && /* @__PURE__ */ l.jsx("select", { value: c, onChange: (w) => h(w.target.value), children: M.map((w) => /* @__PURE__ */ l.jsxs("option", { value: w.id, children: [
        "× ",
        w.label
      ] }, w.id)) }),
      d === "treemap" && /* @__PURE__ */ l.jsxs("select", { value: c === C ? "" : c, onChange: (w) => h(w.target.value), children: [/* @__PURE__ */ l.jsx("option", { value: "", children: "one level" }), ...M.filter((w) => w.id !== C).map((w) => /* @__PURE__ */ l.jsxs("option", { value: w.id, children: ["› ", w.label] }, w.id))] }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", disabled: f && !N.length, onClick: () => {
        n("tile_add_manual", {
          page_id: e.page_id,
          type: d,
          metric: p,
          metric2: d === "scatter" || d === "combo_chart" ? j : null,
          metrics: d === "pnl_table" ? [p, ...(((A = t.bindings) == null ? void 0 : A.supporting_metrics) || [])].filter((w, I, Z) => w && Z.indexOf(w) === I) : [p],
          dimension: f ? C : null,
          dimension2: d === "heatmap" ? c : d === "treemap" && c && c !== C ? c : null,
          dimensions: [C]
        }, "Validating & querying…"), s();
      }, children: "Add" })
    ] }),
    i === "pick" && f && !N.length && /* @__PURE__ */ l.jsx("div", { className: "muted small", children: "No breakdown in the semantic view works with this metric and chart; pick another metric or chart." }),
    /* @__PURE__ */ l.jsx("div", { className: "muted small", children: "Lists only show combinations the semantic view supports. Every new tile still goes through the validator." })
  ] });
}
function Fp({ tile: e, page: t, data: n, send: s, pending: r, onClose: i, viewer: a }) {
  var g, M, S, A, w, D;
  const [u, o] = P.useState(""), [d, m] = P.useState("auto"), p = P.useRef(null), tpRoot = P.useRef(null), v = `${t.page_id}/${e.component_id}`, j = ((g = n.tile_chat) == null ? void 0 : g[v]) || [];
  P.useEffect(() => {
    const R = tpRoot.current;
    R && R.scrollIntoView && R.scrollIntoView({ block: "start" });
  }, [e.component_id]);
  P.useEffect(() => {
    const C = p.current && p.current.parentElement;   // scroll the chat box only, never the page
    const M = C && ([...C.querySelectorAll(".msg.user")].pop() || [...C.querySelectorAll(".msg")].pop());  // newest question, answer below it
    if (C && M) C.scrollTop += M.getBoundingClientRect().top - C.getBoundingClientRect().top - 8;
  }, [j.length, r]);
  const y = (L) => {
    var V, q, F;
    return ((F = (q = (V = n.model) == null ? void 0 : V.metrics) == null ? void 0 : q.find((U) => U.id === L)) == null ? void 0 : F.label) || (L || "").split(".").pop();
  }, C = (L) => {
    var V, q, F;
    return ((F = (q = (V = n.model) == null ? void 0 : V.dimensions) == null ? void 0 : q.find((U) => U.id === L)) == null ? void 0 : F.label) || (L || "").split(".").pop();
  }, k = ((M = n.profile) == null ? void 0 : M.calendar) || {}, c = y(e.metric_id || (e.metrics || [])[0]), h = (A = (((S = n.model) == null ? void 0 : S.dimensions) || []).find((L) => !L.is_time && L.id !== e.dimension)) == null ? void 0 : A.label, f = [
    ["ask", `Why did ${c} change in ${k.current_label} vs ${k.prior_label}?`],
    e.dimension && ["ask", `Which ${C(e.dimension)} drove most of the change in ${c}?`],
    ["ask", `What should I do about this ${c} result?`],
    !a && e.type !== "trend_chart" && ["edit", "Show this as a line chart over time"],
    !a && h && e.dimension && ["edit", `Split this by ${h}`]
  ].filter(Boolean), x = (L, V) => {
    L.trim() && (s(
      "tile_ask",
      { page_id: t.page_id, component_id: e.component_id, text: L, mode: V === "auto" ? void 0 : V },
      V === "edit" ? "Cortex is changing the tile…" : "Cortex Agent is answering…",
      !0
    ), o(""));
  }, N = (r == null ? void 0 : r.type) === "tile_ask";
  return /* @__PURE__ */ l.jsxs("div", { className: "tpanel", ref: tpRoot, children: [
    /* @__PURE__ */ l.jsxs("div", { className: "tpanel-head", children: [
      /* @__PURE__ */ l.jsxs("div", { children: [
        /* @__PURE__ */ l.jsx("div", { className: "ai-title", children: "✦ Tile assistant" }),
        /* @__PURE__ */ l.jsx("b", { children: e.title }),
        /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
          ((D = (w = n.tile_types) == null ? void 0 : w[e.type]) == null ? void 0 : D.label) || e.type,
          " · ",
          c,
          e.dimension ? ` by ${C(e.dimension)}` : "",
          " · ",
          k.current_label
        ] })
      ] }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "x", onClick: i, children: "×" })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "tpanel-sub", children: [
      "Questions go to the ",
      /* @__PURE__ */ l.jsx("b", { children: "Cortex Agent" }),
      " (governed SQL on this semantic view, with this tile's context).",
      !a && /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
        " Change requests go to ",
        /* @__PURE__ */ l.jsx("b", { children: "Cortex" }),
        " and through the layout validator."
      ] })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "tchat", children: [
      !j.length && /* @__PURE__ */ l.jsx("div", { className: "tsuggest", children: f.map(([L, V]) => /* @__PURE__ */ l.jsxs("button", { type: "button", className: `chip ${L}`, onClick: () => x(V, L), children: [
        L === "edit" ? "✎ " : "? ",
        V
      ] }, V)) }),
      j.map((L, V) => {
        var q, F, U, _;
        return /* @__PURE__ */ l.jsx("div", { className: `msg ${L.role}`, children: /* @__PURE__ */ l.jsxs("div", { className: "bubble", children: [
          L.error ? /* @__PURE__ */ l.jsx("div", { className: "alert error small", children: L.error }) : /* @__PURE__ */ l.jsx("div", { className: "answer", children: L.text }),
          (q = L.tables) == null ? void 0 : q.map((E, T) => /* @__PURE__ */ l.jsxs("table", { className: "table compact", children: [
            /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsx("tr", { children: E.columns.map((b) => /* @__PURE__ */ l.jsx("th", { children: b }, b)) }) }),
            /* @__PURE__ */ l.jsx("tbody", { children: E.rows.slice(0, 8).map((b, B) => /* @__PURE__ */ l.jsx("tr", { children: b.map((W, ae) => /* @__PURE__ */ l.jsx("td", { children: String(W) }, ae)) }, B)) })
          ] }, T)),
          (F = L.actions) == null ? void 0 : F.map((E) => /* @__PURE__ */ l.jsxs("div", { className: "act-card", children: [
            "✓ Agent logged decision ",
            /* @__PURE__ */ l.jsx("b", { children: E.id })
          ] }, E.id)),
          ((U = L.citations) == null ? void 0 : U.length) > 0 && /* @__PURE__ */ l.jsxs("div", { className: "cites", children: [
            /* @__PURE__ */ l.jsx("span", { children: "Sources" }),
            L.citations.map((E, T) => /* @__PURE__ */ l.jsx("span", { className: "cite", title: E.text, children: E.label }, T))
          ] }),
          ((_ = L.sql) == null ? void 0 : _.length) > 0 && /* @__PURE__ */ l.jsxs("details", { children: [
            /* @__PURE__ */ l.jsx("summary", { className: "prov", children: "SQL generated by Cortex Analyst" }),
            /* @__PURE__ */ l.jsx("pre", { children: L.sql[0] })
          ] }),
          (L.provenance || L.agent) && /* @__PURE__ */ l.jsxs("div", { className: "prov", children: [
            L.provenance || L.agent,
            L.latency ? ` · ${L.latency}s` : ""
          ] })
        ] }) }, V);
      }),
      N && /* @__PURE__ */ l.jsx("div", { className: "msg agent", children: /* @__PURE__ */ l.jsx("div", { className: "bubble typing", children: r.label }) }),
      /* @__PURE__ */ l.jsx("div", { ref: p })
    ] }),
    /* @__PURE__ */ l.jsxs("form", { className: "task", onSubmit: (L) => {
      L.preventDefault(), x(u, d);
    }, children: [
      !a && /* @__PURE__ */ l.jsx("div", { className: "idea-tabs", children: [["auto", "Auto"], ["ask", "Ask"], ["edit", "Change tile"]].map(([L, V]) => /* @__PURE__ */ l.jsx("button", { type: "button", className: `seg ${d === L ? "on" : ""}`, onClick: () => m(L), children: V }, L)) }),
      /* @__PURE__ */ l.jsxs("div", { className: "addtile-row", children: [
        /* @__PURE__ */ l.jsx(
          "textarea",
          {
            rows: 2,
            value: u,
            onChange: (L) => o(L.target.value),
            disabled: N,
            onKeyDown: (L) => {
              L.key === "Enter" && !L.shiftKey && (L.preventDefault(), x(u, d));
            },
            placeholder: a ? "Ask about this tile…" : "Ask about this tile, or request a change…",
            onKeyDown: (L) => {
              L.key === "Enter" && !L.shiftKey && (L.preventDefault(), x(u, a ? "ask" : d));
            }
          }
        ),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "send", disabled: N || !u.trim(), onClick: () => x(u, a ? "ask" : d), children: "↑" })
      ] })
    ] })
  ] });
}
function Op({ data: e, send: t, name: n, onClose: s }) {
  var y, C, k;
  const [r, i] = P.useState(n), [a, u] = P.useState([]), [o, d] = P.useState(""), [m, p] = P.useState("");
  P.useEffect(() => {
    var c;
    (c = e.roles) != null && c.length || t("list_roles", {}, "Loading roles…", !0);
  }, []);
  const v = e.share, j = (c) => u((h) => h.includes(c) ? h.filter((f) => f !== c) : [...h, c]);
  return /* @__PURE__ */ l.jsx("div", { className: "modal-back", children: /* @__PURE__ */ l.jsx("div", { className: "modal publish", children: v && v.name === r ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsxs("h3", { children: [
      '✓ Published "',
      v.name,
      '" v',
      v.version
    ] }),
    /* @__PURE__ */ l.jsx("p", { children: "Viewers get a read-only dashboard: no builder controls, same live governed numbers, filters, tooltips and the tile assistant (questions only)." }),
    /* @__PURE__ */ l.jsxs("div", { className: "share-box", children: [
      /* @__PURE__ */ l.jsx("div", { children: /* @__PURE__ */ l.jsx("b", { children: "Link to share" }) }),
      /* @__PURE__ */ l.jsx("code", { className: "mono", children: v.link }),
      /* @__PURE__ */ l.jsx("div", { className: "muted small", children: v.link_note || 'Viewers open the Analytics Accelerator Portal from Snowsight; this dashboard is in its catalog.' })
    ] }),
    ((y = v.granted) == null ? void 0 : y.length) > 0 && /* @__PURE__ */ l.jsxs("div", { className: "alert ok small", children: [
      "Analytics Accelerator Portal access granted to roles: ",
      v.granted.join(", ")
    ] }),
    ((C = v.failed) == null ? void 0 : C.length) > 0 && /* @__PURE__ */ l.jsxs("div", { className: "alert warn small", children: [
      "Could not grant: ",
      v.failed.join("; ")
    ] }),
    /* @__PURE__ */ l.jsx("div", { className: "muted small", children: "Numbers are queried with the app owner's role (Streamlit in Snowflake runs with owner's rights), so every viewer sees the same governed data. Per-viewer row filtering is on the roadmap." }),
    /* @__PURE__ */ l.jsx("div", { className: "modal-foot", children: /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", onClick: s, children: "Done" }) })
  ] }) : /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsx("h3", { children: "Publish dashboard" }),
    /* @__PURE__ */ l.jsxs("p", { className: "muted small", children: [
      "Publishing freezes this version for viewers. Keep editing here and publish again to release v",
      (((k = e.dashboard) == null ? void 0 : k.version) || 0) + 1,
      "."
    ] }),
    /* @__PURE__ */ l.jsxs("label", { children: [
      "Name",
      /* @__PURE__ */ l.jsx("input", { value: r, onChange: (c) => i(c.target.value) })
    ] }),
    /* @__PURE__ */ l.jsxs("label", { children: [
      "Share with roles ",
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "(gives these roles the Analytics Accelerator Portal, not the builder)" })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "role-list", children: [
      (e.roles || []).length === 0 && /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "Loading roles…" }),
      (e.roles || []).filter((c) => !["ACCOUNTADMIN", "ORGADMIN", "SECURITYADMIN", "USERADMIN", "SYSADMIN"].includes(c)).map((c) => /* @__PURE__ */ l.jsxs("button", { type: "button", className: `chip ${a.includes(c) ? "on" : ""}`, onClick: () => j(c), children: [
        a.includes(c) ? "✓ " : "",
        c
      ] }, c))
    ] }),
    /* @__PURE__ */ l.jsxs("label", { children: [
      "Limit to users ",
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "(optional, comma-separated Snowflake user names)" }),
      /* @__PURE__ */ l.jsx("input", { value: o, onChange: (c) => d(c.target.value), placeholder: "e.g. JDOE, ASMITH" })
    ] }),
    (() => {
      const vb = e.validation_brief || {}, vc = vb.counts || {}, open = (vc.mismatch || 0) + (vc.review || 0);
      return !vb.status ? /* @__PURE__ */ l.jsx("div", { className: "pub-val none", children: "Not validated yet. Viewers will see no verification line. Open the Validation tab to check every page first." }) : /* @__PURE__ */ l.jsx("div", { className: `pub-val ${vb.status}`, children: `${vb.pages_checked} of ${vb.pages_total} page(s) validated · ${vc.pass || 0} verified` + (vc.accepted ? ` · ${vc.accepted} accepted` : "") + (open ? ` · ${open} open finding(s): publishing is allowed, viewers will see them flagged` : "") });
    })(),
    e.uat && /* @__PURE__ */ l.jsx("div", { className: `pub-val uat-${e.uat.status}`, children: `Business sign-off: ${UAT_TXT[e.uat.status]} · ${e.uat.pages_signed} of ${e.uat.pages_total} page(s) signed off` + (e.uat.status === "approved" || e.uat.status === "approved_notes" ? "" : ": publishing is allowed") }),
    e.uat && e.uat.open_requests > 0 && /* @__PURE__ */ l.jsx("div", { className: "pub-val mismatch", children: `${e.uat.open_requests} change request(s) still open on this dashboard. Publishing is allowed; the requests stay open until the reviewer closes them.` }),
    /* @__PURE__ */ l.jsxs("label", { children: [
      "Release note",
      /* @__PURE__ */ l.jsx("input", { value: m, onChange: (c) => p(c.target.value), placeholder: "What changed in this version" })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "modal-foot", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost", onClick: s, children: "Cancel" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", onClick: () => t("publish", { name: r, roles: a, users: o.split(",").map((c) => c.trim()).filter(Boolean), note: m }, "Publishing to Snowflake…"), children: "Publish" })
    ] })
  ] }) }) });
}
function Dp({ data: e, send: t, ctx: n, pending: s }) {
  var It, ga, xa, ya, ja, Na, wa, ka, Ca;
  const r = e.spec, i = !!e.viewer_mode, [a, u] = P.useState(r.pages[0].page_id), [o, d] = P.useState(((It = e.dashboard) == null ? void 0 : It.name) || r.display_name), [m, p] = P.useState(null), [v, j] = P.useState(null), [y, C] = P.useState(!1), [k, c] = P.useState(null), [h, f] = P.useState(null), [x, N] = P.useState(!1);
  P.useEffect(() => {
    e.focus_page && r.pages.find((R) => R.page_id === e.focus_page) ? u(e.focus_page) : r.pages.find((R) => R.page_id === a) || u(r.pages[0].page_id);
  }, [r, e.focus_page]);
  const g = r.pages.find((R) => R.page_id === a) || r.pages[0], M = g.components.filter((R) => R.state !== "omitted"), S = (ga = e.narratives) == null ? void 0 : ga[g.page_id], A = P.useMemo(() => fd(M), [g, r]), w = Object.values(e.results || {}).some((R) => {
    var K;
    return R.status === "pending" || ((K = R.data) == null ? void 0 : K.insights_pending);
  }), D = P.useRef("");
  P.useEffect(() => {
    const R = `${r.template_id}:${e.revision}`;
    w && D.current !== R && !s && (D.current = R, t("enrich", {}, "Snowflake ML: training forecast & finding key drivers…", !0));
  }, [w, e.revision, s]);
  const L = g.components.some((R) => {
    var K;
    return (K = e.results) == null ? void 0 : K[`${g.page_id}/${R.component_id}`];
  }), V = P.useRef("");
  P.useEffect(() => {
    const R = `${g.page_id}:${e.revision}`;
    !L && !s && g.components.length && V.current !== R && (V.current = R, t("load_page", { page_id: g.page_id }, "Running governed queries…", !0));
  }, [g.page_id, L, e.revision, s]);
  const q = r.persona, F = !!q && q !== "managers" && r.pages.length === 1, [U, _] = P.useState(q === "daily_operations"), E = () => (/* @__PURE__ */ new Date()).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), [T, b] = P.useState(E());
  P.useEffect(() => {
    b(E());
  }, [e.revision]);
  const B = () => t("refresh", { page_id: g.page_id }, "Refreshing live data…", !0);
  P.useEffect(() => {
    if (q !== "daily_operations" || !U) return;
    const R = setInterval(() => {
      !s && document.visibilityState === "visible" && B();
    }, Pp);
    return () => clearInterval(R);
  }, [q, U, s, g.page_id]);
  const W = P.useRef(""), ae = g.components.some((R) => {
    var K, nt;
    return ((nt = (K = e.results) == null ? void 0 : K[`${g.page_id}/${R.component_id}`]) == null ? void 0 : nt.status) === "ready";
  });
  P.useEffect(() => {
    const R = `${g.page_id}:${e.revision}`;
    q === "executives" && ae && !S && !s && W.current !== R && (W.current = R, t("narrative", { page_id: g.page_id }, "Cortex is writing what changed and why…", !0));
  }, [q, ae, S, s, e.revision]);
  const [valOpen, setValOpen] = P.useState(null), valKey = P.useRef(""), [vt, setVt] = P.useState(!1);
  const uatMap = P.useMemo(() => Object.fromEntries(((e.uat || {}).pages || []).flatMap((pg) => pg.tiles.map((x) => [x.cid, x]))), [e.uat]), uatFocus = e.uat_focus || null, uatDone = P.useRef("");
  P.useEffect(() => {
    uatFocus && setVt(!1);
  }, [uatFocus && uatFocus.id]);
  P.useEffect(() => {
    const R = `${g.page_id}:${e.revision}`, need = (e.validation_needed || []).includes(g.page_id), narr = q !== "executives" || !!S || W.current.startsWith(g.page_id + ":") && W.current !== R;
    need && !i && !w && !s && narr && valKey.current !== R && (valKey.current = R, t("validate", { page_id: g.page_id }, "Validating numbers against the base tables…", !0));
  }, [g.page_id, e.revision, s, w, S]);
  const vjob = e.validation_job;
  P.useEffect(() => {
    if (!vjob || !vjob.running || i) return;
    const R = setTimeout(() => t("validate_poll", {}, "", !0), 2000);
    return () => clearTimeout(R);
  }, [vjob && vjob.running, vjob && vjob.done, vjob && vjob.tiles_done, e.revision]);
  const Xe = v && ((xa = r.pages.find((R) => R.page_id === v.page_id)) == null ? void 0 : xa.components.find((R) => R.component_id === v.component_id)), Dn = v && r.pages.find((R) => R.page_id === v.page_id), Ue = r.origin || "catalog", Ds = [
    "Executive variance: what changed, why it changed, and the next three risks",
    "Operations health: service levels, backlog, and bottlenecks by owner",
    "Growth watch: pipeline, conversion, and customer segments needing attention"
  ], rs = k != null && k.trim(), os = () => {
    rs && (t("page_add", { mode: "cortex", instruction: k }, "Cortex is designing the page…"), c(null));
  }, us = () => {
    t("page_add", { mode: "blank", label: rs || "New page" }, "Adding page…"), c(null);
  };
  return /* @__PURE__ */ l.jsxs("section", { className: `view ws2 ${v ? "with-panel" : ""} ${k != null ? "adding-page" : ""}`, "data-theme": (e.theme || {}).kind === "custom" ? "custom" : (e.theme || {}).id || "classic", "data-dark": (e.theme || {}).dark ? "1" : null, style: (e.theme || {}).kind === "custom" ? (e.theme || {}).vars : void 0, children: [
    /* @__PURE__ */ l.jsx(ThemeVars, { theme: e.theme }),
    i && /* @__PURE__ */ l.jsxs("div", { className: "viewer-banner", children: [
      /* @__PURE__ */ l.jsxs("span", { children: [
        "📊 Published dashboard · v",
        (ya = e.dashboard) == null ? void 0 : ya.version,
        " · by ",
        ((ja = e.dashboard) == null ? void 0 : ja.published_by) || "owner",
        " · ",
        (Na = e.dashboard) == null ? void 0 : Na.published_at
      ] }),
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "Read-only · live governed data" })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "ws-head", children: [
      /* @__PURE__ */ l.jsxs("div", { children: [
        /* @__PURE__ */ l.jsxs("div", { className: "mast-eyebrow", children: [/* @__PURE__ */ l.jsx("i", { className: "live-dot" }), `${(Pn[r.audience_id] || "").toUpperCase()} · LIVE${((cal0) => cal0 ? ` · DATA THROUGH ${cal0.max_date}` : "")((e.profile || {}).calendar)}`] }),
        false && /* @__PURE__ */ l.jsxs("div", { className: "eyebrow", children: [
          Pn[r.audience_id],
          " ·",
          " ",
          Ue === "persona" ? /* @__PURE__ */ l.jsxs("span", { className: "origin ai", children: [
            "",
            (wa = Pn[r.audience_id]) == null ? void 0 : wa.toLowerCase(),
            " layout · ✦ ",
            "",
            " · validated"
          ] }) : Ue === "cortex" ? /* @__PURE__ */ l.jsx("span", { className: "origin ai", children: "✦ Designed by Cortex · approved by you · validated" }) : Ue === "catalog-fallback" ? /* @__PURE__ */ l.jsx("span", { className: "origin warn", children: "Reviewed template (Cortex unavailable)" }) : /* @__PURE__ */ l.jsxs("span", { className: "origin", children: [
            "Reviewed template ",
            r.template_id
          ] }),
          r.edited && !i && /* @__PURE__ */ l.jsx("span", { className: "origin", children: " · edited" })
        ] }),
        i ? /* @__PURE__ */ l.jsx("h1", { className: "ws-title-v", children: ((ka = e.dashboard) == null ? void 0 : ka.name) || r.display_name }) : /* @__PURE__ */ l.jsx("input", { className: "ws-title", value: o, onChange: (R) => d(R.target.value) }),
        /* @__PURE__ */ l.jsx("div", { className: "muted", children: r.description })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "ws-actions", children: [
        /* theme picker removed from the header (15 Oct): Classic by default; company themes come from settings */
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost", title: "Refresh the data", "aria-label": "Refresh", onClick: () => t("refresh", { page_id: g.page_id }), children: "↻" }),
        i ? /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost", onClick: () => t("exit_viewer", {}, "Opening…"), children: "Close" }) : /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
          /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost", onClick: () => t("save_dashboard", { name: o }, "Saving draft…"), children: "Save draft" }),
          /* @__PURE__ */ l.jsxs("button", { type: "button", className: "btn", onClick: () => N(!0), children: [
            "Publish",
            (Ca = e.dashboard) != null && Ca.published ? " update" : ""
          ] })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ l.jsx(zp, { persona: q, data: e, onRefresh: B, auto: U, setAuto: _, refreshedAt: T }),
    F && !i && k == null && /* @__PURE__ */ l.jsxs("div", { className: "ptab-single", children: [
      vt && /* @__PURE__ */ l.jsx("button", { type: "button", className: "ptab-add", onClick: () => setVt(!1), children: "← Dashboard" }),
      /* @__PURE__ */ l.jsxs("button", { type: "button", className: `ptab-add vt-single ${vt ? "on" : ""} ${(e.validation_overview || {}).status || "none"}`, onClick: () => setVt(!0), children: [/* @__PURE__ */ l.jsx("span", { className: "ptab-num", children: ((e.validation_overview || {}).status || "none") === "none" ? "?" : VAL_ICON[(e.validation_overview || {}).status] || "✓" }), "Validation"] }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ptab-add", onClick: () => c(""), children: "+ Add page" })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: `ptabs-wrap ${F && k == null ? "hidden" : ""}`, children: [
      /* @__PURE__ */ l.jsxs("div", { className: "ptabs", role: "tablist", children: [
        r.pages.map((R, K) => {
          const nt = R.page_id === g.page_id;
          return /* @__PURE__ */ l.jsxs("div", { className: `ptab ${nt && !vt ? "on" : ""}`, children: [
            h === R.page_id ? /* @__PURE__ */ l.jsx(
              "input",
              {
                autoFocus: !0,
                defaultValue: R.label,
                onBlur: (Ge) => {
                  f(null), Ge.target.value.trim() && Ge.target.value !== R.label && t("page_rename", { page_id: R.page_id, label: Ge.target.value }, "Renaming…");
                },
                onKeyDown: (Ge) => {
                  Ge.key === "Enter" && Ge.target.blur(), Ge.key === "Escape" && f(null);
                }
              }
            ) : /* @__PURE__ */ l.jsxs(
              "button",
              {
                type: "button",
                role: "tab",
                "aria-selected": nt,
                className: "ptab-btn",
                title: `${R.purpose || R.label} · ${R.components.length} tiles${i ? "" : " · double-click to rename"}`,
                onClick: () => (setVt(!1), u(R.page_id)),
                onDoubleClick: () => !i && f(R.page_id),
                children: [
                  /* @__PURE__ */ l.jsx("span", { className: "ptab-num", children: K + 1 }),
                  R.label
                ]
              }
            ),
            !i && nt && h !== R.page_id && /* @__PURE__ */ l.jsxs("span", { className: "ptab-acts", children: [
              /* @__PURE__ */ l.jsx("button", { type: "button", title: "Rename page", onClick: () => f(R.page_id), children: "✎" }),
              /* @__PURE__ */ l.jsx("button", { type: "button", title: "Move left", disabled: K === 0, onClick: () => t("page_move", { page_id: R.page_id, dir: -1 }, "Moving…"), children: "‹" }),
              /* @__PURE__ */ l.jsx("button", { type: "button", title: "Move right", disabled: K === r.pages.length - 1, onClick: () => t("page_move", { page_id: R.page_id, dir: 1 }, "Moving…"), children: "›" }),
              /* @__PURE__ */ l.jsx("button", { type: "button", title: "Remove page", disabled: r.pages.length < 2, onClick: () => t("page_remove", { page_id: R.page_id }, "Removing…"), children: "×" })
            ] })
          ] }, R.page_id);
        }),
        !i && /* @__PURE__ */ l.jsx("div", { className: `ptab vt-tab ${vt ? "on" : ""} ${(e.validation_overview || {}).status || "none"}`, children: /* @__PURE__ */ l.jsxs("button", { type: "button", role: "tab", "aria-selected": vt, className: "ptab-btn", onClick: () => setVt(!0), children: [/* @__PURE__ */ l.jsx("span", { className: "ptab-num", children: ((e.validation_overview || {}).status || "none") === "none" ? "?" : VAL_ICON[(e.validation_overview || {}).status] || "✓" }), "Validation"] }) }),
        !i && /* @__PURE__ */ l.jsx("button", { type: "button", className: `ptab-add ${k != null ? "on" : ""}`, onClick: () => c(k == null ? "" : null), children: "+ Add page" })
      ] }),
      !i && k != null && /* @__PURE__ */ l.jsxs("div", { className: "addpage-pop", role: "dialog", "aria-modal": "true", "aria-labelledby": "addpage-title", children: [
        /* @__PURE__ */ l.jsxs("div", { className: "addpage-head", children: [
          /* @__PURE__ */ l.jsxs("div", { children: [
            /* @__PURE__ */ l.jsx("span", { children: "Cortex page builder" }),
            /* @__PURE__ */ l.jsx("h3", { id: "addpage-title", children: "Add an interactive page" }),
            /* @__PURE__ */ l.jsx("p", { children: "Describe the decision this page should support. Cortex will choose the layout, metrics, charts and questions from governed data." })
          ] }),
          /* @__PURE__ */ l.jsx("button", { type: "button", className: "addpage-close", onClick: () => c(null), "aria-label": "Close add page", children: "×" })
        ] }),
        /* @__PURE__ */ l.jsxs("div", { className: "addpage-bubble", children: [
          /* @__PURE__ */ l.jsx("b", { children: "Try a page brief" }),
          /* @__PURE__ */ l.jsx("span", { children: "Use a shortcut below or type your own goal. Press Enter to design, Shift+Enter for a new line." })
        ] }),
        /* @__PURE__ */ l.jsx("div", { className: "addpage-suggestions", children: Ds.map((R) => /* @__PURE__ */ l.jsx("button", { type: "button", onClick: () => c(R), children: R }, R)) }),
        /* @__PURE__ */ l.jsx(
          "textarea",
          {
            autoFocus: !0,
            rows: 4,
            placeholder: "e.g. Fulfilment health: on-time %, delivery days by carrier, and the top delay drivers",
            value: k,
            onChange: (R) => c(R.target.value),
            onKeyDown: (R) => {
              R.key === "Enter" && !R.shiftKey && (R.preventDefault(), rs && os()), R.key === "Escape" && c(null);
            }
          }
        ),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: us, children: "Blank page" }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small ghost-ai", disabled: !rs, onClick: os, children: "Design with Cortex" })
      ] })
    ] }),
    vt && !i ? /* @__PURE__ */ l.jsx(ValTab, { data: e, send: t, onTile: (R, K) => setValOpen({ focus: R, page_id: K }), onPage: (R) => (setVt(!1), u(R)) }) : /* @__PURE__ */ l.jsxs("div", { className: "ws-body", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "ws-main", children: [
        /* @__PURE__ */ l.jsx("div", { className: "page-q", children: /* @__PURE__ */ l.jsx("b", { children: g.purpose }) }),
        /* @__PURE__ */ l.jsxs("div", { className: "summary", children: [
          /* @__PURE__ */ l.jsxs("div", { className: "summary-head", children: [
            /* @__PURE__ */ l.jsxs("span", { className: "ai-title", children: [
              "✦ ",
              q === "executives" ? "What changed and why" : q === "daily_operations" ? "What is happening today" : "AI summary"
            ] }),
            /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small ghost-ai", onClick: () => t("narrative", { page_id: g.page_id }), children: S ? "Regenerate" : "Generate with Cortex" })
          ] }),
          S ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
            /* @__PURE__ */ l.jsx(StoryText, { text: S.text }),
            /* @__PURE__ */ l.jsxs("details", { children: [
              /* @__PURE__ */ l.jsxs("summary", { className: "prov", children: [
                S.provenance,
                " — show the governed facts it used"
              ] }),
              /* @__PURE__ */ l.jsx("ul", { className: "facts", children: (S.facts || []).map((R, K) => /* @__PURE__ */ l.jsx("li", { children: R }, K)) })
            ] })
          ] }) : /* @__PURE__ */ l.jsx("div", { className: "muted small", children: "Cortex writes the summary only from the governed facts computed for this page." })
        ] }),
        /* @__PURE__ */ l.jsx(ValStrip, { data: e, pageId: g.page_id, viewer: i, onOpen: (R) => R ? setValOpen({ focus: R }) : setVt(!0) }),
        /* @__PURE__ */ l.jsx(Ap, { data: e, send: t, pageId: g.page_id }),
        !i && /* @__PURE__ */ l.jsx("div", { className: "tile add", style: { gridColumn: "span 12" }, children: y ? /* @__PURE__ */ l.jsx(Rp, { page: g, data: e, send: t, onClose: () => C(!1) }) : /* @__PURE__ */ l.jsx("button", { type: "button", className: "add-btn", onClick: () => C(!0), children: "+ Add tile" }) }),
        !M.length && /* @__PURE__ */ l.jsxs("div", { className: "empty", children: [
          "This page is empty. ",
          !i && "Use Add tile above."
        ] }),
        /* @__PURE__ */ l.jsxs("div", { className: "grid", children: [
          A.map((R) => {
            var Sa, ba, Ea, Ma;
            const K = e.results[`${g.page_id}/${R.component_id}`] || {}, nt = yp[R.type], Ge = (Sa = n.defs) == null ? void 0 : Sa[R.metric_id], Ks = (v == null ? void 0 : v.component_id) === R.component_id && (v == null ? void 0 : v.page_id) === g.page_id;
            const ucid = `${g.page_id}/${R.component_id}`, ufoc = !!uatFocus && uatFocus.cid === ucid;
            return /* @__PURE__ */ l.jsxs("div", { className: `tile ${Ks ? "focused" : ""} ${ufoc ? "uat-focused" : ""}`, style: { gridColumn: `span ${R.span}` }, ref: ufoc ? (el) => {
              el && uatDone.current !== uatFocus.id && (uatDone.current = uatFocus.id, setTimeout(() => el.scrollIntoView({ behavior: "smooth", block: "center" }), 120));
            } : void 0, children: [
              /* @__PURE__ */ l.jsxs("div", { className: "tile-head", children: [
                /* @__PURE__ */ l.jsxs("div", { className: `tile-titles ${K.data && K.data.headline ? "has-hl" : ""}`, children: [
                  K.data && K.data.headline ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
                    /* @__PURE__ */ l.jsxs("span", { className: "tile-eyebrow", title: R.question || "", children: [R.title, Ge ? /* @__PURE__ */ l.jsx("span", { className: "def", title: Ge, children: "ⓘ" }) : null] }),
                    /* @__PURE__ */ l.jsx("b", { className: "tile-hl", children: K.data.headline })
                  ] }) : /* @__PURE__ */ l.jsxs("b", { title: R.question || "", children: [
                    R.title,
                    Ge ? /* @__PURE__ */ l.jsx("span", { className: "def", title: Ge, children: "ⓘ" }) : null
                  ] })
                ] }),
                /* @__PURE__ */ l.jsxs("span", { className: "tile-acts", children: [
                  !i && /* @__PURE__ */ l.jsx(ValBadge, { v: ((e.validation || {}).tiles || {})[`${g.page_id}/${R.component_id}`], stale: (e.validation_stale || []).includes(`${g.page_id}/${R.component_id}`), onOpen: () => setValOpen({ focus: `${g.page_id}/${R.component_id}` }) }),
                  R.type === "kpi_plan" && !i ? /* @__PURE__ */ l.jsx("span", { className: "show-as", role: "group", "aria-label": "Show KPIs as", children: [["bullet", "Bars"], ["variance", "Arrows"], ["table", "Table"]].map(([pt, vd]) => {
                    var La;
                    return /* @__PURE__ */ l.jsx(
                      "button",
                      {
                        type: "button",
                        className: (R.display || "bullet") === pt ? "on" : "",
                        title: (La = hd.find((gd) => gd[0] === pt)) == null ? void 0 : La[1],
                        onClick: () => (R.display || "bullet") !== pt && t("tile_update", { page_id: g.page_id, component_id: R.component_id, patch: { display: pt } }, "Switching view…"),
                        children: vd
                      },
                      pt
                    );
                  }) }) : i ? null : /* @__PURE__ */ l.jsx("span", { className: "muted small", children: ((Ea = (ba = e.tile_types) == null ? void 0 : ba[R.type]) == null ? void 0 : Ea.label) || R.type.replace(/_/g, " ") }),
                  /* @__PURE__ */ l.jsx(
                    "button",
                    {
                      type: "button",
                      className: `sparkle ${Ks ? "on" : ""}`,
                      title: "Ask or change this tile with AI",
                      onClick: () => j(Ks ? null : { page_id: g.page_id, component_id: R.component_id }),
                      children: "✦"
                    }
                  ),
                  !i && /* @__PURE__ */ l.jsx("button", { type: "button", className: "dots", title: "Tile options", onClick: () => p(m === R.component_id ? null : R.component_id), children: "⋯" })
                ] }),
                m === R.component_id && /* @__PURE__ */ l.jsx(Tp, { c: R, page: g, data: e, send: t, onClose: () => p(null) })
              ] }),
              !i && /* @__PURE__ */ l.jsx(UatNote, { r: uatMap[ucid], send: t, focus: ufoc }),
              R.question && !(K.data && K.data.headline) && /* @__PURE__ */ l.jsx("div", { className: "tile-q", children: R.question }),
              !K.status && /* @__PURE__ */ l.jsxs("div", { className: "tile-skel", children: [
                /* @__PURE__ */ l.jsx("i", {}),
                /* @__PURE__ */ l.jsx("i", {}),
                /* @__PURE__ */ l.jsx("i", {})
              ] }),
              K.status === "ready" && nt && /* @__PURE__ */ l.jsx(nt, { data: K.data, ctx: n, spec: R }),
              K.status === "error" && /* @__PURE__ */ l.jsxs("div", { className: "alert error small", children: [
                "Query failed — no substitute value shown. ",
                K.error
              ] }),
              K.status === "pending" && /* @__PURE__ */ l.jsxs("div", { className: "pending-tile", children: [
                /* @__PURE__ */ l.jsx("div", { className: "spinner dark" }),
                K.message || "Running Snowflake ML…"
              ] }),
              K.status === "blocked" && /* @__PURE__ */ l.jsxs("div", { className: "alert warn small", children: [
                "Unavailable. Missing: ",
                (K.missing || []).map((pt) => ji[pt] || $e(pt)).join(", ")
              ] }),
              ((Ma = K.skipped_filters) == null ? void 0 : Ma.length) > 0 && /* @__PURE__ */ l.jsxs("div", { className: "skipnote", children: [
                "Filter not applied: ",
                K.skipped_filters.join(", "),
                " can't split this metric in the semantic view."
              ] })
            ] }, R.component_id);
          })
        ] })
      ] }),
      Xe && /* @__PURE__ */ l.jsx(Fp, { tile: Xe, page: Dn, data: e, send: t, pending: s, viewer: i, onClose: () => j(null) })
    ] }),
    x && /* @__PURE__ */ l.jsx(Op, { data: e, send: t, name: o, onClose: () => N(!1) }),
    valOpen && /* @__PURE__ */ l.jsx(ValReport, { data: e, page: r.pages.find((R) => R.page_id === valOpen.page_id) || g, focus: valOpen.focus, send: t, onClose: () => setValOpen(null) })
  ] });
}
const Ip = ["SUM", "AVG", "MIN", "MAX", "COUNT", "COUNT_DISTINCT"];
function Sbc({ checks: e, title: t }) {
  const ic = { ok: "✓", warn: "!", fail: "✕", info: "i" };
  return /* @__PURE__ */ l.jsxs("div", { className: "sbc", children: [
    /* @__PURE__ */ l.jsx("div", { className: "sbc-title", children: t }),
    e.map((c, i) => /* @__PURE__ */ l.jsxs("div", { className: `sbc-row ${c.status}`, children: [/* @__PURE__ */ l.jsx("span", { className: "sbc-ic", children: ic[c.status] || "·" }), /* @__PURE__ */ l.jsx("b", { children: c.check }), /* @__PURE__ */ l.jsx("span", { className: "muted small", children: c.detail })] }, i))
  ] });
}
function Up({ data: e, send: t, pending: n, onDone: s }) {
  var v, j, y, C, k, c, h, f;
  const r = e.sb, [i, a] = P.useState(""), [u, o] = P.useState(null), [SEL, SSEL] = P.useState([]), [SCH, SSCH] = P.useState(""), [ALL, SALL] = P.useState(!1), [SRT, SSRT] = P.useState("changed"), [QQ, SQQ] = P.useState(""), [SYS, SSYS] = P.useState(!1);
  P.useEffect(() => {
    r && r.suggest && r.suggest.question && SQQ(r.suggest.question);
  }, [r && r.suggest && r.suggest.question]);
  P.useEffect(() => {
    r || t("sb_tables", {}, "Listing tables you can read…", !0);
  }, []), P.useEffect(() => {
    o(r != null && r.spec ? JSON.parse(JSON.stringify(r.spec)) : null);
  }, [r == null ? void 0 : r.spec]);
  const d = n && String(n.type).startsWith("sb_");
  if (!r) return /* @__PURE__ */ l.jsx("div", { className: "muted", children: "Listing tables…" });
  if (r.step === "pick") {
    const T = r.tables || [], BY = Object.fromEntries(T.map((g) => [g.fqn, g])), x = i.trim().toLowerCase(), SCHS = [...new Set(T.map((g) => g.schema))].sort(), tog = (f) => SSEL((Z) => Z.includes(f) ? Z.filter((q) => q !== f) : [...Z, f]), hidden = T.filter((g) => g.empty || g.tiny).length, sysN = T.filter((g) => g.system && !(g.empty || g.tiny)).length;
    let N = T.filter((g) => (ALL || !(g.empty || g.tiny)) && (SYS || x || !g.system) && (!SCH || g.schema === SCH) && (!x || `${g.schema} ${g.name} ${g.comment || ""}`.toLowerCase().includes(x) || (g.columns || []).some((c) => c.toLowerCase().includes(x))));
    N = [...N].sort((A2, B2) => (A2.system ? 1 : 0) - (B2.system ? 1 : 0) || (SRT === "rows" ? (Number(B2.rows) || 0) - (Number(A2.rows) || 0) : SRT === "changed" ? String(B2.altered || "").localeCompare(String(A2.altered || "")) : A2.name.localeCompare(B2.name)));
    const NAMES = {};
    T.forEach((g) => { NAMES[g.name] = (NAMES[g.name] || 0) + 1; });
    const colHit = (g) => x && !`${g.schema} ${g.name}`.toLowerCase().includes(x) ? (g.columns || []).filter((c) => c.toLowerCase().includes(x)).slice(0, 3) : [];
    const REL = [];
    SEL.forEach((f) => ((r.related || {})[f] || []).forEach((h) => {
      !SEL.includes(h.fqn) && !REL.some((z) => z.fqn === h.fqn) && BY[h.fqn] && REL.push({ ...h, from: f });
    }));
    const SG = r.suggest, row = (g, extra) => /* @__PURE__ */ l.jsxs("div", { className: `tf-row ${SEL.includes(g.fqn) ? "on" : ""}`, children: [
      /* @__PURE__ */ l.jsx("input", { type: "checkbox", checked: SEL.includes(g.fqn), onChange: () => tog(g.fqn), "aria-label": `Select ${g.name}` }),
      /* @__PURE__ */ l.jsxs("div", { className: "tf-name", children: [
        /* @__PURE__ */ l.jsx("b", { children: g.name }),
        (g.covered || []).length > 0 && /* @__PURE__ */ l.jsx("em", { className: "tf-cov", title: "Already in a semantic view: use that view rather than building another", children: `In ${g.covered.join(", ")}` }),
        g.empty && /* @__PURE__ */ l.jsx("em", { className: "tf-dim", children: "empty" }),
        g.view && /* @__PURE__ */ l.jsx("em", { className: "tf-dim", children: "view" }),
        g.system && /* @__PURE__ */ l.jsx("em", { className: "tf-dim", title: "Looks like an app, log or temporary table", children: "system" }),
        NAMES[g.name] > 1 && /* @__PURE__ */ l.jsx("em", { className: "tf-dup", title: "Same table name exists in another schema: check the schema column", children: `${NAMES[g.name]} schemas` }),
        !g.empty && g.tiny && /* @__PURE__ */ l.jsx("em", { className: "tf-dim", children: "small" }),
        extra ? /* @__PURE__ */ l.jsx("span", { className: "tf-extra", children: extra }) : null,
        colHit(g).length > 0 && /* @__PURE__ */ l.jsx("span", { className: "tf-extra", children: "columns: " + colHit(g).join(", ") }),
        g.comment && /* @__PURE__ */ l.jsx("span", { className: "tf-cmt", children: g.comment })
      ] }),
      /* @__PURE__ */ l.jsx("span", { className: "tf-c muted small", title: g.schema, children: g.schema.split(".").pop() }),
      /* @__PURE__ */ l.jsx("span", { className: "tf-c num", title: g.rows == null ? "Row count not available (usually a view)" : "", children: g.rows != null ? Number(g.rows).toLocaleString() : g.view ? "view" : "n/a" }),
      /* @__PURE__ */ l.jsx("span", { className: "tf-c num", children: g.cols || "" }),
      /* @__PURE__ */ l.jsx("span", { className: "tf-c muted small", children: g.altered || "" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "link tf-go", disabled: d, title: "Draft a semantic view from this table alone", onClick: () => t("sb_draft", { fqn: g.fqn }, "Profiling the table and drafting with Cortex…"), children: "Draft →" })
    ] }, (extra ? "x" : "") + g.fqn);
    return /* @__PURE__ */ l.jsxs("div", { className: "sb tf", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "tf-ask", children: [
        /* @__PURE__ */ l.jsx("b", { children: "What do you want to analyze?" }),
        /* @__PURE__ */ l.jsxs("div", { className: "tf-ask-row", children: [
          /* @__PURE__ */ l.jsx("input", { className: "search", value: QQ, placeholder: "e.g. online orders by customer and product, or freight cost by carrier", onChange: (z) => SQQ(z.target.value), onKeyDown: (z) => {
            z.key === "Enter" && QQ.trim() && !d && t("sb_suggest", { text: QQ }, "Cortex is picking the tables…");
          } }),
          /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", disabled: d || !QQ.trim(), onClick: () => t("sb_suggest", { text: QQ }, "Cortex is picking the tables…"), children: "✦ Suggest tables" })
        ] }),
        SG && /* @__PURE__ */ l.jsxs("div", { className: "tf-sug", children: [
          SG.tables.length ? /* @__PURE__ */ l.jsx("div", { className: "small", children: `✦ Cortex suggests for “${SG.question}”:` }) : /* @__PURE__ */ l.jsx("div", { className: "small", children: SG.note ? `✦ ${SG.note}` : "✦ Cortex found no matching tables." }),
          SG.tables.map((h) => BY[h.fqn] && row(BY[h.fqn], h.why)),
          !SG.tables.length && (SG.nearest || []).length > 0 && /* @__PURE__ */ l.jsx("div", { className: "small muted", children: "Nearest by name, comment or column:" }),
          !SG.tables.length && (SG.nearest || []).map((h) => BY[h.fqn] && row(BY[h.fqn], h.why)),
          !SG.tables.length && !(SG.nearest || []).length && /* @__PURE__ */ l.jsx("div", { className: "small muted", children: "Try the words your data uses (a table or column name), or search the list below." }),
          /* @__PURE__ */ l.jsxs("div", { className: "tf-sug-foot", children: [
            SG.note && SG.tables.length ? /* @__PURE__ */ l.jsx("span", { className: "muted small", children: SG.note }) : /* @__PURE__ */ l.jsx("span", {}),
            SG.tables.length > 0 && /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => SSEL([...new Set([...SEL, ...SG.tables.map((h) => h.fqn)])]), children: "Select all suggested" })
          ] })
        ] })
      ] }),
      SEL.length > 0 && /* @__PURE__ */ l.jsxs("div", { className: "sb-combine tf-tray", children: [
        /* @__PURE__ */ l.jsxs("span", { className: "tf-chips", children: SEL.map((f) => /* @__PURE__ */ l.jsxs("em", { className: "tf-chip", children: [(BY[f] || {}).name || f.split(".").pop(), /* @__PURE__ */ l.jsx("button", { type: "button", "aria-label": "Remove", onClick: () => tog(f), children: "×" })] }, f)) }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => SSEL([]), children: "Clear" }),
        SEL.length === 1 ? /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", disabled: d, onClick: () => t("sb_draft", { fqn: SEL[0] }, "Profiling the table and drafting with Cortex…"), children: "Draft from this table →" }) : /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", disabled: d, onClick: () => t("sb_draft", { fqns: SEL }, `Profiling ${SEL.length} tables, checking the joins and drafting with Cortex…`), children: `Combine ${SEL.length} tables into one semantic view →` })
      ] }),
      REL.length > 0 && /* @__PURE__ */ l.jsxs("div", { className: "tf-rel", children: [
        /* @__PURE__ */ l.jsx("div", { className: "sbc-title", children: `Joins with your selection (${REL.length})` }),
        REL.map((h) => row(BY[h.fqn], `joins ${(BY[h.from] || {}).name || ""} via ${h.via}`))
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "tf-filters", children: [
        /* @__PURE__ */ l.jsx("input", { className: "search", placeholder: "Search tables, comments or column names (e.g. customer_id)…", value: i, onChange: (g) => a(g.target.value) }),
        /* @__PURE__ */ l.jsxs("select", { value: SCH, onChange: (z) => SSCH(z.target.value), children: [/* @__PURE__ */ l.jsx("option", { value: "", children: `All schemas (${SCHS.length})` }), ...SCHS.map((q) => /* @__PURE__ */ l.jsx("option", { value: q, children: q }, q))] }),
        /* @__PURE__ */ l.jsxs("select", { value: SRT, onChange: (z) => SSRT(z.target.value), children: [/* @__PURE__ */ l.jsx("option", { value: "changed", children: "Sort: recently changed" }), /* @__PURE__ */ l.jsx("option", { value: "name", children: "Sort: name" }), /* @__PURE__ */ l.jsx("option", { value: "rows", children: "Sort: most rows" })] }),
        sysN > 0 && /* @__PURE__ */ l.jsxs("label", { className: "tf-all small", children: [/* @__PURE__ */ l.jsx("input", { type: "checkbox", checked: SYS, onChange: (z) => SSYS(z.target.checked) }), ` Show ${sysN} system-like tables`] }),
        hidden > 0 && /* @__PURE__ */ l.jsxs("label", { className: "tf-all small", children: [/* @__PURE__ */ l.jsx("input", { type: "checkbox", checked: ALL, onChange: (z) => SALL(z.target.checked) }), ` Show ${hidden} empty or small tables`] })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "tf-head", children: [/* @__PURE__ */ l.jsx("span", {}), /* @__PURE__ */ l.jsx("span", { children: `Table (${N.length} of ${T.length})` }), /* @__PURE__ */ l.jsx("span", { children: "Schema" }), /* @__PURE__ */ l.jsx("span", { className: "num", children: "Rows" }), /* @__PURE__ */ l.jsx("span", { className: "num", children: "Columns" }), /* @__PURE__ */ l.jsx("span", { children: "Changed" }), /* @__PURE__ */ l.jsx("span", {})] }),
      /* @__PURE__ */ l.jsxs("div", { className: "tf-list", children: [
        N.map((g) => row(g)),
        !N.length && /* @__PURE__ */ l.jsx("div", { className: "empty", children: x ? "No table, comment or column matches." : "No tables to show." })
      ] })
    ] });
  }
  if (r.step === "done") {
    const x = ((v = r.created) == null ? void 0 : v.test_rows) || [], N = x.length ? Object.keys(x[0]) : [];
    return /* @__PURE__ */ l.jsxs("div", { className: "sb", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "sb-done", children: [
        "✓ Created ",
        /* @__PURE__ */ l.jsx("code", { children: (j = r.created) == null ? void 0 : j.semantic_view }),
        " and queried it through ",
        /* @__PURE__ */ l.jsx("code", { children: "SEMANTIC_VIEW()" }),
        "."
      ] }),
      x.length > 0 && /* @__PURE__ */ l.jsxs("table", { className: "table compact", children: [
        /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsx("tr", { children: N.map((g) => /* @__PURE__ */ l.jsx("th", { children: g }, g)) }) }),
        /* @__PURE__ */ l.jsx("tbody", { children: x.map((g, M) => /* @__PURE__ */ l.jsx("tr", { children: N.map((S) => /* @__PURE__ */ l.jsx("td", { children: String(g[S] ?? "") }, S)) }, M)) })
      ] }),
      (((v = r.created) == null ? void 0 : v.checks) || []).length > 0 && /* @__PURE__ */ l.jsx(Sbc, { checks: r.created.checks, title: "Checks after creating" }),
      /* @__PURE__ */ l.jsx("p", { className: "muted small", children: "It now appears on Home: Cortex ideas, prompt routing and the agent can all use it." }),
      /* @__PURE__ */ l.jsxs("div", { className: "sb-actions", children: [
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", onClick: () => {
          s && s(), t("go", { step: "home" }, "Opening Home…");
        }, children: "Back to Home" }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost", onClick: () => t("sb_tables", {}, "Listing tables…"), children: "Draft another" })
      ] })
    ] });
  }
  if (!u) return null;
  const m = (x, N, g) => o((M) => ({ ...M, [x]: M[x].map((S, A) => A === N ? { ...S, ...g } : S) })), p = ["dimensions", "metrics", "ratios"].map((x) => (u[x] || []).filter((N) => N.include !== !1).length);
  return /* @__PURE__ */ l.jsxs("div", { className: "sb", children: [
    /* @__PURE__ */ l.jsxs("div", { className: "sb-head", children: [
      /* @__PURE__ */ l.jsxs("div", { children: [
        r.multi ? /* @__PURE__ */ l.jsxs("b", { children: [(u.tables || []).length, " tables combined"] }) : /* @__PURE__ */ l.jsx("b", { children: (y = r.profile) == null ? void 0 : y.table }),
        " ",
        r.multi ? /* @__PURE__ */ l.jsx("span", { className: "muted small", children: (u.tables || []).map((q) => q.fqn).join(" · ") }) : /* @__PURE__ */ l.jsxs("span", { className: "muted small", children: [
          r.fqn,
          " · ",
          Number(((C = r.profile) == null ? void 0 : C.rows_profiled) || 0).toLocaleString(),
          " rows profiled"
        ] })
      ] }),
      /* @__PURE__ */ l.jsx("span", { className: `pill ${r.origin === "cortex" ? "ai" : "soft"}`, children: r.origin === "cortex" ? "✦ Drafted by Cortex" : "Drafted from profile (Cortex unavailable)" })
    ] }),
    /* @__PURE__ */ l.jsxs("label", { className: "sb-field", children: [
      "View description",
      /* @__PURE__ */ l.jsx("input", { value: u.description || "", onChange: (x) => o({ ...u, description: x.target.value }) })
    ] }),
    r.multi && /* @__PURE__ */ l.jsxs("div", { className: "sbm", children: [
      /* @__PURE__ */ l.jsx("h4", { children: "Tables and joins" }),
      /* @__PURE__ */ l.jsx("div", { className: "sbm-tables", children: (u.tables || []).map((q) => /* @__PURE__ */ l.jsxs("div", { className: "sbm-t", children: [/* @__PURE__ */ l.jsx("b", { children: q.alias }), /* @__PURE__ */ l.jsx("span", { className: "muted small", children: q.key ? `key ${q.key}` : "no unique key" }), /* @__PURE__ */ l.jsx("span", { className: "muted small", children: `${(u.metrics || []).filter((z) => z.table === q.alias && z.include !== !1).length} metrics · ${(u.dimensions || []).filter((z) => z.table === q.alias && z.include !== !1).length} dimensions` })] }, q.alias)) }),
      /* @__PURE__ */ l.jsx("div", { className: "sbm-rels", children: (u.relationships || []).map((q, ix) => /* @__PURE__ */ l.jsxs("label", { className: `sbm-rel ${q.include === !1 ? "off" : ""}`, children: [
        /* @__PURE__ */ l.jsx("input", { type: "checkbox", checked: q.include !== !1, onChange: (z) => m("relationships", ix, { include: z.target.checked }) }),
        /* @__PURE__ */ l.jsx("code", { children: `${q.from}.${q.from_col}` }), /* @__PURE__ */ l.jsx("span", { className: "sbm-arrow", children: "→" }), /* @__PURE__ */ l.jsx("code", { children: `${q.to}.${q.to_col}` }),
        /* @__PURE__ */ l.jsx("em", { className: `sbm-cov ${q.coverage >= 0.95 ? "ok" : "warn"}`, children: `${Math.round(q.coverage * 1000) / 10}% matched` })
      ] }, q.name)) }),
      /* @__PURE__ */ l.jsx(Sbc, { checks: r.checks || [], title: "Automatic checks" })
    ] }),
    /* @__PURE__ */ l.jsxs("h4", { children: [
      "Dimensions ",
      /* @__PURE__ */ l.jsx("span", { className: "count", children: p[0] })
    ] }),
    /* @__PURE__ */ l.jsxs("table", { className: "table compact sb-table", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", {}),
        /* @__PURE__ */ l.jsx("th", { children: "Name" }),
        /* @__PURE__ */ l.jsx("th", { children: r.multi ? "Table · column" : "Column" }),
        /* @__PURE__ */ l.jsx("th", { children: "Definition" })
      ] }) }),
      /* @__PURE__ */ l.jsx("tbody", { children: u.dimensions.map((x, N) => /* @__PURE__ */ l.jsxs("tr", { className: x.include === !1 ? "off" : "", children: [
        /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("input", { type: "checkbox", checked: x.include !== !1, onChange: (g) => m("dimensions", N, { include: g.target.checked }) }) }),
        /* @__PURE__ */ l.jsxs("td", { children: [
          /* @__PURE__ */ l.jsx("input", { value: x.name, onChange: (g) => m("dimensions", N, { name: g.target.value }) }),
          x.column === u.time_dimension && /* @__PURE__ */ l.jsx("em", { className: "tdim", children: "time" })
        ] }),
        /* @__PURE__ */ l.jsx("td", { className: "muted small", children: x.table ? `${x.table} · ${x.column}` : x.column }),
        /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("input", { value: x.comment, onChange: (g) => m("dimensions", N, { comment: g.target.value }) }) })
      ] }, `d${N}`)) })
    ] }),
    /* @__PURE__ */ l.jsxs("h4", { children: [
      "Metrics ",
      /* @__PURE__ */ l.jsx("span", { className: "count", children: p[1] + p[2] })
    ] }),
    /* @__PURE__ */ l.jsxs("table", { className: "table compact sb-table", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", {}),
        /* @__PURE__ */ l.jsx("th", { children: "Name" }),
        /* @__PURE__ */ l.jsx("th", { children: "Aggregation" }),
        /* @__PURE__ */ l.jsx("th", { children: "Column" }),
        /* @__PURE__ */ l.jsx("th", { children: "Definition" })
      ] }) }),
      /* @__PURE__ */ l.jsxs("tbody", { children: [
        u.metrics.map((x, N) => /* @__PURE__ */ l.jsxs("tr", { className: x.include === !1 ? "off" : "", children: [
          /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("input", { type: "checkbox", checked: x.include !== !1, onChange: (g) => m("metrics", N, { include: g.target.checked }) }) }),
          /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("input", { value: x.name, onChange: (g) => m("metrics", N, { name: g.target.value }) }) }),
          /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("select", { value: x.agg, onChange: (g) => m("metrics", N, { agg: g.target.value }), children: Ip.map((g) => /* @__PURE__ */ l.jsx("option", { children: g }, g)) }) }),
          /* @__PURE__ */ l.jsx("td", { className: "muted small", children: (x.table ? `${x.table} · ` : "") + (x.column || "rows") }),
          /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("input", { value: x.comment, onChange: (g) => m("metrics", N, { comment: g.target.value }) }) })
        ] }, `m${N}`)),
        (u.ratios || []).map((x, N) => /* @__PURE__ */ l.jsxs("tr", { className: x.include === !1 ? "off" : "", children: [
          /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("input", { type: "checkbox", checked: x.include !== !1, onChange: (g) => m("ratios", N, { include: g.target.checked }) }) }),
          /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("input", { value: x.name, onChange: (g) => m("ratios", N, { name: g.target.value }) }) }),
          /* @__PURE__ */ l.jsx("td", { className: "small", children: "ratio" }),
          /* @__PURE__ */ l.jsxs("td", { className: "muted small", children: [
            x.numerator,
            " ÷ ",
            x.denominator
          ] }),
          /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("input", { value: x.comment, onChange: (g) => m("ratios", N, { comment: g.target.value }) }) })
        ] }, `r${N}`))
      ] })
    ] }),
    ((k = r.notes) == null ? void 0 : k.length) > 0 && /* @__PURE__ */ l.jsxs("details", { open: !0, children: [
      /* @__PURE__ */ l.jsxs("summary", { className: "prov", children: [
        "Validator: ",
        r.notes.length,
        " change",
        r.notes.length > 1 ? "s" : "",
        " to Cortex's draft"
      ] }),
      /* @__PURE__ */ l.jsx("ul", { className: "small sb-notes", children: r.notes.map((x, N) => /* @__PURE__ */ l.jsxs("li", { children: [
        /* @__PURE__ */ l.jsx("span", { className: `tag ${x.action === "dropped" ? "no" : "warn"}`, children: x.action }),
        " ",
        x.item,
        ": ",
        x.why
      ] }, N)) })
    ] }),
    ((c = u.questions) == null ? void 0 : c.length) > 0 && /* @__PURE__ */ l.jsxs("details", { children: [
      /* @__PURE__ */ l.jsx("summary", { className: "prov", children: "Questions this view should answer" }),
      /* @__PURE__ */ l.jsx("ul", { className: "small", children: u.questions.map((x, N) => /* @__PURE__ */ l.jsx("li", { children: x }, N)) })
    ] }),
    /* @__PURE__ */ l.jsxs("details", { children: [
      /* @__PURE__ */ l.jsx("summary", { className: "prov", children: "SQL that will run (source view + CREATE SEMANTIC VIEW)" }),
      /* @__PURE__ */ l.jsxs("pre", { className: "sql-log", children: [
        (h = r.ddl) == null ? void 0 : h.view_sql,
        `

`,
        (f = r.ddl) == null ? void 0 : f.sv_sql
      ] })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "sb-actions", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost", disabled: d, onClick: () => t("sb_tables", {}, "Listing tables…"), children: "← Other table" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost", disabled: d, onClick: () => t("sb_preview", { spec: u }, "Re-validating…"), children: "Re-check" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", disabled: d || !p[1], onClick: () => t("sb_create", { spec: u }, r.multi ? "Creating the semantic view and reconciling totals…" : "Creating the semantic view in Snowflake…"), children: r.multi ? "Approve and create semantic view" : "Create semantic view" })
    ] })
  ] });
}
const Bp = [
  { id: "home", label: "Home", hint: "Ask Cortex to build" },
  { id: "review", label: "Review", hint: "Metrics & outline" },
  { id: "workspace", label: "Dashboard", hint: "Build & publish" }
], Vp = [
  { id: "source", label: "Data sources" },
  { id: "metrics", label: "Field mapping" },
  { id: "layout", label: "Layout templates" }
];
let Wp = 0;
const qp = () => `${Date.now().toString(36)}-${Wp += 1}`;
function Hp({ data: e, emit: t }) {
  const [n, s] = P.useState(null), [r, i] = P.useState(null), [a, u] = P.useState(null), o = P.useRef(e.revision), RT = P.useRef(null);
  P.useEffect(() => {
    const el = RT.current;
    if (!n || !el) return;
    const act = el.getRootNode && el.getRootNode().activeElement, b = act && act.closest ? act.closest("button") : null;
    if (b && el.contains(b)) {
      b.classList.add("is-pressed");
      return () => b.classList.remove("is-pressed");
    }
  }, [n && n.id]);
  P.useEffect(() => {
    e.revision !== o.current && (o.current = e.revision, s(null));
  }, [e.revision]);
  const d = (y, C = {}, k, c = !1) => {
    const h = qp();
    y !== "validate_poll" && s({ id: h, type: y, quiet: c, label: k || Yp(y) }), t({ id: h, type: y, payload: C });
  }, p = {
    defs: P.useMemo(() => {
      var y;
      return Object.fromEntries((((y = e.model) == null ? void 0 : y.metrics) || []).map((C) => [C.id, C.comment || ""]));
    }, [e.model]),
    send: d,
    ask: (y) => {
      i("agent"), d("ask", { question: y }, "Cortex Agent is answering…");
    },
    decide: (y) => u({ title: "", detail: "", owner: "", due: "", ...y }),
    openDecisions: () => i("decisions"),
    drill: (y, C) => {
      var k;
      return d(
        "set_view",
        { filters: { ...((k = e.view) == null ? void 0 : k.filters) || {}, [y]: [C] } },
        `Drilling into ${C}…`
      );
    }
  }, v = e.step, j = { home: !0, review: !!e.draft, source: !0, metrics: !!e.source, layout: !!e.profile, workspace: !!e.spec };
  return /* @__PURE__ */ l.jsxs("div", { className: "aa", ref: RT, children: [
    /* @__PURE__ */ l.jsxs("aside", { className: "rail", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "brand", children: [
        /* @__PURE__ */ l.jsx("span", { className: "flake", children: "❄" }),
        /* @__PURE__ */ l.jsxs("div", { children: [
          /* @__PURE__ */ l.jsx("b", { children: "Analytics Accelerator" }),
          /* @__PURE__ */ l.jsx("small", { children: "Enterprise · Snowflake-native" })
        ] })
      ] }),
      e.viewer_mode ? /* @__PURE__ */ l.jsx("nav", { className: "steps", children: /* @__PURE__ */ l.jsxs("button", { type: "button", className: "step done", onClick: () => d("exit_viewer", {}, "Opening…"), children: [
        /* @__PURE__ */ l.jsx("span", { className: "num", children: "←" }),
        /* @__PURE__ */ l.jsxs("span", { children: [
          /* @__PURE__ */ l.jsx("b", { children: "Home" }),
          /* @__PURE__ */ l.jsx("small", { children: "Published dashboards" })
        ] })
      ] }) }) : /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
        /* @__PURE__ */ l.jsx("nav", { className: "steps", children: Bp.map((y, C) => /* @__PURE__ */ l.jsxs(
          "button",
          {
            type: "button",
            disabled: !j[y.id],
            className: `step ${v === y.id ? "on" : ""} ${j[y.id] ? "done" : ""}`,
            onClick: () => d("go", { step: y.id }, "Opening…"),
            children: [
              /* @__PURE__ */ l.jsx("span", { className: "num", children: C + 1 }),
              /* @__PURE__ */ l.jsxs("span", { children: [
                /* @__PURE__ */ l.jsx("b", { children: y.label }),
                /* @__PURE__ */ l.jsx("small", { children: y.hint })
              ] })
            ]
          },
          y.id
        )) }),
        /* @__PURE__ */ l.jsxs("details", { className: "advanced", open: ["source", "metrics", "layout"].includes(v), children: [
          /* @__PURE__ */ l.jsx("summary", { children: "Advanced setup" }),
          Vp.map((y) => /* @__PURE__ */ l.jsx(
            "button",
            {
              type: "button",
              disabled: !j[y.id],
              className: `adv ${v === y.id ? "on" : ""}`,
              onClick: () => d("go", { step: y.id }, "Opening…"),
              children: y.label
            },
            y.id
          ))
        ] })
      ] }),
      !e.viewer_mode && e.portal_url && /* @__PURE__ */ l.jsxs("nav", { className: "steps portal-nav", children: [
        /* @__PURE__ */ l.jsx("div", { className: "portal-label", children: "For your viewers" }),
        /* @__PURE__ */ l.jsxs("a", { className: "step done portal-link", href: e.portal_url, target: "_blank", rel: "noopener noreferrer", children: [
          /* @__PURE__ */ l.jsx("span", { className: "num", children: "↗" }),
          /* @__PURE__ */ l.jsxs("span", { children: [
            /* @__PURE__ */ l.jsx("b", { children: "Published dashboards" }),
            /* @__PURE__ */ l.jsx("small", { children: "Open the portal" })
          ] })
        ] })
      ] }),
      !e.is_portal && !e.viewer_mode && /* @__PURE__ */ l.jsxs("nav", { className: "steps portal-nav settings-nav review-nav", children: [
        /* @__PURE__ */ l.jsx("div", { className: "portal-label", children: "Review" }),
        /* @__PURE__ */ l.jsxs("button", { type: "button", className: `step done ${r === "requests" ? "on" : ""}`, onClick: () => i("requests"), children: [
          /* @__PURE__ */ l.jsx("span", { className: "num", children: "📥" }),
          /* @__PURE__ */ l.jsxs("span", { children: [/* @__PURE__ */ l.jsx("b", { children: "Change requests" }), /* @__PURE__ */ l.jsx("small", { children: "Sent back to builders" })] }),
          ((e.uat_inbox || {}).badge_requests || 0) > 0 && /* @__PURE__ */ l.jsx("span", { className: "nav-badge red", children: e.uat_inbox.badge_requests })
        ] }),
        /* @__PURE__ */ l.jsxs("button", { type: "button", className: `step done ${r === "recheck" ? "on" : ""}`, onClick: () => i("recheck"), children: [
          /* @__PURE__ */ l.jsx("span", { className: "num", children: "✅" }),
          /* @__PURE__ */ l.jsxs("span", { children: [/* @__PURE__ */ l.jsx("b", { children: "Waiting for my sign-off" }), /* @__PURE__ */ l.jsx("small", { children: "Fixes to re-check" })] }),
          ((e.uat_inbox || {}).badge_recheck || 0) > 0 && /* @__PURE__ */ l.jsx("span", { className: "nav-badge blue", children: e.uat_inbox.badge_recheck })
        ] })
      ] }),
      /* @__PURE__ */ l.jsxs("nav", { className: "steps portal-nav settings-nav", children: [
        /* @__PURE__ */ l.jsx("div", { className: "portal-label", children: "Settings" }),
        !e.is_portal && !e.viewer_mode && /* @__PURE__ */ l.jsxs("button", { type: "button", className: `step done ${r === "theme" ? "on" : ""}`, onClick: () => i("theme"), children: [
          /* @__PURE__ */ l.jsx("span", { className: "num", children: "🎨" }),
          /* @__PURE__ */ l.jsxs("span", { children: [/* @__PURE__ */ l.jsx("b", { children: "Company theme" }), /* @__PURE__ */ l.jsx("small", { children: "Brand colours" })] })
        ] }),
        /* @__PURE__ */ l.jsxs("button", { type: "button", className: `step done ${r === "governance" ? "on" : ""}`, onClick: () => {
          i("governance"), d("quality", {}, "Loading AI ledger…");
        }, children: [
          /* @__PURE__ */ l.jsx("span", { className: "num", children: "🛡" }),
          /* @__PURE__ */ l.jsxs("span", { children: [/* @__PURE__ */ l.jsx("b", { children: "Governance & AI quality" }), /* @__PURE__ */ l.jsx("small", { children: "AI ledger, usage and SQL" })] })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ l.jsxs("main", { className: "main", children: [
      /* @__PURE__ */ l.jsx(UatDownload, { d: e.download, send: d }),
      v !== "home" && /* @__PURE__ */ l.jsx(Kp, { data: e, onDrawer: i, send: d }),
      e.error && /* @__PURE__ */ l.jsxs("div", { className: "alert error", children: [
        "⚠ ",
        e.error
      ] }),
      e.notice && /* @__PURE__ */ l.jsxs("div", { className: "alert ok", children: [
        "✓ ",
        e.notice
      ] }),
      v === "home" && /* @__PURE__ */ l.jsx(Cp, { data: e, send: d, pending: n, onBuilder: () => i("builder") }),
      v === "source" && /* @__PURE__ */ l.jsx(Xp, { data: e, send: d }),
      v === "metrics" && e.model && /* @__PURE__ */ l.jsx(Gp, { data: e, send: d }),
      v === "layout" && /* @__PURE__ */ l.jsx(Zp, { data: e, send: d }),
      v === "review" && e.draft && /* @__PURE__ */ l.jsx(Ep, { data: e, send: d, ctx: p }),
      v === "workspace" && e.spec && /* @__PURE__ */ l.jsx(Dp, { data: e, send: d, ctx: p, pending: n })
    ] }),
    r && /* @__PURE__ */ l.jsxs(
      _p,
      {
        title: { agent: "Cortex Agent", decisions: "Decisions", governance: "Governance & AI quality", builder: "Connect a table · semantic view drafted by Cortex", theme: "Company theme", requests: "Change requests", recheck: "Waiting for my sign-off" }[r],
        wide: r === "builder" || r === "theme" || r === "requests" || r === "recheck",
        onClose: () => i(null),
        children: [
          e.error && r !== "governance" && /* @__PURE__ */ l.jsx("div", { className: "alert error small drawer-err", children: e.error }),
          r === "agent" && /* @__PURE__ */ l.jsx($p, { data: e, send: d, ctx: p, pending: n }),
          r === "decisions" && /* @__PURE__ */ l.jsx(em, { data: e, send: d, ctx: p }),
          r === "builder" && /* @__PURE__ */ l.jsx(Up, { data: e, send: d, pending: n, onDone: () => i(null) }),
          r === "governance" && /* @__PURE__ */ l.jsx(nm, { data: e, send: d }),
          r === "theme" && /* @__PURE__ */ l.jsx(ThmPanel, { data: e, send: d, pending: n }),
          (r === "requests" || r === "recheck") && /* @__PURE__ */ l.jsx(UatInbox, { data: e, send: d, kind: r, onClose: () => i(null) })
        ]
      }
    ),
    a && /* @__PURE__ */ l.jsx(
      tm,
      {
        draft: a,
        onCancel: () => u(null),
        onSave: (y) => {
          u(null), d("add_decision", y, "Logging decision in Snowflake…");
        }
      }
    ),
    n && /* @__PURE__ */ l.jsx(BusyLayer, { n })
  ] });
}
const AA_STAGES = {
  build_draft: ["Reading the semantic view", "Running governed queries", "Drawing the charts"],
  select_layout: ["Running governed queries", "Running Snowflake ML", "Drawing the charts"],
  compose_layout: ["Reading the data profile", "Cortex is choosing metrics", "Checking every tile against the data"],
  recommend_layout: ["Reading the data profile", "Cortex is recommending a layout"],
  publish: ["Checking the dashboard", "Saving to Snowflake", "Publishing"],
  save_dashboard: ["Saving to Snowflake"],
  page_regenerate: ["Cortex is redesigning the page", "Running governed queries"],
  tile_add: ["Cortex is designing the tile", "Validating against the data", "Running the query"],
  narrative: ["Collecting the governed facts", "Cortex is writing the summary"],
  create_agent: ["Writing the agent definition", "Creating the Cortex Agent"],
  ask: ["Cortex Agent is reading the question", "Querying the governed data", "Writing the answer"],
  select_source: ["Reading the semantic view", "Finding Cortex Agents"],
  set_bindings: ["Profiling the source"],
  sb_draft: ["Profiling the table", "Cortex is drafting the semantic view", "Checking the draft"],
  sb_preview: ["Building a test query", "Running it"],
  sb_create: ["Creating the semantic view", "Checking joins and totals"],
  sb_suggest: ["Reading table names and columns", "Cortex is picking the tables"],
  metric_define: ["Cortex is reading the definition", "Checking the formula"],
  preview_draft: ["Running page 1 with real data"],
  switch_layout: ["Rebuilding the layout"]
};
function BusyLayer({ n: e }) {
  const [t, r] = P.useState(0), s = AA_STAGES[e.type], long = !e.quiet && !!s;
  P.useEffect(() => {
    r(0);
    const a = Date.now(), i = setInterval(() => r(Math.floor((Date.now() - a) / 1e3)), 500);
    return () => clearInterval(i);
  }, [e.id]);
  const cur = s ? Math.min(s.length - 1, Math.floor(t / 5)) : 0;
  const note = t >= 90 ? "Taking longer than usual. Nothing is lost; you can keep waiting." : t >= 25 ? "Still working. Large queries can take a minute." : "";
  return /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
    /* @__PURE__ */ l.jsx("div", { className: "busy-top", children: /* @__PURE__ */ l.jsx("i", {}) }),
    long && /* @__PURE__ */ l.jsx("div", { className: "busy-dim" }),
    long ? /* @__PURE__ */ l.jsxs("div", { className: "busy-card", role: "status", "aria-live": "polite", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "busy-head", children: [/* @__PURE__ */ l.jsx("div", { className: "spinner dark" }), /* @__PURE__ */ l.jsx("b", { children: e.label })] }),
      /* @__PURE__ */ l.jsx("ol", { className: "busy-steps", children: s.map((a, i) => /* @__PURE__ */ l.jsx("li", { className: i < cur ? "done" : i === cur ? "now" : "", children: a }, a)) }),
      /* @__PURE__ */ l.jsxs("div", { className: "busy-foot", children: [/* @__PURE__ */ l.jsx("span", { children: `Working · ${t}s` }), note && /* @__PURE__ */ l.jsx("em", { children: note })] })
    ] }) : !e.quiet && /* @__PURE__ */ l.jsxs("div", { className: "busy", role: "status", children: [
      /* @__PURE__ */ l.jsx("div", { className: "spinner" }),
      /* @__PURE__ */ l.jsx("span", { children: e.label + (t >= 2 ? ` · ${t}s` : "") })
    ] })
  ] });
}
const VAL_ICON = { pass: "✓", accepted: "✓", review: "!", mismatch: "✕", na: "–" }, VAL_TEXT = { pass: "Verified", accepted: "Accepted", review: "Review", mismatch: "Mismatch", na: "Not checked" };
const vfmt = (v) => v == null ? "—" : typeof v === "number" ? (Math.abs(v) >= 1e3 ? v.toLocaleString(void 0, { maximumFractionDigits: 2 }) : String(+v.toPrecision(8))) : String(v);
const VT_TXT = { pass: "Verified", accepted: "Accepted", review: "Review", mismatch: "Mismatch", na: "Not checked", none: "Not validated" };
const VT_HEAD = { pass: "Every number verified", accepted: "Verified, with accepted findings", review: "Validated, with notes to review", mismatch: "Some numbers do not match the source", na: "Validation could not check this dashboard", none: "Not validated yet" };
function ValResolve({ issue: e, send: t, onClose: n }) {
  const [a, u] = P.useState(e.diagnosis && e.diagnosis.action === "issue" ? "issue" : "accept"), [r, s] = P.useState(""), [d, m] = P.useState("30"), [o, c] = P.useState(""), [w, x] = P.useState("");
  return /* @__PURE__ */ l.jsxs("div", { className: "vt-form", children: [
    /* @__PURE__ */ l.jsxs("div", { className: "vt-seg", role: "group", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: a === "accept" ? "on" : "", onClick: () => u("accept"), children: "Accept with reason" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: a === "issue" ? "on" : "", onClick: () => u("issue"), children: "Raise data issue" })
    ] }),
    /* @__PURE__ */ l.jsx("textarea", { rows: 2, value: r, onChange: (y) => s(y.target.value), placeholder: a === "accept" ? "Why is this acceptable? e.g. known late-arriving plan data, confirmed with Finance" : "What needs fixing, e.g. 214 sales rows have a REGION_ID missing from REGIONS" }),
    /* @__PURE__ */ l.jsxs("div", { className: "vt-row", children: [
      a === "accept" ? /* @__PURE__ */ l.jsxs("label", { children: ["Re-open after ", /* @__PURE__ */ l.jsxs("select", { value: d, onChange: (y) => m(y.target.value), children: [
        /* @__PURE__ */ l.jsx("option", { value: "7", children: "7 days" }), /* @__PURE__ */ l.jsx("option", { value: "30", children: "30 days" }), /* @__PURE__ */ l.jsx("option", { value: "90", children: "90 days" })
      ] })] }) : /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
        /* @__PURE__ */ l.jsxs("label", { children: ["Owner ", /* @__PURE__ */ l.jsx("input", { value: o, onChange: (y) => c(y.target.value), placeholder: "name or team" })] }),
        /* @__PURE__ */ l.jsxs("label", { children: ["Due ", /* @__PURE__ */ l.jsx("input", { type: "date", value: w, onChange: (y) => x(y.target.value) })] })
      ] }),
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: a === "accept" ? "Shown as Accepted, never as Verified. Re-opens if the numbers change." : "Logged in Decisions with the evidence attached." }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: n, children: "Cancel" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", disabled: !r.trim() || a === "issue" && !o.trim(), onClick: () => {
        t("val_resolve", { cid: e.cid, action: a, reason: r, days: d, owner: o, due: w }, "Saving…"), n();
      }, children: "Save" })
    ] })
  ] });
}
function ValTab({ data: e, send: t, onTile: n0, onPage: s }) {
  const [sel, setSel] = P.useState(null), evRef = P.useRef(null), n = (cid) => {
    setSel(cid), setTimeout(() => evRef.current && evRef.current.scrollIntoView({ behavior: "smooth", block: "start" }), 60);
  };
  const o = e.validation_overview || {}, job = e.validation_job && e.validation_job.running ? e.validation_job : null, [rf, setRf] = P.useState(null), c = o.counts || {}, st = o.status || "none", hist = e.validation_history || [], lin = o.lineage || {};
  const total = (c.pass || 0) + (c.accepted || 0) + (c.review || 0) + (c.mismatch || 0) + (c.na || 0);
  P.useEffect(() => {
    t("validation_open", {}, "", !0);
  }, []);
  const cell = (v) => /* @__PURE__ */ l.jsx("i", { className: `vt-c ${v || "none"}`, title: v ? VT_TXT[v] : "Not applicable to this tile", children: v ? VAL_ICON[v] || "✓" : "–" });
  return /* @__PURE__ */ l.jsxs("div", { className: "vt", children: [
    /* @__PURE__ */ l.jsxs("div", { className: "vt-score", children: [
      /* @__PURE__ */ l.jsxs("div", { className: `vt-hero ${st}`, children: [
        /* @__PURE__ */ l.jsx("div", { className: "vt-big", children: st === "none" ? "?" : VAL_ICON[st] || "✓" }),
        /* @__PURE__ */ l.jsxs("div", { children: [
          /* @__PURE__ */ l.jsx("h2", { children: job ? "Validating in the background…" : VT_HEAD[st] }),
          /* @__PURE__ */ l.jsx("p", { children: job ? `${job.done} of ${job.total || "?"} checks · ${job.tiles_done} of ${job.tiles_total} tiles done · you can keep working` : "Every number is re-derived from the base tables, independently of the semantic view." })
        ] })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "vt-k", children: [/* @__PURE__ */ l.jsx("small", { children: "Pages checked" }), /* @__PURE__ */ l.jsx("b", { children: `${o.pages_checked || 0} / ${o.pages_total || 0}` }), /* @__PURE__ */ l.jsx("span", { children: o.pages_checked === o.pages_total ? "all pages" : "open the rest or validate all" })] }),
      /* @__PURE__ */ l.jsxs("div", { className: "vt-k", children: [/* @__PURE__ */ l.jsx("small", { children: "Tiles verified" }), /* @__PURE__ */ l.jsx("b", { children: `${c.pass || 0} / ${total}` }), /* @__PURE__ */ l.jsx("span", { children: [c.mismatch ? `${c.mismatch} mismatch` : "", c.review ? `${c.review} review` : "", c.accepted ? `${c.accepted} accepted` : "", c.na ? `${c.na} not checked` : ""].filter(Boolean).join(" · ") || "nothing open" })] }),
      /* @__PURE__ */ l.jsxs("div", { className: "vt-k", children: [/* @__PURE__ */ l.jsx("small", { children: "Values compared" }), /* @__PURE__ */ l.jsx("b", { children: (o.values_compared || 0).toLocaleString() }), /* @__PURE__ */ l.jsx("span", { children: o.queries != null ? `last run: ${o.queries} independent queries` : "—" })] }),
      /* @__PURE__ */ l.jsxs("div", { className: "vt-k", children: [/* @__PURE__ */ l.jsx("small", { children: "Last run" }), /* @__PURE__ */ l.jsx("b", { children: o.at ? String(o.at).slice(11) : "—" }), /* @__PURE__ */ l.jsx("span", { children: o.at ? `${String(o.at).slice(0, 10)}${o.seconds ? ` · took ${o.seconds}s` : ""}` : "not run yet" })] }),
      /* @__PURE__ */ l.jsxs("div", { className: "vt-acts", children: [
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", disabled: !!job, onClick: () => t("validate_all", {}, "Validating all pages in the background…", !0), children: "Validate all pages" }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost", disabled: !!job, onClick: () => t("validate_all", { force: !0 }, "Re-checking every tile…", !0), children: "Re-run everything" })
      ] })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "vt-grid", children: [
      /* @__PURE__ */ l.jsxs("section", { className: "vt-card", children: [
        /* @__PURE__ */ l.jsx("h3", { children: "Check matrix" }),
        /* @__PURE__ */ l.jsx("div", { className: "vt-sub", children: "Every tile × every check. Click a row for its evidence: expected vs actual and both SQL statements." }),
        /* @__PURE__ */ l.jsx("div", { className: "vt-tw", children: /* @__PURE__ */ l.jsxs("table", { className: "vt-m", children: [
          /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [/* @__PURE__ */ l.jsx("th", { children: "Tile" }), /* @__PURE__ */ l.jsx("th", { children: "Status" }), (o.checks || []).map((k) => /* @__PURE__ */ l.jsx("th", { title: `${k.id} ${k.name}`, children: { "QA-01": "Source", "QA-02": "Math", "QA-03": "Totals", "QA-04": "Joins", "QA-05": "Periods", "QA-06": "Health", "QA-07": "Filters" }[k.id] || k.name }, k.id))] }) }),
          /* @__PURE__ */ l.jsx("tbody", { children: (o.pages || []).map((pg) => /* @__PURE__ */ l.jsxs(P.Fragment, { children: [
            /* @__PURE__ */ l.jsx("tr", { className: "vt-pg", children: /* @__PURE__ */ l.jsxs("td", { colSpan: 2 + (o.checks || []).length, children: [pg.label, !pg.checked && /* @__PURE__ */ l.jsx("em", { children: " · not checked yet" })] }) }),
            pg.tiles.map((ti) => /* @__PURE__ */ l.jsxs("tr", { className: "vt-r", onClick: () => ti.status !== "none" ? n(ti.cid, pg.page_id) : s(pg.page_id), children: [
              /* @__PURE__ */ l.jsx("td", { className: "vt-tn", children: ti.title }),
              /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("span", { className: `vpill ${ti.status === "none" ? "na" : ti.status}`, children: VT_TXT[ti.status] }) }),
              (o.checks || []).map((k) => /* @__PURE__ */ l.jsx("td", { children: cell(ti.cells[k.id]) }, k.id))
            ] }, ti.cid))
          ] }, pg.page_id)) })
        ] }) })
      ] }),
      sel && ((V0) => {
        const tv = ((e.validation || {}).tiles || {})[sel];
        return tv ? /* @__PURE__ */ l.jsxs("section", { className: "vt-card vt-ev", ref: evRef, children: [
          /* @__PURE__ */ l.jsxs("div", { className: "vr-tile-head", children: [/* @__PURE__ */ l.jsx("h3", { children: `Evidence · ${tv.title}` }), /* @__PURE__ */ l.jsxs("span", { children: [/* @__PURE__ */ l.jsx("span", { className: `vpill ${tv.status_eff || tv.status}`, children: VAL_TEXT[tv.status_eff || tv.status] }), " ", /* @__PURE__ */ l.jsx("button", { type: "button", className: "addpage-close", "aria-label": "Close evidence", onClick: () => setSel(null), children: "×" })] })] }),
          (tv.checks || []).map((y, i) => /* @__PURE__ */ l.jsx(ValCheck, { c: y, open: i === 0 }, y.id + i))
        ] }) : null;
      })(),
      /* @__PURE__ */ l.jsxs("div", { className: "vt-side", children: [
        /* @__PURE__ */ l.jsxs("section", { className: "vt-card", children: [
          /* @__PURE__ */ l.jsx("h3", { children: "Needs attention" }),
          /* @__PURE__ */ l.jsx("div", { className: "vt-sub", children: "Every finding ends fixed, accepted with a reason, or owned." }),
          (o.issues || []).length ? o.issues.map((is, ix) => {
            const dg = is.diagnosis, rs = is.resolution, key = is.cid || is.check + ix;
            return /* @__PURE__ */ l.jsxs("div", { className: "vt-issue", children: [
              /* @__PURE__ */ l.jsxs("div", { className: "vt-ih", children: [
                /* @__PURE__ */ l.jsx("span", { className: `vpill ${is.status}`, children: VT_TXT[is.status] }),
                /* @__PURE__ */ l.jsxs("div", { children: [/* @__PURE__ */ l.jsx("b", { children: is.title }), /* @__PURE__ */ l.jsx("small", { children: `${is.page} · ${is.check} ${is.check_name}` })] })
              ] }),
              /* @__PURE__ */ l.jsx("p", { className: "vt-sum", children: is.summary }),
              dg && /* @__PURE__ */ l.jsxs("div", { className: `vt-diag ${dg.proven ? "proven" : "open"}`, children: [
                /* @__PURE__ */ l.jsxs("div", { className: "vt-dt", children: [/* @__PURE__ */ l.jsx("em", { children: dg.proven ? "Cause found · explains the whole difference" : "Diagnosis" }), /* @__PURE__ */ l.jsx("b", { children: dg.title })] }),
                /* @__PURE__ */ l.jsx("p", { children: dg.explain }),
                dg.where && /* @__PURE__ */ l.jsxs("p", { children: [/* @__PURE__ */ l.jsx("strong", { children: "Where to fix: " }), dg.where] }),
                dg.fix && /* @__PURE__ */ l.jsxs("p", { children: [/* @__PURE__ */ l.jsx("strong", { children: "Fix: " }), dg.fix] }),
                (dg.ruled_out || []).length > 0 && dg.proven && /* @__PURE__ */ l.jsx("p", { className: "vt-ro", children: "Ruled out first: " + dg.ruled_out.join("; ") })
              ] }),
              rs && /* @__PURE__ */ l.jsxs("div", { className: "vt-res", children: [/* @__PURE__ */ l.jsx("b", { children: rs.action === "data_issue" ? `Owned by ${rs.owner || "—"}${rs.due_date ? ` · due ${rs.due_date}` : ""}` : `Accepted by ${rs.created_by || "—"}${rs.expires_at ? ` until ${rs.expires_at}` : ""}` }), /* @__PURE__ */ l.jsx("span", { children: rs.reason })] }),
              rf === key ? /* @__PURE__ */ l.jsx(ValResolve, { issue: is, send: t, onClose: () => setRf(null) }) : /* @__PURE__ */ l.jsxs("div", { className: "vt-ia", children: [
                dg && dg.action === "refresh" && /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", onClick: () => t("refresh", { page_id: is.page_id }, "Refreshing live data…"), children: "Refresh dashboard" }),
                is.check === "QA-08" && /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", onClick: () => t("narrative", { page_id: is.page_id }, "Cortex is rewriting the summary…"), children: "Regenerate summary" }),
                is.cid && /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => n(is.cid, is.page_id), children: "Evidence" }),
                is.cid && /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => t("validate", { page_id: is.page_id, cids: [is.cid] }, "Re-checking the tile…", !0), children: "Re-run" }),
                is.cid && !rs && /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => setRf(key), children: "Resolve…" }),
                is.page_id && /* @__PURE__ */ l.jsx("button", { type: "button", className: "link small", onClick: () => s(is.page_id), children: "Go to page →" })
              ] })
            ] }, key);
          }) : /* @__PURE__ */ l.jsx("div", { className: "vt-none", children: st === "none" ? "Nothing validated yet. Use Validate all pages." : "No open findings." })
        ] }),
        /* @__PURE__ */ l.jsxs("section", { className: "vt-card", children: [
          /* @__PURE__ */ l.jsx("h3", { children: "What was checked against" }),
          /* @__PURE__ */ l.jsx("div", { className: "vt-sub", children: "Semantic view → base tables, read directly (not through the view)" }),
          /* @__PURE__ */ l.jsxs("div", { className: "vt-lin", children: [
            /* @__PURE__ */ l.jsxs("div", { className: "vt-node", children: [/* @__PURE__ */ l.jsx("b", { children: (lin.view || "").split(".").pop() || "—" }), /* @__PURE__ */ l.jsx("span", { children: "semantic view" })] }),
            /* @__PURE__ */ l.jsx("span", { className: "vt-arrow", children: "→" }),
            /* @__PURE__ */ l.jsxs("div", { className: "vt-node", children: [/* @__PURE__ */ l.jsx("b", { children: `${(lin.tables || []).length} base table${(lin.tables || []).length === 1 ? "" : "s"}` }), /* @__PURE__ */ l.jsx("span", { title: (lin.tables || []).join("\n"), children: (lin.tables || []).map((x) => x.split(".").pop()).join(", ") || "—" })] })
          ] }),
          (lin.joins || []).length > 0 ? /* @__PURE__ */ l.jsxs("table", { className: "vt-j", children: [
            /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [/* @__PURE__ */ l.jsx("th", { children: "Join" }), /* @__PURE__ */ l.jsx("th", { children: "Keys unique" }), /* @__PURE__ */ l.jsx("th", { children: "Rows with no match" })] }) }),
            /* @__PURE__ */ l.jsx("tbody", { children: lin.joins.map((j) => /* @__PURE__ */ l.jsxs("tr", { children: [
              /* @__PURE__ */ l.jsx("td", { children: `${j.left} → ${j.right}` }),
              /* @__PURE__ */ l.jsx("td", { className: j.unique ? "ok" : "bad", children: j.unique ? "✓" : `✕ ${(j.lookup_rows - j.distinct_keys).toLocaleString()} duplicates` }),
              /* @__PURE__ */ l.jsx("td", { className: j.orphans ? "warn" : "ok", children: j.orphans ? j.orphans.toLocaleString() : "0" })
            ] }, j.name)) })
          ] }) : /* @__PURE__ */ l.jsx("div", { className: "vt-none", children: (lin.tables || []).length ? "Single base table per tile: no joins needed." : "Shown after the first validation run." }),
          (lin.nonadd_from_ddl || []).length > 0 && /* @__PURE__ */ l.jsx("p", { className: "vt-ro", children: "End-of-period rules read from the view definition: " + lin.nonadd_from_ddl.join(", ") })
        ] }),
        /* @__PURE__ */ l.jsxs("section", { className: "vt-card", children: [
          /* @__PURE__ */ l.jsx("h3", { children: "Run history" }),
          /* @__PURE__ */ l.jsx("div", { className: "vt-sub", children: "Stored in AA_VALIDATION_RUNS, one row per page run" }),
          hist.length ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
            /* @__PURE__ */ l.jsx("div", { className: "vt-bars", children: hist.slice().reverse().map((h, ix) => /* @__PURE__ */ l.jsx("i", { className: h.status, title: `${h.run_at} · ${h.page_id} · ${VT_TXT[h.status] || h.status}` }, ix)) }),
            /* @__PURE__ */ l.jsx("div", { className: "vt-runs", children: hist.slice(0, 5).map((h, ix) => /* @__PURE__ */ l.jsxs("div", { children: [
              /* @__PURE__ */ l.jsx("span", { children: `${h.run_at} · ${h.run_by || "—"}` }),
              /* @__PURE__ */ l.jsx("span", { className: `vpill ${h.status}`, children: `${h.verified || 0} / ${h.tiles || 0} verified` })
            ] }, ix)) })
          ] }) : /* @__PURE__ */ l.jsx("div", { className: "vt-none", children: "No runs stored yet." })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ l.jsx(UatPanel, { data: e, send: t, onTile: (cid) => n(cid) })
  ] });
}
/* ---- Business sign-off (16 Oct, v2): steps, numbers check vs your decision, fix-and-re-check loop,
   Change requests / Waiting for my sign-off lists ---- */
const UAT_TILE = { accepted: "Looks right", rejected: "Needs change", fixed: "Fixed – please re-check", replied: "Builder replied", pending: "To review", changed: "Changed – please re-check" };
const UAT_TXT = { approved: "Signed off", approved_notes: "Signed off with notes", rejected: "Sent back for changes", changed: "Changed – sign off again", ready: "Ready to sign off", in_review: "In progress", not_started: "Not started" };
const UAT_MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function uatDate(s, time) {
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}:\d{2}))?/.exec(String(s || ""));
  return m ? `${+m[3]} ${UAT_MON[+m[2] - 1]}${time !== !1 && m[4] ? " " + m[4] : ""}` : String(s || "");
}
function uatWho(s) {
  const v = String(s || "");
  return v.includes("@") ? v.split("@")[0] : v;
}
function UatReason({ need, chips, placeholder, cta, onSave, onCancel, danger }) {
  const [chip, setChip] = P.useState(""), [txt, setTxt] = P.useState("");
  const comment = [chip, txt.trim()].filter(Boolean).join(" – "), ok = !need || !!comment;
  return /* @__PURE__ */ l.jsxs("div", { className: "uat-why", children: [
    /* @__PURE__ */ l.jsx("b", { children: need === "mismatch" ? "The numbers differ. Why is it OK to approve?" : need === "change" ? "What needs to change?" : "Comment (optional)" }),
    chips && chips.length > 0 && /* @__PURE__ */ l.jsx("div", { className: "uat-chips", children: [...chips, "Other"].map((c) => /* @__PURE__ */ l.jsx("button", { type: "button", className: `uat-chip ${chip === c ? "on" : ""}`, onClick: () => setChip(chip === c ? "" : c === "Other" ? "" : c), children: c }, c)) }),
    /* @__PURE__ */ l.jsx("input", { autoFocus: !chips, value: txt, maxLength: 1500, onChange: (x) => setTxt(x.target.value), onKeyDown: (x) => x.key === "Enter" && ok && onSave(comment), placeholder }),
    /* @__PURE__ */ l.jsxs("div", { className: "uat-why-acts", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: `btn small ${danger ? "danger" : ""}`, disabled: !ok, onClick: () => onSave(comment), children: cta }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: onCancel, children: "Cancel" })
    ] })
  ] });
}
function UatThread({ thread }) {
  if (!thread || thread.length < 2) return null;
  return /* @__PURE__ */ l.jsx("div", { className: "uat-thread", children: thread.slice(1).map((m, ix) => /* @__PURE__ */ l.jsxs("div", { className: `uat-msg ${m.decision}`, children: [
    /* @__PURE__ */ l.jsx("b", { children: { fixed: "Builder fixed it", replied: "Builder replied", rejected: "Still needs change", accepted: "Looks right" }[m.decision] || m.decision }),
    /* @__PURE__ */ l.jsx("small", { children: ` · ${uatWho(m.by)} · ${uatDate(m.at)}` }),
    m.comment && /* @__PURE__ */ l.jsx("div", { children: `“${m.comment}”` })
  ] }, ix)) });
}
function UatTile({ r: e, send: t, reasons, onDetails }) {
  const [mode, setMode] = P.useState(null), [rq, setRq] = P.useState(e.requirement || ""), [edReq, setEdReq] = P.useState(!1);
  P.useEffect(() => setRq(e.requirement || ""), [e.requirement]);
  P.useEffect(() => setMode(null), [e.state, e.at]);
  const ck = e.check || { status: e.validation, text: "" }, mism = e.validation === "mismatch", none = e.validation === "none";
  const go = (d, cm) => (t("uat_tile", { cid: e.cid, decision: d, comment: cm || "" }, d === "accepted" ? "Recording your decision…" : "Sending the change request…"), setMode(null));
  const decided = e.state !== "pending" && !mode, recheck = e.state === "fixed" || e.state === "replied" || e.state === "changed";
  const saveReq = () => (setEdReq(!1), rq !== (e.requirement || "") && t("uat_requirement", { cid: e.cid, text: rq }, "", !0));
  const buttons = /* @__PURE__ */ l.jsxs("div", { className: "uat-acts", children: [
    /* @__PURE__ */ l.jsx("button", { type: "button", className: "uat-b good", disabled: none, title: none ? "Check the numbers first (Validate all pages)" : "", onClick: () => mism ? setMode("accept") : go("accepted"), children: "✓ Looks right" }),
    /* @__PURE__ */ l.jsx("button", { type: "button", className: "uat-b bad", disabled: none, onClick: () => setMode("change"), children: recheck ? "✎ Still needs change" : "✎ Needs change" }),
    mode === "pick" && /* @__PURE__ */ l.jsx("button", { type: "button", className: "uat-link", onClick: () => setMode(null), children: "Cancel" })
  ] });
  return /* @__PURE__ */ l.jsxs("div", { className: `uat-row ${e.state}`, children: [
    /* @__PURE__ */ l.jsxs("div", { className: "uat-c1", children: [
      /* @__PURE__ */ l.jsx("b", { children: e.title }),
      e.question && /* @__PURE__ */ l.jsx("span", { className: "uat-q", children: e.question }),
      edReq ? /* @__PURE__ */ l.jsx("input", { className: "uat-req", autoFocus: !0, value: rq, maxLength: 300, placeholder: "Requirement / BRD ref, e.g. BRD-4.2", onChange: (x) => setRq(x.target.value), onBlur: saveReq, onKeyDown: (x) => x.key === "Enter" && saveReq() }) : /* @__PURE__ */ l.jsx("button", { type: "button", className: "uat-link", onClick: () => setEdReq(!0), children: e.requirement ? `🔗 ${e.requirement}` : "+ Link requirement" })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "uat-c2", children: [
      /* @__PURE__ */ l.jsxs("span", { className: `uat-ck ${ck.status}`, children: [{ pass: "✓ ", mismatch: "✕ ", review: "! ", accepted: "✓ ", na: "– ", none: "… " }[ck.status] || "", ck.text || "Not checked yet"] }),
      ck.detail && /* @__PURE__ */ l.jsx("small", { children: ck.detail }),
      !none && onDetails && /* @__PURE__ */ l.jsx("button", { type: "button", className: "uat-link", onClick: () => onDetails(e.cid), children: "See details" })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "uat-c3", children: [
      decided && /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
        /* @__PURE__ */ l.jsx("span", { className: `uat-pill ${e.state}`, children: (e.state === "accepted" ? "✓ " : e.state === "rejected" ? "✎ " : "↻ ") + UAT_TILE[e.state] }),
        e.request && e.state !== "accepted" ? /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
          /* @__PURE__ */ l.jsx("small", { children: `Asked by ${uatWho(e.request.by)} · ${uatDate(e.request.at)}` }),
          e.request.comment && /* @__PURE__ */ l.jsx("small", { className: "uat-cm", children: `“${e.request.comment}”` }),
          /* @__PURE__ */ l.jsx(UatThread, { thread: e.thread })
        ] }) : /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
          e.by && /* @__PURE__ */ l.jsx("small", { children: `${uatWho(e.by)} · ${uatDate(e.at)}` }),
          e.comment && /* @__PURE__ */ l.jsx("small", { className: "uat-cm", children: `“${e.comment}”` }),
          e.state === "changed" && /* @__PURE__ */ l.jsx("small", { className: "uat-warnline", children: "The numbers or layout changed after this decision. Look again." })
        ] }),
        recheck ? buttons : e.state === "rejected" ? /* @__PURE__ */ l.jsx("small", { className: "muted", children: "Waiting for the builder to fix it." }) : null,
        !recheck && /* @__PURE__ */ l.jsx("button", { type: "button", className: "uat-link", onClick: () => setMode("pick"), children: "Change decision" })
      ] }),
      !decided && !mode && buttons,
      !decided && mode === "pick" && buttons,
      mode === "accept" && /* @__PURE__ */ l.jsx(UatReason, { need: "mismatch", chips: reasons, placeholder: "Add detail (optional)…", cta: "Approve tile", onSave: (c) => go("accepted", c), onCancel: () => setMode(null) }),
      mode === "change" && /* @__PURE__ */ l.jsx(UatReason, { need: "change", placeholder: "e.g. Show it by region, not the total", cta: "Send to builder", danger: !0, onSave: (c) => go("rejected", c), onCancel: () => setMode(null) })
    ] })
  ] });
}
function UatPage({ pg: e, send: t, reasons, onDetails }) {
  const signed = e.state === "approved" || e.state === "approved_notes";
  const [open, setOpen] = P.useState(!1), [dec, setDec] = P.useState("approved"), [cm, setCm] = P.useState(""), [fold, setFold] = P.useState(signed);
  P.useEffect(() => setOpen(!1), [e.state, e.signed_at]);
  const notOk = e.total - e.accepted, gaps = e.open_findings || notOk > 0, need = dec === "rejected" || gaps;
  const pct = e.total ? Math.round(100 * e.reviewed / e.total) : 0;
  return /* @__PURE__ */ l.jsxs("div", { className: `uat-page ${e.state}`, children: [
    /* @__PURE__ */ l.jsxs("div", { className: "uat-ph", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "uat-fold", "aria-label": fold ? "Show tiles" : "Hide tiles", onClick: () => setFold(!fold), children: fold ? "▸" : "▾" }),
      /* @__PURE__ */ l.jsx("h4", { children: `Page: ${e.label}` }),
      /* @__PURE__ */ l.jsx("span", { className: "uat-prog", children: /* @__PURE__ */ l.jsx("i", { style: { width: `${pct}%` } }) }),
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: `${e.reviewed} of ${e.total} tiles reviewed` + (e.rejected_tiles ? ` · ${e.rejected_tiles} with the builder` : "") }),
      /* @__PURE__ */ l.jsx("span", { className: "uat-sp" }),
      /* @__PURE__ */ l.jsx("span", { className: `uat-pill ${e.state}`, children: UAT_TXT[e.state] })
    ] }),
    e.signed_by && /* @__PURE__ */ l.jsx("div", { className: "uat-signed", children: `${UAT_TXT[e.state] === "Changed – sign off again" ? "Signed off earlier" : UAT_TXT[e.state]} by ${uatWho(e.signed_by)} · ${uatDate(e.signed_at)}` + (e.comment ? ` · “${e.comment}”` : "") }),
    !fold && /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
      /* @__PURE__ */ l.jsxs("div", { className: "uat-row uat-hd", children: [
        /* @__PURE__ */ l.jsx("span", { children: "Tile" }),
        /* @__PURE__ */ l.jsx("span", { children: "Numbers check (automatic)" }),
        /* @__PURE__ */ l.jsx("span", { children: "Your decision" })
      ] }),
      e.tiles.map((r) => /* @__PURE__ */ l.jsx(UatTile, { r, send: t, reasons, onDetails }, r.cid))
    ] }),
    open ? /* @__PURE__ */ l.jsxs("div", { className: "uat-sign", children: [
      /* @__PURE__ */ l.jsx("div", { className: "uat-dec", role: "radiogroup", children: [["approved", "Sign off"], ["rejected", "Send back for changes"]].map(([k, v]) => /* @__PURE__ */ l.jsx("button", { type: "button", className: `seg ${dec === k ? "on" : ""}`, onClick: () => setDec(k), children: v }, k)) }),
      dec !== "rejected" && gaps && /* @__PURE__ */ l.jsx("div", { className: "uat-warn", children: [notOk ? `${notOk} tile(s) not marked Looks right` : "", e.open_findings ? `${e.open_findings} tile(s) where the numbers differ` : ""].filter(Boolean).join(" · ") + ". You can still sign off: give the reason. It is recorded as Signed off with notes." }),
      /* @__PURE__ */ l.jsx("textarea", { rows: 2, autoFocus: !0, value: cm, onChange: (x) => setCm(x.target.value), placeholder: dec === "rejected" ? "Why is the page sent back? (required)" : need ? "Reason (required), e.g. Approved for go-live; region view follows in the next release" : "Comment (optional)" }),
      /* @__PURE__ */ l.jsxs("div", { className: "uat-sact", children: [
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => setOpen(!1), children: "Cancel" }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: `btn small ${dec === "rejected" ? "danger" : ""}`, disabled: need && !cm.trim(), onClick: () => t("uat_page", { page_id: e.page_id, decision: dec, comment: cm }, "Recording the sign-off…"), children: dec === "rejected" ? "Send back" : gaps ? "Sign off with notes" : "Sign off page" })
      ] })
    ] }) : /* @__PURE__ */ l.jsxs("div", { className: "uat-pfoot", children: [
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: signed ? "Signed off. It re-opens by itself if a tile on this page changes." : gaps ? "You can sign off with open items. They are listed on the sign-off and it is recorded as Signed off with notes." : "Every tile looks right. Sign the page off." }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: signed ? "ghost small" : "btn small", onClick: () => (setOpen(!0), setDec("approved"), setCm("")), children: signed || e.state === "rejected" ? "Sign off again…" : "Sign off this page…" })
    ] })
  ] });
}
const UAT_STEPS = [["Numbers checked", "Automatic"], ["Review tiles", ""], ["Sign off pages", ""], ["Ready to publish", ""]];
function UatSteps({ u }) {
  const cur = (u.next || {}).step || 1, tiles = u.pages.reduce((a, p) => a + p.total, 0), rev = u.pages.reduce((a, p) => a + p.reviewed, 0);
  const sub = ["Automatic", `${rev} of ${tiles} reviewed`, `${u.pages_signed} of ${u.pages_total} signed off`, cur === 4 ? "Done" : ""];
  return /* @__PURE__ */ l.jsx("div", { className: "uat-steps", children: UAT_STEPS.map(([b], ix) => /* @__PURE__ */ l.jsxs("div", { className: `uat-step ${ix + 1 < cur ? "done" : ix + 1 === cur ? "now" : ""}`, children: [
    /* @__PURE__ */ l.jsx("span", { className: "n", children: ix + 1 < cur ? "✓" : ix + 1 }),
    /* @__PURE__ */ l.jsxs("div", { children: [/* @__PURE__ */ l.jsx("b", { children: b }), /* @__PURE__ */ l.jsx("small", { children: sub[ix] })] })
  ] }, b)) });
}
function UatPanel({ data: e, send: t, onTile }) {
  const u = e.uat, [dl, setDl] = P.useState(!1), [ref, setRef] = P.useState(""), [rc, setRc] = P.useState(""), [ts, setTs] = P.useState(e.viewer || "");
  if (!u) return null;
  return /* @__PURE__ */ l.jsxs("section", { className: "vt-card uat", children: [
    /* @__PURE__ */ l.jsxs("div", { className: "uat-head", children: [
      /* @__PURE__ */ l.jsxs("div", { children: [
        /* @__PURE__ */ l.jsx("h3", { children: "Business sign-off" }),
        /* @__PURE__ */ l.jsx("div", { className: "vt-sub", children: "A business owner confirms each tile shows what was asked for, then signs each page off for go-live. Every decision is saved in Snowflake with who and when." })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "uat-sum", children: [
        /* @__PURE__ */ l.jsx("span", { className: `uat-pill big ${u.status}`, children: UAT_TXT[u.status] }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => setDl(!dl), children: "⤓ Download UAT pack" })
      ] })
    ] }),
    dl && /* @__PURE__ */ l.jsxs("div", { className: "uat-dl", children: [
      /* @__PURE__ */ l.jsxs("label", { children: ["Change / reference no.", /* @__PURE__ */ l.jsx("input", { value: ref, onChange: (x) => setRef(x.target.value), placeholder: "e.g. CHG0045153" })] }),
      /* @__PURE__ */ l.jsxs("label", { children: ["Testers", /* @__PURE__ */ l.jsx("input", { value: ts, onChange: (x) => setTs(x.target.value) })] }),
      /* @__PURE__ */ l.jsxs("label", { children: ["Recipients", /* @__PURE__ */ l.jsx("input", { value: rc, onChange: (x) => setRc(x.target.value), placeholder: "Names, comma-separated" })] }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", onClick: () => (t("uat_download", { reference: ref, testers: ts, recipients: rc }, "Building the UAT workbook…"), setDl(!1)), children: "Download (.xlsx)" }),
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "Optional. Corporate UAT format with the full review history, for a change ticket." })
    ] }),
    /* @__PURE__ */ l.jsx(UatSteps, { u }),
    u.next && /* @__PURE__ */ l.jsxs("div", { className: `uat-next s${u.next.step}`, children: [/* @__PURE__ */ l.jsx("b", { children: u.next.step === 4 ? "Done: " : "Next step: " }), u.next.text] }),
    u.pages.map((pg) => /* @__PURE__ */ l.jsx(UatPage, { pg, send: t, reasons: u.reasons, onDetails: onTile ? (cid) => onTile(cid, pg.page_id) : null }, pg.page_id))
  ] });
}
/* The change request on a tile, shown to the builder on the dashboard itself */
function UatNote({ r: e, send: t, focus }) {
  const [mode, setMode] = P.useState(null), [txt, setTxt] = P.useState("");
  P.useEffect(() => (setMode(null), setTxt("")), [e && e.state, e && e.at]);
  if (!e || !e.request || !["rejected", "fixed", "replied"].includes(e.state)) return null;
  const q = e.request, go = (d) => t("uat_builder", { cid: e.cid, decision: d, comment: txt }, d === "fixed" ? "Marking as fixed…" : "Sending your reply…");
  return /* @__PURE__ */ l.jsxs("div", { className: `uat-note ${e.state} ${focus ? "focus" : ""}`, children: [
    /* @__PURE__ */ l.jsxs("div", { className: "uat-note-h", children: [
      /* @__PURE__ */ l.jsx("b", { children: e.state === "rejected" ? "✎ Change requested" : e.state === "fixed" ? "✓ Marked as fixed – waiting for re-check" : "↩ Replied – waiting for the reviewer" }),
      /* @__PURE__ */ l.jsx("small", { children: `${uatWho(q.by)} · ${uatDate(q.at)}` })
    ] }),
    q.comment && /* @__PURE__ */ l.jsx("div", { className: "uat-note-q", children: `“${q.comment}”` }),
    /* @__PURE__ */ l.jsx(UatThread, { thread: e.thread }),
    mode ? /* @__PURE__ */ l.jsxs("div", { className: "uat-note-f", children: [
      /* @__PURE__ */ l.jsx("input", { autoFocus: !0, value: txt, maxLength: 1500, onChange: (x) => setTxt(x.target.value), onKeyDown: (x) => x.key === "Enter" && (mode === "fixed" || txt.trim()) && go(mode), placeholder: mode === "fixed" ? "What did you change? (optional)" : "Your reply to the reviewer (required)" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", disabled: mode === "replied" && !txt.trim(), onClick: () => go(mode), children: mode === "fixed" ? "Mark as fixed" : "Send reply" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => setMode(null), children: "Cancel" })
    ] }) : /* @__PURE__ */ l.jsxs("div", { className: "uat-note-a", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", onClick: () => setMode("fixed"), children: e.state === "rejected" ? "Mark as fixed" : "Mark as fixed again" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => setMode("replied"), children: "Reply" })
    ] })
  ] });
}
/* Change requests (builders) and Waiting for my sign-off (reviewers): one list across all dashboards */
function UatInbox({ data: e, send: t, kind, onClose }) {
  const ib = e.uat_inbox || { rows: [] }, req = kind === "requests";
  const [mine, setMine] = P.useState(!0), [st, setSt] = P.useState(req ? "open" : "waiting"), [db, setDb] = P.useState(""), [own, setOwn] = P.useState(null), [ownTxt, setOwnTxt] = P.useState("");
  P.useEffect(() => {
    t("uat_inbox", {}, "", !0);
  }, [kind]);
  P.useEffect(() => setSt(req ? "open" : "waiting"), [kind]);
  const mineRows = ib.rows.filter((r) => !mine || (req ? r.mine_owner : r.mine_reviewer));
  const match = (r) => st === "all" || (st === "open" ? r.state === "rejected" : st === "waiting" ? r.state === "fixed" || r.state === "replied" : r.state === st);
  const rows = mineRows.filter((r) => match(r) && (!db || r.dashboard_id === db));
  const cnt = (f) => mineRows.filter(f).length;
  const kpis = req ? [
    ["red", cnt((r) => r.state === "rejected"), "Open – need a fix", "open"],
    ["blue", cnt((r) => r.state === "fixed"), "Fixed – waiting for reviewer", "fixed"],
    ["amber", cnt((r) => r.state === "replied"), "Replied – waiting for reviewer", "replied"],
    ["green", ib.closed_30d || 0, "Closed in the last 30 days", null]
  ] : [
    ["blue", cnt((r) => r.state === "fixed" || r.state === "replied"), "Waiting for your re-check", "waiting"],
    ["red", cnt((r) => r.state === "rejected"), "Still with the builder", "open"],
    ["green", ib.closed_30d || 0, "Closed in the last 30 days", null]
  ];
  const groups = [];
  rows.forEach((r) => {
    let g = groups.find((x) => x.id === r.dashboard_id);
    g || groups.push(g = { id: r.dashboard_id, name: r.dashboard_name, owner: r.owner, rows: [] });
    g.rows.push(r);
  });
  const dashes = [...new Map(ib.rows.map((r) => [r.dashboard_id, r.dashboard_name])).entries()];
  return /* @__PURE__ */ l.jsxs("div", { className: "uat-inbox", children: [
    /* @__PURE__ */ l.jsx("p", { className: "muted", children: req ? "Everything reviewers have sent back, across all dashboards. Open the tile, fix it, then click Mark as fixed (or Reply if it can't be done)." : "Tiles the builder has fixed or answered, across all dashboards. Open the tile and look again: Looks right closes the request." }),
    /* @__PURE__ */ l.jsx("div", { className: "uat-kpis", children: kpis.map(([c, n, lab, f]) => /* @__PURE__ */ l.jsxs("button", { type: "button", className: `uat-kpi ${c} ${f && st === f ? "on" : ""}`, disabled: !f, onClick: () => f && setSt(f), children: [/* @__PURE__ */ l.jsx("b", { children: n }), /* @__PURE__ */ l.jsx("span", { children: lab })] }, lab)) }),
    /* @__PURE__ */ l.jsxs("div", { className: "uat-filters", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: `uat-f ${mine ? "on" : ""}`, onClick: () => setMine(!0), children: req ? "My dashboards" : "Asked by me" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: `uat-f ${!mine ? "on" : ""}`, onClick: () => setMine(!1), children: req ? "All builders" : "All reviewers" }),
      /* @__PURE__ */ l.jsxs("select", { value: st, onChange: (x) => setSt(x.target.value), children: [
        /* @__PURE__ */ l.jsx("option", { value: "open", children: "Status: Needs change" }),
        /* @__PURE__ */ l.jsx("option", { value: "waiting", children: "Status: Waiting for re-check" }),
        /* @__PURE__ */ l.jsx("option", { value: "fixed", children: "Status: Fixed" }),
        /* @__PURE__ */ l.jsx("option", { value: "replied", children: "Status: Replied" }),
        /* @__PURE__ */ l.jsx("option", { value: "all", children: "Status: All open" })
      ] }),
      /* @__PURE__ */ l.jsxs("select", { value: db, onChange: (x) => setDb(x.target.value), children: [
        /* @__PURE__ */ l.jsx("option", { value: "", children: "Dashboard: All" }),
        dashes.map(([id, n]) => /* @__PURE__ */ l.jsx("option", { value: id, children: n }, id))
      ] }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => t("uat_inbox", {}, "Refreshing…", !0), children: "↻" })
    ] }),
    ib.error && /* @__PURE__ */ l.jsx("div", { className: "alert error small", children: ib.error }),
    !groups.length && /* @__PURE__ */ l.jsx("div", { className: "uat-empty", children: req ? mine && ib.rows.length ? "Nothing here for your dashboards. Switch to All builders to see the team's list." : "No change requests. When a reviewer marks a tile Needs change, it shows up here." : "Nothing is waiting for you. When a builder fixes a tile you sent back, it shows up here." }),
    groups.map((g) => /* @__PURE__ */ l.jsxs("div", { className: "uat-grp", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "uat-gh", children: [
        /* @__PURE__ */ l.jsx("b", { children: g.name }),
        /* @__PURE__ */ l.jsx("span", { className: "muted small", children: `${g.rows.length} item(s)` + ((mx) => mx > 0 ? ` · oldest ${mx} day${mx === 1 ? "" : "s"}` : " · raised today")(g.rows.reduce((a, r) => Math.max(a, r.state === "rejected" ? r.age_days || 0 : 0), 0)) }),
        /* @__PURE__ */ l.jsx("span", { className: "uat-sp" }),
        req && (own === g.id ? /* @__PURE__ */ l.jsxs("span", { className: "uat-own", children: [
          /* @__PURE__ */ l.jsx("input", { autoFocus: !0, value: ownTxt, onChange: (x) => setOwnTxt(x.target.value), placeholder: "Snowflake user name" }),
          /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", disabled: !ownTxt.trim(), onClick: () => (t("uat_owner", { dashboard_id: g.id, owner: ownTxt }, "Handing over…"), setOwn(null)), children: "Hand over" }),
          /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => setOwn(null), children: "Cancel" })
        ] }) : /* @__PURE__ */ l.jsxs("span", { className: "muted small", children: [`Owner: ${uatWho(g.owner) || "—"} · `, /* @__PURE__ */ l.jsx("button", { type: "button", className: "uat-link", onClick: () => (setOwn(g.id), setOwnTxt("")), children: "Change owner" })] }))
      ] }),
      g.rows.map((r) => /* @__PURE__ */ l.jsxs("div", { className: "uat-ir", children: [
        /* @__PURE__ */ l.jsxs("div", { className: "uat-i1", children: [/* @__PURE__ */ l.jsx("b", { children: r.tile_title }), /* @__PURE__ */ l.jsx("small", { children: `Page: ${r.page_label || r.page_id}` })] }),
        /* @__PURE__ */ l.jsxs("div", { className: "uat-i2", children: [
          /* @__PURE__ */ l.jsx("span", { children: `“${r.request.comment || "—"}”` }),
          /* @__PURE__ */ l.jsx("small", { children: `${uatWho(r.request.by)} · ${uatDate(r.request.at, !1)}` }),
          r.state !== "rejected" && r.last && /* @__PURE__ */ l.jsx("small", { className: "uat-last", children: `${r.state === "fixed" ? "Fixed" : "Reply"}${r.last.comment ? `: “${r.last.comment}”` : ""} · ${uatWho(r.last.by)} · ${uatDate(r.last.at, !1)}` })
        ] }),
        /* @__PURE__ */ l.jsx("div", { className: `uat-age ${r.state === "rejected" && (r.age_days || 0) > 3 ? "old" : ""}`, children: r.state !== "rejected" ? "–" : r.age_days == null ? "" : r.age_days === 0 ? "today" : `${r.age_days} day${r.age_days === 1 ? "" : "s"}` }),
        /* @__PURE__ */ l.jsx("div", { children: /* @__PURE__ */ l.jsx("span", { className: `uat-pill ${r.state}`, children: UAT_TILE[r.state] }) }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "uat-open", onClick: () => (t("uat_open", { dashboard_id: r.dashboard_id, cid: r.cid }, "Opening the tile…"), onClose && onClose()), children: "Open tile →" })
      ] }, r.dashboard_id + r.cid))
    ] }, g.id)),
    /* @__PURE__ */ l.jsx("p", { className: "muted small", children: "Only saved dashboards are listed. Requests are stored in AA_UAT_SIGNOFFS; owners are the dashboard's creator unless handed over." })
  ] });
}
function UatDownload({ d: e, send: t }) {
  P.useEffect(() => {
    if (!e || !e.b64) return;
    try {
      const bin = atob(e.b64), arr = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
      const url = URL.createObjectURL(new Blob([arr], { type: e.mime })), a = document.createElement("a");
      a.href = url, a.download = e.name, document.body.appendChild(a), a.click(), a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 4e3);
    } catch (x) {
    }
    t("download_done", {}, "", !0);
  }, [e && e.id]);
  return null;
}
function ValBadge({ v: e, stale: t, onOpen: n }) {
  if (t) return /* @__PURE__ */ l.jsxs("span", { className: "vbadge checking", title: "Checking these numbers against the base tables", children: [/* @__PURE__ */ l.jsx("i", { className: "vspin" }), "Checking"] });
  if (!e) return null;
  const es = e.status_eff || e.status, tip = (e.checks || []).map((c) => `${c.id} ${c.name}: ${c.label} — ${c.summary}`).join("\n") + (e.resolution ? `\n\nAccepted: ${e.resolution.reason}` : "");
  return /* @__PURE__ */ l.jsxs("button", { type: "button", className: `vbadge ${es}`, title: tip + "\n\nClick for the evidence", onClick: n, children: [/* @__PURE__ */ l.jsx("b", { children: VAL_ICON[es] }), VAL_TEXT[es]] });
}
function ValStrip({ data: e, pageId: t, viewer: n, onOpen: s }) {
  if (n) {
    const pv = (e.dashboard || {}).validation || {};
    if (!pv.status) return null;
    const c = pv.counts || {}, flagged = (c.mismatch || 0) + (c.review || 0);
    return /* @__PURE__ */ l.jsxs("div", { className: `vstrip ${pv.status}`, children: [
      /* @__PURE__ */ l.jsx("b", { className: "vdot", children: VAL_ICON[pv.status] }),
      /* @__PURE__ */ l.jsx("span", { className: "vstrip-t", children: pv.status === "pass" ? "Numbers verified against the source tables" : flagged ? `Published with ${flagged} item(s) flagged for review` : "Published before validation finished" }),
      /* @__PURE__ */ l.jsx("span", { className: "vstrip-m", children: `Checked when published ${pv.at || ""} · ${c.pass || 0} tile(s) verified${pv.pages_total ? ` · ${pv.pages_checked} of ${pv.pages_total} page(s)` : ""}` })
    ] });
  }
  const V = e.validation || {}, pg = (V.pages || {})[t], job = e.validation_job && (e.validation_job.page_ids || [e.validation_job.page_id]).includes(t) && e.validation_job.running ? e.validation_job : null, busy = !!job || (e.validation_needed || []).includes(t);
  if (!pg && !busy) return null;
  const c = pg && pg.counts || {}, st = busy ? "checking" : pg.status;
  return /* @__PURE__ */ l.jsxs("div", { className: `vstrip ${st}`, role: "status", children: [
    busy ? /* @__PURE__ */ l.jsx("i", { className: "vspin" }) : /* @__PURE__ */ l.jsx("b", { className: "vdot", children: VAL_ICON[pg.status] }),
    /* @__PURE__ */ l.jsx("span", { className: "vstrip-t", children: busy ? `Validating numbers against the base tables in the background${job && job.total ? ` · ${job.done} of ${job.total} checks · ${job.tiles_done} of ${job.tiles_total} tiles done` : "…"} · you can keep working` : pg.status === "pass" ? "Every number on this page is verified" : pg.status === "mismatch" ? "Some numbers do not match the source" : pg.status === "review" ? "Validated, with notes to review" : "Validation could not check this page" }),
    !busy && pg && /* @__PURE__ */ l.jsxs("span", { className: "vstrip-c", children: [
      /* @__PURE__ */ l.jsx("em", { className: "pass", children: `${c.pass || 0} verified` }),
      c.review ? /* @__PURE__ */ l.jsx("em", { className: "review", children: `${c.review} review` }) : null,
      c.mismatch ? /* @__PURE__ */ l.jsx("em", { className: "mismatch", children: `${c.mismatch} mismatch` }) : null,
      c.na ? /* @__PURE__ */ l.jsx("em", { className: "na", children: `${c.na} not checked` }) : null
    ] }),
    !busy && pg && (pg.notes || []).length > 0 && /* @__PURE__ */ l.jsx("span", { className: "vstrip-n", title: pg.notes.join("\n"), children: pg.notes[0] + (pg.notes.length > 1 ? ` · +${pg.notes.length - 1} more` : "") }),
    !busy && pg && /* @__PURE__ */ l.jsx("span", { className: "vstrip-m", children: `Checked ${pg.at || V.at || ""}${pg.seconds ? ` · ${pg.seconds}s` : ""}` }),
    pg && /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => s(null), children: "View report" })
  ] });
}
function ValCheck({ c: e, open: t }) {
  return /* @__PURE__ */ l.jsxs("details", { className: `vcheck ${e.status}`, open: t || e.status === "mismatch", children: [
    /* @__PURE__ */ l.jsxs("summary", { children: [
      /* @__PURE__ */ l.jsx("span", { className: `vpill ${e.status}`, children: e.label }),
      /* @__PURE__ */ l.jsx("b", { children: `${e.id} · ${e.name}` }),
      /* @__PURE__ */ l.jsx("span", { className: "vsum", children: e.summary })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "vbody", children: [
      /* @__PURE__ */ l.jsx("p", { className: "vmethod", children: e.method }),
      e.detail && /* @__PURE__ */ l.jsx("p", { className: "vdetail", children: e.detail }),
      e.rows && e.rows.length > 0 && /* @__PURE__ */ l.jsx("div", { className: "vtable-wrap", children: /* @__PURE__ */ l.jsxs("table", { className: "vtable", children: [
        /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
          /* @__PURE__ */ l.jsx("th", { children: "Item" }), /* @__PURE__ */ l.jsx("th", { children: "Measure" }),
          /* @__PURE__ */ l.jsx("th", { children: "Dashboard" }), /* @__PURE__ */ l.jsx("th", { children: "Independent" }),
          e.rows.some((r) => r.diff) && /* @__PURE__ */ l.jsx("th", { children: "Difference" }), /* @__PURE__ */ l.jsx("th", { children: "" })
        ] }) }),
        /* @__PURE__ */ l.jsx("tbody", { children: e.rows.map((r, i) => /* @__PURE__ */ l.jsxs("tr", { className: r.ok === !1 ? "bad" : "", children: [
          /* @__PURE__ */ l.jsx("td", { children: String(r.label) }), /* @__PURE__ */ l.jsx("td", { children: String(r.column) }),
          /* @__PURE__ */ l.jsx("td", { className: "num", children: vfmt(r.dashboard) }), /* @__PURE__ */ l.jsx("td", { className: "num", children: vfmt(r.independent) }),
          e.rows.some((x) => x.diff) && /* @__PURE__ */ l.jsx("td", { className: "num", children: r.diff || "" }),
          /* @__PURE__ */ l.jsx("td", { className: "ok", children: r.ok === !1 ? "✕" : "✓" })
        ] }, i)) })
      ] }) }),
      e.sql && /* @__PURE__ */ l.jsxs("div", { className: "vsql", children: [
        /* @__PURE__ */ l.jsxs("div", { children: [/* @__PURE__ */ l.jsx("small", { children: "Dashboard query (semantic view)" }), /* @__PURE__ */ l.jsx("pre", { children: e.sql.dashboard })] }),
        /* @__PURE__ */ l.jsxs("div", { children: [/* @__PURE__ */ l.jsx("small", { children: "Independent query (base tables)" }), /* @__PURE__ */ l.jsx("pre", { children: e.sql.independent })] })
      ] })
    ] })
  ] });
}
function ValReport({ data: e, page: t, focus: n, send: s, onClose: r }) {
  const V = e.validation || {}, pg = (V.pages || {})[t.page_id] || {}, [only, setOnly] = P.useState(!1), c = pg.counts || {};
  let tiles = t.components.map((x) => [x, (V.tiles || {})[`${t.page_id}/${x.component_id}`]]).filter(([, v]) => v);
  n && (tiles = tiles.sort((a, b) => (`${t.page_id}/${b[0].component_id}` === n) - (`${t.page_id}/${a[0].component_id}` === n)));
  only && (tiles = tiles.filter(([, v]) => v.status === "mismatch" || v.status === "review"));
  const pageChecks = [...V.dashboard || [], ...pg.checks || []].filter((x) => !only || x.status === "mismatch" || x.status === "review");
  return /* @__PURE__ */ l.jsx("div", { className: "modal-back", onClick: r, children: /* @__PURE__ */ l.jsxs("div", { className: "modal vreport", role: "dialog", "aria-modal": "true", "aria-label": "Validation report", onClick: (x) => x.stopPropagation(), children: [
    /* @__PURE__ */ l.jsxs("div", { className: "vr-head", children: [
      /* @__PURE__ */ l.jsxs("div", { children: [
        /* @__PURE__ */ l.jsx("span", { className: "vr-eyebrow", children: "QA validation · automatic" }),
        /* @__PURE__ */ l.jsx("h3", { children: t.label }),
        /* @__PURE__ */ l.jsxs("div", { className: "vr-meta", children: [
          pg.status && /* @__PURE__ */ l.jsx("span", { className: `vpill ${pg.status}`, children: pg.label }),
          /* @__PURE__ */ l.jsx("span", { children: `${c.pass || 0} verified · ${c.review || 0} review · ${c.mismatch || 0} mismatch · ${c.na || 0} not checked` }),
          /* @__PURE__ */ l.jsx("span", { children: `Checked ${pg.at || V.at || "—"}${V.queries != null ? ` · ${V.queries} independent queries` : ""}` })
        ] })
      ] }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "addpage-close", onClick: r, "aria-label": "Close report", children: "×" })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "vr-tools", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: `chip ${only ? "on" : ""}`, onClick: () => setOnly(!only), children: only ? "Showing issues only" : "Show issues only" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => {
        s("validate", { page_id: t.page_id, all: !0 }, "Re-validating every tile…", !0), r();
      }, children: "Re-run validation" }),
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "Warn only: nothing is blocked. Every run is stored in AA_VALIDATION_RUNS." })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "vr-body", children: [
      pageChecks.length > 0 && /* @__PURE__ */ l.jsxs("section", { className: "vr-sec", children: [
        /* @__PURE__ */ l.jsx("h4", { children: "Page and data checks" }),
        pageChecks.map((x, i) => /* @__PURE__ */ l.jsx(ValCheck, { c: x }, x.id + i))
      ] }),
      /* @__PURE__ */ l.jsxs("section", { className: "vr-sec", children: [
        /* @__PURE__ */ l.jsx("h4", { children: `Tiles (${tiles.length})` }),
        tiles.length ? tiles.map(([x, v]) => {
          const me = `${t.page_id}/${x.component_id}` === n;
          return /* @__PURE__ */ l.jsxs("div", { className: `vr-tile ${me ? "focus" : ""}`, children: [
            /* @__PURE__ */ l.jsxs("div", { className: "vr-tile-head", children: [/* @__PURE__ */ l.jsx("b", { children: x.title }), /* @__PURE__ */ l.jsx("span", { className: `vpill ${v.status}`, children: VAL_TEXT[v.status] })] }),
            (v.checks || []).map((y, i) => /* @__PURE__ */ l.jsx(ValCheck, { c: y, open: me && i === 0 }, y.id + i))
          ] }, x.component_id);
        }) : /* @__PURE__ */ l.jsx("div", { className: "muted small", children: only ? "No issues on this page." : "No tiles validated yet." })
      ] })
    ] })
  ] }) });
}
function StoryText({ text: e }) {
  const lines = String(e || "").split(/\n+/).map((x) => x.trim()).filter(Boolean), bullet = /^[-•*]\s*/;
  let head = "", pts = [], act = "";
  lines.forEach((x) => {
    if (/^suggested action/i.test(x)) act = x.replace(/^suggested action:?\s*/i, "");
    else if (bullet.test(x)) pts.push(x.replace(bullet, ""));
    else if (!head) head = x;
    else pts.push(x);
  });
  if (!head && pts.length) head = pts.shift();
  const neg = /(slipp|declin|fell|drop|down|lower|lag|shrank|decreas|worse|below)/i;
  const hl = (t) => String(t).split(/([+−-]?\$?\d[\d,.]*(?:[KMB]|%| pt)?)/g).map((x, i) => i % 2 ? /* @__PURE__ */ l.jsx("em", { className: neg.test(String(t).slice(Math.max(0, String(t).indexOf(x) - 28), String(t).indexOf(x))) || /^[−-]/.test(x) ? "neg" : "pos", children: x }, i) : x);
  return /* @__PURE__ */ l.jsxs("div", { className: "story", children: [
    head && /* @__PURE__ */ l.jsx("div", { className: "story-hl", children: hl(head) }),
    pts.length > 0 && /* @__PURE__ */ l.jsx("div", { className: "story-pts", children: pts.map((x, i) => /* @__PURE__ */ l.jsx("span", { className: "story-pt", children: x }, i)) }),
    act && /* @__PURE__ */ l.jsxs("div", { className: "story-act", children: [/* @__PURE__ */ l.jsx("b", { children: "Suggested" }), " ", act] })
  ] });
}
function Yp(e) {
  return {
    select_source: "Reading semantic view & finding Cortex Agents…",
    suggest_bindings: "Cortex is mapping fields…",
    set_bindings: "Profiling the source…",
    set_audience: "Checking layout readiness…",
    recommend_layout: "Cortex is recommending a layout…",
    compose_layout: "Cortex is designing your dashboard from the data profile…",
    tile_add: "Cortex is designing the tile…",
    build_draft: "Running governed queries…",
    set_view: "Re-running governed queries…",
    publish: "Publishing…",
    open_published: "Opening published dashboard…",
    page_add: "Adding page…",
    page_regenerate: "Cortex is redesigning the page…",
    tile_update: "Validating & re-querying…",
    select_layout: "Running governed queries & Snowflake ML…",
    narrative: "Cortex is summarising governed facts…",
    create_agent: "Creating a Cortex Agent…",
    save_dashboard: "Saving to Snowflake…",
    open_dashboard: "Opening saved dashboard…",
    refresh: "Refreshing…"
  }[e] || "Working…";
}
function Kp({ data: e, onDrawer: t }) {
  var s, r, i;
  const n = (s = e.profile) == null ? void 0 : s.calendar;
  return /* @__PURE__ */ l.jsxs("header", { className: "top", children: [
    /* @__PURE__ */ l.jsxs("div", { className: "crumbs", children: [
      e.source ? /* @__PURE__ */ l.jsx("span", { className: "pill", title: e.source.fqn, children: $e(String(e.source.name).replace(/[_ ](SV|SEMANTIC[_ ]VIEW)$/i, "")) }) : /* @__PURE__ */ l.jsx("span", { className: "muted", children: "No data selected" }),
      e.step !== "source" && e.audience && /* @__PURE__ */ l.jsx("span", { className: "pill soft", children: Pn[e.audience] }),
      n && /* @__PURE__ */ l.jsxs("span", { className: "pill soft", children: [
        "as of ",
        n.max_date,
        " · ",
        n.grain
      ] }),
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "top-actions", children: [
      e.source && /* @__PURE__ */ l.jsxs("button", { type: "button", className: "ghost", onClick: () => t("decisions"), children: [
        "☑ Decisions ",
        /* @__PURE__ */ l.jsx("b", { children: ((i = e.decisions) == null ? void 0 : i.length) || 0 })
      ] }),
      e.source && /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", onClick: () => t("agent"), children: "✦ Ask Cortex Agent" })
    ] })
  ] });
}
function Xp({ data: e, send: t }) {
  var o;
  const [n, s] = P.useState(""), r = (e.sources || []).filter((d) => d.fqn), i = n.trim().toLowerCase(), a = r.filter((d) => !i || `${d.fqn} ${d.comment}`.toLowerCase().includes(i)), u = (e.sources || []).find((d) => d.error);
  return /* @__PURE__ */ l.jsxs("section", { className: "view", children: [
    /* @__PURE__ */ l.jsx("div", { className: "hero", children: /* @__PURE__ */ l.jsxs("div", { children: [
      /* @__PURE__ */ l.jsx("div", { className: "eyebrow", children: "Step 1 · Governed source" }),
      /* @__PURE__ */ l.jsx("h1", { children: "Start from a Snowflake semantic view" }),
      /* @__PURE__ */ l.jsxs("p", { children: [
        "Every number in this app is queried through ",
        /* @__PURE__ */ l.jsx("code", { children: "SEMANTIC_VIEW()" }),
        " under your role. Cortex and Snowflake ML add recommendations, forecasts, drivers and narrative — never ungoverned numbers."
      ] })
    ] }) }),
    ((o = e.dashboards) == null ? void 0 : o.length) > 0 && /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
      /* @__PURE__ */ l.jsx("h3", { children: "Saved dashboards" }),
      /* @__PURE__ */ l.jsx("div", { className: "cards", children: e.dashboards.map((d) => /* @__PURE__ */ l.jsxs("button", { type: "button", className: "card link-card", onClick: () => t("open_dashboard", { dashboard_id: d.dashboard_id }), children: [
        /* @__PURE__ */ l.jsx("b", { children: d.name }),
        /* @__PURE__ */ l.jsxs("small", { children: [
          Pn[d.audience],
          " · v",
          d.version,
          " · ",
          d.semantic_view
        ] }),
        /* @__PURE__ */ l.jsxs("small", { className: "muted", children: [
          d.created_by,
          " · ",
          d.created_at
        ] })
      ] }, d.dashboard_id)) })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "source-head", children: [
      /* @__PURE__ */ l.jsxs("h3", { children: [
        "Semantic views you can use ",
        /* @__PURE__ */ l.jsxs("span", { className: "muted", children: [
          "(",
          a.length,
          i ? ` of ${r.length}` : "",
          ")"
        ] })
      ] }),
      /* @__PURE__ */ l.jsx("input", { className: "search", placeholder: "Search semantic views, e.g. superstore", value: n, onChange: (d) => s(d.target.value) })
    ] }),
    u && /* @__PURE__ */ l.jsx("div", { className: "alert error", children: u.error }),
    !a.length && !u && /* @__PURE__ */ l.jsx("div", { className: "empty", children: "No semantic views visible to this role in the allowlisted schemas." }),
    /* @__PURE__ */ l.jsx("div", { className: "cards", children: a.map((d) => {
      var m;
      return /* @__PURE__ */ l.jsxs(
        "button",
        {
          type: "button",
          className: `card link-card ${((m = e.source) == null ? void 0 : m.fqn) === d.fqn ? "sel" : ""}`,
          onClick: () => t("select_source", { fqn: d.fqn }),
          children: [
            /* @__PURE__ */ l.jsx("b", { children: $e(d.name) }),
            /* @__PURE__ */ l.jsx("small", { className: "mono", children: d.fqn }),
            /* @__PURE__ */ l.jsx("small", { className: "muted", children: d.comment || "No description" })
          ]
        },
        d.fqn
      );
    }) })
  ] });
}
function Gp({ data: e, send: t }) {
  var y, C, k;
  const n = e.model, [s, r] = P.useState(e.bindings), [i, a] = P.useState("");
  P.useEffect(() => r(e.bindings), [e.bindings]);
  const u = n.metrics, o = n.dimensions.filter((c) => c.is_time), d = n.dimensions.filter((c) => !c.is_time), m = e.binding_suggestion, p = (c, h) => r({ ...s, [c]: h }), v = (c) => p("supporting_metrics", s.supporting_metrics.includes(c) ? s.supporting_metrics.filter((h) => h !== c) : [...s.supporting_metrics, c]), j = u.filter((c) => c.id !== s.primary_metric).map((c) => c.id);
  return /* @__PURE__ */ l.jsxs("section", { className: "view", children: [
    /* @__PURE__ */ l.jsx("div", { className: "eyebrow", children: "Step 2 · Governed fields" }),
    /* @__PURE__ */ l.jsx("h1", { children: "Map semantic-view fields to dashboard roles" }),
    /* @__PURE__ */ l.jsx("p", { className: "lede", children: "Roles drive which saved layouts are available. The app proposes a mapping; Cortex can refine it; you approve it." }),
    e.metric_draft && /* @__PURE__ */ l.jsx(pd, { md: e.metric_draft, send: t }),
    /* @__PURE__ */ l.jsxs("div", { className: "two", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "panel", children: [
        /* @__PURE__ */ l.jsx(
          Ql,
          {
            label: "Primary metric (headline outcome)",
            value: s.primary_metric,
            onChange: (c) => p("primary_metric", c),
            options: u.map((c) => [c.id, `${c.label}${c.additive ? "" : " · non-additive"}`])
          }
        ),
        /* @__PURE__ */ l.jsxs("div", { className: "field", children: [
          /* @__PURE__ */ l.jsxs("label", { children: [
            "Supporting metrics (",
            s.supporting_metrics.length,
            " selected) ·",
            " ",
            /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => p("supporting_metrics", j), children: "select all" }),
            /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => p("supporting_metrics", []), children: "clear" })
          ] }),
          /* @__PURE__ */ l.jsx("div", { className: "chips", children: u.filter((c) => c.id !== s.primary_metric).map((c) => /* @__PURE__ */ l.jsx("button", { type: "button", className: `chip ${s.supporting_metrics.includes(c.id) ? "on" : ""}`, onClick: () => v(c.id), children: c.label }, c.id)) })
        ] }),
        /* @__PURE__ */ l.jsx(Ql, { label: "Time dimension", value: s.time_dimension, onChange: (c) => p("time_dimension", c), options: o.map((c) => [c.id, c.label]) }),
        /* @__PURE__ */ l.jsx(Ql, { label: "Segment dimension", value: s.segment_dimension, onChange: (c) => p("segment_dimension", c), options: [["", "—"], ...d.map((c) => [c.id, c.label])] }),
        /* @__PURE__ */ l.jsx(Ql, { label: "Region / second dimension", value: s.region_dimension, onChange: (c) => p("region_dimension", c), options: [["", "—"], ...d.map((c) => [c.id, c.label])] }),
        /* @__PURE__ */ l.jsxs("div", { className: "toggles", children: [
          /* @__PURE__ */ l.jsx(Er, { on: s.use_baseline, onChange: (c) => p("use_baseline", c), label: "Prior-year baseline as target", hint: "Labelled as baseline, never as plan" }),
          /* @__PURE__ */ l.jsx(Er, { on: s.use_forecast, onChange: (c) => p("use_forecast", c), label: "Snowflake ML FORECAST", hint: "Trained on the governed series" }),
          /* @__PURE__ */ l.jsx(Er, { on: s.use_drivers, onChange: (c) => p("use_drivers", c), label: "Drivers (ML Top Insights + bridge)", hint: "Additive metrics only" })
        ] }),
        ((y = e.binding_errors) == null ? void 0 : y.length) > 0 && /* @__PURE__ */ l.jsx("div", { className: "alert error", children: e.binding_errors.join(" ") }),
        /* @__PURE__ */ l.jsx("div", { className: "actions", children: /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", onClick: () => t("set_bindings", { bindings: s, advance: !0, source: "user" }), children: "Approve mapping & continue →" }) })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "panel ai", children: [
        /* @__PURE__ */ l.jsx("div", { className: "ai-title", children: "✦ Cortex field mapping" }),
        /* @__PURE__ */ l.jsx("p", { className: "muted", children: "Cortex reads the semantic view's metric and dimension list and proposes roles. Only IDs that exist in the view are accepted." }),
        /* @__PURE__ */ l.jsx("textarea", { placeholder: "Optional intent, e.g. 'weekly revenue review by customer segment and region'", value: i, onChange: (c) => a(c.target.value) }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn ghost-ai", onClick: () => t("suggest_bindings", { intent: i }), children: "Suggest with Cortex" }),
        m && /* @__PURE__ */ l.jsxs("div", { className: "suggestion", children: [
          /* @__PURE__ */ l.jsx("div", { className: "prov", children: m.provenance }),
          /* @__PURE__ */ l.jsxs("ul", { children: [
            /* @__PURE__ */ l.jsxs("li", { children: [
              "Primary: ",
              /* @__PURE__ */ l.jsx("b", { children: $e(m.bindings.primary_metric) })
            ] }),
            /* @__PURE__ */ l.jsxs("li", { children: [
              "Supporting: ",
              m.bindings.supporting_metrics.map($e).join(", ") || "—"
            ] }),
            /* @__PURE__ */ l.jsxs("li", { children: [
              "Time: ",
              $e(m.bindings.time_dimension),
              " · Segment: ",
              $e(m.bindings.segment_dimension),
              " · Region: ",
              $e(m.bindings.region_dimension)
            ] })
          ] }),
          m.reason && /* @__PURE__ */ l.jsxs("p", { className: "muted", children: [
            "“",
            m.reason,
            "”"
          ] }),
          ((C = m.rejected) == null ? void 0 : C.length) > 0 && /* @__PURE__ */ l.jsxs("div", { className: "alert warn", children: [
            "Rejected (not in semantic view): ",
            m.rejected.join(", ")
          ] }),
          (k = m.errors) != null && k.length ? /* @__PURE__ */ l.jsx("div", { className: "alert error", children: m.errors.join(" ") }) : /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", onClick: () => r({ ...m.bindings }), children: "Apply suggestion" })
        ] }),
        /* @__PURE__ */ l.jsx("h4", { children: "Semantic view contents" }),
        /* @__PURE__ */ l.jsxs("table", { className: "table compact", children: [
          /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
            /* @__PURE__ */ l.jsx("th", { children: "Metric" }),
            /* @__PURE__ */ l.jsx("th", { children: "Expression" }),
            /* @__PURE__ */ l.jsx("th", {})
          ] }) }),
          /* @__PURE__ */ l.jsx("tbody", { children: u.map((c) => /* @__PURE__ */ l.jsxs("tr", { children: [
            /* @__PURE__ */ l.jsx("td", { children: c.label }),
            /* @__PURE__ */ l.jsx("td", { className: "mono small", children: c.expression || "—" }),
            /* @__PURE__ */ l.jsx("td", { children: c.additive ? /* @__PURE__ */ l.jsx("span", { className: "tag", children: "additive" }) : /* @__PURE__ */ l.jsx("span", { className: "tag warn", children: "ratio" }) })
          ] }, c.id)) })
        ] }),
        /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
          n.dimensions.length,
          " dimensions: ",
          n.dimensions.map((c) => c.label).join(", ")
        ] })
      ] })
    ] })
  ] });
}
function Ql({ label: e, value: t, onChange: n, options: s }) {
  return /* @__PURE__ */ l.jsxs("div", { className: "field", children: [
    /* @__PURE__ */ l.jsx("label", { children: e }),
    /* @__PURE__ */ l.jsx("select", { value: t || "", onChange: (r) => n(r.target.value), children: s.map(([r, i]) => /* @__PURE__ */ l.jsx("option", { value: r, children: i }, r)) })
  ] });
}
function Er({ on: e, onChange: t, label: n, hint: s }) {
  return /* @__PURE__ */ l.jsxs("button", { type: "button", className: `toggle ${e ? "on" : ""}`, onClick: () => t(!e), children: [
    /* @__PURE__ */ l.jsx("i", {}),
    /* @__PURE__ */ l.jsxs("span", { children: [
      /* @__PURE__ */ l.jsx("b", { children: n }),
      /* @__PURE__ */ l.jsx("small", { children: s })
    ] })
  ] });
}
const Jp = [
  "Margin problems by region for the CFO",
  "Monthly board pack: growth vs last year and outlook",
  "Which categories and segments need attention this month",
  "Customer mix and concentration risk"
];
function Zp({ data: e, send: t }) {
  var o, d, m, p, v, j, y, C, k;
  const [n, s] = P.useState(((o = e.spec) == null ? void 0 : o.goal) || ""), [r, i] = P.useState(!1), a = ((d = e.profile) == null ? void 0 : d.capabilities) || {}, u = Object.values(a).filter((c) => c.granted).length;
  return /* @__PURE__ */ l.jsxs("section", { className: "view", children: [
    /* @__PURE__ */ l.jsx("div", { className: "eyebrow", children: "Step 3 · Audience & layout" }),
    /* @__PURE__ */ l.jsx("h1", { children: "Who is this for, and what should it answer?" }),
    /* @__PURE__ */ l.jsx("div", { className: "audiences", children: e.catalog_audiences.map((c) => /* @__PURE__ */ l.jsx("button", { type: "button", className: `aud ${e.audience === c ? "on" : ""}`, onClick: () => t("set_audience", { audience: c }), children: Pn[c] }, c)) }),
    /* @__PURE__ */ l.jsxs("div", { className: "caps-bar", children: [
      /* @__PURE__ */ l.jsxs("span", { children: [
        /* @__PURE__ */ l.jsx("b", { children: u }),
        " of ",
        Object.keys(a).length,
        " data capabilities proven for ",
        Pn[e.audience]
      ] }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => i(!r), children: r ? "Hide evidence" : "Show evidence" })
    ] }),
    r && /* @__PURE__ */ l.jsx("div", { className: "caps", children: Object.entries(a).map(([c, h]) => /* @__PURE__ */ l.jsxs("div", { className: `cap ${h.granted ? "ok" : "no"}`, children: [
      /* @__PURE__ */ l.jsxs("b", { children: [
        h.granted ? "✓" : "✗",
        " ",
        ji[c] || c
      ] }),
      /* @__PURE__ */ l.jsx("small", { children: h.reason })
    ] }, c)) }),
    /* @__PURE__ */ l.jsxs("div", { className: "panel ai composer", children: [
      /* @__PURE__ */ l.jsx("div", { className: "ai-title", children: "✦ Design with Cortex" }),
      /* @__PURE__ */ l.jsxs("p", { className: "muted small", children: [
        "Cortex reads this semantic view — ",
        ((p = (m = e.model) == null ? void 0 : m.metrics) == null ? void 0 : p.length) || 0,
        " metrics, ",
        (((v = e.model) == null ? void 0 : v.dimensions) || []).filter((c) => !c.is_time).length,
        " dimensions and their cardinality, ",
        ((y = (j = e.profile) == null ? void 0 : j.calendar) == null ? void 0 : y.grain) || "",
        " history, proven capabilities — and designs pages, charts and questions for your goal. Every tile is then validated: only known chart types, only real fields, only charts the data can support."
      ] }),
      /* @__PURE__ */ l.jsx("textarea", { rows: 2, placeholder: "What should this dashboard answer? e.g. 'margin problems by region for the CFO'", value: n, onChange: (c) => s(c.target.value) }),
      /* @__PURE__ */ l.jsx("div", { className: "goal-examples", children: Jp.map((c) => /* @__PURE__ */ l.jsx("button", { type: "button", className: "chip", onClick: () => s(c), children: c }, c)) }),
      /* @__PURE__ */ l.jsxs("div", { className: "composer-foot", children: [
        /* @__PURE__ */ l.jsxs("span", { className: "muted small", children: [
          "Uses Cortex AI_COMPLETE (",
          ((C = e.features) == null ? void 0 : C.model) || "model",
          "); falls back to a reviewed template if Cortex is unavailable."
        ] }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn ai-btn", disabled: !((k = e.features) != null && k.complete), onClick: () => t("compose_layout", { goal: n }), children: "✦ Design my dashboard" })
      ] })
    ] }),
    /* @__PURE__ */ l.jsx("h3", { className: "sec-title", children: "Or start from a reviewed template" }),
    /* @__PURE__ */ l.jsx("div", { className: "templates", children: e.options.map((c) => {
      var h;
      return /* @__PURE__ */ l.jsxs("div", { className: `tpl ${c.selectable ? "" : "blocked"}`, children: [
        /* @__PURE__ */ l.jsxs("div", { className: "tpl-head", children: [
          /* @__PURE__ */ l.jsx("b", { children: c.display_name }),
          c.selectable ? /* @__PURE__ */ l.jsxs("span", { className: "tag ok", children: [
            "Ready · fit ",
            c.fit_score,
            "%"
          ] }) : /* @__PURE__ */ l.jsx("span", { className: "tag no", children: "Blocked" })
        ] }),
        /* @__PURE__ */ l.jsx("p", { children: c.description }),
        /* @__PURE__ */ l.jsx("div", { className: "pagemap", children: c.page_map.map((f, x) => /* @__PURE__ */ l.jsxs("span", { title: f.purpose, children: [
          x + 1,
          ". ",
          f.label
        ] }, f.page_id)) }),
        !c.selectable && /* @__PURE__ */ l.jsxs("div", { className: "missing", children: [
          "Missing: ",
          c.message.replace("Missing: ", "").split(", ").map((f) => ji[f] || $e(f)).join(", ")
        ] }),
        /* @__PURE__ */ l.jsxs("div", { className: "tpl-foot", children: [
          /* @__PURE__ */ l.jsxs("span", { className: "muted small mono", children: [
            c.template_id,
            " v",
            c.version
          ] }),
          /* @__PURE__ */ l.jsxs("span", { className: "tpl-btns", children: [
            /* @__PURE__ */ l.jsx(
              "button",
              {
                type: "button",
                className: "btn small ghost-ai",
                disabled: !c.selectable || !((h = e.features) != null && h.complete),
                title: "Cortex adapts this template to your goal and data",
                onClick: () => t("compose_layout", { goal: n, seed_template_id: c.template_id }, "Cortex is adapting the template…"),
                children: "✦ Adapt"
              }
            ),
            /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", disabled: !c.selectable, onClick: () => t("select_layout", { template_id: c.template_id }), children: "Use as is →" })
          ] })
        ] })
      ] }, c.template_id);
    }) })
  ] });
}
function _p({ title: e, children: t, onClose: n, wide: s }) {
  return /* @__PURE__ */ l.jsx("div", { className: "drawer-wrap", onClick: n, children: /* @__PURE__ */ l.jsxs("div", { className: `drawer ${s ? "wide" : ""}`, onClick: (r) => r.stopPropagation(), children: [
    /* @__PURE__ */ l.jsxs("div", { className: "drawer-head", children: [
      /* @__PURE__ */ l.jsx("b", { children: e }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "x", onClick: n, children: "×" })
    ] }),
    /* @__PURE__ */ l.jsx("div", { className: "drawer-body", children: t })
  ] }) });
}
function $p({ data: e, send: t, ctx: n, pending: s }) {
  var u;
  const [r, i] = P.useState(""), a = P.useRef(null);
  return P.useEffect(() => {
    var o;
    (o = a.current) == null || o.scrollIntoView({ block: "end" });
  }, [(u = e.chat) == null ? void 0 : u.length, s]), e.source ? /* @__PURE__ */ l.jsxs("div", { className: "agent", children: [
    e.agent ? /* @__PURE__ */ l.jsxs("div", { className: "agent-id", children: [
      /* @__PURE__ */ l.jsx("b", { children: e.agent.display_name }),
      /* @__PURE__ */ l.jsx("small", { className: "mono", children: e.agent.fqn }),
      /* @__PURE__ */ l.jsxs("small", { children: [
        ["Cortex Analyst", e.agent.has_search && "Cortex Search (documents)", e.agent.has_actions && "log_decision tool"].filter(Boolean).join(" + "),
        " over ",
        e.source.fqn
      ] })
    ] }) : /* @__PURE__ */ l.jsxs("div", { className: "agent-id", children: [
      /* @__PURE__ */ l.jsx("b", { children: "Cortex Agent" }),
      /* @__PURE__ */ l.jsx("small", { children: "Ask anything about this data. The shared agent for this semantic view is set up automatically on the first question and reused by every dashboard." })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "chat", children: [
      (e.chat || []).map((o, d) => {
        var m, p, v, j;
        return /* @__PURE__ */ l.jsx("div", { className: `msg ${o.role}`, children: o.role === "user" ? /* @__PURE__ */ l.jsx("div", { className: "bubble", children: o.text }) : /* @__PURE__ */ l.jsxs("div", { className: "bubble", children: [
          o.error ? /* @__PURE__ */ l.jsx("div", { className: "alert error small", children: o.error }) : /* @__PURE__ */ l.jsx("div", { className: "answer", children: o.text }),
          (m = o.tables) == null ? void 0 : m.map((y, C) => /* @__PURE__ */ l.jsxs("table", { className: "table compact", children: [
            /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsx("tr", { children: y.columns.map((k) => /* @__PURE__ */ l.jsx("th", { children: k }, k)) }) }),
            /* @__PURE__ */ l.jsx("tbody", { children: y.rows.slice(0, 10).map((k, c) => /* @__PURE__ */ l.jsx("tr", { children: k.map((h, f) => /* @__PURE__ */ l.jsx("td", { children: String(h) }, f)) }, c)) })
          ] }, C)),
          (p = o.actions) == null ? void 0 : p.map((y) => /* @__PURE__ */ l.jsxs("div", { className: "act-card", children: [
            "✓ Logged in Snowflake by the agent · decision ",
            /* @__PURE__ */ l.jsx("b", { children: y.id }),
            /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => n.openDecisions && n.openDecisions(), children: "Open decisions" })
          ] }, y.id)),
          ((v = o.citations) == null ? void 0 : v.length) > 0 && /* @__PURE__ */ l.jsxs("div", { className: "cites", children: [
            /* @__PURE__ */ l.jsx("span", { children: "Sources · Cortex Search" }),
            o.citations.map((y, C) => /* @__PURE__ */ l.jsx("span", { className: "cite", title: y.text, children: y.label }, C))
          ] }),
          ((j = o.sql) == null ? void 0 : j.length) > 0 && /* @__PURE__ */ l.jsxs("details", { children: [
            /* @__PURE__ */ l.jsx("summary", { className: "prov", children: "SQL generated by Cortex Analyst" }),
            /* @__PURE__ */ l.jsx("pre", { children: o.sql[0] })
          ] }),
          o.raw_preview && /* @__PURE__ */ l.jsxs("details", { children: [
            /* @__PURE__ */ l.jsx("summary", { className: "prov", children: "Raw agent response (diagnostics)" }),
            /* @__PURE__ */ l.jsx("pre", { children: o.raw_preview })
          ] }),
          /* @__PURE__ */ l.jsxs("div", { className: "prov", children: [
            o.agent,
            " ",
            o.run_id ? `· run ${o.run_id}` : "",
            " ",
            o.latency ? `· ${o.latency}s` : ""
          ] }),
          !o.error && /* @__PURE__ */ l.jsx("button", { type: "button", className: "link", onClick: () => {
            var y, C;
            return n.decide({ title: "Follow up: " + (((y = e.chat[d - 1]) == null ? void 0 : y.text) || "").slice(0, 90), detail: o.text.slice(0, 900), evidence: { agent: o.agent, run_id: o.run_id, sql: (C = o.sql) == null ? void 0 : C[0] } });
          }, children: "Log as decision" })
        ] }) }, d);
      }),
      (s == null ? void 0 : s.type) === "ask" && /* @__PURE__ */ l.jsx("div", { className: "msg agent", children: /* @__PURE__ */ l.jsx("div", { className: "bubble typing", children: "Thinking with Cortex Analyst…" }) }),
      /* @__PURE__ */ l.jsx("div", { ref: a })
    ] }),
    /* @__PURE__ */ l.jsxs("form", { className: "ask", onSubmit: (o) => {
      o.preventDefault(), r.trim() && (n.ask(r.trim()), i(""));
    }, children: [
      /* @__PURE__ */ l.jsx("input", { value: r, onChange: (o) => i(o.target.value), onKeyDown: (o) => { o.key === "Enter" && (o.preventDefault(), r.trim() && (s == null ? void 0 : s.type) !== "ask" && (n.ask(r.trim()), i(""))); }, placeholder: "Ask a question about this data…" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", disabled: !r.trim() || (s == null ? void 0 : s.type) === "ask", onClick: () => { r.trim() && (n.ask(r.trim()), i("")); }, children: (s == null ? void 0 : s.type) === "ask" ? "Thinking…" : "Ask" })
    ] })
  ] }) : /* @__PURE__ */ l.jsx("div", { className: "empty", children: "Choose a semantic view first." });
}
function em({ data: e, send: t, ctx: n }) {
  var s;
  return /* @__PURE__ */ l.jsxs("div", { children: [
    /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", onClick: () => n.decide({}), children: "+ New decision" }),
    (e.decisions || []).map((r) => /* @__PURE__ */ l.jsxs("div", { className: "decision", children: [
      /* @__PURE__ */ l.jsx("b", { children: r.title }),
      /* @__PURE__ */ l.jsx("div", { className: "muted small", children: r.detail }),
      /* @__PURE__ */ l.jsxs("div", { className: "small", children: [
        "Owner ",
        r.owner || "—",
        " · due ",
        r.due_date || "—",
        " · ",
        r.created_by,
        " ",
        r.created_at
      ] }),
      /* @__PURE__ */ l.jsx("select", { value: r.status, onChange: (i) => t("decision_status", { decision_id: r.decision_id, status: i.target.value }), children: ["Open", "In progress", "Done"].map((i) => /* @__PURE__ */ l.jsx("option", { children: i }, i)) })
    ] }, r.decision_id)),
    !((s = e.decisions) != null && s.length) && /* @__PURE__ */ l.jsx("div", { className: "empty", children: "No decisions yet." })
  ] });
}
function tm({ draft: e, onCancel: t, onSave: n }) {
  var a;
  const [s, r] = P.useState(e), i = (u) => ({ value: s[u] || "", onChange: (o) => r({ ...s, [u]: o.target.value }) });
  return /* @__PURE__ */ l.jsx("div", { className: "modal-wrap", children: /* @__PURE__ */ l.jsxs("div", { className: "modal", children: [
    /* @__PURE__ */ l.jsx("b", { children: "Log a decision" }),
    /* @__PURE__ */ l.jsxs("div", { className: "field", children: [
      /* @__PURE__ */ l.jsx("label", { children: "Title" }),
      /* @__PURE__ */ l.jsx("input", { ...i("title") })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "field", children: [
      /* @__PURE__ */ l.jsx("label", { children: "Detail / rationale" }),
      /* @__PURE__ */ l.jsx("textarea", { ...i("detail") })
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "two tight", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "field", children: [
        /* @__PURE__ */ l.jsx("label", { children: "Owner" }),
        /* @__PURE__ */ l.jsx("input", { ...i("owner") })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "field", children: [
        /* @__PURE__ */ l.jsx("label", { children: "Due date" }),
        /* @__PURE__ */ l.jsx("input", { type: "date", ...i("due") })
      ] })
    ] }),
    s.evidence && Object.keys(s.evidence).length > 0 && /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
      "Evidence attached: ",
      Object.keys(s.evidence).join(", ")
    ] }),
    /* @__PURE__ */ l.jsxs("div", { className: "actions", children: [
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost", onClick: t, children: "Cancel" }),
      /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn", disabled: !((a = s.title) != null && a.trim()), onClick: () => n(s), children: "Save to Snowflake" })
    ] })
  ] }) });
}
function nm({ data: e, send: t }) {
  var r, i, a, u, o, d, m, p, v, j, y, C;
  const n = e.quality, s = e.evals;
  return /* @__PURE__ */ l.jsxs("div", { className: "gov", children: [
    /* @__PURE__ */ l.jsx("h4", { children: "How numbers are produced" }),
    /* @__PURE__ */ l.jsxs("ul", { className: "small", children: [
      /* @__PURE__ */ l.jsxs("li", { children: [
        "All values: ",
        /* @__PURE__ */ l.jsxs("code", { children: [
          "SELECT … FROM SEMANTIC_VIEW(",
          ((r = e.source) == null ? void 0 : r.fqn) || "…",
          ")"
        ] }),
        " under role ",
        ((i = e.profile) == null ? void 0 : i.current_role) || "current role",
        "."
      ] }),
      /* @__PURE__ */ l.jsxs("li", { children: [
        "Forecasts: ",
        /* @__PURE__ */ l.jsx("code", { children: "SNOWFLAKE.ML.FORECAST" }),
        " trained on those governed series."
      ] }),
      /* @__PURE__ */ l.jsxs("li", { children: [
        "Drivers: ",
        /* @__PURE__ */ l.jsx("code", { children: "SNOWFLAKE.ML.TOP_INSIGHTS" }),
        " + reconciled contribution bridge."
      ] }),
      /* @__PURE__ */ l.jsxs("li", { children: [
        "Layouts: ",
        /* @__PURE__ */ l.jsx("code", { children: "AI_COMPLETE" }),
        " designs pages and tiles from a profile of the data; a validator allows only known chart types, real semantic-view fields and proven capabilities."
      ] }),
      /* @__PURE__ */ l.jsxs("li", { children: [
        "Text: ",
        /* @__PURE__ */ l.jsx("code", { children: "AI_COMPLETE" }),
        " over listed governed facts; field suggestions are validated against allowlists."
      ] }),
      /* @__PURE__ */ l.jsx("li", { children: "Q&A: Cortex Agent with a Cortex Analyst tool on the same semantic view." })
    ] }),
    ((u = (a = e.spec) == null ? void 0 : a.governance) == null ? void 0 : u.length) > 0 && /* @__PURE__ */ l.jsxs(l.Fragment, { children: [
      /* @__PURE__ */ l.jsxs("h4", { children: [
        "Layout decisions ",
        /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "(every Cortex-proposed tile, checked against the semantic view & proven capabilities)" })
      ] }),
      /* @__PURE__ */ l.jsxs("table", { className: "table compact", children: [
        /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
          /* @__PURE__ */ l.jsx("th", { children: "Page" }),
          /* @__PURE__ */ l.jsx("th", { children: "Tile" }),
          /* @__PURE__ */ l.jsx("th", { children: "Result" }),
          /* @__PURE__ */ l.jsx("th", { children: "Why" })
        ] }) }),
        /* @__PURE__ */ l.jsx("tbody", { children: e.spec.governance.map((k, c) => /* @__PURE__ */ l.jsxs("tr", { children: [
          /* @__PURE__ */ l.jsx("td", { className: "small", children: k.page }),
          /* @__PURE__ */ l.jsx("td", { children: k.tile }),
          /* @__PURE__ */ l.jsx("td", { children: /* @__PURE__ */ l.jsx("span", { className: `tag ${k.action === "kept" || k.action === "edited" ? "ok" : k.action === "repaired" ? "warn" : "no"}`, children: k.action }) }),
          /* @__PURE__ */ l.jsx("td", { className: "small", children: k.reason })
        ] }, c)) })
      ] })
    ] }),
    /* @__PURE__ */ l.jsxs("h4", { children: [
      "Agent evaluations ",
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "(Snowflake AI Observability · EXECUTE_AI_EVALUATION)" })
    ] }),
    s ? s.configured ? /* @__PURE__ */ l.jsxs("div", { className: "eval", children: [
      /* @__PURE__ */ l.jsxs("div", { className: "eval-bar", children: [
        /* @__PURE__ */ l.jsx("select", { value: s.run || "", onChange: (k) => t("eval_load", { run: k.target.value }, "Loading evaluation…"), children: (s.runs || []).map((k) => /* @__PURE__ */ l.jsxs("option", { value: k.run_name, children: [
          k.run_name,
          " · ",
          k.started_at
        ] }, k.run_name)) }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "ghost small", onClick: () => t("eval_load", { run: s.run }, "Refreshing…"), children: "↻ Refresh" }),
        /* @__PURE__ */ l.jsx("button", { type: "button", className: "btn small", onClick: () => t("eval_start", {}, "Starting Snowflake evaluation…"), children: "Run new evaluation" }),
        s.gate != null && /* @__PURE__ */ l.jsxs("span", { className: `gate ${s.gate ? "ok" : "no"}`, children: [
          "Promotion gate: ",
          s.gate ? "PASS" : "FAIL"
        ] })
      ] }),
      s.status && /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
        "Status: ",
        s.status
      ] }),
      s.error && /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
        "Results not available yet: ",
        s.error
      ] }),
      ((o = s.summary) == null ? void 0 : o.length) > 0 && /* @__PURE__ */ l.jsxs("table", { className: "table compact", children: [
        /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
          /* @__PURE__ */ l.jsx("th", { children: "Metric" }),
          /* @__PURE__ */ l.jsx("th", { children: "Score" }),
          /* @__PURE__ */ l.jsx("th", { children: "Gate" }),
          /* @__PURE__ */ l.jsx("th", { children: "Questions" })
        ] }) }),
        /* @__PURE__ */ l.jsx("tbody", { children: s.summary.map((k) => /* @__PURE__ */ l.jsxs("tr", { children: [
          /* @__PURE__ */ l.jsx("td", { children: k.metric_name }),
          /* @__PURE__ */ l.jsxs("td", { children: [
            /* @__PURE__ */ l.jsx("span", { className: "score", children: /* @__PURE__ */ l.jsx("i", { style: { width: `${Math.round(Math.max(0, Math.min(1, k.score)) * 100)}%` } }) }),
            " ",
            k.score.toFixed(2)
          ] }),
          /* @__PURE__ */ l.jsx("td", { children: k.threshold == null ? "—" : /* @__PURE__ */ l.jsxs("span", { className: `tag ${k.pass ? "ok" : "no"}`, children: [
            k.pass ? "≥" : "<",
            " ",
            k.threshold
          ] }) }),
          /* @__PURE__ */ l.jsx("td", { children: k.n })
        ] }, k.metric_name)) })
      ] }),
      ((d = s.records) == null ? void 0 : d.length) > 0 && /* @__PURE__ */ l.jsxs("details", { children: [
        /* @__PURE__ */ l.jsxs("summary", { className: "prov", children: [
          "Per-question scores (",
          s.records.length,
          ")"
        ] }),
        /* @__PURE__ */ l.jsxs("table", { className: "table compact", children: [
          /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
            /* @__PURE__ */ l.jsx("th", { children: "Question" }),
            /* @__PURE__ */ l.jsx("th", { children: "Metric" }),
            /* @__PURE__ */ l.jsx("th", { children: "Score" })
          ] }) }),
          /* @__PURE__ */ l.jsx("tbody", { children: s.records.map((k, c) => /* @__PURE__ */ l.jsxs("tr", { children: [
            /* @__PURE__ */ l.jsx("td", { className: "small", children: k.input }),
            /* @__PURE__ */ l.jsx("td", { className: "small", children: k.metric_name }),
            /* @__PURE__ */ l.jsx("td", { children: Number(k.score ?? 0).toFixed(2) })
          ] }, c)) })
        ] })
      ] }),
      /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
        "Full traces: Snowsight → AI & ML → Agents → ",
        (m = s.agent) == null ? void 0 : m.split(".").pop(),
        " → Evaluations."
      ] })
    ] }) : /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
      "No evaluation set for ",
      s.agent || "this agent",
      " yet. Run ",
      /* @__PURE__ */ l.jsx("code", { children: "setup\\run_agent_eval.cmd" }),
      " (Harborline retail agent)."
    ] }) : /* @__PURE__ */ l.jsx("div", { className: "muted small", children: "Loading…" }),
    /* @__PURE__ */ l.jsxs("h4", { children: [
      "AI run ledger ",
      /* @__PURE__ */ l.jsxs("span", { className: "muted small", children: [
        "(",
        e.app_schema,
        ".AA_AI_RUNS)"
      ] })
    ] }),
    n ? /* @__PURE__ */ l.jsxs("table", { className: "table compact", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", { children: "When" }),
        /* @__PURE__ */ l.jsx("th", { children: "Feature" }),
        /* @__PURE__ */ l.jsx("th", { children: "Status" }),
        /* @__PURE__ */ l.jsx("th", { children: "Provenance" }),
        /* @__PURE__ */ l.jsx("th", { children: "s" })
      ] }) }),
      /* @__PURE__ */ l.jsx("tbody", { children: n.ledger.map((k, c) => /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("td", { className: "small", children: k.created_at }),
        /* @__PURE__ */ l.jsx("td", { children: k.feature }),
        /* @__PURE__ */ l.jsx("td", { children: k.status }),
        /* @__PURE__ */ l.jsx("td", { className: "small", children: k.provenance }),
        /* @__PURE__ */ l.jsx("td", { children: Number(k.latency_s || 0).toFixed(1) })
      ] }, c)) })
    ] }) : /* @__PURE__ */ l.jsx("div", { className: "muted", children: "Loading…" }),
    /* @__PURE__ */ l.jsxs("h4", { children: [
      "Cost by app feature, last ",
      ((p = n == null ? void 0 : n.by_feature) == null ? void 0 : p.days) || 7,
      " days ",
      /* @__PURE__ */ l.jsx("span", { className: "muted small", children: "(QUERY_TAG on every app query · ACCOUNT_USAGE, lags up to ~3 h)" })
    ] }),
    (v = n == null ? void 0 : n.by_feature) != null && v.error ? /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
      "Needs ACCOUNT_USAGE access: ",
      n.by_feature.error
    ] }) : (((j = n == null ? void 0 : n.by_feature) == null ? void 0 : j.rows) || []).length ? /* @__PURE__ */ l.jsxs("table", { className: "table compact", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", { children: "Feature" }),
        /* @__PURE__ */ l.jsx("th", { children: "Queries" }),
        /* @__PURE__ */ l.jsx("th", { children: "Elapsed s" }),
        /* @__PURE__ */ l.jsx("th", { children: "Cortex credits" }),
        /* @__PURE__ */ l.jsx("th", { children: "Tokens" }),
        /* @__PURE__ */ l.jsx("th", { children: "Warehouse credits" })
      ] }) }),
      /* @__PURE__ */ l.jsx("tbody", { children: n.by_feature.rows.map((k, c) => /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("td", { children: k.feature }),
        /* @__PURE__ */ l.jsx("td", { children: k.queries }),
        /* @__PURE__ */ l.jsx("td", { children: k.elapsed_s }),
        /* @__PURE__ */ l.jsx("td", { children: k.cortex_credits == null ? "—" : Number(k.cortex_credits).toFixed(4) }),
        /* @__PURE__ */ l.jsx("td", { children: k.tokens ?? "—" }),
        /* @__PURE__ */ l.jsx("td", { children: k.warehouse_credits == null ? "—" : Number(k.warehouse_credits).toFixed(4) })
      ] }, c)) })
    ] }) : /* @__PURE__ */ l.jsx("div", { className: "muted small", children: "No tagged queries in ACCOUNT_USAGE yet (new tags appear after the usage views refresh)." }),
    /* @__PURE__ */ l.jsx("h4", { children: "Cortex usage, last 30 days" }),
    (y = n == null ? void 0 : n.usage) != null && y.error ? /* @__PURE__ */ l.jsxs("div", { className: "muted small", children: [
      "Needs ACCOUNT_USAGE access: ",
      n.usage.error
    ] }) : /* @__PURE__ */ l.jsxs("table", { className: "table compact", children: [
      /* @__PURE__ */ l.jsx("thead", { children: /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("th", { children: "Function" }),
        /* @__PURE__ */ l.jsx("th", { children: "Model" }),
        /* @__PURE__ */ l.jsx("th", { children: "Credits" }),
        /* @__PURE__ */ l.jsx("th", { children: "Tokens" })
      ] }) }),
      /* @__PURE__ */ l.jsx("tbody", { children: (((C = n == null ? void 0 : n.usage) == null ? void 0 : C.rows) || []).map((k, c) => /* @__PURE__ */ l.jsxs("tr", { children: [
        /* @__PURE__ */ l.jsx("td", { children: k.function_name }),
        /* @__PURE__ */ l.jsx("td", { children: k.model_name }),
        /* @__PURE__ */ l.jsx("td", { children: Number(k.credits || 0).toFixed(3) }),
        /* @__PURE__ */ l.jsx("td", { children: k.tokens })
      ] }, c)) })
    ] }),
    /* @__PURE__ */ l.jsx("h4", { children: "Recent SQL" }),
    /* @__PURE__ */ l.jsx("pre", { className: "sql-log", children: (e.sql_log || []).slice(-12).join(`

`) })
  ] });
}
const lm = "data:font/woff2;base64,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";
function sm() {
  if (typeof document > "u" || document.getElementById("aa-inter-font")) return;
  const e = document.createElement("style");
  e.id = "aa-inter-font", e.textContent = `@font-face{font-family:"AA Inter";font-style:normal;font-weight:100 900;font-display:swap;src:url(${lm}) format("woff2");}`, document.head.appendChild(e);
}
sm();
function rm(e) {
  const { parentElement: t, data: n, setTriggerValue: s } = e, r = t.querySelector(".aa-root") || t;
  r.__aa || (r.__aa = { root: id(r) });
  const i = (a) => s("action", a);
  r.__aa.root.render(/* @__PURE__ */ l.jsx(Hp, { data: n || {}, emit: i }));
}
export {
  rm as default
};
