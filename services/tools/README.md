# Tools Service

## Purpose

`tools` contains external action integrations used by the agent runtime.

## Responsibilities

- Provide calendar scheduling actions (callback booking).
- Provide email actions (confirmation delivery with calendar details).
- Validate and normalize tool inputs/outputs for agent use.
- Isolate third-party integration code from gateway orchestration logic.

## Image Build/Push

From repository root:

```bash
make build SERVICE=tools
make push SERVICE=tools
```
