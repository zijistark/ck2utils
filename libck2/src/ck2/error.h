// -*- c++ -*-

#pragma once

#include "common.h"
#include "file_location.h"

#include <exception>
#include <stdexcept>
#include <cstdio>
#include <cstdarg>
#include <cstdlib>


_CK2_NAMESPACE_BEGIN


class va_error : public std::exception {
    char msg[1024];

public:
    va_error() = delete;

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


class parse_error : public std::exception {};


class va_parse_error : public parse_error {
    char msg[1024];

public:
    va_parse_error() = delete;

    explicit va_parse_error(const floc& fl, const char* format, ...) {
        auto buf_sz_left = sizeof(msg);
        va_list vl;
        va_start(vl, format);
        auto len = vsnprintf(&msg[0], buf_sz_left, format, vl);
        va_end(vl);

        assert(len >= 0);
        buf_sz_left -= len;

        snprintf(&msg[len], buf_sz_left, " in '%s' at line %u", fl.pathname(), fl.line());
    }

    const char* what() const noexcept {
        return msg;
    }

    ~va_parse_error() noexcept {}
};



_CK2_NAMESPACE_END
