# Cloudflare Integration Guide for MIT-CDFG Survey Website

This directory provides full integration templates for tracking reads and visitors on the survey website using [Cloudflare](https://www.cloudflare.com/).

You have two complementary options available:

---

## Option 1: Cloudflare Web Analytics (Dashboard Traffic & Country Stats)
Cloudflare offers 100% free, privacy-first web analytics with no cookies:

1. Log into your [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. In the left navigation, go to **Analytics & Logs** > **Web Analytics**.
3. Click **Add a site**, and enter:
   - **Hostname**: `mit-cdfg.github.io`
4. Copy your unique JS snippet or Beacon Token (a 32-character string like `1a2b3c4d...`).
5. Open `website/index.html` (or `build_website.py`), find the Cloudflare comment in `<head>`, and replace `YOUR_CLOUDFLARE_BEACON_TOKEN` with your token:
   ```html
   <script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "YOUR_TOKEN"}'></script>
   ```
6. Commit & push. Your visitor count, geography, and page performance will appear in real time in your Cloudflare dashboard.

---

## Option 2: Cloudflare Worker KV Counter (For the Live "Reads" Badge)
If you want the visible "1,500+ Reads" badge on the website to be powered directly by your own Cloudflare Worker:

### Quick Deploy via Web UI (2 minutes):
1. In Cloudflare Dashboard, go to **Workers & Pages** > **Create application** > **Create Worker**.
2. Name it `survey-reads-counter` and click **Deploy**.
3. Click **Edit code**, paste the contents of `worker.js`, and click **Deploy**.
4. In Worker **Settings** > **Variables and Secrets**:
   - Go to **KV Namespace Bindings**
   - Click **Add binding**:
     - Variable name: `READS_KV`
     - KV namespace: Create a new namespace (e.g. `SURVEY_READS_STORE`) and select it.
5. Copy your Worker URL (e.g. `https://survey-reads-counter.<your-subdomain>.workers.dev`).
6. In `website/index.html` (before `reads-counter.js`), define:
   ```html
   <script>
     window.CF_COUNTER_URL = "https://survey-reads-counter.<your-subdomain>.workers.dev/hit";
   </script>
   ```

### Alternatively Deploy via Wrangler CLI:
```bash
cd website/cloudflare
npx wrangler login
npx wrangler kv namespace create READS_KV
# Put the namespace ID into wrangler.toml
npx wrangler deploy
```

*(Note: The website also includes an automated fallback mechanism so the Reads badge displays smoothly even before you link your Cloudflare worker).*
