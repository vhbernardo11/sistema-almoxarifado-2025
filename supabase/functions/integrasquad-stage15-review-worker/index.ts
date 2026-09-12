import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const headers = { "Content-Type": "application/json" };

function stable(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  const obj = value as Record<string, unknown>;
  return `{${Object.keys(obj).sort().map(k => `${JSON.stringify(k)}:${stable(obj[k])}`).join(",")}}`;
}

async function digest(value: Record<string, unknown>): Promise<string> {
  const bytes = new TextEncoder().encode(stable(value));
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, "0")).join("");
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "method_not_allowed" }), { status: 405, headers });
  const url = Deno.env.get("SUPABASE_URL") ?? "";
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  if (!url || !key) return new Response(JSON.stringify({ error: "runtime_env_missing" }), { status: 500, headers });

  const client = createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });
  const token = req.headers.get("x-integrasquad-worker-token") ?? "";
  const auth = await client.rpc("squad_verify_stage8_worker_token", { p_token: token });
  if (auth.error || auth.data !== true) return new Response(JSON.stringify({ error: "unauthorized_worker" }), { status: 401, headers });

  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* body opcional */ }
  const maxReviews = Math.min(Math.max(Number(body.max_reviews ?? 10), 1), 25);
  const workerId = `stage15-review-${crypto.randomUUID().slice(0, 12)}`;
  const tick = await client.from("squad_runtime_ticks").insert({
    worker_id: workerId,
    mode: "test",
    status: "running",
    detail: { source: "edge_function", stage: 15, test_only: true, purpose: "materialize_workflow_reviews" },
  }).select("id").single();
  if (tick.error || !tick.data) return new Response(JSON.stringify({ error: "tick_create_failed" }), { status: 500, headers });

  let inspected = 0;
  let created = 0;
  let failed = 0;
  try {
    const jobsRes = await client.from("squad_jobs")
      .select("id,job_type,status,payload,result,created_at")
      .eq("job_type", "maestro.workflow")
      .eq("status", "completed")
      .order("created_at", { ascending: false })
      .limit(100);
    if (jobsRes.error) throw jobsRes.error;

    const candidates = (jobsRes.data ?? []).filter((job: any) =>
      job?.payload?.test_mode === true &&
      typeof job?.payload?.test_actor_id === "string" &&
      job.payload.test_actor_id.startsWith("stage8-test-") &&
      job?.result?.waiting_approval === true &&
      job?.result?.publication_authorized !== true &&
      job?.result?.external_actions_authorized !== true &&
      job?.result?.workflow && typeof job.result.workflow === "object"
    );
    inspected = candidates.length;

    const ids = candidates.map((j: any) => j.id);
    const existing = new Set<string>();
    if (ids.length) {
      const reviewRes = await client.from("squad_workflow_reviews").select("job_id").in("job_id", ids);
      if (reviewRes.error) throw reviewRes.error;
      for (const row of reviewRes.data ?? []) existing.add(String(row.job_id));
    }

    for (const job of candidates) {
      if (created >= maxReviews) break;
      if (existing.has(String(job.id))) continue;
      const workflow = job.result.workflow as Record<string, unknown>;
      const actor = String(job.payload.test_actor_id);
      const route = String((workflow as any).route ?? "unknown");
      const payloadDigest = await digest(workflow);
      const insert = await client.from("squad_workflow_reviews").insert({
        job_id: job.id,
        test_actor_id: actor,
        route,
        payload_digest: payloadDigest,
        review_payload: workflow,
        decision: "pending",
        metadata: {
          source: "stage15_review_worker",
          runtime: job?.result?.runtime ?? null,
          test_mode: true,
          publication_authorized: false,
        },
        publication_authorized: false,
        external_actions_authorized: false,
      }).select("id").single();
      if (insert.error) { failed++; continue; }
      created++;
      await client.from("squad_runtime_alerts").insert({
        test_actor_id: actor,
        job_id: job.id,
        severity: "info",
        kind: "stage15_review_ticket_created",
        message: "Workflow sintético entrou na Central de Revisão; nenhuma publicação foi autorizada.",
        payload: { review_id: insert.data?.id ?? null, route, publication_authorized: false },
      });
    }

    await client.from("squad_runtime_ticks").update({
      status: "completed",
      jobs_claimed: inspected,
      jobs_completed: created,
      jobs_retried: 0,
      jobs_failed: failed,
      finished_at: new Date().toISOString(),
      detail: { source: "edge_function", stage: 15, test_only: true, materialized_reviews: created, inspected },
    }).eq("id", tick.data.id);

    return new Response(JSON.stringify({ ok: true, stage: 15, test_only: true, worker_id: workerId, inspected, reviews_created: created, failed }), { status: 200, headers });
  } catch (error) {
    const message = String(error instanceof Error ? error.message : error);
    await client.from("squad_runtime_ticks").update({
      status: "failed", jobs_claimed: inspected, jobs_completed: created, jobs_retried: 0, jobs_failed: failed + 1,
      finished_at: new Date().toISOString(),
      detail: { source: "edge_function", stage: 15, test_only: true, error: message },
    }).eq("id", tick.data.id);
    return new Response(JSON.stringify({ ok: false, stage: 15, error: message }), { status: 500, headers });
  }
});
