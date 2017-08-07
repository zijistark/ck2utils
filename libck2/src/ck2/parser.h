// -*- c++ -*-

#pragma once
#include "common.h"

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


_CK2_NAMESPACE_BEGIN


using std::unique_ptr;
typedef fp_decimal<3> fp3;
class block;
class list;
class parser;

/* COMMENT_BLOCK -- a list of lines of contiguous freestanding comments */

// allows blank lines to be in the list under certain sane circumstances (in
// order to heuristically improve [whitespace] information retention when/if
// rewriting the comments after modifying the AST). they will be represented
// as nullptr.

// class comment_block {
//     using vec_t = std::vector<char*>;
//     vec_t _vec; // of lines of text considered to be part of a commented region

// public:
//     comment_block(char* first_line) { append_line(first_line); }

//     void append_line(char* line) { _vec.push_back(line); }

//     void append_blank(int n_blank_lines = 1) {
//         for (int i = n_blank_lines; i > 0; --i) _vec.push_back(nullptr);
//     }

//     vec_t::size_type      size()  const noexcept { return _vec.size(); }
//     bool                  empty() const noexcept { return size() == 0; }
//     vec_t::iterator       begin()       noexcept { return _vec.begin(); }
//     vec_t::iterator       end()         noexcept { return _vec.end(); }
//     vec_t::const_iterator begin() const noexcept { return _vec.cbegin(); }
//     vec_t::const_iterator end()   const noexcept { return _vec.cend(); }
// };


/* OBJECT -- generic "any"-type syntax tree node */

class object {
    enum {
        NIL,
        STRING,
        INTEGER,
        DATE,
        DECIMAL,
        BLOCK,
        LIST,
    } _type;

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
    } _data;

    floc _loc;

    // unique_ptr<comment_block> _up_precomments;
    // char* _postcomment;

    void init() noexcept { } // _postcomment = nullptr; }
    void destroy() noexcept; // helper for dtor & move-assignment

