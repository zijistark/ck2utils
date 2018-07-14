#ifndef __LIBCK2_LEXER_H__
#define __LIBCK2_LEXER_H__

#include "common.h"
#include "scanner.h"
#include "filesystem.h"
#include <memory>
#include <cstdio>


_CK2_NAMESPACE_BEGIN;


class token;

class lexer {
    using uniq_file_ptr = std::unique_ptr<std::FILE, int (*)(std::FILE *)>;

    uniq_file_ptr _f;
    fs::path      _path;

    void reset_scanner() {
        yyin = nullptr;
        yylineno = 0;
        yyrestart(yyin);
    }

protected:
    const fs::path& path() const noexcept { return _path; }

public:
    lexer() = delete;
    ~lexer() noexcept { reset_scanner(); }
    lexer(const fs::path& path);

    // read a new token from the input into t. if max_copy_sz is nonzero, actually copy the token text buffer (capped by
    // this amount) into the token object's preexisting buffer. otherwise, when max_copy_sz == 0, simply swap the token
    // text buffers (zerocopy). returns false when the read token signals the end of input and true otherwise.
    bool read_token_into(token&, size_t max_copy_sz = 0);
};


_CK2_NAMESPACE_END;
#endif
