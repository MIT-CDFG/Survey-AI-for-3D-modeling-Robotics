/**
 * Keep the existing Busuanzi page-view total under one canonical survey URL.
 * Safari strips paths from cross-site Referer headers, so the browser must not
 * call Busuanzi directly. No counter database or historical offset is needed.
 */
export const PAGE_URL = 'https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/';
const ALLOWED_ORIGIN = 'https://mit-cdfg.github.io';
const SOURCE = 'busuanzi-page-pv';

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin');
    const headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'Vary': 'Origin'
    };
    if (origin === ALLOWED_ORIGIN) {
      headers['Access-Control-Allow-Origin'] = origin;
      headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS';
      headers['Access-Control-Allow-Headers'] = 'Content-Type';
    }
    const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers });

    // Safe for deployment checks: this route never contacts or increments Busuanzi.
    if (url.pathname === '/health' && request.method === 'GET') {
      return json({ success: true, page: PAGE_URL, source: SOURCE });
    }
    if (url.pathname !== '/hit' || url.search) {
      return json({ success: false, error: 'Not found' }, 404);
    }
    if (origin !== ALLOWED_ORIGIN) {
      return json({ success: false, error: 'Origin not allowed' }, 403);
    }
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers });
    }
    if (request.method !== 'POST') {
      return json({ success: false, error: 'Use POST to record a page view' }, 405);
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    try {
      // A unique callback avoids caching a hit request. Neither the caller's URL,
      // referrer, cookies nor user-agent is forwarded to the counter service.
      const callback = 'SurveyReads_' + crypto.randomUUID().replaceAll('-', '');
      const upstream = await fetch('https://busuanzi.ibruce.info/busuanzi?jsonpCallback=' + callback, {
        // The provider returns JSONP with application/json; a script request
        // uses */*. Asking only for application/javascript returns HTTP 404.
        headers: { 'Referer': PAGE_URL, 'Accept': '*/*',
          'User-Agent': 'Mozilla/5.0 (compatible; SurveyReadsCounter/1.0)' },
        redirect: 'manual',
        signal: controller.signal
      });
      if (!upstream.ok) throw new Error('Counter unavailable');

      const body = await upstream.text();
      const match = body.match(new RegExp('^\\s*try\\s*\\{\\s*' + callback +
        '\\s*\\((\\{[\\s\\S]*\\})\\);?\\s*\\}\\s*catch\\s*\\(e\\)\\s*\\{\\s*\\}\\s*$'));
      if (!match) throw new Error('Invalid counter response');
      // Parse the JSON payload; never execute third-party JavaScript.
      const data = JSON.parse(match[1]);
      if (!Number.isSafeInteger(data.page_pv) || data.page_pv < 0) {
        throw new Error('Invalid page count');
      }
      return json({ success: true, reads: data.page_pv, page: PAGE_URL, source: SOURCE });
    } catch (error) {
      // A failed request is not a zero count. Do not retry a possibly recorded hit.
      return json({ success: false, error: 'Read count temporarily unavailable' }, 502);
    } finally {
      clearTimeout(timeout);
    }
  }
};
