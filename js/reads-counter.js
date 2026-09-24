/**
 * Living Horizon Scan - Readers & Pageviews Counter
 * Starts from 0 and increments +1 on every page visit/refresh.
 * Supports Cloudflare Workers KV API and standard analytics services.
 * MIT CSAIL CDFG
 */

(function () {
  'use strict';

  var CF_COUNTER_ENDPOINT = window.CF_COUNTER_URL || null;
  var STORAGE_KEY = 'mit_cdfg_survey_reads_pv';

  function formatNumber(num) {
    var n = parseInt(num, 10);
    if (isNaN(n) || n < 0) return '0';
    return n.toLocaleString('en-US');
  }

  function updateDisplay(count) {
    var val = parseInt(count, 10);
    if (isNaN(val) || val < 0) val = 0;
    var formatted = formatNumber(val);
    ['nav-reads-count', 'hero-reads-count', 'footer-reads-count'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.textContent = formatted;
    });
  }

  // 1. Primary: Cloudflare Worker KV counter
  function fetchFromCloudflare() {
    if (!CF_COUNTER_ENDPOINT) return Promise.reject(new Error('No endpoint configured'));

    // Increments by 1 on every page load
    var url = CF_COUNTER_ENDPOINT + (CF_COUNTER_ENDPOINT.indexOf('?') >= 0 ? '&' : '?') + 'action=hit';

    return fetch(url, { method: 'GET', mode: 'cors' })
      .then(function (res) {
        if (!res.ok) throw new Error('Worker response ' + res.status);
        return res.json();
      })
      .then(function (data) {
        var count = data.reads || data.count || data.value;
        if (count !== undefined && !isNaN(count)) {
          var num = parseInt(count, 10);
          localStorage.setItem(STORAGE_KEY, num);
          updateDisplay(num);
          return num;
        }
        throw new Error('Invalid response');
      });
  }

  // 2. Secondary: Public Hit Counter (Busuanzi JSONP - page_pv increments on every refresh)
  function fetchFromPublicCounter() {
    var hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '') {
      return Promise.reject(new Error('Local development'));
    }

    return new Promise(function (resolve, reject) {
      var callbackName = 'BszReadsCallback_' + Math.floor(Math.random() * 10000000);
      var timeout = setTimeout(function () {
        if (window[callbackName]) {
          delete window[callbackName];
        }
        reject(new Error('Timeout'));
      }, 3500);

      window[callbackName] = function (data) {
        clearTimeout(timeout);
        delete window[callbackName];
        try {
          var livePv = (data && (data.page_pv || data.site_pv)) || 0;
          var total = parseInt(livePv, 10);
          localStorage.setItem(STORAGE_KEY, total);
          updateDisplay(total);
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
        reject(new Error('Load error'));
      };
      document.head.appendChild(script);
    });
  }

  // 3. Fallback / Local mode: increment local counter on every page refresh
  function fallbackIncrement() {
    var current = parseInt(localStorage.getItem(STORAGE_KEY), 10);
    if (isNaN(current) || current < 0) {
      current = 0;
    }
    current += 1;
    localStorage.setItem(STORAGE_KEY, current);
    updateDisplay(current);
  }

  function initReadsCounter() {
    // Show current known count immediately
    var current = parseInt(localStorage.getItem(STORAGE_KEY), 10);
    if (!isNaN(current) && current >= 0) {
      updateDisplay(current);
    }

    fetchFromCloudflare()
      .catch(function () {
        return fetchFromPublicCounter();
      })
      .catch(function () {
        fallbackIncrement();
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initReadsCounter);
  } else {
    initReadsCounter();
  }
})();
