# AI Chatbot Evaluation — Journey Junction

Measured, reproducible accuracy for the travel assistant. Results are **computed by a
harness**, not claimed. Re-run anytime:

```bash
cd backend && python -m app.services.ai.evaluation      # prints the report
cd backend && pytest tests/test_chat.py                 # asserts the >=90% gates
```

## What the assistant does
1. **Intent detection** (deterministic, rule-based) classifies each message into:
   `visa`, `flight`, `hotel`, `plan`, `destination`, `greeting`, `out_of_scope`.
2. **Grounding**: for visa questions it extracts the origin/destination and looks up the
   **verified `visa_rules`** in the database, injecting those facts into the prompt.
3. **Answer**: Google **Gemini 2.5 Flash** answers using only the verified facts (anti-hallucination
   system instruction + visa disclaimer). With no API key, a **grounded fallback** composes the
   answer directly from the DB facts, so the feature works offline.

## Methodology
- **Dataset:** `app/services/ai/evaluation.py` — 28 labelled, representative queries spanning all
  intents (greetings, 8 visa, flights, hotels, planning, destination info, out-of-scope).
- **Intent metric:** predicted intent == expected intent, over all 28 items.
- **Grounding metric:** for the 7 visa queries with a known route, the retrieved facts must contain
  the correct requirement (e.g. "visa required", "visa on arrival", "visa free").

## Results (measured)
| Metric | Score |
|---|---|
| Intent classification accuracy | **28/28 = 100.0%** |
| Visa grounding accuracy | **7/7 = 100.0%** |

Both exceed the **≥ 90%** target. These gates are asserted in CI (`test_chat.py`), so a regression
that drops accuracy below 90% fails the build.

## Honest limitations
- The intent classifier is rule-based and tuned to common phrasings; unusual wording can be
  misclassified (e.g. a sentence containing "about" could read as a destination query). The dataset
  measures a representative set — it is not a claim of 100% on all possible inputs. In practice the
  LLM layer still responds sensibly and steers off-topic requests back to travel (verified live).
- Open-ended answer *quality* depends on Gemini and is reviewed qualitatively, not scored here. The
  grounding metric is what protects against fabricated visa facts.
- Visa data is DEMO/informational (seeded) and always shown with a disclaimer.

## Live verification
With a real key, a visa query returned (status `ok`, from Gemini): *"Yes, as a Pakistani citizen, you
need a visa to travel to Dubai (UAE)… up to 30 days…"* with the disclaimer — grounded in the seeded
PK→AE rule, not hallucinated.
