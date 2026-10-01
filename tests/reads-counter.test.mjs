import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import worker, { PAGE_URL } from '../cloudflare/worker.js';

const client = await readFile(new URL('../js/reads-counter.js', import.meta.url), 'utf8');
const origin = 'https://mit-cdfg.github.io';
const endpoint = 'https://survey-reads-counter.frankdou.workers.dev/hit';
const valid = (reads) => ({ success: true, reads, page: PAGE_URL, source: 'd1-page-pv' });
const countIDs = ['nav-reads-count', 'footer-reads-count'];
const badgeIDs = ['nav-reads-badge', 'footer-reads-badge'];
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

test('both visible badges use the shared page count even with blocked browser storage', async () => {
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
  { ...valid(106), page: origin + '/' }, { ...valid(343), source: 'busuanzi-page-pv' }]) {
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

function mockDB(views) {
  const calls = [];
  const env = { DB: { prepare(sql) {
    calls.push(sql);
    return { bind(page) {
      assert.equal(page, PAGE_URL);
      return { async first() {
        if (views instanceof Error) throw views;
        if (typeof views === 'number' && Number.isInteger(views)) views += 1;
        return views === null ? null : { views };
      } };
    } };
  } } };
  return { env, calls };
}

test('desktop, Safari origin-only, and no-referrer requests increment the SAME page row', async () => {
  const db = mockDB(1800);
  for (const [i, referer] of [PAGE_URL, origin + '/', undefined].entries()) {
    const response = await worker.fetch(request({ referer }), db.env);
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), valid(1801 + i));
    assert.equal(response.headers.get('Access-Control-Allow-Origin'), origin);
    assert.equal(response.headers.get('Cache-Control'), 'no-store');
  }
  assert.equal(db.calls.length, 3);
  assert.match(db.calls[0], /SET views = views \+ 1 .* RETURNING views/);
});

test('health checks, preflights, and invalid requests never touch the counter', async () => {
  const db = mockDB(999);
  for (const [options, status] of [
    [{ method: 'GET', path: '/health', requestOrigin: null }, 200],
    [{ method: 'OPTIONS' }, 204],
    [{ method: 'GET' }, 405],
    [{ requestOrigin: null }, 403],
    [{ requestOrigin: 'https://other.example' }, 403],
    [{ path: '/hit?url=https://other.example' }, 404],
    [{ path: '/other' }, 404]
  ]) assert.equal((await worker.fetch(request(options), db.env)).status, status);
  assert.equal(db.calls.length, 0);
});

test('a missing row, invalid count, or database error fails without a false zero', async () => {
  for (const views of [null, -2, '235', 1.5, new Error('D1 unavailable')]) {
    const db = mockDB(views);
    const response = await worker.fetch(request(), db.env);
    assert.equal(response.status, 502);
    assert.equal('reads' in await response.json(), false);
    assert.equal(db.calls.length, 1);
  }
});

test('published HTML and generator both retain versioned counter script and honest loading placeholders', async () => {
  for (const name of ['index.html', 'build_website.py']) {
    const html = await readFile(new URL('../' + name, import.meta.url), 'utf8');
    assert.match(html, /js\/reads-counter\.js\?v=20261001-d1/);
    for (const id of countIDs) assert.match(html, new RegExp('id="' + id + '"[^>]*>&mdash;'));
    for (const id of badgeIDs) assert.match(html, new RegExp('id="' + id + '" data-reads-state="loading"'));
  }
});
