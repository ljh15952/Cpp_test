cmake_minimum_required(VERSION 3.24)
project(AsterDx12Companion VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(ASTER_BUILD_TESTS "Build portable core tests" ON)
option(ASTER_BUILD_D3D12_TRIANGLE "Build Windows D3D12 triangle" ON)

add_library(aster_core
    src/Core/FrameGraph.cpp
    src/Core/JobSystem.cpp
)
target_include_directories(aster_core PUBLIC include)

if(MSVC)
    target_compile_options(aster_core PRIVATE /W4 /permissive- /EHsc)
else()
    target_compile_options(aster_core PRIVATE -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
endif()

if(ASTER_BUILD_TESTS)
    enable_testing()
    add_executable(aster_tests tests/CoreTests.cpp)
    target_link_libraries(aster_tests PRIVATE aster_core)
    add_test(NAME aster_tests COMMAND aster_tests)
endif()

if(WIN32 AND ASTER_BUILD_D3D12_TRIANGLE)
    add_executable(d3d12_triangle WIN32
        apps/D3D12Triangle/main.cpp
    )
    target_include_directories(d3d12_triangle PRIVATE include)
    target_compile_definitions(d3d12_triangle PRIVATE UNICODE _UNICODE NOMINMAX WIN32_LEAN_AND_MEAN)
    target_link_libraries(d3d12_triangle PRIVATE d3d12 dxgi d3dcompiler)
    if(MSVC)
        target_compile_options(d3d12_triangle PRIVATE /W4 /permissive- /EHsc)
    endif()
    add_custom_command(TARGET d3d12_triangle POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory "$<TARGET_FILE_DIR:d3d12_triangle>/shaders"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "${CMAKE_CURRENT_SOURCE_DIR}/shaders/Triangle.hlsl"
                "$<TARGET_FILE_DIR:d3d12_triangle>/shaders/Triangle.hlsl"
    )
endif()
