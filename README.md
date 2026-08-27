# Flowy : General-Purpose Durable AI Workflow Platform

Implementation spec (Phase 1 contracts, Temporal interpreter, open questions): [`docs/implementation-spec.md`](docs/implementation-spec.md)

## 1. Product Definition

Build a **multi-tenant workflow orchestration platform** for designing, executing, monitoring, and modifying long-running workflows containing:

* Deterministic/non-AI tasks
* API integrations
* AI-assisted tasks
* Autonomous AI agents
* Human forms and approvals
* External event waits
* Timers and deadlines
* Conditional branching
* Parallel execution
* Loops
* Sub-workflows
* Runtime workflow modifications

The platform uses **Temporal as the durable execution substrate** and treats the workflow graph as **versioned data interpreted by a generic Temporal Workflow**.

The core principle:

> **Temporal owns durable execution; the platform owns workflow semantics.**

---

# 2. Goals

### Primary goals

1. Allow users to visually construct arbitrary workflows.
2. Execute workflows reliably for milliseconds to years.
3. Support AI and non-AI nodes uniformly.
4. Support durable human interaction.
5. Support durable external-event waiting.
6. Provide retries, timeouts, cancellation, and recovery.
7. Allow workflow versions to evolve safely.
8. Provide complete execution history and auditability.
9. Support multi-tenancy.
10. Make AI runtime replaceable.
11. Allow workflows to be dynamically modified where explicitly permitted.

### Non-goals

The platform should not initially attempt to:

* Replace Temporal's core durability engine.
* Build its own LLM inference infrastructure.
* Become a general-purpose BPMN replacement.
* Allow arbitrary nondeterministic code inside Temporal Workflows.
* Treat an LLM agent as the workflow orchestrator by default.

---

# 3. High-Level Architecture

```text
                         ┌──────────────────────┐
                         │    Workflow Studio   │
                         │                      │
                         │ Graph Editor         │
                         │ Forms                │
                         │ Debugging             │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Workflow Definition  │
                         │       Service        │
                         └──────────┬───────────┘
                                    │
                              Immutable Graph
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────┐
│                         API Layer                          │
│ REST / GraphQL / WebSocket / Webhooks                      │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │     Execution Service   │
                 │                         │
                 │ Start / Signal / Update │
                 │ Cancel / Pause / Resume │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │        Temporal         │
                 │                         │
                 │ Graph Workflow Runner   │
                 └────────────┬────────────┘
                              │
             ┌────────────────┼─────────────────┐
             ▼                ▼                 ▼
       ┌───────────┐    ┌────────────┐    ┌──────────────┐
       │ Task      │    │ AI / Agent │    │ Human Task   │
       │ Workers   │    │ Workers    │    │ Service      │
       └───────────┘    └────────────┘    └──────────────┘
             │                │                 │
             ▼                ▼                 ▼
         APIs / DB        ADK / LLM         Users
```

---

# 4. Core Domain Model

There are five distinct concepts.

```text
Workflow
   │
   ├── Workflow Definition
   │       └── Version
   │             └── Graph
   │
   └── Workflow Instances
           └── Node Executions
```

## 4.1 Workflow

Logical identity:

```json
{
  "workflowId": "invoice-processing",
  "tenantId": "tenant-123",
  "name": "Invoice Processing"
}
```

A Workflow can have many versions.

---

# 5. Workflow Definition

A workflow definition is immutable once published.

```json
{
  "workflowId": "invoice-processing",
  "version": 7,
  "status": "PUBLISHED",

  "inputSchema": {},

  "nodes": [],
  "edges": [],

  "metadata": {
    "createdBy": "user-123",
    "createdAt": "..."
  }
}
```

Versioning:

```text
invoice-processing
       │
       ├── v1
       ├── v2
       ├── v3
       ├── v4
       └── v7 ← latest
```

Existing instances continue using the version with which they started unless explicitly migrated.

---

# 6. Graph Model

The workflow graph consists of:

```text
Node
Edge
```

Nodes have:

```json
{
  "id": "analyze",
  "type": "agent",
  "config": {},
  "inputMapping": {},
  "outputSchema": {}
}
```

