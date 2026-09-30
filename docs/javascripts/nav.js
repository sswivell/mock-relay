/*
 * Homepage behaviour that cannot be done in CSS alone:
 *
 *  1. Reveal sections as they scroll into view, so the page has a sense of
 *     progress without a heavy animation library. Respects
 *     prefers-reduced-motion, and is a no-op if IntersectionObserver is
 *     missing, so the content is never hidden behind a feature check.
 *  2. Cycle the matching showcase through its strategies, so the ranking is
 *     legible as an animation and not only as a static table.
 */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
    : false;

  function reveal() {
    var targets = document.querySelectorAll("[data-reveal]");
    if (!targets.length) return;

    if (reduceMotion || !("IntersectionObserver" in window)) {
      for (var i = 0; i < targets.length; i += 1) {
        targets[i].setAttribute("data-revealed", "true");
      }
      return;
    }

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.setAttribute("data-revealed", "true");
          io.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );

    for (var j = 0; j < targets.length; j += 1) {
      io.observe(targets[j]);
    }
  }

  function showcase() {
    var root = document.querySelector("[data-rank-demo]");
    if (!root) return;
    if (reduceMotion || !("IntersectionObserver" in window)) return;

    var rows = root.querySelectorAll("[data-strategy]");
    if (rows.length < 2) return;

    var index = 0;

    function paint() {
      for (var i = 0; i < rows.length; i += 1) {
        rows[i].setAttribute("data-active", i === index ? "true" : "false");
      }
      var caption = root.querySelector("[data-rank-caption]");
      if (caption) {
        var active = rows[index];
        caption.textContent = active
          ? active.getAttribute("data-caption") || ""
          : "";
      }
    }

    // Only animate while the block is on screen; a background timer that keeps
    // firing is wasted work and a distraction for screen reader users.
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          window.clearInterval(entry.target.__mrRankTimer);
          if (entry.isIntersecting) {
            paint();
            entry.target.__mrRankTimer = window.setInterval(function () {
              index = (index + 1) % rows.length;
              paint();
            }, 1900);
          }
        });
      },
      { threshold: 0.3 }
    );
    io.observe(root);
  }

  function init() {
    reveal();
    showcase();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
  document.addEventListener("DOMContentLoaded", init);
})();
