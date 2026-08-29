# StormClass · 暴雨课堂

A local classroom that is heavier than 雨课堂. One C++ binary. Open it in a browser.

```
cmake -B build -DSTORMSAN=ON
cmake --build build -j
./build/stormclass_tests
./build/stormclass --port 8080
```

Then open:

- [http://127.0.0.1:8080](http://127.0.0.1:8080) landing
- [http://127.0.0.1:8080/demo](http://127.0.0.1:8080/demo) **split inspector** (teacher | student phone)
- `/t/FENZHI` teacher console
- `/s/FENZHI` student phone
- `/p/FENZHI` projection
- `/report/FENZHI` classroom report

Room code for the seeded lecture: **FENZHI**. 32 simulated students join on boot and start talking. Keyboard on the teacher console: `←` `→` slides, `Space` push the item on this page, `R` roll call, `D` mute danmaku, `P` team PK.

## What is stronger than 雨课堂 here

Parity: join code, slide push, 限时习题 (single / multi / true-false / fill / short), live histogram, 弹幕 + 词云, 随机点名, 不懂, 签到, 投稿, 课堂报告.

Stronger:

- Event-sourced kernel: `replay(log) == live state` is a property test
- Per-knowledge-point mastery with n-count (unknown ≠ zero)
- Pace via per-student cursor
- Team PK with fair split
- Confusion heatmap on slide ticks
- Keyboard teacher remote + clean 投屏
- CJK word cloud (lexicon + bigrams, not character soup)
- Named bot personas, not `Student_17`
- Runs offline. No WeChat. No API keys.

Lecture deck: **算法导论 · 分治** (12 slides, 8 items, 6 knowledge points). Kernel: [`docs/ENGINE.md`](docs/ENGINE.md). Wire protocol: [`docs/PROTOCOL.md`](docs/PROTOCOL.md).

## Attack the protocol

With the server running:

```
./build/stormclass_attack 127.0.0.1 8080
```

Bad JSON, stolen teacher actions, double-answers, 80-message danmaku burst.

## Layout

- `src/engine/` classroom kernel
- `src/server/` HTTP + SSE + SQLite event log
- `web/` vanilla HTML/CSS/JS (no bundler)
- `tests/` engine invariants + attack client
- `third_party/` cpp-httplib (MIT), nlohmann/json (MIT)

`STORMSAN=ON` builds with ASan+UBSan.
