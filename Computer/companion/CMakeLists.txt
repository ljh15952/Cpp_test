cmake_minimum_required(VERSION 3.20)
project(ApexFoundations VERSION 1.0.0 LANGUAGES CXX)

option(APEX_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
option(APEX_WARNINGS_AS_ERRORS "Treat warnings as errors" OFF)

add_library(apex_foundations
    src/Tiny8.cpp
    src/Expression.cpp
    src/Graph.cpp
    src/WalKv.cpp
)

target_include_directories(apex_foundations PUBLIC include)
target_compile_features(apex_foundations PUBLIC cxx_std_20)

if(MSVC)
    target_compile_options(apex_foundations PRIVATE /W4 /permissive-)
    if(APEX_WARNINGS_AS_ERRORS)
        target_compile_options(apex_foundations PRIVATE /WX)
    endif()
else()
    target_compile_options(apex_foundations PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
    if(APEX_WARNINGS_AS_ERRORS)
        target_compile_options(apex_foundations PRIVATE -Werror)
    endif()
    if(APEX_ENABLE_SANITIZERS)
        target_compile_options(apex_foundations PUBLIC -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(apex_foundations PUBLIC -fsanitize=address,undefined)
    endif()
endif()

add_executable(apex_labs apps/labs.cpp)
target_link_libraries(apex_labs PRIVATE apex_foundations)

add_executable(apex_tests tests/main.cpp)
target_link_libraries(apex_tests PRIVATE apex_foundations)

include(CTest)
if(BUILD_TESTING)
    add_test(NAME apex_tests COMMAND apex_tests)
endif()