Edges:

```json
{
  "from": "analyze",
  "to": "review",
  "condition": "result.confidence < 0.9"
}
```

---

# 7. Node Taxonomy

The platform should initially support these node types.

## 7.1 Start

No execution logic.

```text
START
  ↓
```

---

## 7.2 End

Terminates a branch/workflow.

---

## 7.3 Task

Generic deterministic operation.

Examples:

* Python function
* Java service
* Database operation
* File processing
* API call

Temporal implementation:

**Activity**

---

## 7.4 HTTP Node

```text
HTTP POST
https://example.com/api
```

Configuration:

```json
{
  "method": "POST",
  "url": "...",
  "headers": {},
  "bodyTemplate": {}
}
```

Temporal:

```text
Activity
```

---

# 8. AI-Assisted Node

This node performs a bounded AI task.

Examples:

```text
Extract fields
Classify document
Summarize
Generate response
Rewrite text
Validate content
```

Configuration:

```json
{
  "model": "gemini-...",
  "systemPrompt": "...",
  "temperature": 0,
  "outputSchema": {}
}
```

Execution:

```text
Temporal Workflow
        │
        ▼
AI Activity
        │
        ▼
LLM
```

The result must be validated against the declared schema.

---

# 9. Agent Node

An Agent Node is more autonomous.

```text
Agent
 ├── Reason
 ├── Call tools
 ├── Retrieve information
 ├── Call other services
 └── Produce result
```

The platform should expose an abstraction:

```text
AgentRuntime
```

Implementations can include:

```text
Google ADK
LangGraph
Custom Agent
```

For example:

```text
Temporal Activity
      │
      ▼
ADK Runtime
      │
      ├── Agent
      ├── Tools
      └── LLM
```

The workflow engine does not depend on ADK-specific concepts.

---

# 10. Human Task Node

First-class node.

Examples:

```text
Approve
Reject
Review
Fill Form
Edit AI Output
Assign Task
```

Configuration:

```json
{
  "taskType": "approval",

  "assignee": {
    "type": "role",
    "value": "risk-reviewer"
  },

  "formSchema": {
    "type": "object",
    "properties": {
      "decision": {
        "type": "string",
        "enum": ["approve", "reject"]
      },
      "comment": {
        "type": "string"
      }
    }
  },

  "timeout": "P3D"
}
```

Execution:

```text
Workflow
   │
   ▼
Create Human Task
   │
   ▼
WAITING
   │
   │ user acts
   ▼
Signal / Update
   │
   ▼
Continue
```

No worker remains blocked during the wait.

---

# 11. Event Wait Node

Example:

```text
Send Payment Request
        ↓
Wait for payment.completed
        ↓
Process Payment
```

Configuration:

```json
{
  "eventType": "payment.completed",

  "correlation": {
    "paymentId": "$.payment.id"
  },

  "timeout": "P7D"
}
```

External event:

```text
Kafka
Webhook
SQS
API
```

becomes:

```text
Event Gateway
     ↓
Find workflow instance
     ↓
Temporal Signal / Update
```

---

# 12. Timer Node

Examples:

```text
Wait 10 minutes
Wait until tomorrow 9 AM
Wait 7 days
```

Implementation:

**Temporal Timer**

No custom scheduler is required.

---

# 13. Decision Node

Pure deterministic logic.

```text
             Analyze
                │
                ▼
             Decision
            /        \
       score > .9   score <= .9
          /             \
       Approve        Human Review
```

Conditions should use a constrained expression language rather than arbitrary code.

For example:

```text
$.confidence >= 0.90
```

or:

```text
$.customer.risk == "HIGH"
```

---

# 14. Parallel Node

Example:

```text
             Start
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
     Fraud   Credit   Identity
       │       │        │
       └───────┼────────┘
               ▼
             Join
```

The runtime schedules activities concurrently.

The Join node becomes ready when its required predecessors complete.

---

# 15. Loop Node

The platform needs explicit loop semantics.

Example:

```text
Fetch Items
    ↓
Process Item
    ↓
More Items?
   ├── yes → Process Item
   └── no  → Complete
```

