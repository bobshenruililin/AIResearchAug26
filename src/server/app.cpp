#include "server/app.hpp"

#include "engine/classroom.hpp"

#include "httplib.h"
#include "json.hpp"

#include <sqlite3.h>

#include <atomic>
#include <chrono>
#include <csignal>
#include <fstream>
#include <iostream>
#include <memory>
#include <mutex>
#include <sstream>
#include <thread>
#include <unordered_map>
#include <unistd.h>
#include <limits.h>

namespace storm {
namespace {

using json = nlohmann::json;

std::atomic<bool> g_stop{false};

void on_sig(int) { g_stop = true; }

std::string read_all(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) return {};
  std::ostringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

struct Room {
  std::mutex mu;
  std::condition_variable cv;
  Classroom room;
  std::mt19937 rng;
  explicit Room(Classroom c, uint32_t seed) : room(std::move(c)), rng(seed) {}
};

class Hub {
public:
  sqlite3* db = nullptr;
  std::mutex mu;
  std::unordered_map<std::string, std::shared_ptr<Room>> rooms;

  explicit Hub(const std::string& db_path) {
    if (sqlite3_open(db_path.c_str(), &db) != SQLITE_OK) {
      std::cerr << "sqlite open failed, continuing without persist\n";
      db = nullptr;
      return;
    }
    char* err = nullptr;
    sqlite3_exec(db,
                 "CREATE TABLE IF NOT EXISTS events ("
                 "room TEXT NOT NULL, seq INTEGER NOT NULL, t_ms INTEGER,"
                 "type TEXT, payload TEXT, PRIMARY KEY(room, seq));",
                 nullptr, nullptr, &err);
    sqlite3_free(err);
  }
  ~Hub() {
    if (db) sqlite3_close(db);
  }

  std::shared_ptr<Room> get(const std::string& code) {
    std::lock_guard<std::mutex> lk(mu);
    auto it = rooms.find(code);
    if (it == rooms.end()) return nullptr;
    return it->second;
  }

  std::shared_ptr<Room> ensure_demo() {
    std::lock_guard<std::mutex> lk(mu);
    auto it = rooms.find("FENZHI");
    if (it != rooms.end()) return it->second;
    auto r = std::make_shared<Room>(Classroom::demo(20260829), 20260829);
    rooms["FENZHI"] = r;
    return r;
  }

  std::shared_ptr<Room> create(const std::string& title_zh, const std::string& title_en) {
    std::lock_guard<std::mutex> lk(mu);
    std::mt19937 rng(static_cast<uint32_t>(
        std::chrono::steady_clock::now().time_since_epoch().count()));
    std::string code;
    for (int i = 0; i < 8; ++i) {
      code = random_room_code(rng);
      if (!rooms.count(code)) break;
    }
    auto r = std::make_shared<Room>(Classroom::blank(code, title_zh, title_en, rng()), rng());
    rooms[code] = r;
    return r;
  }

