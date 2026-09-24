/**
 * Cloudflare Worker: Survey Live Reads Counter API
 *
 * Provides a low-latency, privacy-friendly counter endpoint powered by Cloudflare KV.
 *
 * Endpoints:
 *   GET /hit?key=survey_reads_total   -> Increments count by 1 and returns JSON
 *   GET /get?key=survey_reads_total   -> Returns current count without incrementing
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Set CORS headers so MIT-CDFG GitHub Pages can query this endpoint
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Content-Type": "application/json"
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    const key = url.searchParams.get("key") || "survey_reads_total";
    const action = url.searchParams.get("action") || (url.pathname.includes("hit") ? "hit" : "get");

    try {
      let currentVal = null;
      if (env.READS_KV) {
        currentVal = await env.READS_KV.get(key);
      }

      let count = currentVal ? parseInt(currentVal, 10) : 0;
      if (isNaN(count)) count = 0;

      if (action === "hit") {
        count += 1;
        if (env.READS_KV) {
          await env.READS_KV.put(key, count.toString());
        }
      }

      return new Response(
        JSON.stringify({
          success: true,
          key: key,
          reads: count,
          timestamp: new Date().toISOString()
        }),
        { status: 200, headers: corsHeaders }
      );
    } catch (err) {
      return new Response(
        JSON.stringify({
          success: false,
          reads: 0,
          error: err.message
        }),
        { status: 200, headers: corsHeaders }
      );
    }
  }
};
