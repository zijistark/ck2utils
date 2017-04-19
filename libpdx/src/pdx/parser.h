// -*- c++ -*-

#pragma once
#include "pdx_common.h"

#include "error_queue.h"
#include "cstr_pool.h"
#include "cstr.h"
#include "lexer.h"
#include "date.h"
#include "fp_decimal.h"
#include "token.h"
#include "error.h"

#include <vector>
#include <memory>
#include <string>
#include <algorithm>
#include <unordered_map>
#include <boost/filesystem.hpp>


_PDX_NAMESPACE_BEGIN


using std::unique_ptr;
typedef fp_decimal<3> fp3;
class block;
class list;
class parser;


/* OBJECT -- generic "any"-type parse tree data element (superset of pdx::scalar) */

class object {
    enum {
        STRING,
        INTEGER,
        DATE,
        DECIMAL,
        BLOCK,
        LIST,
    } type;

    union data_union {
        char* s;
        int   i;
        date  d;
        fp3   f;
        unique_ptr<block> up_block;
        unique_ptr<list>  up_list;

        /* tell C++ that we'll manage the nontrivial union members outside of this union */
        data_union() {}
        ~data_union() {}
    } data;

    void destroy() noexcept; // helper for dtor & move-assignment

public:

    object(char* s = nullptr)    : type(STRING)  { data.s = s; }
    object(int i)                : type(INTEGER) { data.i = i; }
    object(date d)               : type(DATE)    { data.d = d; }
    object(fp3 f)                : type(DECIMAL) { data.f = f; }
    object(unique_ptr<block> up) : type(BLOCK)   { new (&data.up_block) unique_ptr<block>(std::move(up)); }
    object(unique_ptr<list> up)  : type(LIST)    { new (&data.up_list) unique_ptr<list>(std::move(up)); }

    /* move-assignment operator */
    object& operator=(object&& other);

    /* move-constructor (implemented via move-assignment) */
    object(object&& other) : object() { *this = std::move(other); }

    /* destructor */
    ~object() { destroy(); }

    /* type accessors */
    bool is_string()  const noexcept { return type == STRING; }
    bool is_integer() const noexcept { return type == INTEGER; }
    bool is_date()    const noexcept { return type == DATE; }
    bool is_decimal() const noexcept { return type == DECIMAL; }
    bool is_block()   const noexcept { return type == BLOCK; }
    bool is_list()    const noexcept { return type == LIST; }
    bool is_number()  const noexcept { return is_integer() || is_decimal(); }

    /* data accessors (unchecked type) */
    char*  as_string()  const noexcept { return data.s; }
    int    as_integer() const noexcept { return data.i; }
    date   as_date()    const noexcept { return data.d; }
    fp3    as_decimal() const noexcept { return data.f; }
    block* as_block()   const noexcept { return data.up_block.get(); }
    list*  as_list()    const noexcept { return data.up_list.get(); }
    fp3    as_number()  const noexcept { return (is_decimal()) ? data.f : fp3(data.i); }

    /* convenience equality operator overloads */
    bool operator==(const char* s)        const noexcept { return is_string() && strcmp(as_string(), s) == 0; }
    bool operator==(const std::string& s) const noexcept { return is_string() && s == as_string(); }
    bool operator==(int i)  const noexcept { return is_integer() && as_integer() == i; }
    bool operator==(date d) const noexcept { return is_date() && as_date() == d; }
    bool operator==(fp3 f)  const noexcept { return is_number() && as_number() == f; }

    bool operator!=(const char* s)        const noexcept { return !is_string() || strcmp(as_string(), s); }
    bool operator!=(const std::string& s) const noexcept { return !is_string() || s != as_string(); }
    bool operator!=(int i)  const noexcept { return !is_integer() || as_integer() != i; }
    bool operator!=(date d) const noexcept { return !is_date() || as_date() != d; }
    bool operator!=(fp3 f)  const noexcept { return !is_number() || as_number() != f; }

    void print(std::ostream&, uint indent = 0) const;
};


/* LIST -- list of N objects */

class list {
    typedef std::vector<object> vec_t;
    vec_t _vec;

public:
    list() = delete;
    list(parser&);

    void print(std::ostream&, uint indent = 0) const;

    object&       operator[](size_t i)       { return _vec[i]; }
    const object& operator[](size_t i) const { return _vec[i]; }

    vec_t::size_type      size() const  { return _vec.size(); }
    bool                  empty() const { return size() == 0; }
    vec_t::iterator       begin()       { return _vec.begin(); }
    vec_t::iterator       end()         { return _vec.end(); }
    vec_t::const_iterator begin() const { return _vec.cbegin(); }
    vec_t::const_iterator end() const   { return _vec.cend(); }
};


enum class opcode {
    EQ,  // =
    LT,  // <
    GT,  // >
    LTE, // <=
    GTE, // >=
    EQ2, // ==
};


