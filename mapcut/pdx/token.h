// -*- c++ -*-

#pragma once
#include "pdx_common.h"


_PDX_NAMESPACE_BEGIN


struct token {
    uint type;
    char* text;

    /* token type identifier constants, sequentially defined starting
       from EOF and ending with the FAIL token */
    static const uint END     = 0;
    static const uint INTEGER = 1;  // integer string sequence
    static const uint EQ      = 2;  // =
    static const uint OPEN    = 3;  // {
    static const uint CLOSE   = 4;  // }
    static const uint STR     = 5;  // "bareword" style string
    static const uint QSTR    = 6;  // quoted string
    static const uint DATE    = 7;  // date string of the form 867.1.1, loosely
    static const uint QDATE   = 8;  // quoted date
    static const uint COMMENT = 9;  // hash-style comment (starts with '#')
    static const uint DECIMAL = 10;
    static const uint FAIL    = 11; // anything the ruleset couldn't match

    static const char* TYPE_MAP[];

    const char* type_name() const { return TYPE_MAP[type]; }

    token() {}
    token(uint _type, char* _text) : type(_type), text(_text) {}
};


_PDX_NAMESPACE_END
