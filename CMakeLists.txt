cmake_minimum_required(VERSION 3.24)
project(cpp_game_client_companion LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(cppbook INTERFACE)
target_include_directories(cppbook INTERFACE include)

add_executable(book_self_test src/main.cpp)
target_link_libraries(book_self_test PRIVATE cppbook)

if(MSVC)
    target_compile_options(book_self_test PRIVATE /W4 /permissive-)
else()
    target_compile_options(book_self_test PRIVATE
        -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
endif()

enable_testing()
add_test(NAME book_self_test COMMAND book_self_test)

option(CPPBOOK_BUILD_UNSAFE_DEMOS "Build intentionally unsafe sanitizer demos" OFF)
if(CPPBOOK_BUILD_UNSAFE_DEMOS)
    add_executable(use_after_free_demo unsafe_demos/use_after_free.cpp)
    add_executable(vector_invalidation_demo unsafe_demos/vector_invalidation.cpp)
endif()
