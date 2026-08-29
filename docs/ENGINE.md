# StormClass engine

The classroom is a single-threaded state machine. The HTTP layer serializes all `apply` calls with a mutex. Time is injected (`clock_`) so tests do not sleep.

## Invariants

1. At most one unlocked quiz per room (`quiz_already_open`).
2. A student answers an open quiz at most once. After lock or timeout, answers return `quiz_not_open` / `quiz_locked`.
3. Roll-call samples without replacement among *present* students until the pool is empty, then reshuffles. The chosen `student_id` is stored on the event so replay does not consult RNG.
4. Team assignment: next student joins the smaller of red/blue. Sizes differ by at most 1.
5. `Classroom::replay(prototype, events) .fingerprint() == live.fingerprint()`.
6. Mastery stays in `[0,1]`. For knowledge point `k`:
   - `n = 0` → displayed as unknown (prior 0.5, not a score)
   - first scored item tagged with `k`: `m := 1` or `0`
   - later: `m := (1-α)m + α·correct` with `α = 0.35`
   - `n` increments only on scored items that list `k` in `kc_ids`
   - unmarked short answers do not move mastery
7. Danmaku mute drops student fan-out. Messages are still stored and still feed the word cloud (`danmaku_in_cloud_when_muted_ = true`).

## Scoring

| kind | correct when |
|---|---|
| single | `option_id` equals the unique key |
| multi | set equality of `option_ids` |
| truefalse | boolean equals `correct[0]` |
| fill | normalized string alias or numeric `\|x-y\| ≤ tolerance` |
| short | unscored until `mark_short` |

XP on a correct scored answer: `xp * (0.8 + 0.2 * remaining_fraction_of_timer)`.

## Word cloud

ASCII tokens (stopword-filtered) + greedy longest match against a CJK lecture lexicon + leftover CJK bigrams. See `tokenize_cloud`.

## Bots

`suggest_bot_action` is a pure policy. The server director thread asks it ~3 times per 160ms per room when `bots_enabled`. Skill in `[0,1]` is P(correct). Phrases depend on the current slide `visual`.
