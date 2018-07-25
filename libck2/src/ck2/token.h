#ifndef __LIBCK2_TOKEN_H__
#define __LIBCK2_TOKEN_H__

#include "common.h"
#include "Location.h"


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
    Loc   _loc;

public:
    static const char* TYPE_MAP[];
    const char* type_name() const noexcept { return TYPE_MAP[_type]; }

    token(uint type_ = END) : _type(type_), _text_len(0), _text(nullptr) {}

    uint type()       const noexcept { return _type; }
    void type(uint t)       noexcept { _type = t; }

    uint text_len()       const noexcept { return _text_len; }
    void text_len(uint n)       noexcept { _text_len = n; }

    const auto& loc()             const noexcept { return _loc; }
    void        loc(const Loc& l)       noexcept { _loc = l; }

    const char* text()                const noexcept { return _text; }
    char*       text()                      noexcept { return _text; }
    void        text(char* p, uint n)       noexcept { _text = p; _text_len = n; }
};


_CK2_NAMESPACE_END;
#endif
