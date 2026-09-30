/*
 * Copy-to-clipboard for the install pill and the fixture buttons on the
 * homepage.
 *
 * Markup contract: a <button class="mr-copy" data-copy="literal text">. The
 * button is a real <button> so it is reachable by keyboard and announced by
 * screen readers; the value lives in data-copy so there is no hidden text to
 * read out.
 */
(function () {
  "use strict";

  var RESET_MS = 1600;

  function announce(btn, text) {
    var live = btn.querySelector(".mr-sr");
    if (live) {
      live.textContent = text;
    }
    btn.setAttribute("data-state", "done");
    btn.setAttribute("aria-label", text);
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    // file:// and plain http previews have no async clipboard API. Fall back
    // to a throwaway textarea so the button still works when someone builds
    // the site locally and opens it from disk.
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.top = "-1000px";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try {
        ok = document.execCommand("copy");
      } catch (e) {
        ok = false;
      }
      document.body.removeChild(ta);
      ok ? resolve() : reject(new Error("copy rejected"));
    });
  }

  function wire(btn) {
    var value = btn.getAttribute("data-copy");
    if (!value) return;

    var timer = null;
    btn.addEventListener("click", function () {
      if (timer) {
        window.clearTimeout(timer);
      }
      copyText(value).then(
        function () {
          announce(btn, "Copied " + value);
        },
        function () {
          btn.setAttribute("data-state", "error");
          btn.setAttribute("aria-label", "Copy failed. Select the text manually.");
        }
      );
      timer = window.setTimeout(function () {
        btn.removeAttribute("data-state");
        btn.setAttribute("aria-label", "Copy to clipboard");
      }, RESET_MS);
    });
  }

  function init() {
    var buttons = document.querySelectorAll(".mr-copy");
    for (var i = 0; i < buttons.length; i += 1) {
      wire(buttons[i]);
    }
  }

  // MkDocs' navigation.instant feature swaps the document without a reload,
  // so the homepage can arrive after this file has already run.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
  document.addEventListener("DOMContentLoaded", init);
})();