/* STATEMENT -- statements are pairs of objects and an operator/separator */

class statement {
    object _k;
    object _v;
    opcode _op;

public:
    statement() = delete;
    statement(object& k, object& v, opcode op) : _k(std::move(k)), _v(std::move(v)), _op(op) {}

    const object&  key()   const noexcept { return _k; }
    const object&  value() const noexcept { return _v; }
    opcode         op()    const noexcept { return _op; }

    void print(std::ostream&, uint indent = 0) const;
};


/* BLOCK -- blocks contain N statements */

class block {
    /* we maintain two data structures for different ways of efficiently accessing
     * the statements in a block. a linear vector is the master data structure;
     * it actually owns the statement objects, which means that when it is
     * destroyed, so too are any memory resources associated with the objects
     * in its statements.
     *
     * the secondary data structure fulfills a more specialized use case: it maps
     * LHS string-type keys to an index into the statement vector to which the
     * key corresponds, if such a key occurs in this block. if it can occur
     * multiple times, then this block was not constructed via the RHS-merge
     * parsing method (i.e., folderization), and this access pattern may be a
     * lot less helpful. in such cases, the final occurrence of the key in
     * this block will be stored in the hash-map.
     *
     * string-type keys are the only type of keys for which I've encountered a
     * realistic use case for the hash-map access pattern, so rather than create
     * a generalized scalar any-type (like pdx::object but only for scalar data
     * types, or more generally, copy-constructible data types) and hash-map via
     * that any-type, I've simply chosen to stick to string keys for now.
     */

    // linear vector of statements
    typedef std::vector<statement> vec_t;
    vec_t _vec;

    // hash-map of LHS keys to their corresponding statement's index in _vec
    std::unordered_map<cstr, vec_t::difference_type> _map;

public:
    block() { }
    block(parser&, bool is_root = false, bool is_save = false);

    void print(std::ostream&, uint indent = 0) const;

    vec_t::size_type      size() const  { return _vec.size(); }
    bool                  empty() const { return size() == 0; }
    vec_t::iterator       begin()       { return _vec.begin(); }
    vec_t::iterator       end()         { return _vec.end(); }
    vec_t::const_iterator begin() const { return _vec.cbegin(); }
    vec_t::const_iterator end() const   { return _vec.cend(); }

    /* map accessor for statements by LHS statement key (if string-type)
     * if not found, returns this object's end iterator.
     * if found, returns a valid iterator which can be dereferenced. */
    vec_t::iterator find_key(const char* key) noexcept {
        auto i = _map.find(key);
        return (i != _map.end()) ? std::next(begin(), i->second) : end();
    }

    vec_t::const_iterator find_key(const char* key) const noexcept {
        auto i = _map.find(key);
        return (i != _map.end()) ? std::next(begin(), i->second) : end();
    }
};


/* PARSER -- construct a parse tree whose resources are owned by the parser via the parser's constructor */

class parser : public lexer {
    struct saved_token : public token {
        char buf[128];
        saved_token() : token(token::END, &buf[0]) { }
    };

    enum {
        NORMAL, // read from lexer::next(...)
        TOK1,   // read from tok1, then tok2
        TOK2,   // read from tok2, then lexer::next()
    } _state;

    saved_token _tok1;
    saved_token _tok2;

    cstr_pool<char> _string_pool;
    unique_ptr<block> _up_root_block;
    error_queue _errors;

protected:
    friend class block;
    friend class list;

    char* strdup(const char* s) { return _string_pool.strdup(s); }

    void next(token*, bool eof_ok = false);
    void next_expected(token*, uint type);
    void unexpected_token(const token&) const;
    void save_and_lookahead(token*);

public:
    parser() = delete;
    parser(const char* p, bool is_save = false)
        : lexer(p), _state(NORMAL) { _up_root_block = std::make_unique<block>(*this, true, is_save); }
    parser(const std::string& p, bool is_save = false) : parser(p.c_str(), is_save) {}
    parser(const fs::path& p, bool is_save = false) : parser(p.string().c_str(), is_save) {}

    block* root_block() noexcept { return _up_root_block.get(); }
    error_queue& errors() noexcept { return _errors; }
};


/* MISC. UTILITY */

static const uint TIER_BARON   = 1;
static const uint TIER_COUNT   = 2;
static const uint TIER_DUKE    = 3;
static const uint TIER_KING    = 4;
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


_PDX_NAMESPACE_END


inline std::ostream& operator<<(std::ostream& os, const pdx::block& a) { a.print(os); return os; }
inline std::ostream& operator<<(std::ostream& os, const pdx::list& a) { a.print(os); return os; }
inline std::ostream& operator<<(std::ostream& os, const pdx::statement& a) { a.print(os); return os; }
inline std::ostream& operator<<(std::ostream& os, const pdx::object& a) { a.print(os); return os; }
