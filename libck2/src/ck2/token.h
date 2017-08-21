// -*- c++ -*-

#pragma once
#include "common.h"
#include "file_location.h"

#include <limits>

_CK2_NAMESPACE_BEGIN;


class token {
public:
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
    static const uint DECIMAL  = 9;
    static const uint FAIL     = 10; // anything the ruleset couldn't match

protected:
    uint  _type;
    uint  _text_len;
    char* _text;
    floc  _loc;

public:
    static const char* TYPE_MAP[];
    const char* type_name() const noexcept { return TYPE_MAP[_type]; }

    token(uint type = END) : _type(type), _text_len(0), _text(nullptr) {}

    uint type()              const noexcept { return _type; }
    void type(uint new_type)       noexcept { _type = new_type; }

    uint text_len()             const noexcept { return _text_len; }
    void text_len(uint new_len)       noexcept { _text_len = new_len; }

    const file_location& location()                const noexcept { return _loc; }
    void                 location(const floc& loc)       noexcept { _loc = loc; }

    char const* text() const noexcept { return _text; }
    char*       text()       noexcept { return _text; }

    void text(char* new_text, uint new_len) noexcept { _text = new_text; _text_len = new_len; }
};


_CK2_NAMESPACE_END;
