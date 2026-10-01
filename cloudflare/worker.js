/**
 * Shared page-view total for the survey, stored in our own Cloudflare D1
 * database (binding DB, table page_views). Busuanzi, the former third-party
 * counter, went down on 2026-09-30; the D1 row was seeded with 1800, the
 * owner's recollection of the last Busuanzi total.
 */
export const PAGE_URL = 'https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/';
const ALLOWED_ORIGIN = 'https://mit-cdfg.github.io';
const SOURCE = 'd1-page-pv';

export default {
  async fetch(request, env) {
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

    // Safe for deployment checks: this route never reads or changes the count.
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

    try {
      // One atomic statement: concurrent visits cannot lose an increment.
      const row = await env.DB.prepare(
        'UPDATE page_views SET views = views + 1 WHERE page = ?1 RETURNING views'
      ).bind(PAGE_URL).first();
      const reads = row && row.views;
      if (!Number.isSafeInteger(reads) || reads < 0) throw new Error('Invalid page count');
      return json({ success: true, reads, page: PAGE_URL, source: SOURCE });
    } catch (error) {
      // A failed request is not a zero count. The client does not retry.
      return json({ success: false, error: 'Read count temporarily unavailable' }, 502);
    }
  }
};
