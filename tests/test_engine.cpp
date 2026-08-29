#include "engine/classroom.hpp"
#include "engine/scoring.hpp"
#include "engine/wordcloud.hpp"

#include <cmath>
#include <cstdio>
#include <iostream>
#include <set>
#include <string>

using namespace storm;

static int g_fail = 0;
static int g_pass = 0;

#define CHECK(cond)                                                                 \
  do {                                                                              \
    if (!(cond)) {                                                                  \
      std::cerr << "FAIL " << __FILE__ << ":" << __LINE__ << "  " << #cond << "\n"; \
      g_fail++;                                                                     \
    } else {                                                                        \
      g_pass++;                                                                      \
    }                                                                               \
  } while (0)

static Classroom tiny(uint32_t seed = 1) {
  int64_t t = 1'000'000;
  Classroom c = Classroom::blank("TEST01", "测", "Test", seed);
  c.apply({{"type", "join"},
           {"role", "teacher"},
           {"name", "T"},
           {"client_id", "teacher-1"}},
          t);
  for (int i = 0; i < 6; ++i) {
    char id[16];
    std::snprintf(id, sizeof(id), "s%d", i);
    c.apply({{"type", "join"},
             {"role", "student"},
             {"name", std::string("S") + std::to_string(i)},
             {"client_id", id},
             {"checkin", true}},
            t + i + 1);
  }
  return c;
}

