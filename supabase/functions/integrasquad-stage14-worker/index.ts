import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const jsonHeaders = { "Content-Type": "application/json" };
const ROUTES: Record<string, string[]> = {
  campaign: ["researcher", "strategist", "copywriter", "reviewer"],
  software: ["researcher", "programmer", "tester", "reviewer"],
  commercial: ["researcher", "commercial", "copywriter", "reviewer"],
  legal: ["researcher", "legal_reviewer", "reviewer"],
  seo: ["researcher", "seo_analyst", "copywriter", "reviewer"],
  analytics: ["analytics", "strategist", "reviewer"],
  operations: ["strategist", "reviewer"],
};
function text(v: unknown, field: string): string { const s = String(v ?? "").trim(); if (!s) throw new Error(`campo obrigatório ausente: ${field}`); return s; }
function list(v: unknown): string[] { return Array.isArray(v) ? v.map(String).map(s => s.trim()).filter(Boolean) : []; }
function inferKind(objective: string): string {
  const s = ` ${objective.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()} `;
  if (/ contrato| juridic| clausula| lei /.test(s)) return "legal";
  if (/ sistema| aplicativo| codigo| bug| site| api| banco de dados| integracao| programar /.test(s)) return "software";
  if (/ venda| cliente| lead| prospeccao| proposta comercial| preco| orcamento /.test(s)) return "commercial";
  if (/ seo | google| palavra-chave| ranking| busca organica /.test(s)) return "seo";
  if (/ metrica| dashboard| conversao| funil| dados| relatorio /.test(s)) return "analytics";
  if (/ campanha| instagram| reels| anuncio| copy| post| marketing| conteudo /.test(s)) return "campaign";
  return "operations";
}
function getPath(value: any, path: string): any { let cur = value; for (const part of (path ? path.split(".") : [])) { if (cur && typeof cur === "object" && part in cur) cur = cur[part]; else throw new Error(`referência inválida: ${path}`); } return cur; }
function resolveRefs(value: any, completed: Record<string, any>): any {
  if (Array.isArray(value)) return value.map(v => resolveRefs(v, completed));
  if (value && typeof value === "object") {
    const keys = Object.keys(value);
    if (keys.length === 2 && keys.includes("$step") && keys.includes("path")) {
      const id = String(value.$step); if (!(id in completed)) throw new Error(`etapa referenciada ausente: ${id}`); return getPath(completed[id], String(value.path));
    }
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, resolveRefs(v, completed)]));
  }
  return value;
}
function result(id: string, actor: string, status: string, data: Record<string, unknown>, warnings: string[] = [], review = false) {
  return { specialist_id: id, actor_id: actor, status, data, warnings, requires_human_review: review, publication_authorized: false, external_actions_authorized: false };
}
function execute(id: string, p: any, actor: string): any {
  if (id === "researcher") {
    const facts = list(p.facts); if (!facts.length) throw new Error("researcher exige facts");
    const sources = Array.isArray(p.sources) ? p.sources.map((x: any) => ({ label: text(x?.label, "source.label"), url: String(x?.url ?? "") })) : [];
    const questions = list(p.questions);
    return result(id, actor, "completed", { facts, sources, open_questions: questions.length ? questions : ["Nenhuma pergunta adicional fornecida."], external_research_performed: false }, ["Researcher opera apenas sobre material fornecido; sem busca externa."]);
  }
  if (id === "strategist") {
    const goal = text(p.goal, "goal"), audience = text(p.audience, "audience"); const facts = list(p.facts), constraints = list(p.constraints); let priorities = list(p.priorities);
    if (!priorities.length) priorities = ["Aderência ao objetivo", "Não inventar provas", "Revisão humana antes de efeito externo"];
    return result(id, actor, "completed", { goal, audience, strategy_statement: `Para ${audience}, orientar o trabalho para ${goal.toLowerCase()}.`, priorities, constraints, facts_used: facts, guardrails: ["Sem publicação automática", "Sem efeitos externos"] });
  }
  if (id === "copywriter") {
    const headline = text(p.headline, "headline"), cta = text(p.cta, "cta"), body = list(p.body_points); if (!body.length) throw new Error("copywriter exige body_points");
    const facts = list(p.facts), caption = `${body.map(x => x.replace(/[. ]+$/, "") + ".").join(" ")} ${cta}`.trim();
    return result(id, actor, "completed", { headline, short_caption: caption, call_to_action: cta, facts_used: facts }, facts.length ? [] : ["Sem fatos verificáveis anexados; copy limitada ao payload."]);
  }
  if (id === "reviewer") {
    if (!p.artifact || typeof p.artifact !== "object") throw new Error("reviewer exige artifact"); const required = list(p.required_fields), missing = required.filter((f: string) => !p.artifact[f]); const violations: string[] = [];
    if (p.artifact.publication_authorized === true) violations.push("artifact tentou autorizar publicação"); if (p.artifact.external_actions_authorized === true) violations.push("artifact tentou autorizar efeito externo"); if (missing.length) violations.push(`campos ausentes: ${missing.join(", ")}`);
    return result(id, actor, "needs_review", { artifact: p.artifact, missing_fields: missing, violations, ready_for_human_review: violations.length === 0 }, [...list(p.warnings), ...violations], true);
  }
  if (id === "programmer") {
    const workspace: Record<string, string> = { ...(p.workspace ?? {}) }; const ops = Array.isArray(p.operations) ? p.operations : []; const changed: any[] = [];
    for (const op of ops) { const path = text(op.path, "operation.path").replaceAll("\\", "/"); if (path.startsWith("/") || path.includes("../")) throw new Error("caminho inválido"); const action = String(op.action ?? "");
      if (action === "write_file") { const existed = path in workspace; workspace[path] = String(op.content ?? ""); changed.push({ path, action: existed ? "updated" : "created" }); }
      else if (action === "append_text") { workspace[path] = String(workspace[path] ?? "") + String(op.content ?? ""); changed.push({ path, action: "appended" }); }
      else if (action === "delete_file") { if (!(path in workspace)) throw new Error(`arquivo ausente: ${path}`); delete workspace[path]; changed.push({ path, action: "deleted" }); }
      else throw new Error(`ação programmer não permitida: ${action}`);
    }
    return result(id, actor, "completed", { workspace, changed_files: changed, operation_count: ops.length });
  }
  if (id === "tester") {
    const workspace: Record<string, string> = p.workspace ?? {}; const checks = Array.isArray(p.checks) ? p.checks : []; const out = checks.map((c: any) => { const path = text(c.path, "check.path"), kind = String(c.kind ?? ""); let passed = false, detail = "";
      if (kind === "file_exists") { passed = path in workspace; detail = passed ? "arquivo presente" : "arquivo ausente"; }
      else if (kind === "contains") { passed = String(workspace[path] ?? "").includes(text(c.value, "check.value")); detail = passed ? "trecho encontrado" : "trecho não encontrado"; }
      else if (kind === "json_valid") { try { JSON.parse(String(workspace[path])); passed = true; detail = "JSON válido"; } catch (e) { detail = `JSON inválido: ${String(e)}`; } }
      else throw new Error(`teste não permitido no edge: ${kind}`); return { kind, path, passed, detail }; }); const passed = out.length > 0 && out.every((x: any) => x.passed);
    return result(id, actor, passed ? "completed" : "needs_review", { passed, checks: out, check_count: out.length }, passed ? [] : ["Um ou mais testes falharam."], !passed);
  }
  if (id === "commercial") {
    const offer = text(p.offer_name, "offer_name"), audience = text(p.audience, "audience"), cta = text(p.cta, "cta"), benefits = list(p.benefits), proofs = list(p.proofs); if (!benefits.length) throw new Error("commercial exige benefit");
    return result(id, actor, "completed", { value_proposition: `${offer} ajuda ${audience} a ${benefits[0].toLowerCase()}.`, outreach_script: `Olá! Estou entrando em contato sobre ${offer}. Para ${audience}, a proposta é: ${benefits[0]}. ${cta}`, facts_used: { benefits, proofs } }, proofs.length ? [] : ["Nenhuma prova fornecida; nenhum resultado foi inventado."]);
  }
  if (id === "legal_reviewer") {
    const source = text(p.text, "text"), patterns: [string, RegExp][] = [["multa", /multa|penalidade/i], ["renovacao", /renova[cç][aã]o\s+autom[aá]tica/i], ["dados_pessoais", /dados\s+pessoais|lgpd|privacidade/i], ["foro", /\bforo\b/i], ["exclusividade", /exclusiv/i]]; const flags = patterns.filter(([, rx]) => rx.test(source)).map(([code]) => ({ code, note: "Ponto identificado para revisão humana." }));
    return result(id, actor, "needs_review", { jurisdiction: p.jurisdiction ?? null, risk_flags: flags, flag_count: flags.length }, ["Triagem automatizada; não substitui advogado."], true);
  }
  if (id === "seo_analyst") {
    const topic = text(p.topic, "topic"), primary = text(p.primary_keyword, "primary_keyword"), secondary = list(p.secondary_keywords), city = String(p.city ?? "").trim(), brand = String(p.brand ?? "").trim(); const slug = (primary + (city ? ` ${city}` : "")).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 80);
    return result(id, actor, "completed", { slug, title: `${topic}: ${primary}${brand ? ` | ${brand}` : ""}`.slice(0, 60), meta_description: `Entenda ${primary} em ${topic}.${city ? ` Conteúdo voltado para ${city}.` : ""}`.slice(0, 155), h1: topic, outline_h2: [`O que é ${primary}`, `Como ${primary} se aplica a ${topic}`, ...secondary.slice(0, 4)], keywords: { primary, secondary } });
  }
  if (id === "analytics") {
    const current = p.current ?? {}, previous = p.previous ?? {}; if (!Object.keys(current).length) throw new Error("analytics exige métricas atuais"); const deltas: Record<string, any> = {}, alerts: string[] = [];
    for (const [k, value] of Object.entries(current)) { if (typeof value !== "number") throw new Error(`métrica não numérica: ${k}`); if (typeof previous[k] === "number") { const before = previous[k], pct = before === 0 ? null : Math.round((((value as number) - before) / before) * 10000) / 100; deltas[k] = { absolute: (value as number) - before, percent: pct }; if (pct !== null && pct <= -20) alerts.push(`${k} caiu ${Math.abs(pct).toFixed(2)}%.`); } }
    return result(id, actor, "completed", { current, previous, deltas, alerts }, ["Métricas calculadas apenas a partir dos valores fornecidos."]);
  }
  throw new Error(`especialista não suportado: ${id}`);
}
function runWorkflow(payload: any) {
  const actor = String(payload.test_actor_id ?? ""); if (payload.test_mode !== true || !actor.startsWith("stage8-test-")) throw new Error("guard test-only recusou workflow"); if (payload.publication_authorized === true || payload.external_actions_authorized === true) throw new Error("autorização externa recusada");
  const work = payload.work ?? {}; const objective = text(work.objective, "work.objective"); const route = work.kind && work.kind !== "auto" ? String(work.kind) : inferKind(objective); const ids = ROUTES[route]; if (!ids) throw new Error(`rota inválida: ${route}`); const stepPayloads = payload.step_payloads ?? {}, completed: Record<string, any> = {}, steps: any[] = [], blockers: string[] = []; let needsReview = false;
  for (let i = 0; i < ids.length; i++) { const id = ids[i]; if (!(id in stepPayloads)) { blockers.push(`Payload ausente para ${id}.`); break; } const p = resolveRefs(stepPayloads[id], completed); const r = execute(id, p, actor); completed[id] = r; steps.push({ sequence: i, specialist_id: id, status: r.status, result: r }); needsReview = needsReview || r.requires_human_review === true; }
  return { actor_id: actor, route, status: blockers.length ? "blocked" : (needsReview ? "needs_review" : "completed"), steps, blockers, requires_human_review: needsReview, publication_authorized: false, external_actions_authorized: false };
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "method_not_allowed" }), { status: 405, headers: jsonHeaders });
  const url = Deno.env.get("SUPABASE_URL"), key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"); if (!url || !key) return new Response(JSON.stringify({ error: "runtime_env_missing" }), { status: 500, headers: jsonHeaders });
  const client = createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } }); const token = req.headers.get("x-integrasquad-worker-token") ?? ""; const auth = await client.rpc("squad_verify_stage8_worker_token", { p_token: token }); if (auth.error || auth.data !== true) return new Response(JSON.stringify({ error: "unauthorized_worker" }), { status: 401, headers: jsonHeaders });
  let body: any = {}; try { body = await req.json(); } catch { /* empty body */ } const maxJobs = Math.min(Math.max(Number(body.max_jobs ?? 3), 1), 10); const workerId = `stage14-edge-${crypto.randomUUID().slice(0, 12)}`;
  const tick = await client.from("squad_runtime_ticks").insert({ worker_id: workerId, mode: "test", status: "running", detail: { source: "edge_function", stage: 14, test_only: true, max_jobs: maxJobs } }).select("id").single(); if (tick.error || !tick.data) return new Response(JSON.stringify({ error: "tick_create_failed" }), { status: 500, headers: jsonHeaders });
  const stats = { jobs_claimed: 0, jobs_completed: 0, jobs_retried: 0, jobs_failed: 0, schedules_materialized: 0, stale_jobs_requeued: 0 };
  try {
    const stale = await client.rpc("squad_requeue_stale_stage14_workflow_jobs", { p_stale_seconds: 300 }); if (stale.error) throw stale.error; stats.stale_jobs_requeued = Number(stale.data ?? 0);
    for (let i = 0; i < maxJobs; i++) { const claim = await client.rpc("squad_claim_next_stage14_workflow_job", { p_worker_id: workerId }); if (claim.error) throw claim.error; const job = Array.isArray(claim.data) ? claim.data[0] : claim.data; if (!job) break; stats.jobs_claimed++;
      try { const workflow = runWorkflow(job.payload ?? {}); const out = { workflow, waiting_approval: workflow.requires_human_review, publication_authorized: false, external_actions_authorized: false, test_actor_id: workflow.actor_id, runtime: "stage14-edge" }; await client.from("squad_jobs").update({ status: "completed", result: out, finished_at: new Date().toISOString(), locked_by: null, locked_at: null, heartbeat_at: null, last_error: null }).eq("id", job.id); stats.jobs_completed++; if (workflow.requires_human_review) await client.from("squad_runtime_alerts").insert({ test_actor_id: workflow.actor_id, job_id: job.id, severity: "info", kind: "stage14_workflow_needs_review", message: "Workflow do Maestro concluído e aguardando revisão humana; publicação permanece bloqueada.", payload: { route: workflow.route, publication_authorized: false } }); }
      catch (e) { await client.from("squad_jobs").update({ status: "failed", last_error: String(e instanceof Error ? e.message : e), finished_at: new Date().toISOString(), locked_by: null, locked_at: null, heartbeat_at: null }).eq("id", job.id); stats.jobs_failed++; }
    }
    await client.from("squad_runtime_ticks").update({ ...stats, status: "completed", finished_at: new Date().toISOString(), detail: { source: "edge_function", stage: 14, test_only: true } }).eq("id", tick.data.id);
    return new Response(JSON.stringify({ ok: true, worker_id: workerId, stage: 14, test_only: true, ...stats }), { status: 200, headers: jsonHeaders });
  } catch (e) { const message = String(e instanceof Error ? e.message : e); await client.from("squad_runtime_ticks").update({ ...stats, status: "failed", finished_at: new Date().toISOString(), detail: { source: "edge_function", stage: 14, test_only: true, error: message } }).eq("id", tick.data.id); return new Response(JSON.stringify({ ok: false, error: message }), { status: 500, headers: jsonHeaders }); }
});
