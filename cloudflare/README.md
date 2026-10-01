# Shared survey reads

The public endpoint is
https://survey-reads-counter.frankdou.workers.dev/hit.

## Counting

The counter records **page views**, not verified unique readers. Each successful
page load or refresh adds one view. Switching between Full Paper, Benchmark, and
Case Archive within the same page does not add another view.

Since 2026-10-01 the total lives in our own Cloudflare D1 database
(`survey-reads`, table `page_views`, see `schema.sql`). Busuanzi, the former
third-party counter, went down on 2026-09-30 and its history cannot be exported,
so the row was seeded with 1800, the last total the owner recalls. Each hit runs
one atomic `UPDATE ... SET views = views + 1 ... RETURNING views`, so concurrent
visits cannot lose an increment.

The frontend uses only this endpoint and accepts only `source: "d1-page-pv"`.
Loading or failed requests show an em dash with a status tooltip; a failed hit
is never retried and never replaced with a device-local count.

## Worker

- POST /hit: record one page view and return its total.
- GET /health: check configuration without recording a view.
- OPTIONS /hit: CORS preflight; does not record a view.

Only the survey's GitHub Pages origin may call /hit. The Worker accepts no
caller-selected page URL and stores no visitor data.

## Development and deployment

Run the regression tests with Node.js 22 or newer (D1 is mocked, so tests never
change the public count):

    node --test tests/reads-counter.test.mjs

Deploy with the owner's Cloudflare login:

    cd cloudflare
    npx wrangler whoami
    npx wrangler deploy

Read the current total without counting a view:

    npx wrangler d1 execute survey-reads --remote --command "SELECT * FROM page_views"