int main() {
  {
    Quiz q;
    q.kind = QuizKind::Single;
    q.correct = {"b"};
    auto r = score_answer(q, json{{"option_id", "b"}});
    CHECK(r.scored && r.correct);
    r = score_answer(q, json{{"option_id", "a"}});
    CHECK(r.scored && !r.correct);
  }
  {
    Quiz q;
    q.kind = QuizKind::Multi;
    q.correct = {"a", "c"};
    auto r = score_answer(q, json{{"option_ids", json::array({"c", "a"})}});
    CHECK(r.correct);
    r = score_answer(q, json{{"option_ids", json::array({"a"})}});
    CHECK(!r.correct);
  }
  {
    Quiz q;
    q.kind = QuizKind::TrueFalse;
    q.correct = {"false"};
    auto r = score_answer(q, json{{"value", false}});
    CHECK(r.correct);
    r = score_answer(q, json{{"value", true}});
    CHECK(!r.correct);
  }
  {
    Quiz q;
    q.kind = QuizKind::Fill;
    q.correct = {"lg n", "log n"};
    auto r = score_answer(q, json{{"text", "lg n"}});
    CHECK(r.correct);
    r = score_answer(q, json{{"text", "LOG-N"}});
    CHECK(r.correct);
    q.numeric_tolerance = 0.01;
    q.correct = {"3.14"};
    r = score_answer(q, json{{"text", "3.141"}});
    CHECK(r.correct);
  }
  {
    Quiz q;
    q.kind = QuizKind::Short;
    auto r = score_answer(q, json{{"text", "重叠就 DP"}});
    CHECK(!r.scored);
  }

  {
    auto cloud = tokenize_cloud({"合并步不是免费的 分治 分治 主定理", "divide and merge 分治"});
    CHECK(!cloud.empty());
    bool hit = false;
    for (const auto& [w, c] : cloud) {
      if (w == "分治") {
        hit = true;
        CHECK(c >= 2);
      }
    }
    CHECK(hit);
  }

  // Invariant 1: at most one unlocked quiz
  {
    auto c = tiny();
    auto a = c.apply({{"type", "push_quiz"},
                      {"actor_id", "teacher-1"},
                      {"quiz_id", "q1"},
                      {"time_limit_sec", 30}},
                     2'000'000);
    CHECK(a.ok);
    CHECK(c.quiz_state() == QuizState::Open);
    auto b = c.apply({{"type", "push_quiz"},
                      {"actor_id", "teacher-1"},
                      {"quiz_id", "q2"}},
                     2'000'100);
    CHECK(!b.ok);
    CHECK(b.error == "quiz_already_open");
  }

  // Invariant 2: answer at most once; reject after lock
  {
    auto c = tiny();
    c.apply({{"type", "push_quiz"},
             {"actor_id", "teacher-1"},
             {"quiz_id", "q1"},
             {"time_limit_sec", 30}},
            3'000'000);
    auto a1 = c.apply({{"type", "answer"},
                       {"actor_id", "s0"},
                       {"answer", {{"option_id", "b"}}}},
                      3'000'100);
    CHECK(a1.ok && a1.reply["correct"].get<bool>());
    auto a2 = c.apply({{"type", "answer"},
                       {"actor_id", "s0"},
                       {"answer", {{"option_id", "a"}}}},
                      3'000'200);
    CHECK(!a2.ok);
    CHECK(a2.error == "already_answered");
    c.apply({{"type", "lock_quiz"}, {"actor_id", "teacher-1"}}, 3'000'300);
    auto a3 = c.apply({{"type", "answer"},
                       {"actor_id", "s1"},
                       {"answer", {{"option_id", "b"}}}},
                      3'000'400);
    CHECK(!a3.ok);
    CHECK(a3.error == "quiz_not_open");
  }

  // Invariant 3: roll-call without replacement until exhausted
  {
    auto c = tiny();
    std::set<std::string> seen;
    for (int i = 0; i < 6; ++i) {
      auto r = c.apply({{"type", "rollcall"}, {"actor_id", "teacher-1"}}, 4'000'000 + i);
      CHECK(r.ok);
      std::string id = r.reply["student_id"].get<std::string>();
      CHECK(seen.insert(id).second);
    }
    CHECK(seen.size() == 6);
    auto r = c.apply({{"type", "rollcall"}, {"actor_id", "teacher-1"}}, 4'000'010);
    CHECK(r.ok);
    CHECK(seen.count(r.reply["student_id"].get<std::string>()));
  }

  // Invariant 4: team sizes differ by <= 1
  {
    auto c = tiny();
    int red = 0, blue = 0;
    for (const auto& s : c.students()) {
      if (s.team == "red") red++;
      else blue++;
    }
    CHECK(std::abs(red - blue) <= 1);
  }

  // Invariant 5: replay(log) == live fingerprint
  {
    auto c = tiny(42);
    c.apply({{"type", "pk_start"}, {"actor_id", "teacher-1"}}, 5'000'000);
    c.apply({{"type", "goto_slide"}, {"actor_id", "teacher-1"}, {"index", 1}}, 5'000'001);
    c.apply({{"type", "push_quiz"},
             {"actor_id", "teacher-1"},
             {"quiz_id", "q1"},
             {"time_limit_sec", 40}},
            5'000'002);
    c.apply({{"type", "answer"},
             {"actor_id", "s0"},
             {"answer", {{"option_id", "b"}}}},
            5'000'003);
    c.apply({{"type", "answer"},
             {"actor_id", "s1"},
             {"answer", {{"option_id", "a"}}}},
            5'000'004);
    c.apply({{"type", "danmaku"}, {"actor_id", "s2"}, {"text", "分治三拍合并步"}}, 5'000'005);
    c.apply({{"type", "confused"}, {"actor_id", "s3"}}, 5'000'006);
    c.apply({{"type", "lock_quiz"}, {"actor_id", "teacher-1"}}, 5'000'007);
    c.apply({{"type", "reveal_quiz"}, {"actor_id", "teacher-1"}}, 5'000'008);
    c.apply({{"type", "rollcall"}, {"actor_id", "teacher-1"}}, 5'000'009);
    auto live = c.fingerprint();
    Classroom proto("TEST01", load_divide_and_conquer_deck(), 42);
    auto folded = Classroom::replay(proto, c.events());
    CHECK(folded.fingerprint() == live);
    auto mid = Classroom::replay(proto, c.events(), 4);
    CHECK(mid.seq() == 4);
  }

  // Invariant 6: mastery in [0,1], n increments only on tagged scored items
  {
    auto c = tiny();
    c.apply({{"type", "push_quiz"},
             {"actor_id", "teacher-1"},
             {"quiz_id", "q1"},
             {"time_limit_sec", 30}},
            6'000'000);
    c.apply({{"type", "answer"},
             {"actor_id", "s0"},
             {"answer", {{"option_id", "b"}}}},
            6'000'001);
    const Student* s = c.find_student("s0");
    CHECK(s);
    for (const auto& [k, m] : s->mastery) {
      CHECK(m >= 0.0 && m <= 1.0);
    }
    CHECK(s->mastery_n.at("dac-structure") == 1);
    CHECK(s->mastery.at("dac-structure") == 1.0);
    CHECK(s->mastery_n.at("master-theorem") == 0);
  }

  // Invariant 7: mute still stores danmaku for word cloud by default
  {
    auto c = tiny();
    c.apply({{"type", "danmaku_mute"}, {"actor_id", "teacher-1"}, {"on", true}}, 7'000'000);
    c.apply({{"type", "danmaku"}, {"actor_id", "s0"}, {"text", "分治 主定理 合并"}}, 7'000'001);
    auto snap_s = c.snapshot("s0", "zh");
    CHECK(snap_s["danmaku"].empty());
    auto snap_t = c.snapshot("teacher-1", "zh");
    CHECK(!snap_t["danmaku"].empty());
    CHECK(!snap_t["wordcloud"].empty());
  }

  // Demo room sanity + bot action
  {
    auto c = Classroom::demo(7);
    CHECK(c.students().size() == 32);
    CHECK(c.code() == "FENZHI");
    std::mt19937 rng(1);
    int produced = 0;
    for (int i = 0; i < 64; ++i) {
      auto act = c.suggest_bot_action("bot-00", rng, 8'000'000 + i * 10);
      if (!act.is_null() && !act.empty()) produced++;
    }
    CHECK(produced > 0);
    auto snap = c.snapshot("teacher-1", "zh");
    CHECK(snap["slides"].size() == 12);
    CHECK(c.report()["attendance"]["total"].get<int>() == 32);
  }

  // Unauthorized teacher action
  {
    auto c = tiny();
    auto r = c.apply({{"type", "push_quiz"}, {"actor_id", "s0"}, {"quiz_id", "q1"}}, 9'000'000);
    CHECK(!r.ok);
    CHECK(r.error == "teacher_only");
  }

  std::cout << "passed " << g_pass << "  failed " << g_fail << "\n";
  return g_fail ? 1 : 0;
}
