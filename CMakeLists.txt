cmake_minimum_required(VERSION 3.16)
if(NOT CMAKE_CXX_COMPILER AND EXISTS "/usr/bin/g++")
  set(CMAKE_CXX_COMPILER "/usr/bin/g++")
endif()
project(stormclass LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(STORMSAN "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE RelWithDebInfo)
endif()

find_package(Threads REQUIRED)
find_library(SQLITE3_LIB sqlite3 REQUIRED)

add_library(storm_engine STATIC
  src/engine/wordcloud.cpp
  src/engine/scoring.cpp
  src/engine/seed.cpp
  src/engine/classroom.cpp
)
target_include_directories(storm_engine PUBLIC
  ${CMAKE_SOURCE_DIR}/src
  ${CMAKE_SOURCE_DIR}/third_party
)
target_link_libraries(storm_engine PUBLIC ${SQLITE3_LIB} Threads::Threads)
target_compile_options(storm_engine PRIVATE -Wall -Wextra -Wpedantic -Wno-unused-parameter)

add_executable(stormclass
  src/server/app.cpp
  src/main.cpp
)
target_link_libraries(stormclass PRIVATE storm_engine)
target_compile_options(stormclass PRIVATE -Wall -Wextra -Wpedantic)

add_executable(stormclass_tests tests/test_engine.cpp)
target_link_libraries(stormclass_tests PRIVATE storm_engine)
target_compile_options(stormclass_tests PRIVATE -Wall -Wextra -Wpedantic)

add_executable(stormclass_attack tests/attack_client.cpp)
target_link_libraries(stormclass_attack PRIVATE storm_engine)
target_compile_options(stormclass_attack PRIVATE -Wall -Wextra -Wpedantic)

function(storm_sanitize tgt)
  if(STORMSAN)
    target_compile_options(${tgt} PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(${tgt} PRIVATE -fsanitize=address,undefined)
  endif()
endfunction()

storm_sanitize(storm_engine)
storm_sanitize(stormclass)
storm_sanitize(stormclass_tests)
storm_sanitize(stormclass_attack)

add_custom_command(TARGET stormclass POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/web $<TARGET_FILE_DIR:stormclass>/web
  COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/data $<TARGET_FILE_DIR:stormclass>/data
)

enable_testing()
add_test(NAME engine COMMAND stormclass_tests)
