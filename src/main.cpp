#include "server/app.hpp"

#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <unistd.h>
#include <limits.h>
#include <libgen.h>

static std::string exe_dir() {
  char buf[PATH_MAX];
  ssize_t n = readlink("/proc/self/exe", buf, sizeof(buf) - 1);
  if (n <= 0) return ".";
  buf[n] = 0;
  char tmp[PATH_MAX];
  std::snprintf(tmp, sizeof(tmp), "%s", buf);
  char* d = dirname(tmp);
  return std::string(d);
}

int main(int argc, char** argv) {
  std::string host = "0.0.0.0";
  int port = 8080;
  bool demo = true;
  std::string root = exe_dir();
  std::string web = root + "/web";
  std::string data = root + "/data";
  std::string db = root + "/stormclass.db";

  for (int i = 1; i < argc; ++i) {
    std::string a = argv[i];
    if ((a == "--port" || a == "-p") && i + 1 < argc) port = std::stoi(argv[++i]);
    else if ((a == "--host") && i + 1 < argc) host = argv[++i];
    else if (a == "--no-demo") demo = false;
    else if (a == "--demo") demo = true;
    else if ((a == "--web") && i + 1 < argc) web = argv[++i];
    else if ((a == "--db") && i + 1 < argc) db = argv[++i];
    else if (a == "--help" || a == "-h") {
      std::cout << "stormclass [--port 8080] [--host 0.0.0.0] [--web DIR] [--no-demo]\n";
      return 0;
    }
  }

  auto exists = [](const std::string& p) {
    return access((p + "/index.html").c_str(), R_OK) == 0;
  };
  if (!exists(web)) {
    if (exists("./web")) web = "./web";
    else if (exists("../web")) web = "../web";
  }

  return storm::run_server(web, data, db, host, port, demo);
}