Loops should have:

* Maximum iteration count
* Optional timeout
* Optional termination condition

This protects against infinite workflows.

---

# 16. Sub-workflow Node

A workflow can invoke another workflow:

```text
Main Workflow
      │
      ▼
Payment Workflow
      │
      ▼
Continue
```

Temporal implementation:

**Child Workflow**

This gives you hierarchical composition without requiring every workflow to be one enormous graph.

---

# 17. Node Execution Contract

Every executable node should conform conceptually to:

```text
NodeExecutor

execute(
    node,
    input,
    execution_context
)
       ↓
NodeResult
```

Result:

```json
{
  "status": "COMPLETED",
  "output": {},
  "metadata": {}
}
```

Potential statuses:

```text
COMPLETED
FAILED
WAITING
CANCELLED
```

However, the actual Temporal Activity should generally only represent executable work. Waiting nodes should use Temporal's native durable mechanisms.

---

# 18. Execution State

The graph engine maintains logical state:

```json
{
  "workflowInstanceId": "instance-123",

  "definition": {
    "workflowId": "invoice",
    "version": 7
  },

  "nodes": {
    "extract": {
      "status": "COMPLETED",
      "output": {}
    },

    "analyze": {
      "status": "COMPLETED",
      "output": {}
    },

    "review": {
      "status": "WAITING"
    }
  }
}
```

Node states:

```text
PENDING
READY
RUNNING
WAITING
COMPLETED
FAILED
SKIPPED
CANCELLED
```

---

# 19. Graph Execution Algorithm

The Temporal Workflow acts as the graph interpreter.

Conceptually:

```python
while not graph.completed():

    ready = graph.find_ready_nodes(state)

    for node in ready:
        execute(node)

    graph.apply_results()

    graph.evaluate_conditions()
```

But execution must use Temporal primitives.

```text
                    Graph State
                        │
                        ▼
                 Find READY nodes
                        │
              ┌─────────┴──────────┐
              ▼                    ▼
         Activity A           Activity B
              │                    │
              └─────────┬──────────┘
                        ▼
                   Apply results
                        │
                        ▼
                 Evaluate edges
                        │
                        ▼
                   Next nodes
```

---

# 20. Temporal Architecture

The platform should treat Temporal as an infrastructure dependency.

```text
                    Platform
                       │
                       ▼
               Temporal Client
                       │
                       ▼
              Temporal Service
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
     Workflow Workers         Activity Workers
```

### Workflow Worker

Runs:

```text
GraphWorkflowRunner
```

### Activity Workers

Execute:

```text
HTTP
Database
Python
AI
Agent
Integration
```

Workers can be independently scaled.

---

# 21. Durable Human Interaction

This is one of the most important platform features.

Workflow:

```text
AI Analyze
    ↓
Human Review
    ↓
WAIT
```

Temporal workflow:

```text
workflow
   │
   ├── execute AI Activity
   │
   ├── create Human Task
   │
   ├── wait_condition(...)
   │
   │      ... days ...
   │
   └── continue
```

Human Task Service:

```text
POST /tasks/{taskId}/complete
```

then:

```text
Human Task Service
       │
       ▼
Temporal Signal/Update
       │
       ▼
Workflow
```

---

# 22. External Event Architecture

```text
                  External System
                        │
                    Webhook
                        ▼
                ┌──────────────┐
                │ Event Gateway│
                └──────┬───────┘
                       │
                 correlation ID
                       ▼
                Temporal Signal
                       │
                       ▼
                  Workflow
```

Correlation must be explicit.

Example:

```text
tenantId
workflowId
workflowInstanceId
eventType
correlationKey
```

Never rely solely on event type.

---

# 23. Data Storage

Use multiple stores for different purposes.

```text
                 ┌───────────────┐
                 │   PostgreSQL  │
                 │               │
                 │ Definitions   │
                 │ Versions      │
                 │ Human Tasks   │
                 │ Metadata      │
                 └───────────────┘

                 ┌───────────────┐
                 │    Temporal   │
                 │               │
                 │ Event History │
                 │ Execution     │
                 │ Timers        │
                 │ Tasks         │
                 └───────────────┘

                 ┌───────────────┐
                 │ Object Store  │
                 │               │
                 │ Large payloads│
                 │ Documents     │
                 │ AI artifacts  │
                 └───────────────┘
```

