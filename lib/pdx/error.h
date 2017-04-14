// -*- c++ -*-

#pragma once

#include <exception>
#include <stdexcept>
#include <cstdio>
#include <cstdarg>
#include <cstdlib>

class va_error : public std::exception {
    char msg[512];

public:
    explicit va_error(const char* format, ...) {
        va_list vl;
        va_start(vl, format);
        vsnprintf(&msg[0], sizeof(msg), format, vl);
        va_end(vl);
    }

    const char* what() const noexcept {
        return msg;
    }

    ~va_error() noexcept {}
};
