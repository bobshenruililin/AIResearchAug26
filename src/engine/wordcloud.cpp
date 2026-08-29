#include "engine/wordcloud.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace storm {
namespace {

bool utf8_next(const std::string& s, size_t& i, uint32_t& cp) {
  if (i >= s.size()) return false;
  unsigned char c = static_cast<unsigned char>(s[i]);
  if (c < 0x80) {
    cp = c;
    i += 1;
    return true;
  }
  int n = 0;
  if ((c & 0xE0) == 0xC0) {
    n = 2;
    cp = c & 0x1F;
  } else if ((c & 0xF0) == 0xE0) {
    n = 3;
    cp = c & 0x0F;
  } else if ((c & 0xF8) == 0xF0) {
    n = 4;
    cp = c & 0x07;
  } else {
    cp = c;
    i += 1;
    return true;
  }
  if (i + static_cast<size_t>(n) > s.size()) {
    cp = c;
    i += 1;
    return true;
  }
  for (int k = 1; k < n; ++k) {
    unsigned char cc = static_cast<unsigned char>(s[i + k]);
    if ((cc & 0xC0) != 0x80) {
      cp = c;
      i += 1;
      return true;
    }
    cp = (cp << 6) | (cc & 0x3F);
  }
  i += n;
  return true;
}

void utf8_append(std::string& o, uint32_t cp) {
  if (cp < 0x80) {
    o.push_back(static_cast<char>(cp));
  } else if (cp < 0x800) {
    o.push_back(static_cast<char>(0xC0 | (cp >> 6)));
    o.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
  } else if (cp < 0x10000) {
    o.push_back(static_cast<char>(0xE0 | (cp >> 12)));
    o.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
    o.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
  } else {
    o.push_back(static_cast<char>(0xF0 | (cp >> 18)));
    o.push_back(static_cast<char>(0x80 | ((cp >> 12) & 0x3F)));
    o.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
    o.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
  }
}

bool is_cjk(uint32_t cp) {
  return (cp >= 0x4E00 && cp <= 0x9FFF) || (cp >= 0x3400 && cp <= 0x4DBF);
}

const std::vector<std::string>& lexicon() {
  static const std::vector<std::string> w = {
      "分治",   "分解",   "解决",   "合并",     "归并",     "归并排序", "主定理",
      "递推",   "递归",   "复杂度", "对数",     "线性",     "子问题",   "最大子数组",
      "平衡",   "深度",   "合并步", "不懂",     "太快",     "明白",     "例题",
      "证明",   "归纳",   "二叉树", "排序",     "时间",     "空间",     "主方法",
      "分而治之", "合并代价", "对数线性", "最坏",   "平均",     "基例",     "递归树",
      "层数",   "每层",   "比较",   "划分",     "哨兵",     "稳定排序", "原地",
      "额外空间", "正确",  "错误",   "为什么",   "老师",     "这题",     "好难",
      "会了",   "还行",   "秒懂",   "再讲",     "板书",     "投影",     "点名",
      "弹幕",   "词云",   "签到",   "红队",     "蓝队",     "加分",     "掌握",
      "定理",   "假设",   "归纳假设", "叶子",   "规模",     "减半",     "两半",
      "左右",   "合并数组", "指针", "中点",     "mid",      "merge",    "conquer",
      "divide", "combine", "log",  "linear",   "recurrence"};
  return w;
}

const std::unordered_set<std::string>& stop() {
  static const std::unordered_set<std::string> s = {
      "的", "了", "是", "在", "我",  "有", "不",  "也",  "就", "都", "而", "和",
      "与", "这", "那", "吗", "啊",  "呢", "吧",  "很",  "到", "说", "要", "会",
      "可以", "什么", "一个", "这个", "那个", "我们", "你们", "他们", "then", "this",
      "that", "with", "from", "have", "just", "the",  "and", "for", "are", "but"};
  return s;
}

}  // namespace

std::vector<std::pair<std::string, int>> tokenize_cloud(const std::vector<std::string>& texts,
                                                        int topk) {
  std::unordered_map<std::string, int> freq;
  const auto& lex = lexicon();
  std::vector<std::string> lex_sorted = lex;
  std::sort(lex_sorted.begin(), lex_sorted.end(),
            [](const std::string& a, const std::string& b) { return a.size() > b.size(); });

  for (const auto& text : texts) {
    std::vector<uint32_t> cps;
    size_t i = 0;
    uint32_t cp = 0;
    while (utf8_next(text, i, cp)) cps.push_back(cp);

    std::vector<char> used(cps.size(), 0);

    auto slice = [&](size_t a, size_t b) {
      std::string o;
      for (size_t k = a; k < b; ++k) utf8_append(o, cps[k]);
      return o;
    };

    // greedy lexicon on CJK runs
    size_t n = cps.size();
    for (size_t p = 0; p < n;) {
      if (!is_cjk(cps[p])) {
        ++p;
        continue;
      }
      bool hit = false;
      for (const auto& w : lex_sorted) {
        std::vector<uint32_t> wc;
        size_t j = 0;
        uint32_t c2 = 0;
        while (utf8_next(w, j, c2)) wc.push_back(c2);
        if (wc.empty() || p + wc.size() > n) continue;
        bool match = true;
        for (size_t k = 0; k < wc.size(); ++k) {
          if (used[p + k] || cps[p + k] != wc[k]) {
            match = false;
            break;
          }
        }
        if (match) {
          freq[w] += 1;
          for (size_t k = 0; k < wc.size(); ++k) used[p + k] = 1;
          p += wc.size();
          hit = true;
          break;
        }
      }
      if (!hit) ++p;
    }

    // CJK bigrams on unused
    for (size_t p = 0; p + 1 < n; ++p) {
      if (used[p] || used[p + 1]) continue;
      if (is_cjk(cps[p]) && is_cjk(cps[p + 1])) {
        auto bg = slice(p, p + 2);
        if (!stop().count(bg)) freq[bg] += 1;
      }
    }

    // ASCII words
    std::string cur;
    auto flush = [&]() {
      if (cur.size() < 2) {
        cur.clear();
        return;
      }
      if (!stop().count(cur)) freq[cur] += 1;
      cur.clear();
    };
    for (uint32_t c : cps) {
      if (c < 128 && std::isalnum(static_cast<int>(c))) {
        char ch = static_cast<char>(c);
        if (c >= 'A' && c <= 'Z') ch = static_cast<char>(c - 'A' + 'a');
        cur.push_back(ch);
      } else {
        flush();
      }
    }
    flush();
  }

  std::vector<std::pair<std::string, int>> items(freq.begin(), freq.end());
  std::sort(items.begin(), items.end(), [](const auto& a, const auto& b) {
    if (a.second != b.second) return a.second > b.second;
    return a.first < b.first;
  });
  if (static_cast<int>(items.size()) > topk) items.resize(topk);
  return items;
}

}  // namespace storm