Do **not** put huge documents or massive LLM outputs directly into Temporal history.

Use references:

```json
{
  "document": "s3://bucket/document.pdf"
}
```

---

# 24. Workflow Versioning

Published definitions are immutable.

```text
Draft
  ↓
Validated
  ↓
Published
```

Once published:

```text
v7
```

cannot be modified.

Editing creates:

```text
v8
```

Existing execution:

```text
instance-123 → v7
```

New execution:

```text
instance-456 → v8
```

This is essential for reproducibility.

---

# 25. Runtime Graph Mutation

Support it explicitly rather than pretending a workflow definition can be mutated.

Example:

```text
Original:

A → B → C → D
```

Runtime modification:

```text
A → B → C → E → D
```

Represent it as an **instance-level graph revision**:

```text
Definition:
    v7

Instance:
    definition_version = 7
    graph_revision = 3
```

A Temporal Update can request:

```json
{
  "operation": "INSERT_NODE",
  "node": {},
  "before": "D"
}
```

The workflow validates whether the mutation is legal.

---

# 26. Mutation Rules

Initially allow only safe mutations:

### Allowed

```text
Insert node after current node
Insert node before an unexecuted node
Add optional branch
Modify future configuration
```

### Potentially dangerous

```text
Modify completed node
Delete completed node
Change dependency of completed node
Change semantics of a running node
```

These should require explicit migration semantics.

---

# 27. AI/HITL Pattern

One of the primary workflows should look like:

```text
                  AI Analysis
                      │
                      ▼
                  Confidence
                  /         \
                 /           \
             High             Low
              │                │
              ▼                ▼
        Auto Process       Human Review
                               │
                         ┌─────┴─────┐
                         ▼           ▼
                      Approve      Reject
                         │           │
                         └─────┬─────┘
                               ▼
                           Complete
```

The AI should be able to return:

```json
{
  "decision": "approve",
  "confidence": 0.82,
  "evidence": [],
  "explanation": "...",
  "proposedAction": {}
}
```

The human task UI can render this as a review screen.

---

# 28. AI Safety Boundary

AI nodes should never automatically have unrestricted workflow-control privileges.

Prefer:

```text
Agent
  ↓
Structured result
  ↓
Workflow Decision
```

rather than:

```text
Agent
  ↓
"Do whatever you think is best"
  ↓
Entire workflow
```

The workflow graph should define the **allowed actions**.

An agent can recommend:

```json
{
  "action": "REQUEST_REVIEW"
}
```

The graph decides what that means.

---

# 29. API Surface

### Workflow management

```http
POST   /workflows
GET    /workflows
GET    /workflows/{id}
POST   /workflows/{id}/versions
POST   /workflows/{id}/publish
```

### Execution

```http
POST   /workflow-executions
GET    /workflow-executions/{id}
POST   /workflow-executions/{id}/cancel
POST   /workflow-executions/{id}/signal
POST   /workflow-executions/{id}/update
```

### Human tasks

```http
GET    /tasks
GET    /tasks/{id}
POST   /tasks/{id}/complete
POST   /tasks/{id}/reject
POST   /tasks/{id}/assign
```

### Events

```http
POST /events
```

---

# 30. Observability

Every execution should expose:

```text
Workflow
 ├── status
 ├── duration
 ├── started_at
 ├── completed_at
 │
 └── Nodes
      ├── status
      ├── duration
      ├── attempts
      ├── input
      ├── output
      └── errors
```

For AI nodes additionally:

```text
model
model_version
prompt_version
token_usage
latency
cost
tool_calls
```

This should integrate with your existing observability stack.

---

# 31. Audit Trail

For regulated workflows:

```text
Workflow Started
Node Completed
AI Decision Generated
Human Task Created
Human Task Viewed
Human Approved
Workflow Modified
Workflow Resumed
Workflow Completed
```

