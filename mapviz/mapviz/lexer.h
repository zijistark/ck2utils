// -*- c++ -*-

#ifndef _MDH_LEXER_H_
#define _MDH_LEXER_H_

#include <cstdio>
#include "scanner.h"

typedef unsigned int uint;
struct token;

class lexer {

  FILE* _f;

  /* position of last-lexed token */
  uint _line;
  const char* _filename;


public:

  lexer(const char* filename);

  lexer(FILE* f) : _f(f), _line(0), _filename("") {
    yyin = f;
    yylineno = 1;
  }

  ~lexer() {
    if (_f)
      fclose(_f);
  }

  bool next(token* p_tok);

  const char* filename() const { return _filename; }
  uint line() const { return _line; }
};


#endif
