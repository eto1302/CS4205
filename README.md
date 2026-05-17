# CS4205 Assignment 2 — Circles in a Square

Group project for TU Delft CS4205 Evolutionary Algorithms (Q4 2025-26).
Topic: **Single-Objective Real-Valued Optimization** — improving a baseline
EA for the *Packing n Circles in a Square* (CiaS) problem. Fitness:
maximize the minimum pairwise distance between point coordinates in the
unit square.

Baseline options:
- **AMaLGaM-Full** (C) — provided and supported by the course
- **Evolution Strategy** (Python, `evopy`) — provided by the TA, at our own discretion

**Constraint:** the improvement we propose must *not* be one already tried in
Bosman & Gallagher (2018), the published case study on AMaLGaM/CMA-ES for
CiaS — see `docs/BosmanGallager Paper.pdf`.

## Team
- Cala
- Leo 
- Martin
- Agatha
- Ivan

**Topic supervisor (per brief):** Peter Bosman
**Day-to-day TA / contact:** Arthur Guijt

## Key dates
| Date              | Milestone                              |
|-------------------|----------------------------------------|
| 2026-05-10        | Group signup deadline (done)           |
| 2026-05-13 14:00  | First supervisor meeting (Arthur)      |
| 2026-06-07 23:59  | Final deliverables due (code + slides) |
| 2026-06-10 / 11   | 9-min presentation + defense           |

## Meetings
- **Weekly:** Wednesdays 13:30
- Notes in [`meetings/`](./meetings/), filename `YYYY-MM-DD-meeting-NN.md`

## Deliverables (per assignment brief)
1. Source code + experimental results (zip)
2. Presentation slides (PDF/PPTX, no animations, no post-deadline edits)
3. 9-min presentation + defense (graded via rubric)

**Grading:** Content 60% · Presentation 20% · Defense 20%

## Documents
- [Assignment brief](./docs/assignment-brief.pdf) — CiaS section is pp. 10–11
- [Presentation rubric](./docs/presentation-rubric.pdf)
- [Bosman & Gallagher 2018 — case study on AMaLGaM/CMA-ES for CiaS](./docs/BosmanGallager%20Paper.pdf) — central paper; defines the off-limits improvements
- [Bosman 2009 — AMaLGaM / EDA paper](./docs/bosman-2009-amalgam-eda.pdf) — original AMaLGaM algorithm

## Algorithm baselines
- [`Algorithms/AMaLGaM-Full/`](./Algorithms/AMaLGaM-Full/) — C, Bosman's EDA with full covariance matrix
- [`Algorithms/EvolutionStrategyPython/`](./Algorithms/EvolutionStrategyPython/) — Python `evopy` (μ, λ)-ES with self-adaptive σ


