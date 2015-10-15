// -*- c++ -*-

#ifndef _MDH_PDX_H_
#define _MDH_PDX_H_


#include <vector>
#include "lexer.h"
#include "token.h"
#include "error.h"

#include <cstring>
#include <cassert>
#include <cstdint>


namespace pdx {

  struct block;
  struct list;

  struct date_t {
    uint16_t y;
    uint8_t  m;
    uint8_t  d;

    bool operator<(const date_t e) const noexcept {
      /* note that since our binary representation is simpy a 32-bit unsigned integer
       * and since our fields are MSB to LSB, we could just compare date_t as a uint,
       * but this is the more correct pattern for multi-field comparison, and I don't
       * feel the need to optimize this. :) */
      if (y < e.y) return true;
      if (e.y < y) return false;
      if (m < e.m) return true;
      if (e.m < y) return false;
      if (d < e.d) return true;
      if (e.d < d) return false;
      return false;
    }

    uint16_t year()  const noexcept { return y; }
    uint8_t  month() const noexcept { return m; }
    uint8_t  day()   const noexcept { return d; }

  } __attribute__ ((packed)); // do indeed make a 32-bit POD out of this

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
      date_t date;
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

    /* more readable accessors (silently-checked type) */
    char*  as_c_str()   const noexcept { assert(type == STR);   return data.s; }
    int    as_integer() const noexcept { assert(type == INT);   return data.i; }
    char*  as_title()   const noexcept { assert(type == TITLE); return data.s; }
    block* as_block()   const noexcept { assert(type == BLOCK); return data.p_block; }
    list*  as_list()    const noexcept { assert(type == LIST);  return data.p_list; }
    date_t as_date()    const noexcept { assert(type == DATE);  return data.date; }

    /* more readable accessors (unchecked type) */
    char*  c_str()   const noexcept { return data.s; }
    int    integer() const noexcept { return data.i; }
    char*  title()   const noexcept { return data.s; }
    block* block()   const noexcept { return data.p_block; }
    list*  list()    const noexcept { return data.p_list; }
    date_t date()    const noexcept { return data.date; }

    /* type accessors */
    bool is_c_str()   const noexcept { return type == STR; }
    bool is_integer() const noexcept { return type == INT; }
    bool is_title()   const noexcept { return type == TITLE; }
    bool is_block()   const noexcept { return type == BLOCK; }
    bool is_list()    const noexcept { return type == LIST; }
    bool is_date()    const noexcept { return type == DATE; }

    void store_date_from_str(char* str, lexer* p_lex = nullptr);
  };

  struct stmt {
    obj key;
    obj val;

    bool key_eq(const char* s) const noexcept {
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

  static const uint TIER_BARON = 1;
  static const uint TIER_COUNT = 2;
  static const uint TIER_DUKE = 3;
  static const uint TIER_KING = 4;
  static const uint TIER_EMPEROR = 5;

  inline uint title_tier(const char* s) {
    switch (*s) {
        case 'b':
            return TIER_BARON;
        case 'c':
            return TIER_COUNT;
        case 'd':
            return TIER_DUKE;
        case 'k':
            return TIER_KING;
        case 'e':
            return TIER_EMPEROR;
        default:
            return 0;
    }
  }

  bool looks_like_title(const char*);
}

#endif
