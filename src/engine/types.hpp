#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include "json.hpp"

namespace storm {

using json = nlohmann::json;

enum class Role { Teacher, Student, Spectator };
enum class QuizKind { Single, Multi, TrueFalse, Fill, Short };
enum class QuizState { Idle, Open, Locked, Revealed };

inline const char* role_str(Role r) {
  switch (r) {
    case Role::Teacher: return "teacher";
    case Role::Student: return "student";
    case Role::Spectator: return "spectator";
  }
  return "spectator";
}

inline const char* kind_str(QuizKind k) {
  switch (k) {
    case QuizKind::Single: return "single";
    case QuizKind::Multi: return "multi";
    case QuizKind::TrueFalse: return "truefalse";
    case QuizKind::Fill: return "fill";
    case QuizKind::Short: return "short";
  }
  return "single";
}

inline const char* qstate_str(QuizState s) {
  switch (s) {
    case QuizState::Idle: return "idle";
    case QuizState::Open: return "open";
    case QuizState::Locked: return "locked";
    case QuizState::Revealed: return "revealed";
  }
  return "idle";
}

inline QuizKind parse_kind(const std::string& s) {
  if (s == "multi") return QuizKind::Multi;
  if (s == "truefalse" || s == "tf") return QuizKind::TrueFalse;
  if (s == "fill") return QuizKind::Fill;
  if (s == "short") return QuizKind::Short;
  return QuizKind::Single;
}

struct KnowledgePoint {
  std::string id;
  std::string name_zh;
  std::string name_en;
};

struct Option {
  std::string id;
  std::string text_zh;
  std::string text_en;
};

struct Quiz {
  std::string id;
  QuizKind kind = QuizKind::Single;
  std::string prompt_zh;
  std::string prompt_en;
  std::vector<Option> options;
  std::vector<std::string> correct;  // option ids, "true"/"false", or fill aliases
  double numeric_tolerance = 0.0;
  std::vector<std::string> kc_ids;
  int time_limit_sec = 30;
  int xp = 100;
  int slide_index = -1;
};

struct Slide {
  std::string id;
  std::string title_zh;
  std::string title_en;
  std::string body_zh;
  std::string body_en;
  std::string visual;
  std::optional<std::string> quiz_id;
};

struct Deck {
  std::string id;
  std::string title_zh;
  std::string title_en;
  std::string subtitle_zh;
  std::string subtitle_en;
  std::vector<KnowledgePoint> kcs;
  std::vector<Slide> slides;
  std::vector<Quiz> quizzes;
};

struct AnswerRecord {
  std::string student_id;
  std::string quiz_id;
  json payload;
  bool scored = false;
  bool correct = false;
  double fraction = 0;
  int xp_awarded = 0;
  int64_t t_ms = 0;
};

struct Student {
  std::string id;
  std::string name;
  std::string team;  // "red" | "blue"
  int xp = 0;
  int slide_index = 0;
  bool present = true;
  bool checked_in = false;
  bool bot = false;
  double skill = 0.7;  // bot only
  std::unordered_map<std::string, double> mastery;
  std::unordered_map<std::string, int> mastery_n;
  int confused_count = 0;
  int answers_correct = 0;
  int answers_total = 0;
};

struct Danmaku {
  int64_t id = 0;
  std::string student_id;
  std::string name;
  std::string text;
  int64_t t_ms = 0;
};

struct Post {
  int64_t id = 0;
  std::string student_id;
  std::string name;
  std::string text;
  bool broadcast = false;
  int64_t t_ms = 0;
};

struct Event {
  int64_t seq = 0;
  int64_t t_ms = 0;
  std::string type;
  json payload;
};

struct ApplyResult {
  bool ok = true;
  std::string error;
  json reply = json::object();
};

struct ScoreResult {
  bool scored = false;
  bool correct = false;
  double fraction = 0;
};

constexpr double kMasteryAlpha = 0.35;
constexpr int kDanmakuRing = 400;

}  // namespace storm
