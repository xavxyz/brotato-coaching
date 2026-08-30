/*
 * lesson.js — the behaviour every lesson and reference doc shares.
 *
 * Two jobs, both small:
 *   1. Light/dark theme: system preference by default, overridden by the toggle button,
 *      remembered across pages in localStorage.
 *   2. Printing: open every collapsed <details> first, so a printed page never hides an
 *      answer behind a control that paper does not have.
 *
 * Load it in <head> without defer. The stored theme has to be applied before the first
 * paint, or the page flashes the wrong theme. The button is wired up on DOMContentLoaded.
 *
 * Markup contract for the toggle, from lesson.css:
 *   <button class="theme-toggle" hidden>
 *     <span class="theme-toggle__icon">…</span>
 *     <span class="theme-toggle__label"></span>
 *   </button>
 * It is `hidden` in the markup so that a page opened with JavaScript off shows no dead
 * control; this script unhides it and fills in the label, which names the theme a click
 * will switch to.
 */

(function () {
  "use strict";

  var STORAGE_KEY = "brotato-coaching:theme";

  // Private browsing and file:// in some browsers throw on localStorage access.
  function readStoredTheme() {
    try {
      var stored = window.localStorage.getItem(STORAGE_KEY);
      return stored === "light" || stored === "dark" ? stored : null;
    } catch (error) {
      return null;
    }
  }

  function storeTheme(theme) {
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch (error) {
      // A theme that doesn't persist is still a theme. Nothing to do.
    }
  }

  function systemTheme() {
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  // No data-theme attribute means "follow the system", which the stylesheet handles on its
  // own. The attribute is only set once a choice has actually been made.
  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") || systemTheme();
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
  }

  var stored = readStoredTheme();
  if (stored) {
    applyTheme(stored);
  }

  // The button names what a click will do, not what the theme currently is.
  function labelToggle(button) {
    var label = button.querySelector(".theme-toggle__label");

    if (label) {
      label.textContent = currentTheme() === "dark" ? "Light" : "Dark";
    }
  }

  function wireToggle() {
    var button = document.querySelector(".theme-toggle");

    if (!button) {
      return;
    }

    button.hidden = false;
    button.setAttribute("type", "button");
    labelToggle(button);

    button.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      applyTheme(next);
      storeTheme(next);
      labelToggle(button);
    });

    // Until a choice is made the page follows the system, so the label has to follow it too.
    if (window.matchMedia) {
      var query = window.matchMedia("(prefers-color-scheme: dark)");
      var onSystemChange = function () {
        labelToggle(button);
      };

      if (query.addEventListener) {
        query.addEventListener("change", onSystemChange);
      } else if (query.addListener) {
        query.addListener(onSystemChange);
      }
    }
  }

  function openDetailsForPrinting() {
    var collapsed = document.querySelectorAll("details:not([open])");

    Array.prototype.forEach.call(collapsed, function (details) {
      details.open = true;
      // Remember which ones the reader had closed, so the screen is left as it was found.
      details.dataset.reopenedForPrint = "true";
    });
  }

  function restoreDetailsAfterPrinting() {
    var reopened = document.querySelectorAll("details[data-reopened-for-print]");

    Array.prototype.forEach.call(reopened, function (details) {
      details.open = false;
      delete details.dataset.reopenedForPrint;
    });
  }

  window.addEventListener("beforeprint", openDetailsForPrinting);
  window.addEventListener("afterprint", restoreDetailsAfterPrinting);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireToggle);
  } else {
    wireToggle();
  }
})();
