# Phase 13 Done - Prompt Builder

## What Was Built

`services/agent_gateway/src/prompt_builder.py` — a deterministic prompt assembler that converts tenant context, session state, RAG retrieval results, and the current user transcript into a structured list of LLM chat messages.

### Public API

```python
from services.agent_gateway.src.prompt_builder import build_messages

messages: list[dict[str, str]] = build_messages(
    context=agent_context,      # AgentContext — tenant identity, rules, personality
    state=session_state,        # SessionState — stage, caller details, history
    rag_matches=matches,        # list[RagMatch] — retrieved document snippets
    user_transcript="Hi there", # current user utterance
)
```

### Message Structure (always in this order)

| # | Role | Content |
|---|---|---|
| 1 | `system` | Business identity + personality + behavioral rules + instructions on how to use the RAG context block |
| 2 | `user` | RAG context block (clearly delimited; omitted when no matches) |
| 3…N | `user` / `assistant` | Conversation history from `SessionState.history` (chronological) |
| last | `user` | Current user transcript |

### Design Decisions

- **Single system message**: all rules, personality, and RAG-usage instructions live in one canonical system message for debuggability and consistent precedence.
- **RAG as a separate user message**: snippets are reference material, not policy. Delivered as a clearly delimited block so the model cannot conflate them with authoritative rules.
- **History includes both user and assistant turns**: required for coherence, coreference, and consistency across multi-turn conversations.
- **Deterministic**: same inputs always produce byte-identical output.

### Per-Tenant Token Budget (new `prompt:` config section)

Each tenant YAML now requires a `prompt:` section:

```yaml
prompt:
  token_budget: 4096      # max total tokens for the full message list
  max_history_turns: 10   # max user+assistant turn pairs to retain
  max_rag_snippets: 5     # max RAG matches to inject (≤ rag.top_k)
```

Budget enforcement (character-based estimate, chars / 4 ≈ tokens):
1. Cap RAG snippets at `max_rag_snippets`.
2. Cap history at `max_history_turns * 2` messages.
3. Drop oldest history pairs first until within `token_budget`.
4. If still over budget, trim RAG snippets from the end.
5. The system message and final user turn are **never** dropped.

### Config Changes

- `config_loader.py` — added `PromptConfig` dataclass; `prompt:` section is now required and validated (`token_budget >= 256`, `max_history_turns >= 1`, `max_rag_snippets >= 1`).
- `context_builder.py` — `AgentContext` now carries `prompt_config: PromptConfig`.
- All three tenant YAMLs (`silver_pine`, `smith_law`, `bright_path_dental`) updated with `prompt:` blocks.

## Tests

### Unit / Golden tests — `tests/test_prompt_builder.py`

| Test class | What it verifies |
|---|---|
| `MessageOrderTests` | system is first; final user is last; RAG before history; history is chronological; no RAG block when empty |
| `SystemMessageContentTests` | business name, industry, personality fields, all rules, RAG-usage instructions, and greeting are present |
| `RagBlockTests` | header/footer delimiters; snippet text present; role is `user`; multiple snippets all included |
| `MaxRagSnippetsTests` | snippets capped at `max_rag_snippets`; extras silently ignored |
| `MaxHistoryTurnsTests` | history capped at `max_history_turns` pairs; within-cap history fully included |
| `TokenBudgetTests` | oldest history dropped first; RAG trimmed after history exhausted; system + final user never dropped |
| `DeterminismTests` | same input → byte-identical JSON; transcript is stripped |

### E2E tests — `tests/test_e2e.py` (`PromptBuilderE2ETests`)

| Test method | What it verifies |
|---|---|
| `test_build_messages_returns_list_of_dicts` | output is a list of `{role, content}` dicts |
| `test_first_message_is_system` | system message is always first |
| `test_last_message_matches_transcript` | final user turn matches the input transcript |
| `test_build_messages_with_live_rag` | RAG block present when embedding service returns matches (skips if service down) |
| `test_determinism_with_all_tenants` | deterministic output for every loaded tenant |
| `test_each_tenant_has_distinct_system_message` | each tenant produces a unique system message |

### Running Tests

```bash
cd services/agent_gateway
make test   # brings up docker-compose, runs all 50 tests
```
