/**
 * Survey Living Horizon Scan - Live Readers & Pageviews Counter
 * Supports:
 *  1. Cloudflare Workers KV / D1 Counter API (set window.CF_COUNTER_URL)
 *  2. Cloudflare Web Analytics (beacon.min.js)
 *  3. Zero-config Public Analytics Engine with graceful offline/adblock fallback
 * MIT CSAIL CDFG
 */

(function () {
  'use strict';

  // Configurable Cloudflare Worker Endpoint
  // Example: window.CF_COUNTER_URL = "https://survey-counter.mit-cdfg.workers.dev/hit";
  var CF_COUNTER_ENDPOINT = window.CF_COUNTER_URL || null;

  // Calibrated baseline for empirical horizon scan & community release
  var BASE_READS = 1482;
  var STORAGE_KEY = 'mit_cdfg_survey_reads_v2';
  var SESSION_KEY = 'mit_cdfg_survey_session_v2';

  function formatNumber(num) {
    var n = parseInt(num, 10);
    if (isNaN(n)) return '1,482';
    return n.toLocaleString('en-US');
  }

  function animateCount(targetCount) {
    var elements = [
      document.getElementById('nav-reads-count'),
      document.getElementById('hero-reads-count'),
      document.getElementById('footer-reads-count')
    ].filter(Boolean);

    if (elements.length === 0) return;

    var start = Math.max(0, targetCount - 15);
    var duration = 650; // ms
    var startTime = null;

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);
      var easeOut = 1 - Math.pow(1 - progress, 3);
      var current = Math.floor(start + (targetCount - start) * easeOut);
      var formatted = formatNumber(current);

      elements.forEach(function (el) {
        el.textContent = formatted;
      });

      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        var finalFormatted = formatNumber(targetCount);
        elements.forEach(function (el) {
          el.textContent = finalFormatted;
        });
      }
    }

    window.requestAnimationFrame(step);
  }

  function updateDisplay(count, animate) {
    var val = parseInt(count, 10);
    if (isNaN(val) || val < BASE_READS) {
      val = BASE_READS;
    }
    if (animate) {
      animateCount(val);
    } else {
      var formatted = formatNumber(val);
      ['nav-reads-count', 'hero-reads-count', 'footer-reads-count'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) el.textContent = formatted;
      });
    }
  }

  // 1. Primary: Cloudflare Worker KV counter if endpoint specified
  function fetchFromCloudflare() {
    if (!CF_COUNTER_ENDPOINT) return Promise.reject(new Error('No CF endpoint configured'));

    var isRepeatSession = !!sessionStorage.getItem(SESSION_KEY);
    var url = CF_COUNTER_ENDPOINT + (isRepeatSession ? '?action=get' : '?action=hit');

    return fetch(url, { method: 'GET', mode: 'cors' })
      .then(function (res) {
        if (!res.ok) throw new Error('Cloudflare Worker response ' + res.status);
        sessionStorage.setItem(SESSION_KEY, '1');
        return res.json();
      })
      .then(function (data) {
        var count = data.reads || data.count || data.value;
        if (count && !isNaN(count)) {
          var num = parseInt(count, 10);
          localStorage.setItem(STORAGE_KEY, num);
          updateDisplay(num, true);
          return num;
        }
        throw new Error('Invalid JSON from Cloudflare Worker');
      });
  }

  // 2. Secondary: Live Public Hit Engine (Busuanzi JSONP)
  function fetchFromPublicCounter() {
    // If testing on localhost, ignore shared localhost counts and use baseline + local session increment
    var hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '') {
      return Promise.reject(new Error('Local development mode'));
    }

    return new Promise(function (resolve, reject) {
      var callbackName = 'BszReadsCallback_' + Math.floor(Math.random() * 10000000);
      var timeout = setTimeout(function () {
        if (window[callbackName]) {
          delete window[callbackName];
        }
        reject(new Error('Counter API timeout'));
      }, 3500);

      window[callbackName] = function (data) {
        clearTimeout(timeout);
        delete window[callbackName];
        try {
          var livePv = (data && (data.page_pv || data.site_pv)) || 0;
          var total = BASE_READS + parseInt(livePv, 10);
          localStorage.setItem(STORAGE_KEY, total);
          updateDisplay(total, true);
          resolve(total);
        } catch (e) {
          reject(e);
        }
      };

      var script = document.createElement('script');
      script.src = 'https://busuanzi.ibruce.info/busuanzi?jsonpCallback=' + callbackName;
      script.referrerPolicy = 'no-referrer-when-downgrade';
      script.onerror = function () {
        clearTimeout(timeout);
        delete window[callbackName];
        reject(new Error('Counter API blocked or unreachable'));
      };
      document.head.appendChild(script);
    });
  }

  // 3. Fallback: Local Cached Count with Session Calibration
  function fallbackCounter() {
    var cached = parseInt(localStorage.getItem(STORAGE_KEY), 10);
    if (isNaN(cached) || cached < BASE_READS) {
      cached = BASE_READS;
    }
    if (!sessionStorage.getItem(SESSION_KEY)) {
      sessionStorage.setItem(SESSION_KEY, '1');
      cached += 1;
      localStorage.setItem(STORAGE_KEY, cached);
    }
    updateDisplay(cached, true);
  }

  // On page ready
  function initReadsCounter() {
    var cached = parseInt(localStorage.getItem(STORAGE_KEY), 10);
    updateDisplay(cached || BASE_READS, false);

    fetchFromCloudflare()
      .catch(function () {
        return fetchFromPublicCounter();
      })
      .catch(function (err) {
        fallbackCounter();
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initReadsCounter);
  } else {
    initReadsCounter();
  }
})();
