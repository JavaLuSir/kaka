export const onRequest: PagesFunction = async (context) => {
  const url = new URL(context.request.url);
  const method = context.request.method;
  const path = url.pathname;
  
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };

  if (method === "OPTIONS") {
    return new Response("", { headers: corsHeaders });
  }

  const env = context.env as any;
  const DATA_KEY = "weight_records";
  const PER_PAGE = 10;

  async function loadRecords(env: any) {
    const data = await env.WEIGHT_KV.get(DATA_KEY, "json");
    return (data as any[]) || [];
  }

  async function saveRecords(env: any, records: any[]) {
    await env.WEIGHT_KV.put(DATA_KEY, JSON.stringify(records));
  }

  const recordId = url.searchParams.get("id");

  if (method === "GET") {
    const page = parseInt(url.searchParams.get("page") || "1");
    const perPage = parseInt(url.searchParams.get("per_page") || String(PER_PAGE));

    const allRecords = await loadRecords(env);
    allRecords.sort((a: any, b: any) => b.date.localeCompare(a.date));

    const total = allRecords.length;
    const totalPages = Math.ceil(total / perPage) || 1;
    const start = (page - 1) * perPage;
    const end = start + perPage;
    const records = allRecords.slice(start, end);

    return new Response(
      JSON.stringify({ records, total, page, per_page: perPage, totalPages }),
      { headers: { "Content-Type": "application/json", ...corsHeaders } }
    );
  }

  if (method === "POST") {
    const data = await context.request.json();
    const records = await loadRecords(env);
    const newRecord = {
      id: String(Date.now()),
      date: data.date,
      weight: data.weight,
      time: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString().slice(11, 19),
    };
    records.push(newRecord);
    await saveRecords(env, records);
    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  if (method === "DELETE" && recordId) {
    const records = await loadRecords(env);
    const filtered = records.filter((r: any) => r.id !== recordId);
    await saveRecords(env, filtered);
    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  return new Response("API endpoint", {
    headers: { "Content-Type": "text/plain" },
  });
};

interface Env {
  WEIGHT_KV: KVNamespace;
}
