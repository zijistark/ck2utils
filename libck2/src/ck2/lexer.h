// -*- c++ -*-

#pragma once
#include "common.h"
#include "scanner.h"
#include "token.h"
#include "error.h"

#include "file_location.h"

#include <cstdio>
#include <string>
#include <memory>
#include <algorithm>
#include <boost/filesystem.hpp>


_CK2_NAMESPACE_BEGIN;


namespace fs = boost::filesystem;


class lexer {
    using unique_file_ptr = std::unique_ptr<std::FILE, int (*)(std::FILE *)>;

    unique_file_ptr _f;
    const char*     _pathname;

    void reset_scanner() {
        yyin = nullptr;
        yylineno = 0;
        yyrestart(yyin);
    }

protected:
    const char* pathname() const noexcept { return _pathname; }

public:
    lexer() = delete;
    ~lexer() noexcept { reset_scanner(); }
    lexer(const char* path);
    lexer(const std::string& path) : lexer(path.c_str()) {}
    lexer(const fs::path& path) : lexer(path.string().c_str()) {}

    // read a new token from the input into t. if max_copy_sz is nonzero, actually copy the token text buffer (capped by
    // this amount) into the token object's preexisting buffer. otherwise, when max_copy_sz == 0, simply swap the token
    // text buffers (zerocopy). returns false when the read token signals the end of input and true otherwise.
    bool read_token_into(token&, size_t max_copy_sz = 0);
};


_CK2_NAMESPACE_END;
