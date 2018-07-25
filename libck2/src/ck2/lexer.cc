#include "Location.h"
#include "token.h"
#include "lexer.h"


_CK2_NAMESPACE_BEGIN;


bool lexer::read_token_into(token& t, size_t max_copy_sz)
{
    bool ret = true;

    t.type( yylex() );
    t.loc( Loc{ static_cast<uint>(yylineno) } );

    if (t.type() == token::END) {
        t.text(nullptr, 0);
        ret = false;
        // reset the flex scanner and close the underlying file early (otherwise, it'd be at object destruction time)
        _f.reset();
        reset_scanner();
        return ret;
    }

    if (t.type() == token::FAIL)
        ret = false;

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

    if (max_copy_sz == 0)
        t.text(p_txt, len);
    else
        t.text_len(static_cast<uint>( mdh_strncpy(t.text(), max_copy_sz, p_txt, len + 1) ));

    return ret;
}

lexer::lexer(const fs::path& path)
: _f( std::fopen(path.generic_string().c_str(), "rb"), std::fclose ),
  _path(path)
{

    if (_f.get() == nullptr)
        throw Error("Failed to open file: {}: {}", strerror(errno), path.generic_string());

    yyin = _f.get();
    yylineno = 1;
}


_CK2_NAMESPACE_END;