  void persist(const std::string& code, const Event& e) {
    if (!db) return;
    sqlite3_stmt* st = nullptr;
    sqlite3_prepare_v2(
        db, "INSERT OR REPLACE INTO events(room,seq,t_ms,type,payload) VALUES(?,?,?,?,?)",
        -1, &st, nullptr);
    sqlite3_bind_text(st, 1, code.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int64(st, 2, e.seq);
    sqlite3_bind_int64(st, 3, e.t_ms);
    sqlite3_bind_text(st, 4, e.type.c_str(), -1, SQLITE_TRANSIENT);
    auto dump = e.payload.dump();
    sqlite3_bind_text(st, 5, dump.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_step(st);
    sqlite3_finalize(st);
  }

  std::vector<std::shared_ptr<Room>> all() {
    std::lock_guard<std::mutex> lk(mu);
    std::vector<std::shared_ptr<Room>> out;
    for (auto& kv : rooms) out.push_back(kv.second);
    return out;
  }
};

void cors(httplib::Response& res) {
  res.set_header("Access-Control-Allow-Origin", "*");
  res.set_header("Access-Control-Allow-Headers", "Content-Type, X-Storm-Actor");
  res.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
}

void json_res(httplib::Response& res, const json& j, int status = 200) {
  cors(res);
  res.status = status;
  res.set_content(j.dump(), "application/json; charset=utf-8");
}

void serve_html(httplib::Response& res, const std::string& web, const std::string& name) {
  auto body = read_all(web + "/" + name);
  cors(res);
  if (body.empty()) {
    res.status = 404;
    res.set_content("missing " + name, "text/plain");
    return;
  }
  res.set_content(body, "text/html; charset=utf-8");
}

}  // namespace

int run_server(const std::string& web_root, const std::string& data_dir, const std::string& db_path,
               const std::string& host, int port, bool seed_demo) {
  (void)data_dir;
  Hub hub(db_path);
  if (seed_demo) hub.ensure_demo();

  std::thread director([&] {
    int64_t step = 0;
    while (!g_stop) {
      std::this_thread::sleep_for(std::chrono::milliseconds(160));
      auto rooms = hub.all();
      auto now = std::chrono::duration_cast<std::chrono::milliseconds>(
                     std::chrono::system_clock::now().time_since_epoch())
                     .count();
      for (auto& rm : rooms) {
        std::lock_guard<std::mutex> lk(rm->mu);
        bool changed = false;
        if (rm->room.tick(now)) {
          changed = true;
          if (!rm->room.events().empty()) hub.persist(rm->room.code(), rm->room.events().back());
        }
        if (rm->room.bots_enabled()) {
          std::uniform_int_distribution<int> how(1, 3);
          int n = how(rm->rng);
          for (int i = 0; i < n; ++i) {
            const auto& st = rm->room.students();
            if (st.empty()) break;
            std::uniform_int_distribution<size_t> pick(0, st.size() - 1);
            const auto& who = st[pick(rm->rng)];
            if (!who.bot) continue;
            json act = rm->room.suggest_bot_action(who.id, rm->rng, now + step);
            if (act.is_object() && act.contains("type")) {
              auto before = rm->room.seq();
              rm->room.apply(act, now + step);
              if (rm->room.seq() > before) {
                changed = true;
                if (!rm->room.events().empty())
                  hub.persist(rm->room.code(), rm->room.events().back());
              }
            }
          }
        }
        if (changed) rm->cv.notify_all();
      }
      step += 1;
    }
  });

  httplib::Server svr;
  svr.set_read_timeout(std::chrono::seconds(3600));
  svr.set_write_timeout(std::chrono::seconds(30));
  svr.set_keep_alive_max_count(1000);
  svr.new_task_queue = [] { return new httplib::ThreadPool(48); };

  svr.Options("/.*", [&](const httplib::Request&, httplib::Response& res) {
    cors(res);
    res.status = 204;
  });

  svr.Get("/api/health", [&](const httplib::Request&, httplib::Response& res) {
    json_res(res, {{"ok", true}, {"name", "stormclass"}, {"version", "1.0.0"}});
  });

  svr.Post("/api/rooms", [&](const httplib::Request& req, httplib::Response& res) {
    json body = json::object();
    if (!req.body.empty()) {
      try {
        body = json::parse(req.body);
      } catch (...) {
        json_res(res, {{"ok", false}, {"error", "bad_json"}}, 400);
        return;
      }
    }
    auto title_zh = body.value("title_zh", "新课堂");
    auto title_en = body.value("title_en", "New classroom");
    auto rm = hub.create(title_zh, title_en);
    json_res(res, {{"ok", true}, {"code", rm->room.code()}});
  });

  svr.Post("/api/demo/start", [&](const httplib::Request&, httplib::Response& res) {
    auto rm = hub.ensure_demo();
    json_res(res, {{"ok", true}, {"code", rm->room.code()}});
  });

  auto require_room = [&](const httplib::Request& req) -> std::shared_ptr<Room> {
    auto code = req.path_params.at("code");
    auto rm = hub.get(code);
    if (!rm && code == "FENZHI") rm = hub.ensure_demo();
    return rm;
  };

  svr.Get("/api/rooms/:code", [&](const httplib::Request& req, httplib::Response& res) {
    auto rm = require_room(req);
    if (!rm) {
      json_res(res, {{"ok", false}, {"error", "no_room"}}, 404);
      return;
    }
    auto viewer = req.get_param_value("viewer");
    auto locale = req.get_param_value("locale");
    if (locale.empty()) locale = "zh";
    std::lock_guard<std::mutex> lk(rm->mu);
    json_res(res, {{"ok", true}, {"room", rm->room.snapshot(viewer, locale)}});
  });

  svr.Get("/api/rooms/:code/report", [&](const httplib::Request& req, httplib::Response& res) {
    auto rm = require_room(req);
    if (!rm) {
      json_res(res, {{"ok", false}, {"error", "no_room"}}, 404);
      return;
    }
    std::lock_guard<std::mutex> lk(rm->mu);
    json_res(res, {{"ok", true}, {"report", rm->room.report()}});
  });

  svr.Get("/api/rooms/:code/events", [&](const httplib::Request& req, httplib::Response& res) {
    auto rm = require_room(req);
    if (!rm) {
      json_res(res, {{"ok", false}, {"error", "no_room"}}, 404);
      return;
    }
    int64_t after = 0;
    if (req.has_param("after")) after = std::stoll(req.get_param_value("after"));
    std::lock_guard<std::mutex> lk(rm->mu);
    json arr = json::array();
    for (const auto& e : rm->room.events()) {
      if (e.seq > after)
        arr.push_back({{"seq", e.seq}, {"t_ms", e.t_ms}, {"type", e.type}, {"payload", e.payload}});
    }
    json_res(res, {{"ok", true}, {"events", arr}, {"seq", rm->room.seq()}});
  });

  svr.Post("/api/rooms/:code/action", [&](const httplib::Request& req, httplib::Response& res) {
    auto rm = require_room(req);
    if (!rm) {
      json_res(res, {{"ok", false}, {"error", "no_room"}}, 404);
      return;
    }
    json body;
    try {
      body = json::parse(req.body.empty() ? "{}" : req.body);
    } catch (...) {
      json_res(res, {{"ok", false}, {"error", "bad_json"}}, 400);
      return;
    }
    if (req.has_header("X-Storm-Actor") && !body.contains("actor_id")) {
      body["actor_id"] = req.get_header_value("X-Storm-Actor");
    }
    std::lock_guard<std::mutex> lk(rm->mu);
    auto now = std::chrono::duration_cast<std::chrono::milliseconds>(
                   std::chrono::system_clock::now().time_since_epoch())
                   .count();
    auto result = rm->room.apply(body, now);
    if (result.ok && !rm->room.events().empty()) hub.persist(rm->room.code(), rm->room.events().back());
    rm->cv.notify_all();
    json_res(res,
             {{"ok", result.ok},
              {"error", result.error},
              {"reply", result.reply},
              {"seq", rm->room.seq()},
              {"room", rm->room.snapshot(body.value("actor_id", ""),
                                          body.value("locale", "zh"))}},
             result.ok ? 200 : 400);
  });

  svr.Get("/api/rooms/:code/stream", [&](const httplib::Request& req, httplib::Response& res) {
    auto rm = require_room(req);
    if (!rm) {
      json_res(res, {{"ok", false}, {"error", "no_room"}}, 404);
      return;
    }
    int64_t after = 0;
    if (req.has_param("after")) {
      try {
        after = std::stoll(req.get_param_value("after"));
      } catch (...) {
        after = 0;
      }
    }
    auto viewer = req.get_param_value("viewer");
    auto locale = req.get_param_value("locale");
    if (locale.empty()) locale = "zh";
    cors(res);
    res.set_header("Cache-Control", "no-cache");
    res.set_header("Connection", "keep-alive");
    res.set_header("X-Accel-Buffering", "no");
    auto held = rm;
    res.set_chunked_content_provider(
        "text/event-stream; charset=utf-8",
        [held, after, viewer, locale](size_t, httplib::DataSink& sink) {
          int64_t last = after;
          bool first = true;
          while (!g_stop && sink.is_writable()) {
            json snap;
            json evs = json::array();
            {
              std::unique_lock<std::mutex> lk(held->mu);
              if (!first) {
                held->cv.wait_for(lk, std::chrono::seconds(12));
              }
              snap = held->room.snapshot(viewer, locale);
              if (!first) {
                for (const auto& e : held->room.events()) {
                  if (e.seq > last) {
                    evs.push_back({{"seq", e.seq},
                                   {"t_ms", e.t_ms},
                                   {"type", e.type},
                                   {"payload", e.payload}});
                    last = e.seq;
                  }
                }
              } else {
                last = held->room.seq();
              }
              first = false;
            }
            json payload = {{"events", evs}, {"room", snap}};
            std::string msg = "event: state\ndata: " + payload.dump() + "\n\n";
            if (!sink.write(msg.data(), msg.size())) return false;
          }
          return true;
        });
  });

  svr.Get("/", [&](const httplib::Request&, httplib::Response& res) {
    serve_html(res, web_root, "index.html");
  });
  svr.Get("/demo", [&](const httplib::Request&, httplib::Response& res) {
    hub.ensure_demo();
    serve_html(res, web_root, "demo.html");
  });
  svr.Get("/t/:code", [&](const httplib::Request&, httplib::Response& res) {
    serve_html(res, web_root, "teacher.html");
  });
  svr.Get("/s/:code", [&](const httplib::Request&, httplib::Response& res) {
    serve_html(res, web_root, "student.html");
  });
  svr.Get("/p/:code", [&](const httplib::Request&, httplib::Response& res) {
    serve_html(res, web_root, "project.html");
  });
  svr.Get("/report/:code", [&](const httplib::Request&, httplib::Response& res) {
    serve_html(res, web_root, "report.html");
  });

  svr.set_mount_point("/static", web_root);

  std::signal(SIGINT, on_sig);
  std::signal(SIGTERM, on_sig);

  std::cout << "StormClass 暴雨课堂  http://" << host << ":" << port << "\n"
            << "  demo     /demo\n"
            << "  teacher  /t/FENZHI\n"
            << "  student  /s/FENZHI\n"
            << "  project  /p/FENZHI\n"
            << "  report   /report/FENZHI\n";

  std::thread stopper([&] {
    while (!g_stop) std::this_thread::sleep_for(std::chrono::milliseconds(200));
    svr.stop();
  });

  bool ok = svr.listen(host.c_str(), port);
  g_stop = true;
  if (director.joinable()) director.join();
  if (stopper.joinable()) stopper.join();
  if (!ok) {
    std::cerr << "listen failed on " << host << ":" << port << "\n";
    return 1;
  }
  return 0;
}

}  // namespace storm
