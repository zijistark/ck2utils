// -*- c++ -*-

#ifndef _MDH_PDX_H_
#define _MDH_PDX_H_


#include <vector>
#include "lexer.h"
#include "token.h"
#include "error.h"

#include <cstring>

namespace pdx {

  struct block;
  struct list;

  struct obj {
    uint type;

    union {
      char* s;
      uint id;
      int i;
      block* p_block;
      list* p_list;
      struct {
        uint8_t r;
        uint8_t g;
        uint8_t b;
      } color;
    } data;

    static const uint STR     = 0;
    static const uint KEYWORD = 1;
    static const uint INT     = 2;
    static const uint DECIMAL = 3;
    static const uint DATE    = 4;
    static const uint COLOR   = 5;
    static const uint TITLE   = 6;
    static const uint BLOCK   = 7;
    static const uint LIST    = 8;

    obj() : type(STR) {}
  };

  struct stmt {
    obj key;
    obj val;

    bool key_eq(const char* s) {
      return (key.type == obj::STR
              && strcmp(key.data.s, s) == 0);
    }
  };

  struct plexer : public lexer {
    void next(token*, bool eof_ok = false);
    void next_expected(token*, uint type);
    void unexpected_token(const token&) const;
    void save_and_lookahead(token*);
    
  private:
    struct saved_token : public token {
      char buf[128];
      saved_token() : token(0, &buf[0]) { }
    };
    
    enum {
      NORMAL, // read from lexer::next(...)
      TOK1,   // read from tok1, then tok2
      TOK2,   // read from tok2, then lexer::next()
    } state;

    saved_token tok1;
    saved_token tok2;

  public:
    plexer(const char* filename) : lexer(filename), state(NORMAL) { }
  };

  struct list {
    std::vector<obj> obj_list;

    list(plexer&);
  };

  struct block {
    std::vector<stmt> stmt_list;

    block() { }
    block(plexer&, bool is_root = false, bool is_save = false);

  protected:
    static block EMPTY_BLOCK;
    
    void slurp_color(obj&, plexer&) const;
  };

  bool looks_like_title(const char*);
}
  
#endif
