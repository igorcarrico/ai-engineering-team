# The LangGraph workflow

The orchestration is a compiled [LangGraph](https://langchain-ai.github.io/langgraph/)
`StateGraph`. This document describes its state, topology, control flow and the
runtime concerns layered around it.

## Topology

```
        START
          │
          ▼
   product_manager
          │
          ▼
      architect ◀─────────────────────┐
        │   │                         │
   ┌────┘   └────┐                    │ refine (iteration += 1)
   ▼             ▼                     │
backend_     frontend_                │
engineer     engineer                 │
   └────┬────────┘                    │
        ▼  (join: waits for both)     │
    qa_engineer                       │
        ▼                             │
 security_reviewer                    │
        ▼                             │
   code_reviewer ──── route_after_review
        │                  │
        │ approve          │ revise & budget left
        ▼                  └──────────┘
     finalize
        ▼
       END
```

- **Parallel fan-out**: `architect` has edges to both engineer nodes; they run
  concurrently in the same superstep.
- **Join**: `qa_engineer` has inbound edges from both engineers, so LangGraph
  waits for both before it runs.
- **Conditional loop**: `route_after_review` is the only branch — it returns
  `refine` or `finalize`.

## State

`EngineeringTeamState` (a `TypedDict`) carries everything through the graph:

- Inputs: `idea`, `name`, `constraints`, `provider`, `model`.
- Control: `iteration`, `max_iterations`, `revision_focus`.
- Per-agent outputs: `product_manager`, `architect`, … `code_reviewer`
  (JSON-serializable dicts).
- `artifacts`: the **only reduced field** — annotated with `operator.add` so the
  two parallel engineer nodes can both append without clobbering each other.
- Outputs: `status`, `review_score`, `final_summary`.

Every other field is written by exactly one node per superstep, so last-write
semantics are correct and intentional (a refine pass overwrites the architect's
prior output while artifacts accumulate as history; duplicates are de-duplicated
by path at persistence time).

## Nodes

Each agent is wrapped by `make_agent_node()` (in `graph/nodes.py`), which owns
the orchestration concerns the agent shouldn't:

1. Emit `agent_started`.
2. Stream `agent_progress` steps (gives the activity feed its cinematic pacing).
3. Invoke the agent with **bounded retries** (`agent_max_retries`), emitting
   `agent_retry` on transient failures and `agent_failed` if exhausted.
4. Render artifacts and emit `artifact_created` for each.
5. Emit `agent_completed` (with duration and, for the reviewer, the score).
6. Return the state delta.

Two control nodes complete the graph:

- `refine` — increments `iteration`, emits `iteration_started`, loops to
  `architect`.
- `finalize` — composes the executive **Delivery Summary** artifact and emits
  `run_completed`.

## Routing

```python
def route_after_review(state) -> "refine" | "finalize":
    wants_revision = state["code_reviewer"]["verdict"] == "revise"
    has_budget = state["iteration"] + 1 < state["max_iterations"]
    return "refine" if (wants_revision and has_budget) else "finalize"
```

With the default `max_iterations = 2` and the mock reviewer (which requests
`revise` on the first pass and `approve` afterward), every demo shows **exactly
one refinement loop** — a visible, deterministic demonstration of the
conditional cycle.

## Dependency injection

Provider and emitter are injected via LangGraph's `config["configurable"]`, so
the same compiled graph runs against any provider and any event sink:

```python
config = {
    "configurable": {
        "thread_id": run_id,        # checkpointer scope
        "provider": llm,            # LLMProvider
        "emitter": emitter,         # EventEmitter
        "agent_max_retries": 2,
    },
    "recursion_limit": 60,
}
```

## Checkpointing & streaming

- The graph compiles with a `MemorySaver` checkpointer keyed by `thread_id`
  (`run_id`), making a run resumable/replayable within the process.
- The orchestration service drives execution with
  `graph.astream(state, config, stream_mode="values")`, persisting the latest
  outputs and artifacts after each superstep while node-level events stream live
  to the UI in parallel.

## Extending the graph

Adding an agent is local: define its `*_Output` schema, write the agent class
(system prompt + prompt builder + artifact renderer), register it, and wire one
or two edges in `graph/builder.py`. No other layer needs to change.
