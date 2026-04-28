cmake_minimum_required(VERSION 3.22)
project(hybridfontzygisk LANGUAGES CXX)

add_library(hybridfontzygisk SHARED src/main.cpp)

target_compile_features(hybridfontzygisk PRIVATE cxx_std_20)
target_compile_options(hybridfontzygisk PRIVATE -Wall -Wextra -Werror -fvisibility=hidden)
target_include_directories(hybridfontzygisk PRIVATE "${ZYGISK_API_DIR}")
target_link_libraries(hybridfontzygisk log)
