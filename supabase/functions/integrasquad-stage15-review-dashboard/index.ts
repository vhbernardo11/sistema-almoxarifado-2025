import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const cors = { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" };

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "GET") return new Response(JSON.stringify({ error: "method_not_allowed" }), { status: 405, headers: cors });
  const url = Deno.env.get("SUPABASE_URL") ?? "";
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  if (!url || !key) return new Response(JSON.stringify({ error: "runtime_not_configured" }), { status: 503, headers: cors });

  const client = createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });
  const reviews = await client.from("squad_workflow_reviews")
    .select("id,job_id,test_actor_id,route,payload_digest,decision,reviewer,note,metadata,publication_authorized,external_actions_authorized,created_at,decided_at,review_payload")
    .order("created_at", { ascending: false })
    .limit(100);
  if (reviews.error) return new Response(JSON.stringify({ error: "review_query_failed", detail: reviews.error.message }), { status: 500, headers: cors });

  const items = (reviews.data ?? []).filter((r: any) =>
    typeof r.test_actor_id === "string" &&
    r.test_actor_id.startsWith("stage8-test-") &&
    r.publication_authorized !== true &&
    r.external_actions_authorized !== true
  ).map((r: any) => ({
    id: r.id,
    job_id: r.job_id,
    test_actor_id: r.test_actor_id,
    route: r.route,
    decision: r.decision,
    reviewer: r.reviewer,
    note: r.note,
    created_at: r.created_at,
    decided_at: r.decided_at,
    payload_digest: r.payload_digest,
    publication_authorized: false,
    external_actions_authorized: false,
    workflow_status: r.review_payload?.status ?? null,
    step_count: Array.isArray(r.review_payload?.steps) ? r.review_payload.steps.length : 0,
    preview: Array.isArray(r.review_payload?.steps) ? r.review_payload.steps.map((s: any) => ({ specialist_id: s.specialist_id, status: s.status })) : [],
  }));

  const summary = {
    total: items.length,
    pending: items.filter((r: any) => r.decision === "pending").length,
    accepted: items.filter((r: any) => r.decision === "accepted").length,
    changes_requested: items.filter((r: any) => r.decision === "changes_requested").length,
    rejected: items.filter((r: any) => r.decision === "rejected").length,
  };

  return new Response(JSON.stringify({
    test_mode: true,
    stage: 15,
    read_only: true,
    generated_at: new Date().toISOString(),
    summary,
    reviews: items,
    decision_channel: "explicit_human_instruction_only",
    publication_authorized: false,
  }), { status: 200, headers: { ...cors, "x-integrasquad-mode": "test-only-read-only" } });
});
