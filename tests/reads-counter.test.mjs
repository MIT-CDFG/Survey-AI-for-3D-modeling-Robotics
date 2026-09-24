import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import worker, { PAGE_URL } from '../cloudflare/worker.js';

const client = await readFile(new URL('../js/reads-counter.js', import.meta.url), 'utf8');
const origin = 'https://mit-cdfg.github.io';
const endpoint = 'https://survey-reads-counter.frankdou.workers.dev/hit';
const valid = (reads) => ({ success: true, reads, page: PAGE_URL, source: 'busuanzi-page-pv' });
const countIDs = ['nav-reads-count', 'hero-reads-count', 'footer-reads-count'];
const badgeIDs = ['nav-reads-badge', 'hero-reads-badge', 'footer-reads-badge'];
const flush = () => new Promise(resolve => setImmediate(resolve));

function browser({ fetch, localOrigin = origin, override, readyState = 'complete' }) {
  const nodes = new Map([...countIDs, ...badgeIDs].map(id => [id, {
    textContent: '106',
    attrs: {},
    setAttribute(name, value) { this.attrs[name] = value; }
  }]));
  const listeners = new Map();
  const timers = new Map();
  const requests = [];
  const window = { location: new URL(localOrigin + '/Survey-AI-for-3D-modeling-Robotics/#view-gallery') };
  if (override) window.CF_COUNTER_URL = override;
  const context = {
    window, AbortController,
    document: {
      readyState,
      getElementById: id => nodes.get(id),
      addEventListener: (name, callback) => listeners.set(name, callback)
    },
    // Catch any return to device-specific counts, including when storage is blocked.
    get localStorage() { throw new Error('Browser storage is unavailable'); },
    fetch: (url, options) => { requests.push({ url, options }); return fetch(url, options); },
    setTimeout: (callback, ms) => { const id = timers.size + 1; timers.set(id, { callback, ms }); return id; },
    clearTimeout: id => timers.delete(id)
  };
  vm.runInNewContext(client, context);
  return { nodes, timers, requests, listeners, window };
}

function assertDisplay(page, text, state) {
  for (const id of countIDs) assert.equal(page.nodes.get(id).textContent, text, id);
  for (const id of badgeIDs) assert.equal(page.nodes.get(id).attrs['data-reads-state'], state, id);
}

test('all three badges use the shared page count even with blocked browser storage', async () => {
  const page = browser({ fetch: async () => Response.json(valid(1234)) });
  assertDisplay(page, '\u2014', 'loading');
  await flush();
  assertDisplay(page, '1,234', 'ready');
  assert.equal(page.requests.length, 1);
  assert.equal(page.requests[0].url, endpoint);
  assert.equal(page.requests[0].options.method, 'POST');
  assert.equal(page.requests[0].options.credentials, 'omit');
  assert.equal(page.timers.size, 0);
});

test('a slow shared response is accepted without the former 3.5-second fallback', async () => {
  let resolve;
  const page = browser({ fetch: () => new Promise(done => { resolve = done; }) });
  assert.equal([...page.timers.values()][0].ms, 15000);
  assertDisplay(page, '\u2014', 'loading');
  resolve(Response.json(valid(231)));
  await flush();
  assertDisplay(page, '231', 'ready');
});

test('zero is a valid page total, never replaced with the site total', async () => {
  const page = browser({ fetch: async () => Response.json({ ...valid(0), site_pv: 9000 }) });
  await flush();
  assertDisplay(page, '0', 'ready');
});

for (const data of [null, { success: false, reads: 0 }, valid(-1), valid(1.5),
  valid('231'), valid(Number.MAX_SAFE_INTEGER + 1),
  { ...valid(106), page: origin + '/' }, { ...valid(343), source: 'busuanzi-site-pv' }]) {
  test('reject invalid or wrong-source totals: ' + JSON.stringify(data), async () => {
    const page = browser({ fetch: async () => Response.json(data) });
    await flush();
    assertDisplay(page, '\u2014', 'unavailable');
    assert.equal(page.requests.length, 1);
    assert.equal(page.timers.size, 0);
  });
}

test('network errors and HTTP failures never increment a local count or retry a hit', async () => {
  for (const fetch of [async () => { throw new Error('Offline'); }, async () => new Response('', { status: 502 })]) {
    const page = browser({ fetch });
    await flush();
    assertDisplay(page, '\u2014', 'unavailable');
    assert.equal(page.requests.length, 1);
  }
});

test('timeout aborts the request without recording another visit', async () => {
  const page = browser({ fetch: (url, { signal }) => new Promise((resolve, reject) => {
    signal.addEventListener('abort', () => reject(new Error('Timeout')));
  }) });
  [...page.timers.values()][0].callback();
  await flush();
  assertDisplay(page, '\u2014', 'unavailable');
  assert.equal(page.requests.length, 1);
  assert.equal(page.timers.size, 0);
});

