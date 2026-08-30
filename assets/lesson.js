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
 *     <span class="theme-toggle__label">…</span>
 *   </button>
 * It is `hidden` in the markup so that a page opened with JavaScript off shows no dead
 * control; this script unhides it. The label text comes from CSS, which knows the theme.
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

  function wireToggle() {
    var buttons = document.querySelectorAll(".theme-toggle");

    Array.prototype.forEach.call(buttons, function (button) {
      button.hidden = false;
      button.setAttribute("type", "button");

      button.addEventListener("click", function () {
        var next = currentTheme() === "dark" ? "light" : "dark";
        applyTheme(next);
        storeTheme(next);
      });
    });
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
