import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const jsonHeaders = { "Content-Type": "application/json" };
const allowedJobTypes = new Set(["test.echo", "test.retry_once", "test.waiting_approval", "test.fail"]);

function safeInt(value: unknown, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.trunc(parsed) : fallback;
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "method_not_allowed" }), { status: 405, headers: jsonHeaders });
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceRole = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!supabaseUrl || !serviceRole) {
    return new Response(JSON.stringify({ error: "runtime_env_missing" }), { status: 500, headers: jsonHeaders });
  }

  const client = createClient(supabaseUrl, serviceRole, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const workerToken = req.headers.get("x-integrasquad-worker-token") ?? "";
  const { data: tokenOk, error: authError } = await client.rpc("squad_verify_stage8_worker_token", { p_token: workerToken });
  if (authError || tokenOk !== true) {
    return new Response(JSON.stringify({ error: "unauthorized_worker" }), { status: 401, headers: jsonHeaders });
  }

  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* empty body is valid */ }
  const maxJobs = Math.min(Math.max(safeInt(body.max_jobs, 5), 1), 10);
  const workerId = `stage8-edge-${crypto.randomUUID().slice(0, 12)}`;

  const { data: tick, error: tickError } = await client
    .from("squad_runtime_ticks")
    .insert({ worker_id: workerId, mode: "test", status: "running", detail: { source: "edge_function", max_jobs: maxJobs } })
    .select("id")
    .single();
  if (tickError || !tick) {
    return new Response(JSON.stringify({ error: "tick_create_failed", detail: tickError?.message }), { status: 500, headers: jsonHeaders });
  }

  const stats = {
    jobs_claimed: 0,
    jobs_completed: 0,
    jobs_retried: 0,
    jobs_failed: 0,
    schedules_materialized: 0,
    stale_jobs_requeued: 0,
  };

  try {
    const { data: materialized, error: materializeError } = await client.rpc("squad_materialize_due_test_schedules", { p_limit: 25 });
    if (materializeError) throw materializeError;
    stats.schedules_materialized = Number(materialized ?? 0);

    const { data: stale, error: staleError } = await client.rpc("squad_requeue_stale_test_jobs", { p_stale_seconds: 300 });
    if (staleError) throw staleError;
    stats.stale_jobs_requeued = Number(stale ?? 0);

    for (let i = 0; i < maxJobs; i += 1) {
      const { data: rows, error: claimError } = await client.rpc("squad_claim_next_test_job", { p_worker_id: workerId });
      if (claimError) throw claimError;
      const job = Array.isArray(rows) ? rows[0] : rows;
      if (!job) break;
      stats.jobs_claimed += 1;

      const payload = (job.payload ?? {}) as Record<string, unknown>;
      const actorId = String(payload.test_actor_id ?? "");
      const testMode = payload.test_mode === true;
      if (!testMode || !actorId.startsWith("stage8-test-") || !allowedJobTypes.has(job.job_type)) {
        await client.from("squad_jobs").update({
          status: "failed",
          last_error: "stage8 test runtime recusou job fora do perímetro de teste",
          finished_at: new Date().toISOString(),
          locked_by: null, locked_at: null, heartbeat_at: null,
        }).eq("id", job.id);
        await client.from("squad_runtime_alerts").insert({
          test_actor_id: actorId || null,
          job_id: job.id,
          severity: "error",
          kind: "test_guard_blocked",
          message: "Job bloqueado pelo guard de usuário de teste.",
          payload: { job_type: job.job_type },
        });
        stats.jobs_failed += 1;
        continue;
      }

      if (job.job_type === "test.echo") {
        await client.from("squad_jobs").update({
          status: "completed",
          result: { echoed: payload.message ?? null, test_actor_id: actorId, runtime: "stage8-edge" },
          finished_at: new Date().toISOString(),
          locked_by: null, locked_at: null, heartbeat_at: null, last_error: null,
        }).eq("id", job.id);
        stats.jobs_completed += 1;
        continue;
      }

      if (job.job_type === "test.retry_once") {
        if (Number(job.attempt) <= 1) {
          await client.from("squad_jobs").update({
            status: "retry",
            available_at: new Date(Date.now() + 5000).toISOString(),
            last_error: "falha temporária sintética da Etapa 8",
            locked_by: null, locked_at: null, heartbeat_at: null,
          }).eq("id", job.id);
          stats.jobs_retried += 1;
        } else {
          await client.from("squad_jobs").update({
            status: "completed",
            result: { recovered_after_retry: true, attempt: job.attempt, test_actor_id: actorId },
            finished_at: new Date().toISOString(),
            locked_by: null, locked_at: null, heartbeat_at: null, last_error: null,
          }).eq("id", job.id);
          stats.jobs_completed += 1;
        }
        continue;
      }

      if (job.job_type === "test.waiting_approval") {
        await client.from("squad_jobs").update({
          status: "completed",
          result: { waiting_approval: true, publication_authorized: false, test_actor_id: actorId },
          finished_at: new Date().toISOString(),
          locked_by: null, locked_at: null, heartbeat_at: null, last_error: null,
        }).eq("id", job.id);
        await client.from("squad_runtime_alerts").insert({
          test_actor_id: actorId,
          job_id: job.id,
          severity: "info",
          kind: "waiting_approval",
          message: "Peça de teste aguardando aprovação humana; nenhuma publicação foi autorizada.",
          payload: { publication_authorized: false },
        });
        stats.jobs_completed += 1;
        continue;
      }

      await client.from("squad_jobs").update({
        status: "failed",
        last_error: "falha permanente sintética da Etapa 8",
        finished_at: new Date().toISOString(),
        locked_by: null, locked_at: null, heartbeat_at: null,
      }).eq("id", job.id);
      await client.from("squad_runtime_alerts").insert({
        test_actor_id: actorId,
        job_id: job.id,
        severity: "error",
        kind: "synthetic_failure",
        message: "Falha sintética capturada pelo runtime de teste.",
        payload: { attempt: job.attempt },
      });
      stats.jobs_failed += 1;
    }

    await client.from("squad_runtime_ticks").update({
      ...stats,
      status: "completed",
      finished_at: new Date().toISOString(),
      detail: { source: "edge_function", test_only: true },
    }).eq("id", tick.id);

    return new Response(JSON.stringify({ ok: true, worker_id: workerId, test_only: true, ...stats }), { status: 200, headers: jsonHeaders });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    await client.from("squad_runtime_ticks").update({
      ...stats,
      status: "failed",
      finished_at: new Date().toISOString(),
      detail: { source: "edge_function", error: message, test_only: true },
    }).eq("id", tick.id);
    return new Response(JSON.stringify({ ok: false, error: message, worker_id: workerId }), { status: 500, headers: jsonHeaders });
  }
});
