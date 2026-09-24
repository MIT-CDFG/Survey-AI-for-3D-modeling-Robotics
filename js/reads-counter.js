/**
 * Shared page views for the survey, including its Paper and Archive views.
 * The Worker uses the existing desktop counter's canonical page URL.
 * Browser storage is never used as a source of read counts.
 */
(function () {
  'use strict';

  var PAGE_URL = 'https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/';
  var ENDPOINT = window.CF_COUNTER_URL || 'https://survey-reads-counter.frankdou.workers.dev/hit';
  var COUNT_IDS = ['nav-reads-count', 'footer-reads-count'];
  var BADGE_IDS = ['nav-reads-badge', 'footer-reads-badge'];

  function updateDisplay(count, state) {
    var formatted = count === null ? '\u2014' : count.toLocaleString('en-US');
    var description = state === 'ready' ? formatted + ' page views of this survey' :
      state === 'loading' ? 'Loading shared read count' : 'Read count temporarily unavailable';

    COUNT_IDS.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.textContent = formatted;
    });
    BADGE_IDS.forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      el.setAttribute('data-reads-state', state);
      el.setAttribute('title', description);
      el.setAttribute('aria-label', description);
    });
  }

  function initReadsCounter() {
    updateDisplay(null, 'loading');

    // Local previews must opt in to a local/mock endpoint, never the live counter.
    if (window.location.origin !== 'https://mit-cdfg.github.io' && !window.CF_COUNTER_URL) {
      updateDisplay(null, 'unavailable');
      return;
    }

    var controller = new AbortController();
    var timeout = setTimeout(function () { controller.abort(); }, 15000);

    // One request per page load. Retrying a hit could count the same visit twice.
    fetch(ENDPOINT, {
      method: 'POST',
      mode: 'cors',
      credentials: 'omit',
      cache: 'no-store',
      referrerPolicy: 'no-referrer',
      signal: controller.signal
    })
      .then(function (res) {
        if (!res.ok) throw new Error('Counter response ' + res.status);
        return res.json();
      })
      .then(function (data) {
        if (!data || data.success !== true || data.page !== PAGE_URL ||
            data.source !== 'busuanzi-page-pv' ||
            !Number.isSafeInteger(data.reads) || data.reads < 0) {
          throw new Error('Invalid counter response');
        }
        updateDisplay(data.reads, 'ready');
      })
      .catch(function () {
        // Never replace the shared total with a device-local count or site-wide PV.
        updateDisplay(null, 'unavailable');
      })
      .finally(function () { clearTimeout(timeout); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initReadsCounter, { once: true });
  } else {
    initReadsCounter();
  }
})();
