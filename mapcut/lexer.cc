
#include <cstdio>
#include <cassert>
#include "lexer.h"
#include "scanner.h"
#include "token.h"
#include "error.h"

lexer::lexer(const char* filename)
  : _f(fopen(filename, "rb")),
    _line(0),
    _filename(filename) {

  if (!_f)
    throw va_error("Could not open file: %s\n", filename);

  yyin = _f;
  yylineno = 1;
}


bool lexer::next(token* p_tok) {

  uint type;

  if (( type = yylex() ) == 0) {
    /* EOF, so close our filehandle, and signal EOF */
    fclose(_f);
    _f = 0;
    _line = yylineno;
    p_tok->type = token::END;
    p_tok->text = 0;
    return false;
  }

  /* yytext contains token,
     yyleng contains token length,
     yylineno contains line number,
     type contains token ID */

  _line = yylineno;
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

  if (type == token::COMMENT) {
    /* if found, strip any trailing '\r' */

    char* last = &yytext[ yyleng-1 ];

    if (*last == '\r')
      *last = '\0';
  }

  return true;
}
