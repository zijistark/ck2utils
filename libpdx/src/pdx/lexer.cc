
#include <cstdio>
#include "lexer.h"
#include "scanner.h"
#include "token.h"
#include "error.h"


_PDX_NAMESPACE_BEGIN


lexer::lexer(const char* pathname)
    : _f( std::fopen(pathname, "rb"), std::fclose ),
      _location(pathname, 0) {

    if (_f.get() == nullptr)
        throw va_error("Could not open file: %s", pathname);

    yyin = _f.get();
    yylineno = 1;
}


lexer::~lexer() noexcept {
    yyin = nullptr;
    yylineno = 0;
    yyrestart(yyin);
}


bool lexer::next(token* p_tok) {
    uint type;

    if (( type = yylex() ) == 0) {
        /* EOF, so close our filehandle, and signal EOF */
        _f.reset();
        _location._line = yylineno;
        p_tok->type = token::END;
        p_tok->text = 0;
        yyin = nullptr;
        yylineno = 0;
        yyrestart(yyin);
        return false;
    }

    /* yytext contains token,
       yyleng contains token length,
       yylineno contains line number,
       type contains token ID */

    _location._line = yylineno;
    p_tok->type = type;

    if (type == token::QSTR || type == token::QDATE) {
        assert( yyleng >= 2 );

        /* trim quote characters from actual string */
        yytext[ yyleng-1 ] = '\0';
        p_tok->text = yytext + 1;

        return true;
    }
    else {
        p_tok->text = yytext;
    }

    /* if found, strip any trailing '\r' */

    if (yyleng > 0) {
        char* last = &yytext[ yyleng-1 ];

        if (*last == '\r')
            *last = '\0';
    }

    return true;
}



_PDX_NAMESPACE_END