Each event:

```json
{
  "timestamp": "...",
  "actor": "user-123",
  "action": "APPROVE",
  "workflowInstanceId": "...",
  "nodeId": "review"
}
```

Human decisions should be immutable audit records.

---

# 32. Multi-Tenancy

Every resource carries:

```text
tenant_id
```

Logical hierarchy:

```text
Tenant
 ├── Workflows
 ├── Workflow Versions
 ├── Executions
 ├── Human Tasks
 └── Credentials
```

Never trust tenant IDs supplied by clients for authorization. Resolve them from authenticated identity/context.

---

# 33. Security Model

RBAC:

```text
Workflow Admin
Workflow Designer
Workflow Operator
Reviewer
Viewer
```

Permissions:

```text
workflow:create
workflow:edit
workflow:publish
workflow:execute
workflow:cancel
workflow:view
task:approve
task:assign
```

AI agents should use scoped credentials.

For example:

```text
Agent A
 ├── KB read
 ├── Customer API read
 └── No payment-write permission
```

---

# 34. Reliability Semantics

Every Activity must define:

```text
timeout
retry policy
maximum attempts
backoff
```

Example:

```json
{
  "retry": {
    "maxAttempts": 5,
    "initialInterval": "2s",
    "backoffCoefficient": 2
  },
  "timeout": "5m"
}
```

Activities interacting with external systems should be **idempotent** wherever possible.

For example:

```text
paymentId = workflowInstanceId + nodeExecutionId
```

can act as an idempotency key.

---

# 35. Failure Handling

A node can have:

```text
Retry
Fallback
Ignore
Compensate
Fail Workflow
```

Example:

```text
             Call Payment
                  │
             ┌────┴─────┐
             │          │
           Success    Failure
             │          │
             ▼          ▼
           Continue   Retry
                         │
                    max attempts
                         │
                         ▼
                     Compensate
```

Compensation becomes particularly important for distributed business processes.

---

# 36. Cancellation

Cancellation should propagate:

```text
Workflow
   │
   ├── Activity A
   ├── Activity B
   └── Human Task
```

If the workflow is cancelled:

```text
Temporal cancellation
        │
        ├── cancel Activities
        ├── close human tasks
        └── execute cleanup/compensation
```

---

# 37. Workflow State vs Business Data

Keep them separate.

### Temporal

```text
"Where is this workflow?"
```

### Application database

```text
"What is the customer's account?"
```

### Object storage

```text
"Where is the PDF?"
```

### Workflow metadata DB

```text
"What definition/version/configuration does this workflow use?"
```

This separation prevents Temporal from becoming your general-purpose database.

---

# 38. Recommended Technology Stack

Given your existing stack, I'd use:

```text
Frontend
    Next.js + React + React Flow

API
    Python + FastAPI

Workflow
    Temporal

Workflow Workers
    Python

AI
    Google ADK
    Gemini / other LLM providers

Database
    PostgreSQL

Object Storage
    S3

Messaging / Event Gateway
    Kafka / SQS depending on integration

Observability
    OpenTelemetry
    Datadog / CloudWatch

Authentication
    OAuth/OIDC

Infrastructure
    AWS ECS/EKS
    Terraform
```

You could also use Java for Activities where existing enterprise services need it.

---

# 39. Repository Structure

I'd keep the platform separated roughly like:

```text
workflow-platform/
│
├── api/
│   ├── workflows/
│   ├── executions/
│   ├── tasks/
│   └── events/
│
├── workflow-engine/
│   ├── graph/
│   ├── scheduler/
│   ├── state/
│   ├── expressions/
│   └── validation/
│
├── temporal/
│   ├── workflows/
│   │   └── graph_runner.py
│   ├── activities/
│   │   ├── http.py
│   │   ├── database.py
│   │   ├── ai.py
│   │   └── integrations.py
│   └── workers/
│
├── agents/
│   ├── adk/
│   └── common/
│
├── human-tasks/
│
├── event-gateway/
│
├── definitions/
│
└── frontend/
    ├── designer/
    ├── executions/
    └── tasks/
```

---

# 40. MVP

