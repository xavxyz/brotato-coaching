/*
 * quiz.js — the retrieval-practice component every lesson uses.
 *
 * A quiz here is not a test. It is the part of a lesson where the reader
 * produces an answer from memory, and the component's whole job is to keep
 * production from collapsing into recognition: the options stay hidden until
 * the reader says they have an answer, and the moment one is chosen the
 * feedback is already on screen. There is no marking step, and no score — the
 * number this workspace tracks is the drill's prediction hit rate, not this.
 *
 * Load it in <head> alongside lesson.js. Markup contract:
 *
 *   <ol class="quiz">
 *     <li class="quiz__question">
 *       <p class="quiz__prompt">…</p>
 *       <button class="quiz__reveal" type="button" hidden>Show the options</button>
 *       <ul class="quiz__options">
 *         <li class="quiz__option" data-correct>
 *           <button class="quiz__choice" type="button">the answer</button>
 *           <p class="quiz__note">why it is the answer</p>
 *         </li>
 *         …
 *
 * Exactly one option carries `data-correct`; every option carries a note, so a
 * wrong choice is answered with a reason rather than a cross. Answers are
 * written to the same word count and near-identical length — enforced by
 * `tests/test_lessons.py` — so that nothing but knowing the material picks one.
 *
 * Nothing is hidden in the markup. This script hides what it is able to
 * re-show, so a page opened with JavaScript off is a complete, readable quiz
 * with its answers and notes already visible, and a printed page is the same.
 * The state lives in `data-state` on each question, which is also the whole of
 * the styling contract in lesson.css:
 *
 *   (absent)  no script: everything visible      hidden   options not yet shown
 *   open      options shown, nothing chosen      correct  answered, and right
 *   wrong     answered, and not right
 */

(function () {
  "use strict";

  var VERDICTS = {
    correct: "Right — and worth saying why, out loud, before moving on.",
    wrong: "Not this one. The answer is marked; read both notes.",
  };

  function options(question) {
    return Array.prototype.slice.call(question.querySelectorAll(".quiz__option"));
  }

  function verdictFor(question) {
    var existing = question.querySelector(".quiz__verdict");

    if (existing) {
      return existing;
    }

    var verdict = document.createElement("p");
    verdict.className = "quiz__verdict";
    // Answering is a click, not a navigation, so the outcome has to be spoken.
    verdict.setAttribute("role", "status");
    question.appendChild(verdict);
    return verdict;
  }

  // The first answer is the only one that measures anything, so the question
  // locks once it has been given.
  function answer(question, chosen) {
    var right = chosen.hasAttribute("data-correct");

    options(question).forEach(function (option) {
      option.dataset.mark = option.hasAttribute("data-correct") ? "answer" : "";
      option.querySelector(".quiz__choice").disabled = true;
    });
    chosen.dataset.chosen = "true";
    question.dataset.state = right ? "correct" : "wrong";
    verdictFor(question).textContent = right ? VERDICTS.correct : VERDICTS.wrong;
  }

  function wire(question) {
    var reveal = question.querySelector(".quiz__reveal");

    if (!reveal || !options(question).length) {
      return;
    }

    question.dataset.state = "hidden";
    reveal.hidden = false;
    reveal.setAttribute("type", "button");
    reveal.addEventListener("click", function () {
      question.dataset.state = "open";
      reveal.hidden = true;
      var first = question.querySelector(".quiz__choice");
      if (first) {
        first.focus();
      }
    });

    options(question).forEach(function (option) {
      var choice = option.querySelector(".quiz__choice");

      if (choice) {
        choice.setAttribute("type", "button");
        choice.addEventListener("click", function () {
          if (question.dataset.state === "open") {
            answer(question, option);
          }
        });
      }
    });
  }

  // Paper has no controls: a printed quiz is a page of questions with their
  // answers, and the reader's own state is put back afterwards.
  function openForPrinting() {
    each(".quiz__question[data-state]", function (question) {
      question.dataset.printedFrom = question.dataset.state;
      delete question.dataset.state;
    });
  }

  function restoreAfterPrinting() {
    each(".quiz__question[data-printed-from]", function (question) {
      question.dataset.state = question.dataset.printedFrom;
      delete question.dataset.printedFrom;
    });
  }

  function each(selector, visit) {
    Array.prototype.forEach.call(document.querySelectorAll(selector), visit);
  }

  window.addEventListener("beforeprint", openForPrinting);
  window.addEventListener("afterprint", restoreAfterPrinting);

  function start() {
    each(".quiz__question", wire);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
