#pragma once

#include "engine/types.hpp"

namespace storm {

ScoreResult score_answer(const Quiz& quiz, const json& answer);

// Lowercased, punctuation-stripped, whitespace-collapsed.
std::string normalize_text(const std::string& s);

bool parse_number(const std::string& s, double& out);

}  // namespace storm
