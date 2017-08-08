// -*- c++ -*-

#pragma once
#include "common.h"
#include "file_location.h"

_CK2_NAMESPACE_BEGIN;


class token {
    // size token text buffer so as to allow for 3 aligned 64-bit words (24 bytes) to be associated with it. thus,
    // sizeof(token) probably won't exceed and probably will be exactly 1024. with 2 tokens of lookahead, that'll be a
    // perfect 4K page of RAM for the lexer's token queue (queue size is 2 + num of lookahead tokens). amusingly, this
    // also means that the max token length is 999 characters.
public:
    static const size_t TEXT_MAX_SZ = 1000;
    static const size_t TEXT_MAX_LEN = TEXT_MAX_SZ - 1;

    /* token type identifier constants, sequentially defined starting
       from EOF and ending with the FAIL token */
    static const uint END      = 0;
    static const uint INTEGER  = 1;  // integer string sequence
    static const uint OPERATOR = 2;  // =
    static const uint OPEN     = 3;  // {
    static const uint CLOSE    = 4;  // }
    static const uint STR      = 5;  // "bareword" style string
    static const uint QSTR     = 6;  // quoted string
    static const uint DATE     = 7;  // date string of the form 867.1.1, loosely
    static const uint QDATE    = 8;  // quoted date
    static const uint COMMENT  = 9;  // hash-style comment (starts with '#')
    static const uint DECIMAL  = 10;
    static const uint FAIL     = 11; // anything the ruleset couldn't match

protected:
    uint _type;
    floc _loc;
    char _text[TEXT_MAX_SZ];

public:
    static const char* TYPE_MAP[];
    const char* type_name() const noexcept { return TYPE_MAP[_type]; }

    token(uint type = END) : _type(type) { _text[0] = '\0'; }

    token(uint type, const char* text, size_t text_len = SIZE_MAX) : _type(type) {
        if (text_len == SIZE_MAX) text_len = strlen(text);
        mdh_strncpy<TEXT_MAX_SZ>(&_text[0], text, text_len + 1);
    }

    uint type()              const noexcept { return _type; }
    void type(uint new_type)       noexcept { _type = new_type; }

    const file_location& location()                const noexcept { return _loc; }
    void                 location(const floc& loc)       noexcept { _loc = loc; }

    char const* text() const noexcept { return &_text[0]; }
    char*       text()       noexcept { return &_text[0]; }
};


_CK2_NAMESPACE_END;
