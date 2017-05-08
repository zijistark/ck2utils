// -*- c++ -*-

#pragma once
#include "pdx_common.h"

#include <cstdio>
#include <string>
#include <memory>
#include <boost/filesystem.hpp>

#include "file_location.h"


_PDX_NAMESPACE_BEGIN


namespace fs = boost::filesystem;
struct token;


class lexer {
    typedef std::unique_ptr<std::FILE, int (*)(std::FILE *)> unique_file_ptr;
    unique_file_ptr _f;

    /* position of last-lexed token */
    file_location _location;

public:
    lexer() = delete;
    ~lexer() noexcept;
    lexer(const char* path);
    lexer(const std::string& path) : lexer(path.c_str()) {}
    lexer(const fs::path& path) : lexer(path.string().c_str()) {}

    bool next(token* p_tok);

    const char* pathname() const noexcept { return _location.pathname(); }
    uint line() const noexcept { return _location.line(); }
    const file_location& location() const noexcept { return _location; }
};


_PDX_NAMESPACE_END
