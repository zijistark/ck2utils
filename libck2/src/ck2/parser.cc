
#include "parser.h"
#include "token.h"
#include "error.h"

#include <iomanip>
#include <ctype.h>


_CK2_NAMESPACE_BEGIN;


struct binary_op_text {
    const char* text;
    binary_op op;
};

const binary_op_text BINOP_TBL[] = {
    { "=",  binary_op::EQ },
    { "<",  binary_op::LT },
    { ">",  binary_op::GT },
    { "<=", binary_op::LTE },
    { ">=", binary_op::GTE },
    { "==", binary_op::EQ2 },
};


block::block(parser& prs, bool is_root, bool is_save) {
    token t;

    if (is_root && is_save) {
        /* skip over CK2txt header (savegames only) */
        prs.next_expected(&t, token::STR);
    }

    while (true) {
        prs.next(&t, is_root);

        if (t.type() == token::END)
            return;

        if (t.type() == token::CLOSE) {
            if (is_root && !is_save) // closing braces are only bad at root level
                throw va_parse_error(t.location(), "Unmatched closing brace");

            // otherwise, they mean it's time return to the previous block
            return;
        }

        object key;

        if (t.type() == token::STR)
            key = object{ prs.strdup(t.text()), t.location() };
        else if (t.type() == token::DATE)
            key = object{ date{ t.text(), t.location(), prs.errors() }, t.location() };
        else if (t.type() == token::INTEGER)
            key = object{ atoi(t.text()), t.location() };
        else
            prs.unexpected_token(t);

        /* ...done with key */

        prs.next_expected(&t, token::OPERATOR);
        object op;

        for (auto const& bop : BINOP_TBL)
            if (strcmp(t.text(), bop.text) == 0) {
                op = object{ bop.op, t.location() };
                break;
            }

        /* on to value... */
        object val;
        prs.next(&t);

        if (t.type() == token::OPEN) {
            // currently our only token lookahead case required

            token* pt1 = prs.peek<0>(); // like next() but doesn't modify the input
            token* pt2 = prs.peek<1>(); // ... whereas this is time travel

            if (pt1 && pt1->type() == token::CLOSE) { // empty block (or list, but we choose to see it as a block)
                // FIXME: optimize: empty blocks are a waste of memory and cycles and ambiguous with empty lists, so add
                // a static object type (i.e., one of the possible dynamic types for ck2::object) that codifies an empty
                // block OR list (vector syntax nodes, essentially)
                prs.next(&t); // suspicions confirmed, consume token
                val = object{ std::make_unique<block>(), t.location() };
            }
            // all but an operator in this position implies this will be a list
            else if (pt2 && pt2->type() != token::OPERATOR)
                val = object{ std::make_unique<list>(prs), t.location() };
            else // but with the operator in position, it's definitely a block
                val = object{ std::make_unique<block>(prs), t.location() };
        }
        else if (t.type() == token::STR || t.type() == token::QSTR)
            val = object{ prs.strdup(t.text()), t.location() };
        else if (t.type() == token::QDATE || t.type() == token::DATE)
            val = object{ date{ t.text(), t.location(), prs.errors() }, t.location() };
        else if (t.type() == token::DECIMAL)
            val = object{ fp3{ t.text(), t.location(), prs.errors() }, t.location() };
        else if (t.type() == token::INTEGER)
            val = object{ atoi(t.text()), t.location() };
        else
            prs.unexpected_token(t);

        _vec.emplace_back(key, op, val);

        if (key.is_string())
            _map[key.as_string()] = _vec.size() - 1;
    }
}


void object::destroy() noexcept {
    switch (_type) {
        case NIL:
        case STRING:
        case INTEGER:
        case DATE:
        case DECIMAL:
        case BINARY_OP:
            break;
        case BLOCK: _data.up_block.~unique_ptr<block>(); break;
        case LIST:  _data.up_list.~unique_ptr<list>(); break;
    }
}


object& object::operator=(object&& other) {
    if (this == &other) return *this; // guard against self-assignment

    /* destroy our current resources, then move resources from other, and return new self */
    destroy();
    _type = other._type;
    // _precomment = other._precomment;
    // _postcomment = other._postcomment;

    switch (other._type) {
        case NIL:       break;
        case STRING:    _data.s = other._data.s; break;
        case INTEGER:   _data.i = other._data.i; break;
        case DATE:      _data.d = other._data.d; break;
        case DECIMAL:   _data.f = other._data.f; break;
        case BINARY_OP: _data.o = other._data.o; break;
        case BLOCK:     new (&_data.up_block) unique_ptr<block>(std::move(other._data.up_block)); break;
        case LIST:      new (&_data.up_list)  unique_ptr<list>(std::move(other._data.up_list));   break;
    }

