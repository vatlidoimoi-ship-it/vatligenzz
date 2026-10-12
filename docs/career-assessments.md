# PHYEDU Care: questionnaire provenance and behavior

Reviewed 2026-10-13. Assets are derived from the five images supplied in `anhnen/`.
Question definitions, labels, sources and scoring dimensions are stored in the Supabase
`app_json_store` row `data/career_assessments.json` (or the configured table name).
The authenticated Flask page reads that catalog through the configured storage backend
and safely embeds it with Jinja `tojson`. `data/career_assessments.json` is the local seed.
Publish updates with `python scripts/publish_career_assessments.py --env-file ../.env`.
The browser no longer bundles the question bank in JavaScript.

The gallery and all scores run locally in the browser. Student responses are not persisted to localStorage,
cookies, or the backend. Closing the assessment clears answers. Sharing places a score-only
summary in the existing chat composer; the user must press Send to transmit it to Gemini.

## Available self-reflection activities

- **Holland / RIASEC:** 30 original PHYEDU activity preferences, five per domain.
  Not the O*NET Interest Profiler and not a validated Holland instrument. Model reference:
  https://www.onetcenter.org/IP.html . Mean 1–5 per domain, displayed as `(mean - 1) * 25`.
  Ties are not arbitrarily converted into a three-letter code. Career examples are exploratory.
- **Big Five:** translation of all 50 items of the IPIP Big-Five Factor Markers (ten per domain).
  Source and positive/negative keys: https://ipip.ori.org/newBigFive5broadKey.htm .
  IPIP public-domain terms: https://ipip.ori.org/newPermission.htm .
  Translation prepared for this project; not psychometrically validated in Vietnamese.
  Negative-keyed items use `6 - response`; each mean is rescaled to 0–100.
  Emotional Stability is scored in the stability direction, not Neuroticism.
  Factor V is Intellect/Imagination, not an IQ measure. Scores are not population percentiles.
- **Four preferences (MBTI-related):** 16 original reflection statements, four per pair,
  two positively and two negatively keyed. No proprietary MBTI items are reproduced.
  No four-letter type is generated. Does not claim to be the official MBTI assessment.
  https://www.myersbriggs.org/my-mbti-personality-type/myers-briggs-overview/ .
- **WHO-5:** project translation of five WHO 2024 English items; two-week timeframe,
  response values 0–5, raw sum 0–25, displayed score `raw * 4`. Below 50 prompts a supportive
  suggestion for professional assessment, not a diagnosis. No safety inference from a high score.
  Source: https://www.who.int/publications/m/item/WHO-UCN-MSD-MHE-2024.01 .
  WHO/UCN/MSD/MHE/2024.1, © World Health Organization 2024.
  World Health Organization. The World Health Organization-Five Well-Being Index (WHO-5).
  Geneva: World Health Organization; 2024. License: CC-BY-NC-SA 3.0 IGO.
  The translated WHO-5 content is distributed under the same
  https://creativecommons.org/licenses/by-nc-sa/3.0/igo/ license, for non-commercial use.
  Commercial use requires appropriate permission or removal of this instrument.
  This translation was not created by the World Health Organization (WHO). WHO is not
  responsible for the content or accuracy of this translation. The original English edition
  shall be the binding and authentic edition.
  WHO does not endorse PHYEDU; no WHO logo is used. No claim of Vietnamese validation.

## DASS-21: information card only

The author's FAQ explicitly disallows administration on public websites/apps, and direct
automated feedback to respondents. A login for general students is not a clinician-led
restricted cohort. Consequently this package contains information and help-seeking guidance,
not the 21 items or a self-scoring flow. No fake substitute is presented as DASS-21.
Source: https://www2.psy.unsw.edu.au/dass/DASSFAQ.htm , questions 9 and 21.
Professional deployment would require a separate clinician/researcher workflow conforming
to these conditions, rather than a switch enabling public self-scoring.

## Verification

Run `node --test tests/career-assessments.test.mjs` for scoring extremes, reverse keys,
ties, invalid/incomplete answers, and WHO-5 threshold boundaries. Browser checks should
cover all packages, next/back, cancellation, filters, mobile layout, keyboard focus,
reviewing answers, and the explicit handoff to the existing chat.
