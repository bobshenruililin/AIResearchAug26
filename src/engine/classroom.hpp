#pragma once

#include <cstdint>
#include <functional>
#include <mutex>
#include <random>
#include <string>
#include <unordered_map>
#include <vector>

#include "engine/types.hpp"

namespace storm {

class Classroom {
public:
  using Clock = std::function<int64_t()>;

  Classroom(std::string code, Deck deck, uint32_t rng_seed, Clock clock = {});

  static Classroom demo(uint32_t rng_seed = 20260829);
  static Classroom blank(const std::string& code, const std::string& title_zh,
                          const std::string& title_en, uint32_t rng_seed);

  const std::string& code() const { return code_; }
  const Deck& deck() const { return deck_; }
  int64_t seq() const { return seq_; }
  const std::vector<Event>& events() const { return events_; }

  ApplyResult apply(json action, int64_t now_ms = 0);

  // Rebuild state from a prefix of events (property: fold(events) == snapshot).
  static Classroom replay(const Classroom& prototype, const std::vector<Event>& events,
                         int64_t upto_seq = -1);

  json snapshot(const std::string& viewer_id = "", const std::string& locale = "zh") const;
  json report() const;

  // Close quiz if timer elapsed. Returns true if state changed.
  bool tick(int64_t now_ms);

  // Bot policy: maybe produce an action for this bot at now. Empty if idle.
  json suggest_bot_action(const std::string& bot_id, std::mt19937& rng, int64_t now_ms) const;

  const std::vector<Student>& students() const { return students_; }
  Student* find_student(const std::string& id);
  const Student* find_student(const std::string& id) const;

  const std::string& teacher_id() const { return teacher_id_; }
  const std::string& teacher_name() const { return teacher_name_; }
  QuizState quiz_state() const { return quiz_state_; }
  const std::string& open_quiz_id() const { return open_quiz_id_; }

  void set_bots_enabled(bool on) { bots_enabled_ = on; }
  bool bots_enabled() const { return bots_enabled_; }

  json fingerprint() const;  // compact comparable state for replay tests

private:
  ApplyResult apply_inner(json action, int64_t now_ms, bool record);
  void emit(const std::string& type, json payload, int64_t now_ms);
  void reset_live_keep_deck();
  void assign_team(Student& s);
  void apply_mastery(Student& s, const Quiz& q, bool correct);
  void award_xp(Student& s, int amount);
  const Quiz* quiz_by_id(const std::string& id) const;
  Quiz* quiz_by_id(const std::string& id);
  json student_json(const Student& s, bool include_answers) const;
  json quiz_public(const Quiz& q, QuizState st, const std::string& viewer_id) const;
  json histogram_json(const std::string& quiz_id) const;
  std::string pick_rollcall(int64_t now_ms);
  void ensure_kc_maps(Student& s);

  std::string code_;
  Deck deck_;
  uint32_t rng_seed_ = 1;
  Clock clock_;
  mutable std::mt19937 rng_;

  int64_t seq_ = 0;
  std::vector<Event> events_;

  std::string teacher_id_;
  std::string teacher_name_ = "沈老师";
  std::vector<Student> students_;
  int slide_index_ = 0;
  QuizState quiz_state_ = QuizState::Idle;
  std::string open_quiz_id_;
  int64_t quiz_opens_at_ = 0;
  int64_t quiz_closes_at_ = 0;
  std::vector<AnswerRecord> answers_;
  std::vector<Danmaku> danmaku_;
  int64_t danmaku_seq_ = 0;
  bool danmaku_muted_ = false;
  bool danmaku_in_cloud_when_muted_ = true;
  std::vector<Post> posts_;
  int64_t post_seq_ = 0;
  std::unordered_map<std::string, int> confused_;  // slide id -> count
  std::unordered_map<std::string, int64_t> last_confused_ms_;
  std::string last_rollcall_id_;
  std::vector<std::string> rollcall_pool_;
  bool pk_on_ = false;
  int pk_red_ = 0;
  int pk_blue_ = 0;
  bool bots_enabled_ = false;
  std::unordered_map<std::string, int64_t> bot_last_act_;
  int next_human_ = 1;
};

Deck load_divide_and_conquer_deck();
std::vector<std::pair<std::string, double>> demo_bot_roster();
std::string random_room_code(std::mt19937& rng);

}  // namespace storm
