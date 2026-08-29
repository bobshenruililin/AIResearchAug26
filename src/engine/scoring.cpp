#include "engine/scoring.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <sstream>

namespace storm {

std::string normalize_text(const std::string& s) {
  std::string out;
  out.reserve(s.size());
  for (unsigned char c : s) {
    if (c >= 'A' && c <= 'Z') {
      out.push_back(static_cast<char>(c - 'A' + 'a'));
    } else if (c == '\t' || c == '\n' || c == '\r') {
      out.push_back(' ');
    } else {
      out.push_back(static_cast<char>(c));
    }
  }
  std::string compact;
  bool space = false;
  for (char c : out) {
    if (c == ' ') {
      if (!space) compact.push_back(' ');
      space = true;
    } else if (c == '.' || c == '+' ) {
      compact.push_back(c);
    } else if (std::ispunct(static_cast<unsigned char>(c))) {
      if (!space) compact.push_back(' ');
      space = true;
    } else {
      compact.push_back(c);
      space = false;
    }
  }
  auto b = compact.find_first_not_of(' ');
  auto e = compact.find_last_not_of(' ');
  if (b == std::string::npos) return "";
  return compact.substr(b, e - b + 1);
}

bool parse_number(const std::string& s, double& out) {
  std::string t = normalize_text(s);
  if (t.empty()) return false;
  std::istringstream iss(t);
  double v = 0;
  iss >> v;
  if (!iss || !iss.eof()) return false;
  out = v;
  return true;
}

static std::vector<std::string> as_ids(const json& answer) {
  std::vector<std::string> ids;
  if (answer.contains("option_ids") && answer["option_ids"].is_array()) {
    for (const auto& x : answer["option_ids"]) ids.push_back(x.get<std::string>());
  } else if (answer.contains("option_id") && answer["option_id"].is_string()) {
    ids.push_back(answer["option_id"].get<std::string>());
  } else if (answer.is_string()) {
    ids.push_back(answer.get<std::string>());
  } else if (answer.is_array()) {
    for (const auto& x : answer) ids.push_back(x.get<std::string>());
  }
  std::sort(ids.begin(), ids.end());
  ids.erase(std::unique(ids.begin(), ids.end()), ids.end());
  return ids;
}

ScoreResult score_answer(const Quiz& quiz, const json& answer) {
  ScoreResult r;
  if (quiz.kind == QuizKind::Short) {
    r.scored = false;
    r.correct = false;
    r.fraction = 0;
    return r;
  }

  if (quiz.kind == QuizKind::Fill) {
    std::string text;
    if (answer.contains("text")) text = answer["text"].get<std::string>();
    else if (answer.is_string()) text = answer.get<std::string>();
    std::string n = normalize_text(text);
    double got = 0;
    bool got_num = parse_number(n, got);
    for (const auto& c : quiz.correct) {
      std::string cn = normalize_text(c);
      if (!n.empty() && n == cn) {
        r.scored = true;
        r.correct = true;
        r.fraction = 1;
        return r;
      }
      double expect = 0;
      if (got_num && parse_number(cn, expect) &&
          std::fabs(got - expect) <= quiz.numeric_tolerance) {
        r.scored = true;
        r.correct = true;
        r.fraction = 1;
        return r;
      }
    }
    r.scored = true;
    r.correct = false;
    r.fraction = 0;
    return r;
  }

  if (quiz.kind == QuizKind::TrueFalse) {
    bool val = false;
    if (answer.contains("value")) {
      if (answer["value"].is_boolean()) val = answer["value"].get<bool>();
      else if (answer["value"].is_string()) {
        auto s = normalize_text(answer["value"].get<std::string>());
        val = (s == "true" || s == "t" || s == "1" || s == "yes");
      }
    } else if (answer.is_boolean()) {
      val = answer.get<bool>();
    } else {
      auto ids = as_ids(answer);
      if (!ids.empty()) {
        auto s = normalize_text(ids[0]);
        val = (s == "true" || s == "t" || s == "true_id" || s == "a");
      }
    }
    bool expect = false;
    if (!quiz.correct.empty()) {
      auto s = normalize_text(quiz.correct[0]);
      expect = (s == "true" || s == "t" || s == "1");
    }
    r.scored = true;
    r.correct = (val == expect);
    r.fraction = r.correct ? 1.0 : 0.0;
    return r;
  }

  auto got = as_ids(answer);
  auto expect = quiz.correct;
  std::sort(expect.begin(), expect.end());
  r.scored = true;
  r.correct = (got == expect);
  r.fraction = r.correct ? 1.0 : 0.0;
  return r;
}

}  // namespace storm