    _loc = other._loc;
    return *this;
}


list::list(parser& prs) {
    token t;
    while (true) {
        prs.next(&t);

        if (t.type() == token::QSTR || t.type() == token::STR)
            _vec.emplace_back( prs.strdup(t.text()), t.location() );
        else if (t.type() == token::INTEGER)
            _vec.emplace_back( atoi(t.text()), t.location() );
        else if (t.type() == token::DECIMAL)
            _vec.emplace_back( fp3{ t.text(), t.location(), prs.errors() }, t.location() );
        else if (t.type() == token::OPEN)
            _vec.emplace_back( std::make_unique<block>(prs), t.location() );
        else if (t.type() != token::CLOSE)
            prs.unexpected_token(t);
        else
            return;
    }
}


void parser::next_expected(token* p_tok, uint type) {
    next(p_tok, (type == token::END));

    if (p_tok->type() != type)
        throw va_parse_error(p_tok->location(), "Expected %s token but got %s -- '%s'",
                             token::TYPE_MAP[type], p_tok->type_name(), (p_tok->text()) ? p_tok->text() : "");
}


void parser::unexpected_token(const token& t) const {
    throw va_parse_error(t.location(), "Unexpected token %s", t.type_name());
}


bool parser::next(token* p_tok, bool eof_ok) {
    if (_tq_n == 0) {
        if (_tq_done) return false;
        // nothing in queue and not done, so read directly from scanner buffer into p_tok (avoids token text copy)
        _tq_done = !( _lex.read_token_into(*p_tok) );
    }
    else {
        // token(s) are in lookahead queue, so drain that rather than lexer. as long as there are tokens in the queue,
        // we've got work to do (regardless of _tq_done).

        // NOTE: here we are passing out token objects that have token text buffer pointers into our preallocated
        // _tq_text[]. how will the buffers make it back into the token queue? they never leave. remember, we have a bit
        // of an odd contract regarding the internal token text buffers: the user is allowed to mutate the pointed-to
        // memory, but they cannot change to what buffer is pointed (only we do that), and the text buffer itself might
        // be overwritten as soon as the next call to this method.

        // FIXME: (re: above) also, the buffer could be overwritten by peek()ing past the currently-queued tokens,
        // because that would initiate filling of the nec. amount of tokens from input into the queue. This can be
        // smoothed over by adding a "spare" token element to the "end" of the circular queue, so solve it.
        *p_tok = _tq[_tq_head_idx];
        _tq_head_idx = (_tq_head_idx + 1) % TQ_SZ;
        --_tq_n;
    }

    if (p_tok->type() == token::END && !eof_ok)
        throw va_parse_error(p_tok->location(), "Unexpected EOF");

    if (p_tok->type() == token::FAIL)
        throw va_parse_error(p_tok->location(), "Unrecognized input");

    return true;
}


void block::print(std::ostream& os, uint indent) const {
    for (auto&& stmt : _vec)
        stmt.print(os, indent);
}


void list::print(std::ostream& os, uint indent) const {
    for (auto&& obj : _vec) {
        obj.print(os, indent);
        os << ' ';
    }
}


void statement::print(std::ostream& os, uint indent) const {
    os << std::setfill(' ') << std::setw(indent) << "";
    _k.print(os, indent);
    os << " = ";
    _v.print(os, indent);
    os << std::endl;
}


void object::print(std::ostream& os, uint indent) const {

    if (_type == STRING) {
        if (strpbrk(as_string(), " \t\r\n\'"))
            os << '"' << as_string() << '"';
        else
            os << as_string();
    }
    else if (_type == INTEGER)
        os << as_integer();
    else if (_type == DATE)
        os << as_date();
    else if (_type == DECIMAL)
        os << as_decimal();
    else if (_type == BLOCK) {
        os << '{' << std::endl;
        as_block()->print(os, indent + 4);
        os << std::setfill(' ') << std::setw(indent) << "";
        os << '}';
    }
    else if (_type == LIST) {
        os << "{ ";
        as_list()->print(os, indent);
        os << '}';
    }
    else
        assert(false && "Unhandled object type");
}


/* not handled directly by scanner because there are some things that look like titles
     and are not, but these aberrations (e.g., mercenary composition tags) only appear on
     the RHS of statements. */
bool looks_like_title(const char* s) {
    if (strlen(s) < 3)
        return false;

    if ( !(*s == 'b' || *s == 'c' || *s == 'd' || *s == 'k' || *s == 'e') )
        return false;

    if (s[1] != '_')
        return false;

    if (!isalpha(s[2])) // eliminates c_<character_id> syntax, among other things
        return false;

    return true;
}


_CK2_NAMESPACE_END;
