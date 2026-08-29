# StormClass protocol

Transport: JSON over HTTP. Live updates: Server-Sent Events (inspectable with `curl -N`).

## REST

| method | path | body / query |
|---|---|---|
| GET | `/api/health` | |
| POST | `/api/rooms` | `{title_zh, title_en}` → `{code}` |
| POST | `/api/demo/start` | seeds `FENZHI` |
| GET | `/api/rooms/:code` | `?viewer=&locale=` snapshot |
| GET | `/api/rooms/:code/report` | 课堂报告 |
| GET | `/api/rooms/:code/events?after=` | event log |
| POST | `/api/rooms/:code/action` | action JSON; header `X-Storm-Actor` |
| GET | `/api/rooms/:code/stream` | SSE `event: state` |

Pages: `/` `/demo` `/t/:code` `/s/:code` `/p/:code` `/report/:code`. Static files under `/static/`.

## Actions

Every action is `{ "type": "...", "actor_id": "...", ... }`.

Teacher: `slide_next` `slide_prev` `goto_slide{index}` `push_quiz{quiz_id?, time_limit_sec?}` `lock_quiz` `reveal_quiz` `clear_quiz` `rollcall` `pk_start` `pk_end` `danmaku_mute{on}` `bots{on}` `broadcast_post{id}` `mark_short{student_id, quiz_id, correct}`.

Anyone: `join{role, name, client_id, bot?, skill?, checkin?}` `leave` `checkin` `cursor{slide_index}` `answer{answer}` `danmaku{text}` `confused` `submit_post{text}`.

`answer.answer` is `{option_id}` / `{option_ids}` / `{value:bool}` / `{text}`.

## Snapshot (abridged)

`seq, code, title_*, slides[], kcs[], students[], quiz, danmaku, wordcloud, rollcall, pk, posts, leaderboard, mastery_class, reteach, you, bots_enabled, present, checked_in`.

SSE payload: `{events, room}` where `room` is a full snapshot. First frame is snapshot-only; later frames include events since `after`.