I would **not build everything above initially**.

### Phase 1

Support:

```text
Start
Task
HTTP
LLM
Agent
Human Approval
Decision
End
```

Plus:

```text
Sequential execution
Conditional branching
Retries
Timeouts
Temporal persistence
Basic UI
```

Example:

```text
Upload Document
       ↓
Extract
       ↓
AI Analyze
       ↓
Confidence?
    /       \
  High      Low
   │         │
   │      Human Review
   │         │
   └────┬────┘
        ▼
     Complete
```

---

# 41. Phase 2

Add:

```text
Parallelism
Join
Timers
External Events
Webhooks
Sub-workflows
Dynamic forms
RBAC
Audit
Versioning
```

---

# 42. Phase 3

Add the genuinely differentiated functionality:

```text
Runtime graph mutation
Workflow migration
AI-assisted workflow creation
Agent-generated plans
Advanced compensation
Workflow simulation
Replay/debugging
Cost-aware AI routing
Policy enforcement
```

---

# 43. One Critical Architectural Decision

There are two ways to build this.

### Approach A — Compile graph into Temporal code

```text
Graph
 ↓
Generate Python
 ↓
Temporal Workflow
```

I would **not choose this** as the primary architecture.

It makes dynamic workflows and versioning unnecessarily complicated.

### Approach B — Graph interpreter

```text
Graph JSON
     ↓
Generic Temporal Workflow
     ↓
Interpret graph
     ↓
Activities / Signals / Timers
```

**I strongly recommend B.**

Your product then has:

```text
                     Workflow Graph
                           │
                           ▼
                 ┌──────────────────┐
                 │ Graph Interpreter│
                 └────────┬─────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          Activity       Signal       Timer
             │            │            │
             ▼            ▼            ▼
         API / AI       Human       Delay
```

This is what allows a workflow created at **10:37 PM by a customer** to become a durable Temporal execution without deploying new code.

---

# 44. The Core Abstraction

Ultimately, the entire platform can revolve around this:

```text
Node
│
├── deterministic work
├── AI work
├── human work
├── external wait
├── timer
├── decision
└── child workflow
```

Every node has:

```text
Input
Configuration
Execution Policy
Output Schema
Error Policy
```

And the runtime gives it:

```text
Execution Context
├── workflow instance
├── variables
├── previous outputs
├── tenant
├── identity
└── credentials
```

The result is:

```text
COMPLETED
WAITING
FAILED
CANCELLED
```

That is the abstraction I would build the entire system around.

---

## 45. Final Architecture

```text
                         ┌──────────────────────┐
                         │    Workflow Studio   │
                         │                      │
                         │  Graph Designer      │
                         │  Forms               │
                         │  Execution Viewer    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Workflow Definition  │
                         │       Service        │
                         │                      │
                         │ Graph + Versioning   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Execution API     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │          Temporal            │
                     │                             │
                     │   GraphWorkflowRunner       │
                     │                             │
                     │  Durable State / Timers     │
                     │  Signals / Retries          │
                     └──────────────┬──────────────┘
                                    │
            ┌───────────────────────┼──────────────────────┐
            │                       │                      │
            ▼                       ▼                      ▼
      ┌───────────┐          ┌────────────┐        ┌────────────┐
      │ Activities│          │ AI Runtime │        │ Human Task │
      │           │          │            │        │            │
      │ HTTP      │          │ ADK        │        │ Forms      │
      │ DB        │          │ Gemini     │        │ Approval   │
      │ Python    │          │ Agents     │        │ Review     │
      │ Services  │          │ RAG        │        │ Assignment │
      └─────┬─────┘          └─────┬──────┘        └─────┬──────┘
            │                      │                     │
            └──────────────────────┼─────────────────────┘
                                   ▼
                          External Systems
```

The resulting platform is **not an "AI workflow engine."** It is a **durable general-purpose workflow engine with AI as a first-class execution capability**.

That distinction is important: once you model **AI, deterministic computation, humans, events, and timers all as nodes in the same durable graph**, the platform can handle conventional business processes and agentic workflows without needing a separate orchestration model for each.
