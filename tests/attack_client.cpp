#include "httplib.h"
#include "json.hpp"

#include <iostream>
#include <string>

using json = nlohmann::json;

static int g_fail = 0;
static int g_ok = 0;

#define CHECK(cond)                                                                 \
  do {                                                                              \
    if (!(cond)) {                                                                  \
      std::cerr << "ATTACK FAIL " << __LINE__ << " " << #cond << "\n";             \
      g_fail++;                                                                     \
    } else {                                                                        \
      g_ok++;                                                                        \
    }                                                                               \
  } while (0)

int main(int argc, char** argv) {
  std::string host = "127.0.0.1";
  int port = 8080;
  if (argc >= 2) host = argv[1];
  if (argc >= 3) port = std::stoi(argv[2]);

  httplib::Client cli(host, port);
  cli.set_connection_timeout(2, 0);
  cli.set_read_timeout(5, 0);

  auto health = cli.Get("/api/health");
  if (!health || health->status != 200) {
    std::cerr << "server not reachable at " << host << ":" << port << "\n";
    return 2;
  }

  auto demo = cli.Post("/api/demo/start", "{}", "application/json");
  CHECK(demo && demo->status == 200);

  auto bad = cli.Post("/api/rooms/FENZHI/action", "not-json", "application/json");
  CHECK(bad && bad->status == 400);

  json join = {{"type", "join"},
               {"role", "student"},
               {"name", "攻击者"},
               {"client_id", "atk-1"}};
  auto j1 = cli.Post("/api/rooms/FENZHI/action", join.dump(), "application/json");
  CHECK(j1 && j1->status == 200);

  json steal = {{"type", "push_quiz"}, {"actor_id", "atk-1"}, {"quiz_id", "q1"}};
  auto s1 = cli.Post("/api/rooms/FENZHI/action", steal.dump(), "application/json");
  CHECK(s1);
  auto sj = json::parse(s1->body);
  CHECK(sj["ok"] == false);

  json lockish = {{"type", "answer"},
                  {"actor_id", "atk-1"},
                  {"answer", {{"option_id", "a"}}}};
  auto a0 = cli.Post("/api/rooms/FENZHI/action", lockish.dump(), "application/json");
  CHECK(a0);
  auto aj = json::parse(a0->body);
  if (aj["ok"] == true) {
    auto a1 = cli.Post("/api/rooms/FENZHI/action", lockish.dump(), "application/json");
    auto a1j = json::parse(a1->body);
    CHECK(a1j["ok"] == false);
  } else {
    CHECK(aj["error"].get<std::string>() == "quiz_not_open" ||
          aj["error"].get<std::string>() == "already_answered");
  }

  for (int i = 0; i < 80; ++i) {
    json d = {{"type", "danmaku"},
              {"actor_id", "atk-1"},
              {"text", "burst-分治-" + std::to_string(i)}};
    auto r = cli.Post("/api/rooms/FENZHI/action", d.dump(), "application/json");
    CHECK(r && r->status == 200);
  }

  auto ghost = cli.Post("/api/rooms/NOPE01/action", join.dump(), "application/json");
  CHECK(ghost && ghost->status == 404);

  std::cout << "attack passed " << g_ok << " failed " << g_fail << "\n";
  return g_fail ? 1 : 0;
}