public:
    object() : _type(NIL) {};

    object(char* s, const floc& fl) : _type(STRING),  _loc(fl) { _data.s = s; init(); }
    object(int i,   const floc& fl) : _type(INTEGER), _loc(fl) { _data.i = i; init(); }
    object(date d,  const floc& fl) : _type(DATE),    _loc(fl) { _data.d = d; init(); }
    object(fp3 f,   const floc& fl) : _type(DECIMAL), _loc(fl) { _data.f = f; init(); }
    // object()                     : _type(EMPTY)   { memset(&_data, 0, sizeof(_data)); init(); }
    object(unique_ptr<block> up, const floc& fl) : _type(BLOCK), _loc(fl) { new (&_data.up_block) unique_ptr<block>(std::move(up)); init(); }
    object(unique_ptr<list> up,  const floc& fl) : _type(LIST),  _loc(fl) { new (&_data.up_list) unique_ptr<list>(std::move(up)); init(); }

    /* move-assignment operator */
    object& operator=(object&& other);

    /* move-constructor (implemented via move-assignment) */
    object(object&& other) : object() { *this = std::move(other); }

    /* destructor */
    ~object() { destroy(); }

    floc const& location() const noexcept { return _loc; }
    floc&       location()       noexcept { return _loc; }
    // const comment_block* precomments() const noexcept { return _up_precomments.get(); }
    // const char*          postcomment() const noexcept { return _postcomment; }

    /* type accessors */
    bool is_string()  const noexcept { return _type == STRING; }
    bool is_integer() const noexcept { return _type == INTEGER; }
    bool is_date()    const noexcept { return _type == DATE; }
    bool is_decimal() const noexcept { return _type == DECIMAL; }
    // bool is_empty()   const noexcept { return _type == EMPTY; }
    bool is_block()   const noexcept { return _type == BLOCK; }
    bool is_list()    const noexcept { return _type == LIST; }
    bool is_number()  const noexcept { return is_integer() || is_decimal(); }

    /* data accessors (unchecked type) */
    char*  as_string()  const noexcept { return _data.s; }
    int    as_integer() const noexcept { return _data.i; }
    date   as_date()    const noexcept { return _data.d; }
    fp3    as_decimal() const noexcept { return _data.f; }
    block* as_block()   const noexcept { return _data.up_block.get(); }
    list*  as_list()    const noexcept { return _data.up_list.get(); }
    fp3    as_number()  const noexcept { return (is_decimal()) ? _data.f : fp3(_data.i); }

    // void set_precomments(unique_ptr<comment_block> up) noexcept { _up_precomments = std::move(up); }
    // void set_postcomment(char* str) noexcept { _postcomment = str; }

    /* convenience equality operator overloads */
    bool operator==(const char* s)        const noexcept { return is_string() && strcmp(as_string(), s) == 0; }
    bool operator==(const std::string& s) const noexcept { return is_string() && s == as_string(); }
    bool operator==(int i)  const noexcept { return is_integer() && as_integer() == i; }
    bool operator==(date d) const noexcept { return is_date() && as_date() == d; }
    bool operator==(fp3 f)  const noexcept { return is_number() && as_number() == f; }

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

    object&       operator[](size_t i)       noexcept { return _vec[i]; }
    const object& operator[](size_t i) const noexcept { return _vec[i]; }

    vec_t::size_type      size()  const noexcept { return _vec.size(); }
    bool                  empty() const noexcept { return size() == 0; }
    vec_t::iterator       begin()       noexcept { return _vec.begin(); }
    vec_t::iterator       end()         noexcept { return _vec.end(); }
    vec_t::const_iterator begin() const noexcept { return _vec.cbegin(); }
    vec_t::const_iterator end()   const noexcept { return _vec.cend(); }
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
     * a generalized scalar any-type (like ck2::object but only for scalar data
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

    vec_t::size_type      size()  const noexcept { return _vec.size(); }
    bool                  empty() const noexcept { return size() == 0; }
    vec_t::iterator       begin()       noexcept { return _vec.begin(); }
    vec_t::iterator       end()         noexcept { return _vec.end(); }
    vec_t::const_iterator begin() const noexcept { return _vec.cbegin(); }
    vec_t::const_iterator end()   const noexcept { return _vec.cend(); }

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


/* PARSER -- construct a parse tree from a file whose resources are owned by the parser object */

class parser : public lexer<2> { // derives from a lexer with 2 tokens of lookahead
    typedef lexer<2> super;
    // we keep a raw pointer to the last-parsed object so that we may associate a comment token following it
    // on the same line with the object as a postcomment.
    //object* _last_parsed_object;

    /* we accrue free-standing comments here before associating them with a
     * pdx::object later in the parse (as precomments to it) */
    //unique_ptr<comment_block> up_comments;

    cstr_pool<char> _string_pool;
    unique_ptr<block> _up_root_block;
    error_queue _errors;

protected:
    friend class block;
    friend class list;

    char* strdup(const char* s) { return _string_pool.strdup(s); }

    token& next(bool eof_ok = false);
    token& next_expected(uint type);
    void   unexpected_token(const token&) const;

    // at current point in input token stream, consume all consecutive comment tokens and attach them to the
    // appropriate AST objects, leaving us to definitely not deal with a comment token next.
    // void consume_comments(); FIXME

public:
    parser() = delete;
    parser(const std::string& p, bool is_save = false) : parser(p.c_str(), is_save) {}
    parser(const fs::path& p, bool is_save = false) : parser(p.string().c_str(), is_save) {}
    parser(const char* p, bool is_save = false) : lexer(p) { //, _last_parsed_object(nullptr) {
        _up_root_block = std::make_unique<block>(*this, true, is_save);
    }

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


_CK2_NAMESPACE_END


inline std::ostream& operator<<(std::ostream& os, const ck2::block& a) { a.print(os); return os; }
inline std::ostream& operator<<(std::ostream& os, const ck2::list& a) { a.print(os); return os; }
inline std::ostream& operator<<(std::ostream& os, const ck2::statement& a) { a.print(os); return os; }
inline std::ostream& operator<<(std::ostream& os, const ck2::object& a) { a.print(os); return os; }
