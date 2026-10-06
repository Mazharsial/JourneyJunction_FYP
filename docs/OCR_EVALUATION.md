# OCR & Document Verification Evaluation — VoynixAI

Two layers are measured independently and honestly.

## 1. Document verification (validation layer) — gated in CI
Given extracted fields, does the rule engine flag the right issues (missing/expired/format/
future-DOB/mismatch)?

- **Harness:** `app/services/documents/evaluation.py` (12 labelled field sets, deterministic).
- **Result:** **12/12 = 100.0%** accuracy (exact match of detected finding codes to expected).
- Asserted in CI (`tests/test_documents.py::test_validation_accuracy_meets_target`, ≥90%).

Re-run: `cd backend && python -m app.services.documents.evaluation`

## 2. OCR field extraction (Gemini Vision) — live benchmark
How accurately are fields read from document images?

- **Harness:** `app/services/documents/ocr_benchmark.py` — generates 4 synthetic passport images
  with known ground-truth fields, runs them through the real extractor, compares per field
  (names token-set, numbers exact, dates normalised, country code prefix).
- **Result (measured, Gemini 2.5 Flash Vision):**

  | Field | Accuracy |
  |---|---|
  | full_name | 4/4 = 100% |
  | document_number | 4/4 = 100% |
  | nationality | 4/4 = 100% |
  | date_of_birth | 4/4 = 100% |
  | expiry_date | 4/4 = 100% |
  | issuing_country | 4/4 = 100% |
  | **Overall** | **24/24 = 100.0%** |

Re-run (needs `GEMINI_API_KEY`): `cd backend && python -m app.services.documents.ocr_benchmark`

## Engine choice
**Gemini Vision** was chosen over Tesseract/EasyOCR/PaddleOCR because: it needs no local binaries
(Tesseract isn't installed in this environment), it's free on the Gemini tier, it extracts
**structured fields** directly (not just raw text), and it handles both images and PDFs. A
deterministic **mock** extractor is the keyless fallback (used in CI and when no key is set).

## Honest limitations
- The OCR benchmark uses **clean, synthetic, high-contrast images**. Real scanned/photographed
  passports (glare, skew, low resolution, handwriting) will score lower — 100% here is an
  upper bound, not a guarantee on real-world documents. A real-document test set should be added
  before any production claim.
- Field extraction depends on Gemini; the validation layer is the deterministic, always-on safety
  net that catches missing/expired/malformed fields regardless of OCR source.
- The pipeline extracts a fixed field set (passport-oriented); more document types/fields can be
  added to the prompt and validation rules.
