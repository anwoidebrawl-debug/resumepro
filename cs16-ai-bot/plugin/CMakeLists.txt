cmake_minimum_required(VERSION 3.16)
project(neurbot_plugin VERSION 0.1.0 LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Platform detection
if(UNIX AND NOT APPLE)
    set(LINUX TRUE)
endif()

# Source files
set(NEURBOT_SOURCES
    src/neurbot_plugin.cpp
    src/perception.cpp
    src/action_executor.cpp
    src/ipc_bridge.cpp
    src/bot_manager.cpp
    src/navigation.cpp
)

set(NEURBOT_HEADERS
    include/neurbot_plugin.h
    include/perception.h
    include/action_executor.h
    include/ipc_bridge.h
    include/bot_manager.h
    include/navigation.h
    include/protocol.h
)

# Build shared library (MetaMod plugin)
add_library(neurbot SHARED ${NEURBOT_SOURCES} ${NEURBOT_HEADERS})

target_include_directories(neurbot PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/hlsdk
    ${CMAKE_CURRENT_SOURCE_DIR}/metamod
)

# Compiler flags
if(MSVC)
    target_compile_options(neurbot PRIVATE /W3 /O2)
    target_compile_definitions(neurbot PRIVATE WIN32 _WINDOWS)
else()
    target_compile_options(neurbot PRIVATE -Wall -Wextra -O2 -fno-exceptions)
    target_compile_definitions(neurbot PRIVATE LINUX _LINUX)
    target_link_libraries(neurbot PRIVATE rt pthread)
endif()

# Output name
if(LINUX)
    set_target_properties(neurbot PROPERTIES
        PREFIX ""
        SUFFIX "_i386.so"
        OUTPUT_NAME "neurbot_mm"
    )
else()
    set_target_properties(neurbot PROPERTIES
        OUTPUT_NAME "neurbot_mm"
    )
endif()

# Install
install(TARGETS neurbot DESTINATION lib)
