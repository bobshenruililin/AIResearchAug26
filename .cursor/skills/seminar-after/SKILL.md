---
name: seminar-after
description: >-
  Three-minute walk-back after a seminar. Trigger on /seminar-after.
  Appends ## After to the same seminars/*.md pocket. Never Notion.
---

# /seminar-after

Append to **the same** `seminars/YYYY-MM-DD-speaker-slug.md` file `/seminar` wrote. Do not create a second file. Do not open Notion.

## Need from the user (3 minutes)

- Did they sit the talk? If no, do not invent an after-log.
- `asked`: `Q1` (the pocket’s first Ask, or a close paraphrase) or `none`
- keep | kill | change the decision
- One sentence of what was actually said if they asked

## Write

1. Set frontmatter `asked` to `Q1` or `none`.
2. Append:

```markdown
## After

- asked: Q1 | none
- keep | kill | change: ...
- note: (one sentence, or "did not ask")
```

## Routing after the talk

- If after-log says **INDEPENDENT**: tell them `/seminar-deep` is a Friday job **before** any analysis run. Do not run deep now.
- If they want **COLLAB** and deep was not done before the talk: `/seminar-deep` before sending any email.
- SKIP stays SKIP: `asked: none`, no email, no results file.

A writeup is not an after artifact. The artifact is this log line.
