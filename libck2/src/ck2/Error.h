#ifndef __LIBCK2_ERROR_H__
#define __LIBCK2_ERROR_H__


#include "fmt/format.h"
#include <string_view>
#include <exception>
#include <stdexcept>


_CK2_NAMESPACE_BEGIN;


class Error : public std::runtime_error {
    using Base = std::runtime_error;

public:
    Error(const std::string& msg) : Base(msg) {}

    // Error(const char* format, fmt::format_args args)
    //     : std::runtime_error( fmt::vformat(format, args) ) {}

    template<typename... Args>
    Error(std::string_view format, const Args& ...args)
        : Base( fmt::vformat(format, fmt::make_format_args(args...) ) ) {}
};


_CK2_NAMESPACE_END;
#endif
