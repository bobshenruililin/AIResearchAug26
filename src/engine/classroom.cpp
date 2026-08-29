#include "engine/classroom.hpp"

#include "engine/scoring.hpp"
#include "engine/wordcloud.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <sstream>

namespace storm {
namespace {

int64_t system_now() {
  return std::chrono::duration_cast<std::chrono::milliseconds>(
             std::chrono::system_clock::now().time_since_epoch())
      .count();
}

std::string trim(const std::string& s) {
  auto b = s.find_first_not_of(" \t\n\r");
  auto e = s.find_last_not_of(" \t\n\r");
  if (b == std::string::npos) return "";
  return s.substr(b, e - b + 1);
}

}  // namespace

Classroom::Classroom(std::string code, Deck deck, uint32_t rng_seed, Clock clock)
    : code_(std::move(code)),
      deck_(std::move(deck)),
      rng_seed_(rng_seed),
      clock_(std::move(clock)),
      rng_(rng_seed) {
  if (!clock_) clock_ = system_now;
}

Classroom Classroom::demo(uint32_t rng_seed) {
  Classroom c("FENZHI", load_divide_and_conquer_deck(), rng_seed);
  json join_t = {{"type", "join"},
                 {"role", "teacher"},
                 {"name", "沈老师"},
                 {"client_id", "teacher-1"}};
  c.apply(join_t);
  int i = 0;
  for (const auto& [name, skill] : demo_bot_roster()) {
    char id[32];
    std::snprintf(id, sizeof(id), "bot-%02d", i++);
    json j = {{"type", "join"},  {"role", "student"}, {"name", name},
              {"client_id", id}, {"bot", true},      {"skill", skill},
              {"checkin", true}};
    c.apply(j);
  }
  c.set_bots_enabled(true);
  return c;
}

Classroom Classroom::blank(const std::string& code, const std::string& title_zh,
                          const std::string& title_en, uint32_t rng_seed) {
  Deck d = load_divide_and_conquer_deck();
  d.title_zh = title_zh;
  d.title_en = title_en;
  return Classroom(code, std::move(d), rng_seed);
}

Student* Classroom::find_student(const std::string& id) {
  for (auto& s : students_)
    if (s.id == id) return &s;
  return nullptr;
}

const Student* Classroom::find_student(const std::string& id) const {
  for (const auto& s : students_)
    if (s.id == id) return &s;
  return nullptr;
}

const Quiz* Classroom::quiz_by_id(const std::string& id) const {
  for (const auto& q : deck_.quizzes)
    if (q.id == id) return &q;
  return nullptr;
}

Quiz* Classroom::quiz_by_id(const std::string& id) {
  for (auto& q : deck_.quizzes)
    if (q.id == id) return &q;
  return nullptr;
}

void Classroom::ensure_kc_maps(Student& s) {
  for (const auto& kc : deck_.kcs) {
    if (!s.mastery.count(kc.id)) s.mastery[kc.id] = 0.5;
    if (!s.mastery_n.count(kc.id)) s.mastery_n[kc.id] = 0;
  }
}

void Classroom::assign_team(Student& s) {
  int red = 0, blue = 0;
  for (const auto& x : students_) {
    if (x.id == s.id) continue;
    if (x.team == "red") red++;
    else if (x.team == "blue") blue++;
  }
  s.team = (red <= blue) ? "red" : "blue";
}

void Classroom::apply_mastery(Student& s, const Quiz& q, bool correct) {
  ensure_kc_maps(s);
  for (const auto& kc : q.kc_ids) {
    int& n = s.mastery_n[kc];
    double& m = s.mastery[kc];
    if (n == 0) {
      m = correct ? 1.0 : 0.0;
    } else {
      m = (1.0 - kMasteryAlpha) * m + kMasteryAlpha * (correct ? 1.0 : 0.0);
    }
    if (m < 0) m = 0;
    if (m > 1) m = 1;
    n += 1;
  }
}

void Classroom::award_xp(Student& s, int amount) {
  if (amount <= 0) return;
  s.xp += amount;
  if (pk_on_) {
    if (s.team == "red") pk_red_ += amount;
    else if (s.team == "blue") pk_blue_ += amount;
  }
}

void Classroom::emit(const std::string& type, json payload, int64_t now_ms) {
  if (!payload.contains("type")) payload["type"] = type;
  Event e;
  e.seq = ++seq_;
  e.t_ms = now_ms;
  e.type = type;
  e.payload = std::move(payload);
  events_.push_back(std::move(e));
}

void Classroom::reset_live_keep_deck() {
  seq_ = 0;
  events_.clear();
  teacher_id_.clear();
  students_.clear();
  slide_index_ = 0;
  quiz_state_ = QuizState::Idle;
  open_quiz_id_.clear();
  quiz_opens_at_ = 0;
  quiz_closes_at_ = 0;
  answers_.clear();
  danmaku_.clear();
  danmaku_seq_ = 0;
  danmaku_muted_ = false;
  posts_.clear();
  post_seq_ = 0;
  confused_.clear();
  last_confused_ms_.clear();
  last_rollcall_id_.clear();
  rollcall_pool_.clear();
  pk_on_ = false;
  pk_red_ = 0;
  pk_blue_ = 0;
  bots_enabled_ = false;
  bot_last_act_.clear();
  next_human_ = 1;
  rng_ = std::mt19937(rng_seed_);
}

ApplyResult Classroom::apply(json action, int64_t now_ms) {
  if (now_ms <= 0) now_ms = clock_();
  return apply_inner(std::move(action), now_ms, true);
}

ApplyResult Classroom::apply_inner(json action, int64_t now_ms, bool record) {
  ApplyResult r;
  if (!action.is_object() || !action.contains("type") || !action["type"].is_string()) {
    r.ok = false;
    r.error = "missing_type";
    return r;
  }
  const std::string type = action["type"].get<std::string>();
  auto actor = action.value("actor_id", action.value("client_id", std::string()));

  auto need_teacher = [&]() {
    if (actor.empty() || actor != teacher_id_) {
      r.ok = false;
      r.error = "teacher_only";
      return false;
    }
    return true;
  };

  if (type == "join") {
    std::string role = action.value("role", "student");
    std::string name = trim(action.value("name", "同学"));
    std::string cid = action.value("client_id", std::string());
    if (cid.empty()) {
      r.ok = false;
      r.error = "missing_client_id";
      return r;
    }
    if (role == "teacher" || role == "instructor") {
      if (!teacher_id_.empty() && teacher_id_ != cid) {
        r.ok = false;
        r.error = "teacher_exists";
        return r;
      }
      teacher_id_ = cid;
      if (!name.empty()) teacher_name_ = name;
      if (record) emit("join", action, now_ms);
      r.reply = {{"id", teacher_id_}, {"role", "teacher"}};
      return r;
    }
    if (auto* existing = find_student(cid)) {
      existing->present = true;
      if (!name.empty()) existing->name = name;
      if (record) emit("rejoin", action, now_ms);
      r.reply = {{"id", cid}, {"role", "student"}, {"team", existing->team}};
      return r;
    }
    Student s;
    s.id = cid;
    s.name = name.empty() ? ("同学" + std::to_string(next_human_++)) : name;
    s.bot = action.value("bot", false);
    s.skill = action.value("skill", 0.7);
    s.present = true;
    s.checked_in = action.value("checkin", false);
    s.slide_index = slide_index_;
    assign_team(s);
    ensure_kc_maps(s);
    students_.push_back(std::move(s));
    json payload = action;
    payload["team"] = students_.back().team;
    payload["name"] = students_.back().name;
    if (record) emit("join", payload, now_ms);
    r.reply = {{"id", cid}, {"role", "student"}, {"team", students_.back().team}};
    return r;
  }

  if (type == "leave") {
    if (auto* s = find_student(actor)) s->present = false;
    if (record) emit("leave", action, now_ms);
    return r;
  }

  if (type == "checkin") {
    if (auto* s = find_student(actor)) s->checked_in = true;
    else {
      r.ok = false;
      r.error = "unknown_student";
      return r;
    }
    if (record) emit("checkin", action, now_ms);
    return r;
  }

  if (type == "cursor") {
    if (auto* s = find_student(actor)) {
      int idx = action.value("slide_index", slide_index_);
      if (idx < 0) idx = 0;
      if (idx >= static_cast<int>(deck_.slides.size()))
        idx = static_cast<int>(deck_.slides.size()) - 1;
      s->slide_index = idx;
      if (record) emit("cursor", {{"actor_id", actor}, {"slide_index", idx}}, now_ms);
    }
    return r;
  }

  if (type == "slide_next" || type == "slide_prev" || type == "goto_slide") {
    if (!need_teacher()) return r;
    int idx = slide_index_;
    if (type == "slide_next") idx += 1;
    else if (type == "slide_prev") idx -= 1;
    else idx = action.value("index", 0);
    if (idx < 0) idx = 0;
    if (idx >= static_cast<int>(deck_.slides.size()))
      idx = static_cast<int>(deck_.slides.size()) - 1;
    slide_index_ = idx;
    if (record) emit(type, {{"actor_id", actor}, {"index", idx}}, now_ms);
    r.reply = {{"index", idx}};
    return r;
  }

  if (type == "push_quiz") {
    if (!need_teacher()) return r;
    if (quiz_state_ == QuizState::Open) {
      r.ok = false;
      r.error = "quiz_already_open";
      return r;
    }
    std::string qid = action.value("quiz_id", std::string());
    if (qid.empty()) {
      const auto& sl = deck_.slides[static_cast<size_t>(slide_index_)];
      if (sl.quiz_id) qid = *sl.quiz_id;
    }
    const Quiz* q = quiz_by_id(qid);
    if (!q) {
      r.ok = false;
      r.error = "unknown_quiz";
      return r;
    }
    quiz_state_ = QuizState::Open;
    open_quiz_id_ = qid;
    int limit = action.value("time_limit_sec", q->time_limit_sec);
    if (limit < 5) limit = 5;
    quiz_opens_at_ = now_ms;
    quiz_closes_at_ = now_ms + static_cast<int64_t>(limit) * 1000;
    if (record)
      emit("push_quiz",
           {{"actor_id", actor},
            {"quiz_id", qid},
            {"time_limit_sec", limit},
            {"closes_at_ms", quiz_closes_at_}},
           now_ms);
    r.reply = {{"quiz_id", qid}, {"closes_at_ms", quiz_closes_at_}};
    return r;
  }

  if (type == "lock_quiz") {
    if (!need_teacher()) return r;
    if (quiz_state_ != QuizState::Open) {
      r.ok = false;
      r.error = "no_open_quiz";
      return r;
    }
    quiz_state_ = QuizState::Locked;
    quiz_closes_at_ = now_ms;
    if (record) emit("lock_quiz", {{"actor_id", actor}, {"quiz_id", open_quiz_id_}}, now_ms);
    return r;
  }

  if (type == "reveal_quiz") {
    if (!need_teacher()) return r;
    if (quiz_state_ != QuizState::Open && quiz_state_ != QuizState::Locked) {
      r.ok = false;
      r.error = "no_quiz_to_reveal";
      return r;
    }
    if (quiz_state_ == QuizState::Open) {
      quiz_state_ = QuizState::Locked;
      quiz_closes_at_ = now_ms;
    }
    quiz_state_ = QuizState::Revealed;
    if (record) emit("reveal_quiz", {{"actor_id", actor}, {"quiz_id", open_quiz_id_}}, now_ms);
    return r;
  }

  if (type == "clear_quiz") {
    if (!need_teacher()) return r;
    quiz_state_ = QuizState::Idle;
    open_quiz_id_.clear();
    if (record) emit("clear_quiz", {{"actor_id", actor}}, now_ms);
    return r;
  }

  if (type == "answer") {
    auto* s = find_student(actor);
    if (!s) {
      r.ok = false;
      r.error = "unknown_student";
      return r;
    }
    if (quiz_state_ != QuizState::Open) {
      r.ok = false;
      r.error = "quiz_not_open";
      return r;
    }
    if (now_ms > quiz_closes_at_) {
      quiz_state_ = QuizState::Locked;
      r.ok = false;
      r.error = "quiz_locked";
      return r;
    }
    for (const auto& a : answers_) {
      if (a.student_id == actor && a.quiz_id == open_quiz_id_) {
        r.ok = false;
        r.error = "already_answered";
        return r;
      }
    }
    const Quiz* q = quiz_by_id(open_quiz_id_);
    if (!q) {
      r.ok = false;
      r.error = "unknown_quiz";
      return r;
    }
    json payload = action.contains("answer") ? action["answer"] : action;
    auto sc = score_answer(*q, payload);
    AnswerRecord rec;
    rec.student_id = actor;
    rec.quiz_id = open_quiz_id_;
    rec.payload = payload;
    rec.scored = sc.scored;
    rec.correct = sc.correct;
    rec.fraction = sc.fraction;
    rec.t_ms = now_ms;
    rec.xp_awarded = 0;
    if (sc.scored) {
      s->answers_total += 1;
      if (sc.correct) s->answers_correct += 1;
      apply_mastery(*s, *q, sc.correct);
      if (sc.correct) {
        double remain = 0;
        if (quiz_closes_at_ > quiz_opens_at_) {
          remain = std::max(0.0, static_cast<double>(quiz_closes_at_ - now_ms) /
                                       static_cast<double>(quiz_closes_at_ - quiz_opens_at_));
        }
        rec.xp_awarded = static_cast<int>(q->xp * (0.8 + 0.2 * remain));
        award_xp(*s, rec.xp_awarded);
      }
    }
    answers_.push_back(rec);
    json ev = {{"actor_id", actor},
               {"quiz_id", open_quiz_id_},
               {"answer", payload},
               {"scored", rec.scored},
               {"correct", rec.correct},
               {"xp", rec.xp_awarded},
               {"team", s->team}};
    if (record) emit("answer", ev, now_ms);
    r.reply = {{"scored", rec.scored}, {"correct", rec.correct}, {"xp", rec.xp_awarded}};
    return r;
  }

  if (type == "mark_short") {
    if (!need_teacher()) return r;
    std::string sid = action.value("student_id", "");
    std::string qid = action.value("quiz_id", open_quiz_id_);
    bool correct = action.value("correct", false);
    auto* s = find_student(sid);
    const Quiz* q = quiz_by_id(qid);
    if (!s || !q) {
      r.ok = false;
      r.error = "not_found";
      return r;
    }
    for (auto& a : answers_) {
      if (a.student_id == sid && a.quiz_id == qid) {
        if (a.scored) break;
        a.scored = true;
        a.correct = correct;
        a.fraction = correct ? 1.0 : 0.0;
        s->answers_total += 1;
        if (correct) {
          s->answers_correct += 1;
          a.xp_awarded = q->xp;
          award_xp(*s, a.xp_awarded);
        }
        apply_mastery(*s, *q, correct);
        break;
      }
    }
    if (record) emit("mark_short", action, now_ms);
    return r;
  }

  if (type == "danmaku") {
    auto* s = find_student(actor);
    if (!s && actor != teacher_id_) {
      r.ok = false;
      r.error = "unknown_student";
      return r;
    }
    std::string text = trim(action.value("text", ""));
    if (text.empty()) {
      r.ok = false;
      r.error = "empty";
      return r;
    }
    if (text.size() > 240) text = text.substr(0, 240);
    Danmaku d;
    d.id = ++danmaku_seq_;
    d.student_id = actor;
    d.name = s ? s->name : teacher_name_;
    d.text = text;
    d.t_ms = now_ms;
    danmaku_.push_back(d);
    if (static_cast<int>(danmaku_.size()) > kDanmakuRing) {
      danmaku_.erase(danmaku_.begin(), danmaku_.begin() + (danmaku_.size() - kDanmakuRing));
    }
    json ev = {{"id", d.id},
               {"actor_id", actor},
               {"name", d.name},
               {"text", text},
               {"muted", danmaku_muted_}};
    if (record) emit("danmaku", ev, now_ms);
    return r;
  }

  if (type == "danmaku_mute") {
    if (!need_teacher()) return r;
    danmaku_muted_ = action.value("on", !danmaku_muted_);
    if (record) emit("danmaku_mute", {{"on", danmaku_muted_}}, now_ms);
    r.reply = {{"on", danmaku_muted_}};
    return r;
  }

  if (type == "confused") {
    auto* s = find_student(actor);
    if (!s) {
      r.ok = false;
      r.error = "unknown_student";
      return r;
    }
    std::string sid = deck_.slides[static_cast<size_t>(slide_index_)].id;
    std::string key = actor + ":" + sid;
    int64_t last = last_confused_ms_[key];
    if (now_ms - last < 4000) {
      r.ok = false;
      r.error = "cooldown";
      return r;
    }
    last_confused_ms_[key] = now_ms;
    confused_[sid] += 1;
    s->confused_count += 1;
    if (record)
      emit("confused", {{"actor_id", actor}, {"slide_id", sid}, {"count", confused_[sid]}},
           now_ms);
    return r;
  }

  if (type == "rollcall") {
    if (!need_teacher()) return r;
    std::string picked = action.value("student_id", std::string());
    if (picked.empty()) picked = pick_rollcall(now_ms);
    last_rollcall_id_ = picked;
    if (record) emit("rollcall", {{"actor_id", actor}, {"student_id", picked}}, now_ms);
    r.reply = {{"student_id", picked}};
    return r;
  }

  if (type == "pk_start") {
    if (!need_teacher()) return r;
    pk_on_ = true;
    pk_red_ = 0;
    pk_blue_ = 0;
    if (record) emit("pk_start", {{"actor_id", actor}}, now_ms);
    return r;
  }

  if (type == "pk_end") {
    if (!need_teacher()) return r;
    pk_on_ = false;
    if (record) emit("pk_end", {{"red", pk_red_}, {"blue", pk_blue_}}, now_ms);
    return r;
  }

  if (type == "submit_post") {
    auto* s = find_student(actor);
    if (!s) {
      r.ok = false;
      r.error = "unknown_student";
      return r;
    }
    std::string text = trim(action.value("text", ""));
    if (text.empty()) {
      r.ok = false;
      r.error = "empty";
      return r;
    }
    Post p;
    p.id = ++post_seq_;
    p.student_id = actor;
    p.name = s->name;
    p.text = text;
    p.t_ms = now_ms;
    posts_.push_back(p);
    if (record)
      emit("submit_post", {{"id", p.id}, {"actor_id", actor}, {"name", p.name}, {"text", text}},
           now_ms);
    r.reply = {{"id", p.id}};
    return r;
  }

  if (type == "broadcast_post") {
    if (!need_teacher()) return r;
    int64_t id = action.value("id", 0);
    for (auto& p : posts_) {
      if (p.id == id) {
        p.broadcast = true;
        if (record) emit("broadcast_post", {{"id", id}, {"text", p.text}, {"name", p.name}}, now_ms);
        return r;
      }
    }
    r.ok = false;
    r.error = "unknown_post";
    return r;
  }

  if (type == "bots") {
    if (!need_teacher()) return r;
    bots_enabled_ = action.value("on", !bots_enabled_);
    if (record) emit("bots", {{"on", bots_enabled_}}, now_ms);
    r.reply = {{"on", bots_enabled_}};
    return r;
  }

  if (type == "tick") {
    bool ch = tick(now_ms);
    r.reply = {{"changed", ch}};
    return r;
  }

  r.ok = false;
  r.error = "unknown_action";
  return r;
}

std::string Classroom::pick_rollcall(int64_t now_ms) {
  (void)now_ms;
  std::vector<std::string> present;
  for (const auto& s : students_) {
    if (s.present) present.push_back(s.id);
  }
  if (present.empty()) return "";
  rollcall_pool_.erase(std::remove_if(rollcall_pool_.begin(), rollcall_pool_.end(),
                                      [&](const std::string& id) {
                                        return std::find(present.begin(), present.end(), id) ==
                                               present.end();
                                      }),
                       rollcall_pool_.end());
  if (rollcall_pool_.empty()) {
    rollcall_pool_ = present;
    std::shuffle(rollcall_pool_.begin(), rollcall_pool_.end(), rng_);
  }
  std::string picked = rollcall_pool_.back();
  rollcall_pool_.pop_back();
  return picked;
}

bool Classroom::tick(int64_t now_ms) {
  if (quiz_state_ != QuizState::Open || now_ms < quiz_closes_at_) return false;
  quiz_state_ = QuizState::Locked;
  quiz_closes_at_ = now_ms;
  emit("lock_quiz",
       {{"actor_id", teacher_id_}, {"quiz_id", open_quiz_id_}, {"auto", true}}, now_ms);
  return true;
}

Classroom Classroom::replay(const Classroom& prototype, const std::vector<Event>& events,
                           int64_t upto_seq) {
  Classroom c(prototype.code_, prototype.deck_, prototype.rng_seed_, prototype.clock_);
  for (const auto& e : events) {
    if (upto_seq >= 0 && e.seq > upto_seq) break;
    json action = e.payload;
    if (e.type == "tick_lock") {
      action["type"] = "lock_quiz";
      if (!action.contains("actor_id")) action["actor_id"] = c.teacher_id_;
    } else if (e.type == "rejoin") {
      action["type"] = "join";
    } else {
      action["type"] = e.type;
    }
    c.apply_inner(action, e.t_ms, true);
    if (!c.events_.empty()) {
      c.events_.back().seq = e.seq;
      c.events_.back().t_ms = e.t_ms;
      c.seq_ = e.seq;
    }
  }
  return c;
}

json Classroom::histogram_json(const std::string& quiz_id) const {
  const Quiz* q = quiz_by_id(quiz_id);
  json h = json::object();
  if (!q) return h;
  if (q->kind == QuizKind::TrueFalse) {
    h["true"] = 0;
    h["false"] = 0;
  } else if (q->kind == QuizKind::Fill || q->kind == QuizKind::Short) {
    h["answered"] = 0;
  } else {
    for (const auto& o : q->options) h[o.id] = 0;
  }
  int n = 0;
  for (const auto& a : answers_) {
    if (a.quiz_id != quiz_id) continue;
    n++;
    if (q->kind == QuizKind::TrueFalse) {
      bool val = false;
      if (a.payload.contains("value") && a.payload["value"].is_boolean())
        val = a.payload["value"].get<bool>();
      h[val ? "true" : "false"] = h[val ? "true" : "false"].get<int>() + 1;
    } else if (q->kind == QuizKind::Fill || q->kind == QuizKind::Short) {
      h["answered"] = h["answered"].get<int>() + 1;
    } else {
      std::vector<std::string> ids;
      if (a.payload.contains("option_ids")) {
        for (const auto& x : a.payload["option_ids"]) ids.push_back(x.get<std::string>());
      } else if (a.payload.contains("option_id")) {
        ids.push_back(a.payload["option_id"].get<std::string>());
      }
      for (const auto& id : ids) {
        if (!h.contains(id)) h[id] = 0;
        h[id] = h[id].get<int>() + 1;
      }
    }
  }
  h["_n"] = n;
  return h;
}

json Classroom::quiz_public(const Quiz& q, QuizState st, const std::string& viewer_id) const {
  json o = {{"id", q.id},
             {"kind", kind_str(q.kind)},
             {"prompt_zh", q.prompt_zh},
             {"prompt_en", q.prompt_en},
             {"time_limit_sec", q.time_limit_sec},
             {"xp", q.xp},
             {"kc_ids", q.kc_ids},
             {"state", qstate_str(st)},
             {"options", json::array()}};
  for (const auto& op : q.options) {
    o["options"].push_back(
        {{"id", op.id}, {"text_zh", op.text_zh}, {"text_en", op.text_en}});
  }
  o["closes_at_ms"] = quiz_closes_at_;
  o["opens_at_ms"] = quiz_opens_at_;
  o["histogram"] = histogram_json(q.id);
  int answered = 0, correct = 0, present = 0;
  for (const auto& s : students_)
    if (s.present) present++;
  for (const auto& a : answers_) {
    if (a.quiz_id != q.id) continue;
    answered++;
    if (a.scored && a.correct) correct++;
  }
  o["answered"] = answered;
  o["present"] = present;
  o["correct"] = correct;
  o["accuracy"] = answered ? static_cast<double>(correct) / answered : 0.0;
  bool you = false;
  json your = nullptr;
  for (const auto& a : answers_) {
    if (a.quiz_id == q.id && a.student_id == viewer_id) {
      you = true;
      your = {{"scored", a.scored}, {"correct", a.correct}, {"xp", a.xp_awarded}};
    }
  }
  o["you_answered"] = you;
  o["your_result"] = your;
  if (st == QuizState::Revealed) {
    o["correct_ids"] = q.correct;
  }
  return o;
}

json Classroom::student_json(const Student& s, bool include_answers) const {
  json m = json::object();
  json mn = json::object();
  for (const auto& kc : deck_.kcs) {
    auto it = s.mastery.find(kc.id);
    m[kc.id] = it == s.mastery.end() ? 0.5 : it->second;
    auto jt = s.mastery_n.find(kc.id);
    mn[kc.id] = jt == s.mastery_n.end() ? 0 : jt->second;
  }
  json o = {{"id", s.id},
             {"name", s.name},
             {"team", s.team},
             {"xp", s.xp},
             {"slide_index", s.slide_index},
             {"present", s.present},
             {"checked_in", s.checked_in},
             {"bot", s.bot},
             {"mastery", m},
             {"mastery_n", mn},
             {"confused_count", s.confused_count},
             {"answers_correct", s.answers_correct},
             {"answers_total", s.answers_total}};
  if (include_answers) {
    json arr = json::array();
    for (const auto& a : answers_) {
      if (a.student_id == s.id)
        arr.push_back({{"quiz_id", a.quiz_id},
                       {"correct", a.correct},
                       {"scored", a.scored},
                       {"xp", a.xp_awarded}});
    }
    o["answers"] = arr;
  }
  return o;
}

json Classroom::snapshot(const std::string& viewer_id, const std::string& locale) const {
  json slides = json::array();
  for (size_t i = 0; i < deck_.slides.size(); ++i) {
    const auto& sl = deck_.slides[i];
    int conf = 0;
    auto it = confused_.find(sl.id);
    if (it != confused_.end()) conf = it->second;
    json sj = {{"id", sl.id},
               {"index", i},
               {"title_zh", sl.title_zh},
               {"title_en", sl.title_en},
               {"body_zh", sl.body_zh},
               {"body_en", sl.body_en},
               {"visual", sl.visual},
               {"quiz_id", sl.quiz_id ? json(*sl.quiz_id) : json(nullptr)},
               {"confused", conf}};
    slides.push_back(sj);
  }
  json kcs = json::array();
  for (const auto& kc : deck_.kcs)
    kcs.push_back({{"id", kc.id}, {"name_zh", kc.name_zh}, {"name_en", kc.name_en}});

  json students = json::array();
  for (const auto& s : students_) students.push_back(student_json(s, viewer_id == teacher_id_));

  json live_quiz = nullptr;
  if (quiz_state_ != QuizState::Idle && !open_quiz_id_.empty()) {
    if (const Quiz* q = quiz_by_id(open_quiz_id_)) {
      live_quiz = quiz_public(*q, quiz_state_, viewer_id);
    }
  }

  std::vector<std::string> cloud_src;
  for (const auto& d : danmaku_) {
    if (danmaku_muted_ && !danmaku_in_cloud_when_muted_) continue;
    cloud_src.push_back(d.text);
  }
  auto cloud = tokenize_cloud(cloud_src, 40);
  json cloudj = json::array();
  for (const auto& [w, c] : cloud) cloudj.push_back(json::array({w, c}));

  json dan = json::array();
  int start = std::max(0, static_cast<int>(danmaku_.size()) - 80);
  for (int i = start; i < static_cast<int>(danmaku_.size()); ++i) {
    const auto& d = danmaku_[i];
    if (danmaku_muted_ && viewer_id != teacher_id_) continue;
    dan.push_back({{"id", d.id},
                   {"name", d.name},
                   {"text", d.text},
                   {"t_ms", d.t_ms},
                   {"student_id", d.student_id}});
  }

  json posts = json::array();
  for (const auto& p : posts_) {
    bool show = p.broadcast || viewer_id == teacher_id_ || p.student_id == viewer_id;
    if (!show) continue;
    posts.push_back({{"id", p.id},
                     {"name", p.name},
                     {"text", p.text},
                     {"broadcast", p.broadcast},
                     {"student_id", p.student_id}});
  }

  json lb = json::array();
  std::vector<const Student*> ranked;
  for (const auto& s : students_) ranked.push_back(&s);
  std::sort(ranked.begin(), ranked.end(), [](const Student* a, const Student* b) {
    if (a->xp != b->xp) return a->xp > b->xp;
    return a->name < b->name;
  });
  for (size_t i = 0; i < ranked.size() && i < 12; ++i) {
    lb.push_back({{"rank", i + 1},
                   {"id", ranked[i]->id},
                   {"name", ranked[i]->name},
                   {"xp", ranked[i]->xp},
                   {"team", ranked[i]->team}});
  }

  json mastery_class = json::object();
  for (const auto& kc : deck_.kcs) {
    double sum = 0;
    int n = 0;
    for (const auto& s : students_) {
      auto itn = s.mastery_n.find(kc.id);
      if (itn == s.mastery_n.end() || itn->second == 0) continue;
      sum += s.mastery.at(kc.id);
      n++;
    }
    mastery_class[kc.id] = {{"mean", n ? json(sum / n) : json(nullptr)}, {"n", n}};
  }

  json reteach = nullptr;
  if (quiz_state_ == QuizState::Revealed || quiz_state_ == QuizState::Locked) {
    if (const Quiz* q = quiz_by_id(open_quiz_id_)) {
      int answered = 0, correct = 0;
      for (const auto& a : answers_) {
        if (a.quiz_id != q->id) continue;
        if (!a.scored) continue;
        answered++;
        if (a.correct) correct++;
      }
      double acc = answered ? static_cast<double>(correct) / answered : 1.0;
      const auto& sl = deck_.slides[static_cast<size_t>(slide_index_)];
      int conf = confused_.count(sl.id) ? confused_.at(sl.id) : 0;
      int present = 0;
      for (const auto& s : students_)
        if (s.present) present++;
      double crate = present ? static_cast<double>(conf) / present : 0;
      if ((answered >= 5 && acc < 0.4) || crate >= 0.3) {
        std::string kc = q->kc_ids.empty() ? "" : q->kc_ids[0];
        reteach = {{"on", true},
                   {"reason_zh", acc < 0.4 ? "正确率偏低，建议当场复讲这一拍。"
                                            : "本页「不懂」偏多，放慢或换个例子。"},
                   {"reason_en", acc < 0.4 ? "Accuracy is low — reteach this beat now."
                                            : "Confusion is high on this slide — slow down."},
                   {"kc", kc},
                   {"accuracy", acc},
                   {"confused_rate", crate}};
      }
    }
  }

  json you = nullptr;
  if (viewer_id == teacher_id_) {
    you = {{"id", teacher_id_}, {"role", "teacher"}, {"name", teacher_name_}};
  } else if (const Student* s = find_student(viewer_id)) {
    you = student_json(*s, true);
    you["role"] = "student";
  }

  json roll = nullptr;
  if (!last_rollcall_id_.empty()) {
    if (const Student* s = find_student(last_rollcall_id_)) {
      roll = {{"student_id", s->id}, {"name", s->name}, {"team", s->team}};
    }
  }

  int present = 0, checked = 0;
  for (const auto& s : students_) {
    if (s.present) present++;
    if (s.checked_in) checked++;
  }

  return json{{"seq", seq_},
              {"code", code_},
              {"locale", locale},
              {"title_zh", deck_.title_zh},
              {"title_en", deck_.title_en},
              {"subtitle_zh", deck_.subtitle_zh},
              {"subtitle_en", deck_.subtitle_en},
              {"slide_index", slide_index_},
              {"slides", slides},
              {"kcs", kcs},
              {"students", students},
              {"teacher", {{"id", teacher_id_}, {"name", teacher_name_}}},
              {"quiz", live_quiz},
              {"danmaku", dan},
              {"danmaku_muted", danmaku_muted_},
              {"wordcloud", cloudj},
              {"rollcall", roll},
              {"pk", {{"on", pk_on_}, {"red", pk_red_}, {"blue", pk_blue_}}},
              {"posts", posts},
              {"leaderboard", lb},
              {"mastery_class", mastery_class},
              {"reteach", reteach},
              {"you", you},
              {"bots_enabled", bots_enabled_},
              {"present", present},
              {"checked_in", checked},
              {"roster_n", students_.size()}};
}

json Classroom::report() const {
  json quizzes = json::array();
  for (const auto& q : deck_.quizzes) {
    int answered = 0, correct = 0;
    for (const auto& a : answers_) {
      if (a.quiz_id != q.id) continue;
      if (!a.scored) continue;
      answered++;
      if (a.correct) correct++;
    }
    quizzes.push_back({{"id", q.id},
                       {"prompt_zh", q.prompt_zh},
                       {"prompt_en", q.prompt_en},
                       {"kind", kind_str(q.kind)},
                       {"answered", answered},
                       {"correct", correct},
                       {"accuracy",
                        answered ? json(static_cast<double>(correct) / answered) : json(nullptr)},
                       {"kc_ids", q.kc_ids}});
  }
  json conf_slides = json::array();
  for (size_t i = 0; i < deck_.slides.size(); ++i) {
    const auto& sl = deck_.slides[i];
    int c = confused_.count(sl.id) ? confused_.at(sl.id) : 0;
    conf_slides.push_back(
        {{"id", sl.id}, {"index", i}, {"title_zh", sl.title_zh}, {"confused", c}});
  }
  std::vector<std::string> src;
  for (const auto& d : danmaku_) src.push_back(d.text);
  auto cloud = tokenize_cloud(src);
  json top = json::array();
  for (const auto& [w, c] : cloud) top.push_back(json::array({w, c}));

  json people = json::array();
  for (const auto& s : students_) people.push_back(student_json(s, true));

  int present = 0, checked = 0;
  for (const auto& x : students_) {
    if (x.present) present++;
    if (x.checked_in) checked++;
  }

  return json{{"code", code_},
              {"title_zh", deck_.title_zh},
              {"title_en", deck_.title_en},
              {"attendance",
               {{"present", present},
                {"checked_in", checked},
                {"total", students_.size()},
                {"rate", students_.empty() ? 0.0
                                            : static_cast<double>(checked) / students_.size()}}},
              {"quizzes", quizzes},
              {"confused_slides", conf_slides},
              {"top_words", top},
              {"students", people},
              {"pk", {{"red", pk_red_}, {"blue", pk_blue_}}},
              {"event_count", events_.size()}};
}

json Classroom::fingerprint() const {
  json ids = json::array();
  for (const auto& s : students_) {
    json m = json::object();
    for (const auto& kc : deck_.kcs) {
      auto it = s.mastery.find(kc.id);
      auto jt = s.mastery_n.find(kc.id);
      m[kc.id] = {{"m", it == s.mastery.end() ? 0.5 : it->second},
                  {"n", jt == s.mastery_n.end() ? 0 : jt->second}};
    }
    ids.push_back({{"id", s.id},
                   {"team", s.team},
                   {"xp", s.xp},
                   {"present", s.present},
                   {"checked_in", s.checked_in},
                   {"slide_index", s.slide_index},
                   {"confused_count", s.confused_count},
                   {"answers_correct", s.answers_correct},
                   {"answers_total", s.answers_total},
                   {"mastery", m}});
  }
  json ans = json::array();
  for (const auto& a : answers_) {
    ans.push_back({{"sid", a.student_id},
                    {"qid", a.quiz_id},
                    {"correct", a.correct},
                    {"scored", a.scored},
                    {"xp", a.xp_awarded}});
  }
  json conf = json::object();
  for (const auto& [k, v] : confused_) conf[k] = v;
  return json{{"seq", seq_},
              {"slide_index", slide_index_},
              {"quiz_state", qstate_str(quiz_state_)},
              {"open_quiz_id", open_quiz_id_},
              {"students", ids},
              {"answers", ans},
              {"confused", conf},
              {"pk", {{"on", pk_on_}, {"red", pk_red_}, {"blue", pk_blue_}}},
              {"danmaku_n", danmaku_.size()},
              {"posts_n", posts_.size()},
              {"rollcall", last_rollcall_id_},
              {"muted", danmaku_muted_}};
}

json Classroom::suggest_bot_action(const std::string& bot_id, std::mt19937& rng,
                                   int64_t now_ms) const {
  const Student* s = find_student(bot_id);
  if (!s || !s->bot || !s->present) return json();
  std::uniform_real_distribution<double> u(0.0, 1.0);

  if (!s->checked_in) {
    return {{"type", "checkin"}, {"actor_id", bot_id}, {"client_id", bot_id}};
  }
  if (s->slide_index != slide_index_ && u(rng) < 0.5) {
    return {{"type", "cursor"},
            {"actor_id", bot_id},
            {"client_id", bot_id},
            {"slide_index", slide_index_}};
  }

  if (quiz_state_ == QuizState::Open && now_ms < quiz_closes_at_) {
    bool answered = false;
    for (const auto& a : answers_) {
      if (a.student_id == bot_id && a.quiz_id == open_quiz_id_) {
        answered = true;
        break;
      }
    }
    if (!answered && u(rng) < 0.42) {
      const Quiz* q = quiz_by_id(open_quiz_id_);
      if (!q) return json();
      bool right = u(rng) < s->skill;
      json ans;
      if (q->kind == QuizKind::TrueFalse) {
        bool truth = !q->correct.empty() && normalize_text(q->correct[0]) == "true";
        ans = {{"value", right ? truth : !truth}};
      } else if (q->kind == QuizKind::Fill) {
        ans = {{"text", right ? (q->correct.empty() ? "lg n" : q->correct.front()) : "n"}};
      } else if (q->kind == QuizKind::Short) {
        static const char* shorts[] = {
            "子问题重叠就改 DP。", "算过的子问题不要再递归。",
            "重叠严重时制表，不要分治树。", "Fibonacci 那种重复就算重叠。"};
        ans = {{"text", shorts[static_cast<int>(u(rng) * 4) % 4]}};
      } else if (q->kind == QuizKind::Multi) {
        json ids = json::array();
        if (right) {
          for (const auto& c : q->correct) ids.push_back(c);
        } else {
          for (const auto& o : q->options) {
            if (std::find(q->correct.begin(), q->correct.end(), o.id) == q->correct.end()) {
              ids.push_back(o.id);
              break;
            }
          }
          if (!q->correct.empty()) ids.push_back(q->correct.front());
        }
        ans = {{"option_ids", ids}};
      } else {
        std::string pick = q->correct.empty() ? "a" : q->correct.front();
        if (!right) {
          for (const auto& o : q->options) {
            if (std::find(q->correct.begin(), q->correct.end(), o.id) == q->correct.end()) {
              pick = o.id;
              break;
            }
          }
        }
        ans = {{"option_id", pick}};
      }
      return {{"type", "answer"},
              {"actor_id", bot_id},
              {"client_id", bot_id},
              {"answer", ans}};
    }
  }

  const std::string& vis =
      deck_.slides.empty() ? std::string()
                           : deck_.slides[static_cast<size_t>(slide_index_)].visual;
  if (u(rng) < 0.045) {
    return {{"type", "confused"}, {"actor_id", bot_id}, {"client_id", bot_id}};
  }
  if (u(rng) < 0.16) {
    std::vector<std::string> phrases = {
        "合并步不是免费的", "每一层都是 Θ(n)", "分治三拍：分解解决合并",
        "主定理 Case 2", "这页有点快", "明白了", "递推树好清楚",
        "combine 才是陷阱", "子问题重叠就别硬分治", "θ(n lg n)",
        "中点向两边扫", "红队加油", "蓝队呢", "再讲一遍主定理",
        "divide merge conquer", "不懂第三拍", "例题再来一个"};
    if (vis == "master") {
      phrases = {"Case 2 各层相当", "a=2 b=2", "f 和 n^{log_b a} 比", "主定理三扇门"};
    } else if (vis == "merge-tree") {
      phrases = {"树高 lg n", "每层 Θ(n)", "归并两个指针", "稳定排序"};
    } else if (vis == "dac-dp") {
      phrases = {"重叠就 DP", "斐波那契别分治", "制表不是认输"};
    }
    auto& pick = phrases[static_cast<size_t>(u(rng) * phrases.size()) % phrases.size()];
    return {{"type", "danmaku"},
            {"actor_id", bot_id},
            {"client_id", bot_id},
            {"text", pick}};
  }
  if (u(rng) < 0.012) {
    return {{"type", "submit_post"},
            {"actor_id", bot_id},
            {"client_id", bot_id},
            {"text", "老师，带宽里为什么不是 n²？"}};
  }
  (void)now_ms;
  return json();
}

}  // namespace storm
