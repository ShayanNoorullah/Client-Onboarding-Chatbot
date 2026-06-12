# Self-Learning Onboarding Agent

The ATI onboarding agent improves from user feedback while keeping RAG retrieval and shadow prompt validation.

## Feedback signals

| Signal | Where | Effect |
|--------|-------|--------|
| Thumbs up/down | Chat assistant messages | `LearningExample` + accuracy tracking |
| Brief Great/OK/Poor | After brief completes | Brief feedback + pattern gating |
| Corrections (free text) | Thumbs-down / Poor brief | `UserMemory` `[correction]` facts |

## Architecture

```
User feedback → AgentFeedbackEvent → LearningExample
                      ↓
         Negative → shadow PromptVersion
                      ↓
              Validation gate (failures fixed, zero regressions)
                      ↓
              Promote to active prompt (auto)
```

RAG (`ati_kb`, `ati_kb_learned`, client, memory) is **unchanged** and still injected via `{rag_context}`. Learned patterns are quality-gated before append to `learned_patterns.txt`.

## Shadow validation policy

- New prompts start as `shadow`
- Replay up to 20 failure + 20 success examples
- Promote when: `failures_fixed > 0`, `regressions == 0`, `confidence >= 0.85`
- Max promotion rate capped by scheduler (every 5 minutes)

## Admin

- **Configuration → Learning** — accuracy by task, feedback feed, validation runs
- `GET /api/admin/learning/report` — JSON trajectory API

## Privacy

- Global patterns remain anonymized (no client names in `learned_patterns.txt`)
- Users can opt out via future `UserMemory.learning_opt_out` (planned)

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for full system architecture.
