#pragma once

#include <string>

namespace storm {

int run_server(const std::string& web_root, const std::string& data_dir, const std::string& db_path,
               const std::string& host, int port, bool seed_demo);

}  // namespace storm
