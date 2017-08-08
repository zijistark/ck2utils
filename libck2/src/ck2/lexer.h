// -*- c++ -*-

#pragma once
#include "common.h"
#include "scanner.h"
#include "token.h"
#include "error.h"

#include "file_location.h"

#include <cstdio>
#include <cstring>
#include <string>
#include <memory>
#include <algorithm>
#include <boost/filesystem.hpp>


_CK2_NAMESPACE_BEGIN;


namespace fs = boost::filesystem;


template<const size_t TokenLookahead = 1>
class lexer {
    // if ever have the impetus: if the user were to supply TokenLookahead == 0, then we could specialize the
    // implementation to avoid any token text copying at all and pass that straight from the scanner to the consumer.
    static_assert(TokenLookahead >= 1, "lexer is designed for at least 1 token of lookahead (no-lookahead version should be specialized with zero-copy)");
    static const size_t TokenQueueSize = TokenLookahead + 2;

    using unique_file_ptr = std::unique_ptr<std::FILE, int (*)(std::FILE *)>;
    unique_file_ptr _f;
    const char* _pathname;

    enum {
        NORMAL,
        FAILED,
        DONE,
    } _state;

    uint  _head_idx; // index of head of token queue (i.e., next to be handed to user); not nec. to store it but simple
    uint  _tail_idx; // index of tail of currently queued tokens (i.e., last slot which we populated with a new token)
    token _tq[TokenQueueSize];

    void read_token_into(token& t); // read from input into given object (can mutate _state); used by enqueue_token()
    void enqueue_token(); // dependent upon _state, enqueue a token (always enqueues something); used by next() and ctor

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

    // return and dequeue next token (and usually enqueue another lookahead token from input file)
    // NOTE: once we have produced our first END token, we will just keep returning an END token ad infinitum if the
    // caller keeps asking us for tokens. [basically, the token queue is always full, if even only with END tokens.]
    token& next();

    // peek into the token lookahead queue by logical index, Position, of token. position 0 is simply the next token
    // were we to call next(...), and position 1 would be second to next in the input stream (the 1st lookahead token),
    // and so on. if the input stream has ended (EOF or unmatched text) sometime before the lookahead token at which
    // we're peeking, we'll just see an END token -- no harm, no foul.
    template<const uint Position>
    token& peek() noexcept {
        static_assert(Position <= TokenLookahead, "cannot peek at position greater than lexer's configured number of lookahead tokens");
        return _tq[ (_head_idx + Position) % TokenQueueSize ];
    }
};


template<const size_t TokenLookahead>
lexer<TokenLookahead>::lexer(const char* pathname)
    : _f( std::fopen(pathname, "rb"), std::fclose ),
      _pathname(pathname),
      _state(NORMAL),
      _head_idx(0),
      _tail_idx(0) {

    if (_f.get() == nullptr)
        throw va_error("Could not open file: %s", pathname);

    yyin = _f.get();
    yylineno = 1;

    // pre-fill token queue [fully-constructed lexer object invariant: token queue is always full of valid tokens]
    for (size_t i = 0; i <= TokenLookahead; ++i) enqueue_token();
}


template<const size_t TokenLookahead>
void lexer<TokenLookahead>::read_token_into(token& t) {
    t.type( yylex() );
    t.location( floc{ _pathname, static_cast<uint>(yylineno) } );

    if (t.type() == token::END) {
        _state = DONE;
        _f.reset();
        reset_scanner();
        return;
    }

    if (t.type() == token::FAIL)
        _state = FAILED;

    auto p_txt = yytext;
    auto len   = yyleng;

    if (t.type() == token::QSTR || t.type() == token::QDATE) {
        p_txt[ len -= 1 ] = '\0'; // ending quote
        // starting quote
        *p_txt++ = '\0';
        --len;
    }

    /* if found, strip any trailing '\n' and then same for '\r' (covers all possible mixed EOL cases correctly) */
    if (len > 0 && p_txt[ len-1 ] == '\n') p_txt[ len -= 1 ] = '\0';
    if (len > 0 && p_txt[ len-1 ] == '\r') p_txt[ len -= 1 ] = '\0';

    mdh_strncpy<token::TEXT_MAX_SZ>(t.text(), p_txt, len + 1);
}

template<const size_t TokenLookahead>
void lexer<TokenLookahead>::enqueue_token() {
    auto next_idx = (_tail_idx + 1) % TokenQueueSize;
    token& next_tok = _tq[next_idx];
    token& tail_tok = _tq[_tail_idx];

    _tail_idx = next_idx;

    if (_state == FAILED)
        _state = DONE;

    if (_state == DONE) {
        next_tok.type( token::END );
        next_tok.location( tail_tok.location() );
        return;
    }

    // _state == NORMAL
    read_token_into(next_tok);
}


template<const size_t TokenLookahead>
token& lexer<TokenLookahead>::next() {
    enqueue_token();
    token& head_tok = _tq[_head_idx];
    _head_idx = (_head_idx + 1) % TokenQueueSize;
    return head_tok;
}


_CK2_NAMESPACE_END;