test('local previews do not hit production, but may use an explicit mock endpoint', async () => {
  const page = browser({ localOrigin: 'http://localhost:8000', fetch: async () => Response.json(valid(1)) });
  await flush();
  assertDisplay(page, '\u2014', 'unavailable');
  assert.equal(page.requests.length, 0);
  const mock = browser({ localOrigin: 'http://localhost:8000', override: 'http://localhost:8787/hit',
    fetch: async () => Response.json(valid(231)) });
  await flush();
  assertDisplay(mock, '231', 'ready');
  assert.equal(mock.requests[0].url, 'http://localhost:8787/hit');
});

test('one page load counts once; switching Paper/Archive fragments does not count again', async () => {
  const page = browser({ readyState: 'loading', fetch: async () => Response.json(valid(231)) });
  assert.equal(page.requests.length, 0);
  page.listeners.get('DOMContentLoaded')();
  await flush();
  page.window.location.hash = '#view-html';
  await flush();
  assertDisplay(page, '231', 'ready');
  assert.equal(page.requests.length, 1);
  assert.equal(page.listeners.has('hashchange'), false);
});

function request({ method = 'POST', path = '/hit', referer, requestOrigin = origin } = {}) {
  const headers = {};
  if (requestOrigin !== null) headers.Origin = requestOrigin;
  if (referer) headers.Referer = referer;
  return new Request('https://counter.example' + path, { method, headers });
}

function mockUpstream(t, payload) {
  return t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(new URL(url).origin, 'https://busuanzi.ibruce.info');
    assert.equal(options.headers.Referer, PAGE_URL);
    assert.equal(options.headers.Accept, '*/*');
    assert.equal(options.redirect, 'manual');
    assert.equal(options.headers.Cookie, undefined);
    const callback = new URL(url).searchParams.get('jsonpCallback');
    return new Response('try{' + callback + '(' + JSON.stringify(payload) + ');}catch(e){}');
  });
}

test('desktop, Safari origin-only, and no-referrer requests reach the SAME existing page key', async t => {
  const upstream = mockUpstream(t, { page_pv: 235, site_pv: 344 });
  for (const referer of [PAGE_URL, origin + '/', undefined]) {
    const response = await worker.fetch(request({ referer }));
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), valid(235));
    assert.equal(response.headers.get('Access-Control-Allow-Origin'), origin);
    assert.equal(response.headers.get('Cache-Control'), 'no-store');
  }
  assert.equal(upstream.mock.calls.length, 3);
});

test('the Worker preserves zero instead of substituting site-wide traffic', async t => {
  mockUpstream(t, { page_pv: 0, site_pv: 344 });
  assert.deepEqual(await (await worker.fetch(request())).json(), valid(0));
});

test('health checks, preflights, and invalid requests never increment the upstream counter', async t => {
  const upstream = mockUpstream(t, { page_pv: 999 });
  for (const [options, status] of [
    [{ method: 'GET', path: '/health', requestOrigin: null }, 200],
    [{ method: 'OPTIONS' }, 204],
    [{ method: 'GET' }, 405],
    [{ requestOrigin: null }, 403],
    [{ requestOrigin: 'https://other.example' }, 403],
    [{ path: '/hit?url=https://other.example' }, 404],
    [{ path: '/other' }, 404]
  ]) assert.equal((await worker.fetch(request(options))).status, status);
  assert.equal(upstream.mock.calls.length, 0);
});

test('missing/invalid page_pv never falls back to site_pv', async t => {
  for (const payload of [{ site_pv: 344 }, { page_pv: -1 }, { page_pv: '235' }, { page_pv: 1.5 }]) {
    const upstream = mockUpstream(t, payload);
    const response = await worker.fetch(request());
    assert.equal(response.status, 502);
    assert.equal('reads' in await response.json(), false);
    upstream.mock.restore();
  }
});

test('malformed JSONP, network errors, and upstream HTTP errors fail without false zero or retry', async t => {
  for (const outcome of [new Response('invalid'), new Response('', { status: 500 }), new Error('Offline'),
    new Response(null, { status: 302, headers: { Location: 'https://other.example' } }),
    new Response('globalThis.untrustedScriptExecuted = true;')]) {
    const upstream = t.mock.method(globalThis, 'fetch', async () => {
      if (outcome instanceof Error) throw outcome;
      return outcome;
    });
    const response = await worker.fetch(request());
    assert.equal(response.status, 502);
    assert.equal('reads' in await response.json(), false);
    assert.equal(upstream.mock.calls.length, 1);
    assert.equal(globalThis.untrustedScriptExecuted, undefined);
    upstream.mock.restore();
  }
});

test('published HTML and generator both retain versioned counter script and honest loading placeholders', async () => {
  for (const name of ['index.html', 'build_website.py']) {
    const html = await readFile(new URL('../' + name, import.meta.url), 'utf8');
    assert.match(html, /js\/reads-counter\.js\?v=20260924-canonical/);
    for (const id of countIDs) assert.match(html, new RegExp('id="' + id + '"[^>]*>&mdash;'));
    for (const id of badgeIDs) assert.match(html, new RegExp('id="' + id + '" data-reads-state="loading"'));
  }
});
