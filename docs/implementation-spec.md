# Flowy Implementation Spec

**Status:** draft, pending decisions in [§19 Open questions](#19-open-questions)
**Source of truth:** [`README.md`](../README.md) product definition
**Scope of this document:** first shippable slice (README §40 Phase 1), plus the invariants later phases must not violate
**Non-source:** no existing branches, prototypes, or prior code. This is a greenfield spec.

Legend:

- **MUST / MUST NOT / SHOULD** — requirements taken from the README or required by Temporal correctness
- **PROPOSAL** — a concrete default so implementation can start. Overturning a proposal is expected; overturning a MUST is a product change

---

## 1. Product contract

Flowy is a **multi-tenant workflow orchestration platform**. Users design a workflow as a **versioned graph**. A **generic Temporal workflow** interprets that graph. Node implementations (HTTP, LLM, agent, human, …) are Activities, Signals/Updates, Timers, or Child Workflows.

Invariant:

> Temporal owns durable execution. The platform owns workflow semantics.

Consequences that the implementation MUST honor:

1. No nondeterministic code inside the Temporal workflow (no clocks, no I/O, no LLM calls, no dict iteration that depends on insertion unless the payload is ordered and recorded).
2. No compiling a customer graph into generated Temporal workflow code as the primary architecture (README §43 Approach B).
3. AI is a node type, not the orchestrator.
4. Waiting (humans, events, timers) MUST use Temporal’s durable wait primitives. Workers MUST NOT block on those waits.
5. Published workflow definitions are immutable. Running instances pin the version they started with.
6. Large payloads MUST NOT be written into Temporal history. Store a reference (object storage key) instead.
7. Tenant identity MUST be resolved from authenticated context, never trusted from the request body.

---

## 2. What we are building first

README §40 is the Phase 1 contract. Everything else is explicitly later.

### 2.1 In scope (Phase 1)

**Node types**

| Type        | Temporal primitive                         | Phase 1 behavior |
|-------------|--------------------------------------------|------------------|
| `start`     | none                                       | Graph entry. Exactly one per definition. |
| `end`       | none                                       | Completes a branch. Workflow completes when no running/waiting/ready nodes remain and at least one `end` was reached, or all remaining nodes are unreachable. |
| `task`      | Activity                                   | **Catalogued** deterministic operations only. See Q1. |
| `http`      | Activity                                   | Templated HTTP call. |
| `llm`       | Activity                                   | Bounded model call; output validated against schema. |
| `agent`     | Activity                                   | Bounded `AgentRuntime` call; structured result only. |
| `human`     | Activity (create task) + Workflow Update   | Approval / form; durable wait. |
| `decision`  | workflow-side expression eval              | Exclusive branch. |

**Control flow**

- Sequential edges
- Conditional branching (`decision` plus conditional edges)
- Implicit join: a node with multiple incoming edges becomes READY only when **all** in-edge predecessors that were not SKIPPED have COMPLETED (AND-join)
- Retries and timeouts on Activities
- Cancel an execution

**Platform surfaces**

- Workflow definition CRUD + publish
- Start execution (manual)
- Execution detail + node history
- Human task inbox + complete/reject
- Workflow Studio: graph editor sufficient to author and publish the Phase 1 node set; execution viewer; task inbox

**Supporting infrastructure**

- Temporal (workflow + activity workers)
- PostgreSQL (definitions, versions, executions metadata, human tasks, audit-lite events)
- Object storage interface (can be local filesystem or MinIO in dev) for oversized node I/O
- REST API
- Single-region Docker Compose for local development

### 2.2 Explicitly out of scope (Phase 1)

From README §§41–42 and non-goals:

- Parallel *fork* node as a distinct type (implicit concurrency of independent READY nodes is allowed; a first-class Parallel/Join pair is Phase 2)
- Timer node, Event Wait node, webhooks-as-correlation, Kafka/SQS event gateway
- Sub-workflows / child workflows
- Runtime graph mutation
- Workflow instance migration across definition versions
- RBAC beyond a single authenticated operator identity
- Immutable compliance-grade audit log (emit events; do not build a regulated audit product)
- Compensation / sagas
- Pause / Resume (shown in the architecture diagram; not in Phase 1 node set)
- GraphQL, WebSocket (SSE is acceptable for execution tailing if cheap)
- Arbitrary user Python inside Temporal, or a general plugin sandbox
- LLM inference infrastructure
- BPMN import/export
- AI-assisted workflow authoring

### 2.3 Success criteria for Phase 1

A published graph equivalent to README §40 can run end-to-end:

```text
Start → HTTP/Task (upload/extract) → LLM (analyze)
        → Decision (confidence)
            → high → Task (auto process) → End
            → low  → Human (review)     → End
```

Required properties:

- Restarting the API process does not lose an in-flight execution
- Killing and restarting the worker resumes from Temporal history
- Human wait of arbitrary duration consumes no worker thread
- LLM output that fails schema validation does not silently continue
- Two published versions of the same workflow can have concurrent instances, each on its own version
- Cancel closes open human tasks

---

## 3. Architectural decisions that are closed

These are not proposals. They are the README.

| ID | Decision | Implication |
|----|----------|-------------|
| A1 | Graph interpreter, not codegen | One Temporal workflow type: `GraphWorkflowRunner` |
| A2 | Definitions are data | Publishing does not require a deploy |
| A3 | Version pin at start | `StartWorkflow` input includes `workflowId` + integer `version` |
| A4 | Replaceable AI runtime | `AgentRuntime` and `LlmRuntime` are interfaces; Google ADK / Gemini is the first adapter, not the domain model |
| A5 | Waiting ≠ Activity | Human/event/timer waits are workflow-level |
| A6 | AI cannot steer the graph except via structured output consumed by `decision` | No “agent as orchestrator” mode in Phase 1 |
| A7 | Multi-store | Postgres = definitions & metadata; Temporal = execution; object store = blobs |

---

## 4. System layout

### 4.1 Runtime topology

```text
Studio (Next.js)
    │ REST
    ▼
API (FastAPI) ── PostgreSQL
    │ Temporal Client
    ▼
Temporal Server
    │
    ├── Workflow worker: GraphWorkflowRunner
    └── Activity workers: http, task, llm, agent, human_task_create, blob
              │
              ├── LLM provider
              ├── AgentRuntime adapter
              └── Object store
```

### 4.2 Repository layout (PROPOSAL)

Monorepo, matching README §39, collapsed to what Phase 1 actually needs:

```text
flowy/
├── README.md
├── docs/
│   └── implementation-spec.md
├── docker-compose.yml          # postgres, temporal, temporal-ui, minio, api, worker, studio
├── packages/                   # optional shared JSON Schema for the graph IR
├── api/                        # FastAPI: REST, authn, definition service, execution service, task service
├── engine/                     # graph IR, validation, expression eval, ready-set algorithm (pure, no I/O)
├── temporal/
│   ├── workflows/graph_runner.py
│   ├── activities/
│   └── worker.py
├── agents/                     # AgentRuntime protocol + ADK adapter
├── studio/                     # Next.js + React Flow
└── tests/
```

`engine` MUST be importable from both `api` (validate-on-publish) and `temporal` (interpret-on-run). It MUST be free of FastAPI, Temporal, and ORM imports so the interpreter can be unit-tested without a cluster.

### 4.3 Technology (PROPOSAL, README §38)

| Layer | Choice | Why |
|-------|--------|-----|
| API | Python 3.12, FastAPI | Matches workers; one language for graph IR |
| Workers | Python Temporal SDK | Same |
| Studio | Next.js + React + React Flow | README |
| DB | PostgreSQL 16 | README |
| Objects | S3 API (MinIO locally) | README |
| Authn | OIDC (dev: any one provider, or a static-dev bypass flag that is illegal in prod) | README §38 |
| Observability | OpenTelemetry traces + logs | README §30 |
| IaC | deferred; Compose is the Phase 1 environment | — |

Java activity workers are **not** in Phase 1.

---

## 5. Domain model

Five concepts, as in README §4.

```text
Tenant
 └── Workflow                  # logical identity (slug)
      ├── WorkflowDefinition   # immutable published (or mutable draft) version
      │     └── Graph          # nodes + edges + schemas
      └── WorkflowInstance     # one Temporal workflow execution
            └── NodeExecution  # per-node status + I/O refs
```

### 5.1 Identifiers (PROPOSAL)

| Entity | Public ID |
|--------|-----------|
| Tenant | `ten_` + ulid |
| Workflow | slug, unique per tenant, `[a-z0-9][a-z0-9-]{1,62}` |
| Definition version | integer, monotonic from 1, per workflow |
| Instance | `run_` + ulid, also used as Temporal workflow ID: `{tenantId}:{workflowId}:{instanceId}` |
| Node | string, unique within a definition, `[a-zA-Z][a-zA-Z0-9_]{0,63}` |
| Human task | `tsk_` + ulid |

Temporal workflow ID MUST be deterministic and globally unique. Do not let clients pick Temporal IDs.

### 5.2 Workflow

```json
{
  "tenantId": "ten_01H...",
  "workflowId": "invoice-processing",
  "name": "Invoice Processing",
  "latestPublishedVersion": 7,
  "draftVersion": 8
}
```

A workflow has **at most one draft** at a time (PROPOSAL). Publishing the draft creates the next integer version and opens a new empty draft copy.

### 5.3 Workflow definition

Status state machine (README §24):

```text
DRAFT → VALIDATED → PUBLISHED
              ↓
           DRAFT (failed validation stays editable; VALIDATED is a cache of “last validation passed”)
```

`PUBLISHED` is terminal for that version row. Edits clone to a new draft version.

Minimum JSON:

```json
{
  "tenantId": "ten_01H...",
  "workflowId": "invoice-processing",
  "version": 7,
  "status": "PUBLISHED",
  "inputSchema": { "type": "object" },
  "nodes": [],
  "edges": [],
  "metadata": {
    "createdBy": "usr_...",
    "createdAt": "2026-08-27T00:00:00Z"
  }
}
```

`inputSchema` and every node `outputSchema` are **JSON Schema draft 2020-12**.

### 5.4 Instance

```json
{
  "tenantId": "ten_01H...",
  "workflowInstanceId": "run_01H...",
  "workflowId": "invoice-processing",
  "version": 7,
  "graphRevision": 0,
  "status": "RUNNING",
  "temporalWorkflowId": "ten_01H...:invoice-processing:run_01H...",
  "temporalRunId": "...",
  "startedAt": "...",
  "completedAt": null
}
```

`graphRevision` exists in the model now (always `0` in Phase 1) so Phase 3 mutation does not require a migration of meaning.

Instance status:

```text
PENDING | RUNNING | WAITING | COMPLETED | FAILED | CANCELLED
```

`WAITING` means the Temporal workflow is alive and blocked on a human (Phase 1) or, later, an event/timer.

### 5.5 Node execution

States from README §18:

```text
PENDING | READY | RUNNING | WAITING | COMPLETED | FAILED | SKIPPED | CANCELLED
```

Transitions (Phase 1):

```text
PENDING → READY          predecessors satisfied
READY → RUNNING          worker started the unit of work
RUNNING → COMPLETED      success
RUNNING → FAILED         activity failure after retries, or validation failure
RUNNING → WAITING        only human (create-task succeeded; waiting on Update)
WAITING → COMPLETED      human completed
WAITING → FAILED         human rejected with fail-workflow policy, or timeout
WAITING → CANCELLED      parent cancelled
READY/PENDING → SKIPPED  branch not taken after decision
* → CANCELLED            workflow cancelled
```

A FAILED node with `errorPolicy = FAIL_WORKFLOW` (default) fails the instance.
Phase 1 does **not** implement Fallback / Ignore / Compensate (README §35). Those fields may exist on the node as `FAIL_WORKFLOW` only.

---

## 6. Graph IR

This is the document the interpreter runs. Studio persistence uses the same IR plus a `layout` map that the engine ignores.

### 6.1 Node

```json
{
  "id": "analyze",
  "type": "llm",
  "config": {},
  "inputMapping": {
    "documentText": "$.nodes.extract.output.text"
  },
  "outputSchema": { "type": "object" },
  "executionPolicy": {
    "timeout": "5m",
    "retry": {
      "maxAttempts": 5,
      "initialInterval": "2s",
      "backoffCoefficient": 2.0,
      "nonRetryableErrorTypes": ["ValidationError", "HttpClientError"]
    }
  },
  "errorPolicy": "FAIL_WORKFLOW"
}
```

`inputMapping` values are **paths into the execution context**, not free-form templates (except `http` body/headers, which are JSON templates over the same context — see §7.4).

### 6.2 Edge

```json
{
  "id": "e_analyze_review",
  "from": "analyze",
  "to": "review",
  "condition": null
}
```

`condition` is either `null` (unconditional) or an expression string (see §8.4).

Rules:

1. Graph MUST be a single connected DAG except for **structured loops**, which Phase 1 **forbids**. Phase 1 publish MUST reject cycles.
2. Exactly one `start`. At least one `end`.
3. `start` has in-degree 0. `end` has out-degree 0.
4. Every node except `start` has in-degree ≥ 1.
5. Conditional edges may only leave `decision` nodes in Phase 1. Other node types: all out-edges MUST have `condition: null`.
6. A `decision` MUST have ≥ 2 out-edges. Exactly one MAY be the default (`condition: null`). If no default and no condition matches, the node execution FAILS (do not silently stall).
7. Multiple edges from one node MAY be true only for `decision` if we allowed inclusive split — **we do not**. Phase 1 `decision` is **exclusive**: evaluate in **edge-id sort order**, take the first match, SKIP the rest. (See Q3.)

### 6.3 Execution context

The interpreter’s only data plane:

```json
{
  "tenantId": "...",
  "workflowId": "...",
  "workflowInstanceId": "...",
  "version": 7,
  "input": {},
  "nodes": {
    "extract": {
      "status": "COMPLETED",
      "output": { "text": "..." }
    }
  }
}
```

Node outputs stored in Temporal MUST be small. If an Activity result exceeds **PROPOSAL 24 KiB**, the Activity writes the blob to object storage and returns `{ "$ref": "s3://..." }` only. Downstream mappings that need the blob fetch it inside their Activity, never in the workflow.

---

## 7. Node contracts (Phase 1)

Every executable node conceptually implements README §17. In Temporal terms:

- **Sync work** (`task`, `http`, `llm`, `agent`): one Activity; status COMPLETED or FAILED.
- **Durable wait** (`human`): Activity to persist the task, then `workflow.wait_condition` / Update handler; status WAITING then COMPLETED/FAILED.
- **Pure** (`start`, `end`, `decision`): no Activity.

### 7.1 `start`

Config: empty.
Output: `{ "input": <workflow input> }` so mappings can use `$.nodes.start.output.input` or `$.input` equivalently.

### 7.2 `end`

Config: optional `outputMapping` from context to workflow result.
The workflow result is the mapped object of the first `end` that completes (PROPOSAL). Other ends that later become reachable are SKIPPED if the workflow already completed — **do not** wait for all ends. (See Q4.)

### 7.3 `task`

Phase 1 config:

```json
{
  "operation": "catalog:extract_text",
  "params": {}
}
```

`operation` MUST be a **registered catalog id** known to the worker, not a Python source string.

The catalog is code-reviewed, versioned with the worker image. Adding an operation is a deploy. This is the only way Phase 1 stays inside Temporal’s “deterministic workflow + well-defined activities” model.

If Q1 decides user Python is required for Phase 1, this spec is incomplete (sandbox, billing, infinite loops, network egress).

### 7.4 `http`

```json
{
  "method": "POST",
  "url": "https://example.com/api",
  "headers": { "Content-Type": "application/json" },
  "bodyTemplate": { "id": "{{ $.input.invoiceId }}" },
  "secretRef": "cred_invoice_api",
  "successStatuses": [200, 201, 202]
}
```

- URL, headers, body are rendered from context. Render MUST NOT be done in the workflow; the Activity receives context + template and renders internally.
- Secrets are **not** in the graph. `secretRef` is resolved in the Activity from a tenant credential store. In Phase 1 the store can be a Postgres table of encrypted blobs (envelope encryption, one key per env).
- 4xx in `successStatuses` miss → `HttpClientError` (non-retryable). 5xx / network → retryable.
- Idempotency: send header `Idempotency-Key: {workflowInstanceId}:{nodeId}:{attempt}` when the target is ours; for third parties, still generate the key and include it if `config.idempotencyHeader` is set.

### 7.5 `llm`

```json
{
  "model": "gemini-2.5-flash",
  "systemPrompt": "...",
  "userPromptTemplate": "...",
  "temperature": 0,
  "outputSchema": { "type": "object", "required": ["decision", "confidence"] }
}
```

Behavior:

1. Render prompts in the Activity.
2. Call `LlmRuntime`.
3. Parse JSON (or provider structured-output).
4. Validate against `outputSchema`. Failure → `ValidationError` (retry policy decides; default **do not retry** schema failures — retries will not change a stubborn model unless temperature > 0).
5. Return `{ output, metadata: { model, modelVersion, promptHash, tokenUsage, latencyMs, costEstimate } }`.

The workflow stores `output` (or `$ref`) plus a truncated metadata object. Full prompt/response bodies go to object storage if large.

### 7.6 `agent`

```json
{
  "runtime": "adk",
  "instructions": "...",
  "toolAllowlist": ["catalog:search", "catalog:fetch_doc"],
  "maxToolCalls": 8,
  "outputSchema": { "type": "object", "required": ["action"] }
}
```

`AgentRuntime.execute(...)` MUST:

- Run entirely inside an Activity
- Be bounded by `executionPolicy.timeout` and `maxToolCalls`
- Use **scoped credentials** derived from tenant + allowlist (README §33)
- Return a structured object that validates against `outputSchema`
- MUST NOT return “the next graph node to run” as a control instruction. It MAY return `{ "action": "REQUEST_REVIEW" }` as **data** for a downstream `decision`

Phase 1 ships one adapter: Google ADK. A second adapter is a later task, not a Phase 1 deliverable — but the Python protocol is required now.

### 7.7 `human`

```json
{
  "taskType": "approval",
  "assignee": { "type": "role", "value": "risk-reviewer" },
  "formSchema": {
    "type": "object",
    "properties": {
      "decision": { "type": "string", "enum": ["approve", "reject"] },
      "comment": { "type": "string" }
    },
    "required": ["decision"]
  },
  "timeout": "P3D",
  "onTimeout": "FAIL_WORKFLOW",
  "onReject": "FAIL_WORKFLOW"
}
```

Execution:

1. Activity `create_human_task` writes the row (idempotent on `instanceId+nodeId`).
2. Workflow waits on an Update `complete_human_task` **or** a timer for `timeout`.
3. API `POST /tasks/{id}/complete` authorizes the user, validates `formSchema`, then calls Temporal Update.
4. Output = the form payload.

`onReject` / `onTimeout` in Phase 1 are only `FAIL_WORKFLOW` or `COMPLETE_WITH_PAYLOAD` (payload specified in config). Routing “reject” to another branch is done by a downstream `decision` on the form output, not by magic edges from the human node. (See Q5.)

Assignee resolution in Phase 1: **any authenticated user in the tenant** may complete the task if `assignee.type = role` and the user’s token contains that role. If we ship without RBAC (Q8), treat assignee as display-only and allow any tenant user.

### 7.8 `decision`

Config: empty (conditions live on edges).
Evaluation is **deterministic** and happens **inside the workflow** using the recorded context. No Activity.

Expression language: **PROPOSAL = CEL (Common Expression Language)** over a sealed context document. Allowed types: bool, int, double, string, list, map. **No function that does I/O.** Expose fields as `input`, `nodes`. Example:

```text
nodes.analyze.output.confidence >= 0.90
```

README examples used `$.confidence`. We will support JSONPath-like field access **inside CEL**, not JSONPath itself, to avoid two languages. Publish-time validation compiles every `condition`.

---

## 8. Graph interpreter

### 8.1 Temporal workflow

**Type:** `GraphWorkflowRunner`
**Task queue:** `flowy-graph` (workflow) and `flowy-activities` (activities). Split later per node type if scale requires it.
**Input:**

```json
{
  "tenantId": "...",
  "workflowId": "...",
  "version": 7,
  "workflowInstanceId": "...",
  "inputRef": { "inline": {} }
}
```

**Loading the graph (critical):**

The workflow MUST NOT fetch Postgres on replay. Procedure:

1. First (and only) graph-load Activity: `load_definition(tenantId, workflowId, version)` → returns the IR.
2. That Activity result is in history; subsequent replays reuse it.
3. If the IR exceeds history-size comfort (PROPOSAL: 256 KiB serialized), the Activity stores the IR in object storage and returns `{ "$ref": "..." }` **plus a content hash**. A second Activity `fetch_graph_blob` is then also recorded. Still not a live fetch on replay.
4. Workflow memory holds the IR + node state. Use `continue_as-new` when history grows past a threshold (PROPOSAL: 10k events or 4 MiB), passing compacted node state + the same `$ref` hash. `continue_as_new` MUST fail if the blob hash cannot be verified.

### 8.2 Ready-set algorithm

Pure function in `engine`, called from the workflow after every state change:

```
ready(node) iff
  status == PENDING
  AND every incoming edge:
        predecessor is SKIPPED  → ignore this edge
        predecessor is COMPLETED AND (edge.condition is null OR already selected by a decision)
  AND if any non-skipped predecessor is not COMPLETED → not ready
```

For `decision` nodes, after COMPLETED (instant), evaluate out-edges exclusively; mark taken successor PENDING→READY path; mark not-taken successor subgraph SKIPPED (DFS through nodes whose all remaining in-edges are from skipped branches).

**Concurrency:** all READY nodes are started in the same workflow task using `asyncio.gather` / `workflow.gather` of their execute handlers. This gives parallel Activities without a Parallel node. Joins wait naturally via the ready-set.

### 8.3 Execute dispatch

```text
start     → mark COMPLETED, output = {input}
end       → mark COMPLETED, maybe set workflow result, maybe complete workflow
decision  → mark COMPLETED, evaluate edges
task/http/llm/agent → execute Activity with retry/timeout from executionPolicy
human     → create_human_task Activity; WAITING until Update or timeout
```

Activities receive:

```text
ExecutionContext { tenantId, workflowInstanceId, nodeId, nodeExecutionId, input, credentialsHandle }
```

They return `NodeResult { status, output | $ref, metadata }`.

`nodeExecutionId` is `{workflowInstanceId}:{nodeId}` for Phase 1 (no loop iterations). Idempotency keys derive from it.

### 8.4 Determinism checklist

Forbidden in workflow code:

- `datetime.now`, random, dicts from JSON that we iterate without sorting
- network, ORM, log-and-branch on side effects
- CEL that is non-pure

Allowed: CEL on recorded payloads; `workflow.now()` only for human-timeout deadlines (Temporal-safe); `workflow.uuid4()` only if recorded via Temporal SDK helpers.

### 8.5 Cancellation

API cancel → `temporalClient.cancel_workflow`.

Workflow cancellation handler MUST:

1. Mark remaining PENDING/READY/RUNNING/WAITING nodes CANCELLED in state (best-effort; history will show cancel)
2. Activity `close_open_human_tasks(instanceId)`
3. Do not run compensation (Phase 3)

Heartbeat long Activities so cancel is prompt.

### 8.6 Failure

Uncaught activity error after retries → instance FAILED. Persist last error on the node execution in Postgres via a fire-and-forget Activity `record_node_failure` (so the UI does not depend on querying Temporal internals). If that Activity also fails, Temporal history remains the source of truth.

---

## 9. Persistence

### 9.1 PostgreSQL (logical schema)

```text
tenants
users                          # Phase 1: enough to attach OIDC subject → tenant
workflows                      # (tenant_id, workflow_id)
workflow_definitions           # (tenant_id, workflow_id, version) JSONB graph, status
workflow_instances             # metadata + temporal ids + status denormalized for UI
node_executions                # optional denormalized mirror; Temporal is canonical
human_tasks                    # task inbox
credentials                    # encrypted secrets, referenced by secretRef
audit_events                   # append-only, Phase 1 lite
```

Every table has `tenant_id`. All queries MUST include it. RLS is a SHOULD for Phase 1, MUST before a second tenant exists in production.

Denormalized instance/node rows exist because listing “all waiting invoices for tenant X” is a Postgres query, not a Temporal visibility query. Writers: Activities and the API (for create/start). The workflow SHOULD NOT talk to Postgres itself.

### 9.2 Temporal

Owns: event history, timers, retries, the interpreter’s node-state as workflow-local variables.

Visibility search attributes (PROPOSAL): `TenantId`, `WorkflowId`, `InstanceStatus`, `DefinitionVersion`.

### 9.3 Object store

Bucket prefix: `{tenantId}/{workflowInstanceId}/{nodeId}/...`
Used for: documents, oversized LLM I/O, oversized graph IR.

### 9.4 What not to store where

| Data | Store |
|------|--------|
| Graph IR | Postgres (canonical); Temporal history (pinned copy / hash) |
| “Where is this run?” | Temporal |
| Run list / task inbox | Postgres |
| Customer business records | **not Flowy** (README §37) |
| PDFs / long generations | Object store |

---

## 10. API (Phase 1)

REST only. JSON. All routes prefixed `/v1`. Auth: `Authorization: Bearer`. Tenant from token.

Idempotency: mutating endpoints accept `Idempotency-Key`.

### 10.1 Workflows

```http
POST   /v1/workflows
GET    /v1/workflows
GET    /v1/workflows/{workflowId}
POST   /v1/workflows/{workflowId}/draft            # create or replace draft graph
POST   /v1/workflows/{workflowId}/validate
POST   /v1/workflows/{workflowId}/publish
GET    /v1/workflows/{workflowId}/versions
GET    /v1/workflows/{workflowId}/versions/{n}
```

Publish runs engine validation (schema, DAG, CEL compile, catalog refs, exactly one start). Failure → 400 with path-localized errors. Success → new published version, Temporal is not involved yet.

### 10.2 Executions

```http
POST   /v1/workflow-executions
GET    /v1/workflow-executions/{id}
GET    /v1/workflow-executions?workflowId=&status=
POST   /v1/workflow-executions/{id}/cancel
GET    /v1/workflow-executions/{id}/history
```

Start body:

```json
{
  "workflowId": "invoice-processing",
  "version": null,
  "input": {}
}
```

`version: null` → latest published. Reject start if no published version.

Start procedure:

1. Validate `input` against `inputSchema`
2. Insert instance row PENDING
3. `StartWorkflow`; on success set RUNNING and store run id
4. Return 201

`POST .../signal` and `POST .../update` from README §29 are **not** general-purpose in Phase 1. Human completion goes through the task API, which performs the Update. A generic signal endpoint is a foot-gun.

### 10.3 Human tasks

```http
GET    /v1/tasks
GET    /v1/tasks/{id}
POST   /v1/tasks/{id}/complete
POST   /v1/tasks/{id}/reject
```

`assign` is Phase 2.

`GET /v1/tasks` filters: `status=PENDING`, `workflowInstanceId`.

### 10.4 Events

`POST /v1/events` is Phase 2 (event gateway). Do not add a stub that pretends to correlate.

### 10.5 Errors

RFC 7807 problem+json. Validation errors include `instancePath` into the graph.

---

## 11. Studio (Phase 1)

Three screens, nothing else:

1. **Designer** — React Flow canvas; palette of Phase 1 node types; properties panel bound to each type’s config schema; validate + publish.
2. **Runs** — list + detail. Detail overlays node states on the same graph. Click a node: input/output/errors. No fake “step through” debugger.
3. **Inbox** — pending human tasks; render `formSchema` with a JSON-schema form; complete/reject.

Studio MUST load and save the IR in §6. Layout (`position: {x,y}`) lives under `metadata.layout` so the engine can ignore it.

---

## 12. Security (Phase 1 minimum)

- OIDC login; API verifies JWT; `tenant_id` and `sub` from claims.
- No tenant id in client-supplied body used for authz.
- Credentials never returned by API after create (write-only + last-4).
- Agent/LLM Activities get a **scoped credential handle**, not the tenant’s full secret bag.
- Graph JSON is untrusted data. CEL compilation with a cost budget. HTTP URL allowlist **PROPOSAL: optional per-tenant**; if unset, allow HTTPS only, block link-local/metadata IPs.
- `task` catalog operations run in-process in Phase 1 (no user code).
- Dev bypass auth: compile-time / env flag `FLOWY_DEV_AUTH=1`, default off in any non-dev profile.

RBAC roles from README §33 are **not** implemented as a permission graph in Phase 1. Document them as the target model. Ship one role: `operator`.

---

## 13. Observability and audit

### 13.1 Traces and metrics

Every API request and every Activity: OTel span.
Workflow: Temporal’s built-in traces; attach `tenantId`, `workflowInstanceId`, `nodeId`.

AI node metadata from README §30 is required on `llm` and `agent` results even in Phase 1 (model, tokens, latency). Cost MAY be null if the provider does not return it.

### 13.2 Audit lite

Append-only `audit_events` for:

```text
WORKFLOW_PUBLISHED
WORKFLOW_STARTED
NODE_COMPLETED
NODE_FAILED
HUMAN_TASK_CREATED
HUMAN_TASK_COMPLETED
HUMAN_TASK_REJECTED
WORKFLOW_CANCELLED
WORKFLOW_COMPLETED
```

Payload: `{ timestamp, actor, action, workflowInstanceId, nodeId }`.
Human decisions are immutable rows; updates are not allowed, only new events.

`HUMAN_TASK_VIEWED` is Phase 2 (requires product intent about surveillance of reviewers).

---

## 14. Reliability

Defaults if a node omits `executionPolicy`:

```json
{
  "timeout": "5m",
  "retry": {
    "maxAttempts": 5,
    "initialInterval": "2s",
    "backoffCoefficient": 2.0
  }
}
```

Human create-task Activity: timeout 30s, maxAttempts 8 (must succeed for the wait to be meaningful).
`llm`/`agent`: default timeout 2m / 10m respectively; `ValidationError` non-retryable.

At-least-once Activities ⇒ catalog operations and HTTP calls SHOULD be idempotent. Document this on each catalog entry.

---

## 15. Testing strategy

| Layer | What |
|-------|------|
| `engine` unit | DAG validation, skip-set, exclusive decision, AND-join, cycle reject |
| CEL unit | README examples + injection attempts |
| Workflow | Temporal test env: happy path invoice graph; human Update; cancel; activity retry; schema validation fail |
| API | publish validation errors; start pins version; task complete unauthorized |
| Contract | JSON Schema of IR checked against Studio fixtures |
| Compose smoke | start stack, publish fixture, run, complete human task |

No production LLM required for CI: `LlmRuntime` has a `replay/scripted` implementation used in tests.

---

## 16. Phase 2+ hooks (do not build, do not paint into a corner)

Keep these extension points:

- Node type registry so `timer`, `event_wait`, `parallel`, `join`, `subworkflow`, `loop` can register without changing the interpreter loop
- `graphRevision` on instances
- Update handler interface that Phase 3 mutation can reuse
- `AgentRuntime` protocol
- Event correlation key table (empty)

Do **not** add stub nodes that raise `NotImplementedError` on the canvas. If it is not runnable, it is not in the palette.

---

## 17. Implementation order

Build in this order so each step is demoable:

1. Graph IR JSON Schema + `engine` validation + ready-set (no Temporal)
2. Postgres models + definition API (draft / validate / publish)
3. Compose: Temporal + worker that runs a hard-coded two-node graph
4. `GraphWorkflowRunner` + `task` + `http` + `decision` + `end`
5. `llm` with scripted runtime + schema validation
6. `human` + task API + Update wait + timeout
7. `agent` with bounded fake runtime, then ADK adapter
8. Studio designer against the real publish API
9. Runs viewer + inbox
10. Cancel, audit events, OTel, blob offload

Do not start Studio before step 4. The canvas otherwise invents an IR the engine cannot run.

---

## 18. Assumptions register

| ID | Assumption | If wrong |
|----|------------|----------|
| P1 | Python everywhere for Phase 1 | Dual-language workers slip the schedule; IR still stays JSON |
| P2 | One draft per workflow | Need draft branches / named drafts |
| P3 | Exclusive decision + AND-join | Inclusive splits and OR-joins change the interpreter |
| P4 | First `end` completes the run | Multi-end wait-all is a different completion rule |
| P5 | No user Python | Task node is a catalog |
| P6 | CEL | Different expression language |
| P7 | Graph loaded once via Activity | Alternate: ship IR as workflow input only |
| P8 | Single region, one Temporal cluster, tenant_id as data | Hard isolation would be per-tenant namespaces |
| P9 | Studio is Next.js in this repo | Separate frontend repo |
| P10 | Phase 1 can run with one real tenant and one operator user | Full SaaS multi-tenancy from day one |

---

## 19. Open questions

These are ordered by how badly a wrong answer wrecks the design. Please answer with a decision, not a preference cloud. Where I have a default, fight it if it is wrong.

### Q1. What is a Phase 1 `task` node allowed to run?

README lists “Python function / Java service / Database operation / File processing / API call”. That cannot all be true on day one without a sandbox.

Pick one:

- **A (spec default):** worker-side catalog of named operations; adding a function is a deploy
- **B:** user-supplied Python (then: where does it run, CPU/memory limits, network policy, how is it versioned with the definition?)
- **C:** no `task` type in Phase 1; only `http` + `llm` + `agent` + `human`

If you pick B, Phase 1 is a sandbox product, not a workflow product.

### Q2. Is Phase 1 actually multi-tenant?

README primary goal 9 and §32 say yes, and “never trust tenant_id from the client.” That forces OIDC, tenant-on-every-row, and credential isolation before a single invoice demo.

Pick one:

- **A (spec default):** tenant_id on every row + JWT, but only one tenant configured; no self-serve signup
- **B:** hard-code a single tenant in the API until Phase 2; faster demo, migrate later
- **C:** real multi-tenant SaaS (invites, isolation review, RLS, per-tenant secret KMS) in Phase 1

B is a one-way leak if you then store secrets. If there will ever be a second tenant in this deployment, do not pick B.

### Q3. Decision semantics: exclusive or inclusive?

README §13 draws a diamond (`score > .9` vs `score <= .9`) which is exclusive. Nothing says what happens if two conditions are true, or none.

Pick one:

- **A (spec default):** exclusive, first matching edge in stable id order, optional default edge, else FAIL
- **B:** exclusive, but conditions MUST be proven disjoint at publish time
- **C:** inclusive (all matching edges fire) — this is Parallel in disguise and pulls Join into Phase 1

If you want B, who writes the prover — us, or the user?

### Q4. When is a workflow complete?

The §40 diagram joins two branches at Complete **without** a Join node. Possible rules:

- **A (spec default):** AND-join on any node with multiple in-edges, including `end`; workflow completes when that `end` runs
- **B:** first `end` reached completes the workflow and cancels in-flight siblings
- **C:** all `end` nodes that are not SKIPPED must complete (wait-all)

A and B disagree on “auto process” vs “human review” if a bug takes **both** branches. This is a safety choice, not a style choice.

### Q5. Human reject and human timeout: fail the run, or become data?

README shows Approve/Reject as graph branches, and also `POST /tasks/{id}/reject`. Those are different products.

Pick one per signal:

Reject:

- **A (spec default):** `reject` API marks task rejected and FAILS the instance unless `onReject = COMPLETE_WITH_PAYLOAD`; routing is a `decision` on `{ decision: "reject" }`
- **B:** `reject` is just a form value; there is no separate reject API
- **C:** reject auto-follows a reserved edge `from: human, condition: rejected`

Timeout (`P3D`):

- **A (spec default):** FAIL_WORKFLOW
- **B:** COMPLETE with `{ timedOut: true }` and let the graph continue
- **C:** escalate (reassign) — Phase 2+

If you pick C for reject, the IR needs reserved edges and Studio UX for them now.

### Q6. Where do secrets live, and may HTTP nodes call the public internet?

A workflow designer that can HTTP POST is an SSRF cannon.

Pick:

- **A (spec default):** HTTPS only, block RFC1918/link-local/metadata; secrets in encrypted Postgres; optional per-tenant URL allowlist
- **B:** allowlist required, no arbitrary URLs in Phase 1
- **C:** unrestricted in Phase 1 (internal users only)

Also: are credentials **per tenant**, **per workflow**, or **per node**?

### Q7. Agent node in Phase 1: real ADK, or interface + stub?

README Phase 1 includes Agent. ADK as an Activity with tools is the highest-variance component (long runtimes, tool creds, non-structured output, cost).

Pick:

- **A (spec default):** protocol + scripted runtime in CI; one ADK happy-path behind a flag
- **B:** ADK is a Phase 1 blocker; invoice demo must use a real agent with tools
- **C:** drop Agent from Phase 1; `llm` is enough for the §40 demo

If B: list the tools the invoice demo is allowed to call. “Whatever the model wants” violates README §28.

### Q8. AuthN/Z for the first demo

README §33 lists five roles and eight permissions. Phase 1 spec collapses to OIDC + `operator`.

Pick:

- **A (spec default):** OIDC, one role, assignee.role is cosmetic
- **B:** skip auth in Phase 1 (localhost)
- **C:** implement the full RBAC table now

If B, Q2 must also be B. Do not ship an unauthenticated multi-tenant API.

### Q9. Expression language

README: “constrained expression language rather than arbitrary code,” examples `$.confidence >= 0.90`.

Pick:

- **A (spec default):** CEL
- **B:** JSONPath existence + a tiny comparison grammar we own
- **C:** JSONata
- **D:** CEL subset we reimplement so we do not take a dependency

D is how you get a CVE. If you hate CEL, pick B and keep it tiny.

### Q10. Versioning in Phase 1 or Phase 2?

README contradicts itself:

- Goal 7 and §24: published versions are immutable; instances pin a version
- §41 Phase 2 list includes “Versioning”

Pick:

- **A (spec default):** integer versions + pin at start are in Phase 1; no migration of running instances
- **B:** overwrite a single graph blob until Phase 2 (running instances can change meaning mid-flight — this is incompatible with A1/A2)

If you pick B you are not building the system in the README. Say so.

### Q11. Temporal: Cloud or self-hosted Compose?

Affects auth to Temporal, namespaces, how CI runs workers.

Pick: **Cloud** / **self-hosted in Compose** (spec default for local) / **both, namespace-per-env**.

Is a dedicated Temporal namespace **per tenant** a Phase 1 requirement? (Spec default: **no**, one namespace, tenant as search attribute.)

### Q12. Workflow result and input size

What is the hard cap on `input` JSON? On node output before `$ref` offload?

Spec defaults: **64 KiB** start input inline; **24 KiB** node output inline. Anything else is object storage.

Do you have a real document size for the invoice demo (MB PDFs)? If yes, upload-to-object-store is a Phase 1 feature, not a nicety.

### Q13. Pause / Resume

The architecture diagram lists Pause/Resume. Phase 1 list does not.

Pick: **drop until Phase 2** (spec default) / **required for Phase 1**. If required, define: pause between nodes only, or also cooperative pause inside Activities?

### Q14. Who is the user of Studio in Phase 1?

Internal operator building a handful of workflows, or customers self-serve designing graphs?

This decides how much validation UX, how much guardrail copy, and whether `agent` tools can include “run HTTP to customer-chosen URL.”

### Q15. Catalog contents for the §40 demo

Name the exact operations the first demo needs, e.g.:

- `catalog:put_blob` / `catalog:extract_text`
- `http` to a fake invoice API
- `llm:analyze_invoice` with a fixed output schema
- `human:review`

If you cannot name them, Phase 1 `task` is undefined and Q1 is not actually answered.

### Q16. Failure policy surface in Studio

README §35 lists Retry / Fallback / Ignore / Compensate / Fail Workflow. Phase 1 spec implements Retry (via Temporal) and Fail Workflow only.

Confirm: **no Fallback/Ignore/Compensate in the Phase 1 UI**. Adding a disabled dropdown is how Studio and engine drift.

### Q17. Language of timestamps and durations

Human timeout is ISO-8601 duration `P3D`. Timers (Phase 2) mention “tomorrow 9 AM”.

Pick timezone rule now even if timers are later: **UTC only** (spec default) / **tenant default TZ** / **per-workflow TZ**. “Tomorrow 9 AM” is meaningless without this.

### Q18. Open-source vs internal, and license

There is no license in the README. Does this repo ship an OSS license in Phase 1? If yes, ADK/Gemini coupling belongs behind the interface even more strictly.

---

## 20. What I will not implement until Q1–Q7, Q10, Q15 are answered

Those six decide the IR, the worker threat model, and the demo. The rest can default.

If no reply, implementation will follow the **spec defaults (A options)** and treat Q15 catalog as:

1. `extract_text` — fixture/plain-text passthrough
2. `auto_process` — no-op persist of the decision
3. `llm` analyze with schema `{ decision, confidence, explanation }`
4. `human` review of that object

That is enough to prove the interpreter. It is not enough to prove a product. Tell me if the product bar is higher.
