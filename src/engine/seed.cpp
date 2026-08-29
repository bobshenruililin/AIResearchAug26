#include "engine/classroom.hpp"

namespace storm {

Deck load_divide_and_conquer_deck() {
  Deck d;
  d.id = "dac-01";
  d.title_zh = "算法导论 · 分治";
  d.title_en = "CLRS · Divide and Conquer";
  d.subtitle_zh = "把大问题劈成会响的小问题，再把答案缝回去";
  d.subtitle_en = "Split until it sings, then stitch the answers back";

  d.kcs = {
      {"dac-structure", "分治结构", "D&C structure"},
      {"merge-cost", "合并代价", "Combine cost"},
      {"master-theorem", "主定理", "Master theorem"},
      {"recognize-dac", "识别分治", "Recognize D&C"},
      {"dac-vs-dp", "分治与 DP", "D&C vs DP"},
      {"recurrences", "递推式", "Recurrences"},
  };

  auto S = [&](std::string id, std::string tz, std::string te, std::string bz, std::string be,
                std::string vis, std::optional<std::string> q = {}) {
    Slide s;
    s.id = std::move(id);
    s.title_zh = std::move(tz);
    s.title_en = std::move(te);
    s.body_zh = std::move(bz);
    s.body_en = std::move(be);
    s.visual = std::move(vis);
    s.quiz_id = std::move(q);
    d.slides.push_back(std::move(s));
  };

  S("s0", "今夜下暴雨", "Tonight, a downpour",
    "这不是另一份 PPT。这是一间可检验的教室：幻灯片、限时题、弹幕、点名、不懂、掌握度——全部在本地 C++ 内核里发生。\n\n今晚的题：把一个大问题劈开，直到它变得诚实。",
    "This is not another slide deck. It is an inspectable classroom: slides, timed items, danmaku, roll call, confusion, mastery — all inside a local C++ kernel.\n\nTonight's problem: split a large question until it becomes honest.",
    "storm-title");

  S("s1", "分治的三拍", "Three beats",
    "Divide　把问题切成若干规模更小、结构相同的子问题。\nConquer　子问题足够小就直接解；否则递归。\nCombine　把子答案缝成原问题的答案。\n\n漏掉第三拍的人，会得到两堆正确的碎片，和一道仍然错误的原题。",
    "Divide — cut into smaller instances of the same shape.\nConquer — solve the base, or recurse.\nCombine — stitch sub-answers into the original answer.\n\nSkip the third beat and you own two correct piles and one still-wrong problem.",
    "three-beats", "q1");

  S("s2", "归并：一棵会说话的树", "Mergesort as a talking tree",
    "n 个元素 → 两半 n/2 → 直到 1。\n合并两个有序数组：两个指针，谁小取谁，线性扫过。\n\n树高 ⌈lg n⌉。每一层的合并总量是 Θ(n)。所以整棵树是 Θ(n lg n)。\n\n请盯着“每一层都是 Θ(n)”这句话。它比公式更重要。",
    "n items → two halves of n/2 → until 1.\nMerge two sorted arrays with two pointers — linear.\n\nHeight ⌈lg n⌉. Each level costs Θ(n) to merge. The tree is Θ(n lg n).\n\nWatch the sentence “every level is Θ(n)”. It matters more than the closed form.",
    "merge-tree", "q2");

  S("s3", "合并步不是免费的", "Combine is not free",
    "初学者把分治写成：T(n) = 2T(n/2)，然后宣布 O(n)。\n那是忘了把切开的苹果再拼回果盘。\n\n归并的合并是 Θ(n)。最大子数组的跨越情形也要花线性时间扫过中点。\n\n经验：先写出 Combine 的代价，再谈主定理。",
    "Beginners write T(n) = 2T(n/2) and declare O(n).\nThat is leaving the apple sliced and never rebuilding the bowl.\n\nMergesort's combine is Θ(n). The crossing case of maximum subarray also walks the midpoint in linear time.\n\nHabit: write the combine cost first, then invoke the master theorem.",
    "combine-cost", "q5");

  S("s4", "递推 T(n) = 2T(n/2) + Θ(n)", "The recurrence",
    "递归树：\n第 0 层代价 cn\n第 1 层两份，各 c(n/2)，合计 cn\n第 i 层 2^i 份，各 c(n/2^i)，合计 cn\n共 lg n 层 → cn lg n\n\n叶子 n 个，每个 Θ(1)，也是 Θ(n)，被对数层盖过。",
    "Recursion tree:\nLevel 0 costs cn\nLevel 1: two copies of c(n/2), total cn\nLevel i: 2^i copies of c(n/2^i), total cn\nlg n levels → cn lg n\n\nn leaves of Θ(1) add Θ(n), dominated by the log factor.",
    "recurrence", "q6");

  S("s5", "主定理：三扇门", "Master theorem: three doors",
    "对 T(n) = a T(n/b) + f(n)，比较 f 与 n^{log_b a}。\n\nCase 1　叶子更重：f = O(n^{log_b a − ε}) → Θ(n^{log_b a})\nCase 2　各层相当：f = Θ(n^{log_b a} lg^k n) → Θ(n^{log_b a} lg^{k+1} n)\nCase 3　根更重：f = Ω(n^{log_b a + ε}) 且正则 → Θ(f(n))\n\n归并：a=2, b=2, f=Θ(n) = Θ(n^{log_2 2}) → Case 2, k=0 → Θ(n lg n)。",
    "For T(n) = a T(n/b) + f(n), compare f with n^{log_b a}.\n\nCase 1 leaves dominate.\nCase 2 levels are even.\nCase 3 the root dominates (with regularity).\n\nMergesort: a=2, b=2, f=Θ(n) = Θ(n^{log_2 2}) → Case 2 → Θ(n lg n).",
    "master", "q3");

  S("s6", "最大子数组：中点是钥匙", "Maximum subarray",
    "数组可能负数。最大连续和要么全在左半，要么全在右半，要么跨越中点。\n跨越：从中点向左取最大前缀，向右取最大后缀，相加。Θ(n)。\n\n这是分治，不是 DP。我们没有“以 i 结尾”的最优子结构表，只有结构相同的子区间。",
    "The array may contain negatives. The best contiguous sum lives entirely left, entirely right, or crosses the midpoint.\nCrossing: best prefix left of mid + best suffix right of mid. Θ(n).\n\nThis is D&C, not DP. There is no table of “best ending at i” — only same-shaped subintervals.",
    "maxsub", "q7");

  S("s7", "哪些题闻起来像分治", "What smells like D&C",
    "好兆头：\n· 规模能均匀减半\n· 子问题互不共享（或共享可忽略）\n· 合并有干净的线性或对数扫描\n\n坏兆头：\n· 子问题严重重叠 → 改 DP 或加记忆化\n· 划分不平衡（像最坏快排）→ 小心期望与最坏分家\n· Combine 是 Θ(n²) → 你可能选错了缝法",
    "Good signs: even splits, independent subproblems, a clean linear/log combine.\nBad signs: heavy overlap (use DP), unbalanced cuts (worst-case quicksort), quadratic stitching.",
    "recognize", "q4");

  S("s8", "分治不是 DP 的别名", "Not a nickname for DP",
    "分治：子问题基本不相交，合并一次。\nDP：子问题重叠，必须制表，否则指数爆炸。\n\n斐波那契用分治树会重复计算同一 k。那不是勇敢，是健忘。\n\n课堂口令：先问“算过这个子问题没有？”再决定递归还是制表。",
    "D&C: subproblems are essentially disjoint; combine once.\nDP: overlap; tabulate or explode.\n\nFibonacci via a D&C tree recomputes the same k. That is not bravery. That is amnesia.\n\nPassword: ask “have I already solved this?” before you recurse.",
    "dac-dp", "q8");

  S("s9", "陷阱清单", "Trap list",
    "1. 忘记 Combine，复杂度少写一整层。\n2. 基例写错：n=2 时合并空数组。\n3. 奇数长度忘了处理中间元素。\n4. 用主定理前没检查 f 的多项式间隙 ε。\n5. 把“平均 O(n lg n)”说成“最坏 O(n lg n)”。快排会起诉你。",
    "1. Dropping Combine and under-counting a whole level.\n2. Wrong base: merging empty arrays at n=2.\n3. Odd length, lost middle element.\n4. Invoking the master theorem without a polynomial gap ε.\n5. Calling average O(n lg n) a worst-case bound. Quicksort will object.",
    "traps");

  S("s10", "六个知识点的雷达", "Six knowledge points",
    "这堂课的掌握度不是分数，是六根轴：\n分治结构 · 合并代价 · 主定理 · 识别分治 · 分治与 DP · 递推式。\n\n每道随堂题会更新对应轴。n=0 时轴是未知，不是零。\n不懂按钮加在当前页上，不扣分，但会点亮教师的复讲灯。",
    "Mastery is six axes, not a score: structure, combine cost, master theorem, recognition, D&C vs DP, recurrences.\n\nn=0 is unknown, not zero.\n“Confused” is free. It lights the teacher's reteach lamp.",
    "radar");

  S("s11", "开放：最近点对", "Open: closest pair",
    "平面 n 个点，最近欧氏距离。暴力 Θ(n²)。\n分治：按 x 排序，左右各算，再检查中线 2δ 带宽里的点——关键是每个点只需看 y 序上有限个邻居。\n\n作业不是把算法背完。作业是：你能不能在弹幕里用一句话说清“为什么带宽里不是 Θ(n²)”。",
    "n points in the plane, nearest Euclidean pair. Brute Θ(n²).\nD&C: sort on x, solve left/right, then inspect a 2δ strip — each point only looks at a constant number of y-neighbors.\n\nThe assignment is not memorizing the algorithm. It is saying, in one danmaku, why the strip is not Θ(n²).",
    "closest");

  auto Q = [&](Quiz q) { d.quizzes.push_back(std::move(q)); };

  Q(Quiz{"q1", QuizKind::Single,
         "分治的正确顺序是？", "The correct D&C order is?",
         {{"a", "合并 → 分解 → 解决", "Combine → Divide → Conquer"},
          {"b", "分解 → 解决 → 合并", "Divide → Conquer → Combine"},
          {"c", "解决 → 分解 → 合并", "Conquer → Divide → Combine"},
          {"d", "分解 → 合并 → 解决", "Divide → Combine → Conquer"}},
         {"b"}, 0, {"dac-structure"}, 25, 100, 1});

  Q(Quiz{"q2", QuizKind::Single,
         "归并排序整棵递归树的时间是？", "Mergesort's whole recursion tree costs?",
         {{"a", "Θ(n)", "Θ(n)"},
          {"b", "Θ(n lg n)", "Θ(n lg n)"},
          {"c", "Θ(n²)", "Θ(n²)"},
          {"d", "Θ(lg n)", "Θ(lg n)"}},
         {"b"}, 0, {"merge-cost", "recurrences"}, 25, 100, 2});

  Q(Quiz{"q3", QuizKind::Single,
         "T(n)=2T(n/2)+Θ(n) 用主定理属于？", "T(n)=2T(n/2)+Θ(n) falls into?",
         {{"a", "Case 1，叶子更重", "Case 1, leaves dominate"},
          {"b", "Case 2，各层相当", "Case 2, levels even"},
          {"c", "Case 3，根更重", "Case 3, root dominates"},
          {"d", "主定理不适用", "Master theorem does not apply"}},
         {"b"}, 0, {"master-theorem"}, 30, 120, 5});

  Q(Quiz{"q4", QuizKind::Multi,
         "哪些更像分治而不是重叠子问题的 DP？（多选）",
         "Which smell like D&C rather than overlapping DP? (multi)",
         {{"a", "归并排序", "Mergesort"},
          {"b", "朴素递归斐波那契", "Naive recursive Fibonacci"},
          {"c", "最大子数组（中点跨越）", "Maximum subarray (crossing mid)"},
          {"d", "0-1 背包", "0-1 knapsack"}},
         {"a", "c"}, 0, {"recognize-dac", "dac-vs-dp"}, 35, 140, 7});

  Q(Quiz{"q5", QuizKind::TrueFalse,
         "判断：分治可以忽略 Combine 的代价，因为递归才是主体。",
         "True/false: D&C may ignore combine cost because recursion is the main work.",
         {{"true", "正确 / True", "True"}, {"false", "错误 / False", "False"}},
         {"false"}, 0, {"merge-cost"}, 20, 80, 3});

  Q(Quiz{"q6", QuizKind::Fill,
         "归并递归树有多少层（用 n 的对数，填 lg n 或 log n）？",
         "How many levels in the mergesort tree? (lg n or log n)",
         {},
         {"lg n", "log n", "logn", "lgn", "log2 n", "lg n", "⌈lg n⌉", "ceil(lg n)"},
         0, {"recurrences"}, 25, 100, 4});

  Q(Quiz{"q7", QuizKind::Single,
         "最大子数组跨越中点时，扫描方向是？",
         "For the crossing case of maximum subarray, we scan?",
         {{"a", "只向左", "Left only"},
          {"b", "只向右", "Right only"},
          {"c", "从中点向左取最大前缀，向右取最大后缀", "Best prefix left + best suffix right of mid"},
          {"d", "重新排序后再扫", "Sort, then scan"}},
         {"c"}, 0, {"dac-structure", "recognize-dac"}, 25, 100, 6});

  Q(Quiz{"q8", QuizKind::Short,
         "用一句话：什么时候不该用分治，该改 DP？",
         "In one sentence: when should you abandon D&C for DP?",
         {},
         {}, 0, {"dac-vs-dp"}, 60, 80, 8});

  return d;
}

std::vector<std::pair<std::string, double>> demo_bot_roster() {
  return {
      {"林小雨", 0.86}, {"陈思远", 0.72}, {"王浩然", 0.64}, {"李沐阳", 0.81},
      {"张晓雯", 0.77}, {"赵子涵", 0.58}, {"刘一诺", 0.90}, {"周明杰", 0.61},
      {"吴思琪", 0.83}, {"黄俊熙", 0.54}, {"徐嘉怡", 0.75}, {"孙博文", 0.69},
      {"马欣然", 0.48}, {"朱天佑", 0.71}, {"胡梦琪", 0.80}, {"郭宇航", 0.62},
      {"何诗涵", 0.88}, {"罗景行", 0.66}, {"梁雨桐", 0.79}, {"宋子轩", 0.57},
      {"郑清妍", 0.84}, {"冯浩宇", 0.60}, {"韩雪宁", 0.73}, {"曹致远", 0.67},
      {"彭佳乐", 0.52}, {"董思睿", 0.76}, {"谢安然", 0.70}, {"邓博雅", 0.82},
      {"蒋子墨", 0.55}, {"沈清禾", 0.91}, {"叶知秋", 0.63}, {"任星河", 0.68},
  };
}

std::string random_room_code(std::mt19937& rng) {
  static const char* alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  std::string s(6, '0');
  std::uniform_int_distribution<int> dist(0, 31);
  for (char& c : s) c = alphabet[dist(rng)];
  return s;
}

}  // namespace storm
