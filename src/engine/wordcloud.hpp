#pragma once

#include <string>
#include <utility>
#include <vector>

namespace storm {

// CJK lexicon + bigrams, ASCII tokens; stopword-filtered. Highest count first.
std::vector<std::pair<std::string, int>> tokenize_cloud(const std::vector<std::string>& texts,
                                                        int topk = 48);

}  // namespace storm
