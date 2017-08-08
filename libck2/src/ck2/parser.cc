
#include "parser.h"
#include "token.h"
#include "error.h"

#include <iomanip>
#include <ctype.h>


_CK2_NAMESPACE_BEGIN;


block::block(parser& lex, bool is_root, bool is_save) {

    if (is_root && is_save) {
        /* skip over CK2txt header (savegames only) */
        lex.next_expected(token::STR);
    }

    while (true) {
        token& tA = lex.next(is_root);

        if (tA.type() == token::END)
            return;

        if (tA.type() == token::CLOSE) {
            if (is_root && !is_save) // closing braces are only bad at root level
                throw va_parse_error(tA.location(), "Unmatched closing brace");

            // otherwise, they mean it's time return to the previous block
            return;
        }

        object key;

        if (tA.type() == token::STR)
            key = object{ lex.strdup(tA.text()), tA.location() };
        else if (tA.type() == token::DATE)
            key = object{ date{ tA.text(), tA.location(), lex.errors() }, tA.location() };
        else if (tA.type() == token::INTEGER)
            key = object{ atoi(tA.text()), tA.location() };
        else
            lex.unexpected_token(tA);

        /* ...done with key */

        token& tB = lex.next_expected(token::OPERATOR);
        opcode op = (strcmp(tB.text(), "=") == 0) ? opcode::EQ :
                    (strcmp(tB.text(), "<") == 0) ? opcode::LT :
                    (strcmp(tB.text(), ">") == 0) ? opcode::GT :
                    (strcmp(tB.text(), "<=") == 0) ? opcode::LTE :
                    (strcmp(tB.text(), ">=") == 0) ? opcode::GTE : opcode::EQ2;

        // FIXME: we need to also record the file location of the operator token! [for completeness]

        /* on to value... */
        object val;
        token& tC = lex.next();

        if (tC.type() == token::OPEN) {
            // need to do token lookahead for 2 tokens to determine whether this is opening a list or a block

            token& t1 = lex.peek(1);
            token& t2 = lex.peek(2);

            if (t1.type() == token::CLOSE) { // empty block (or list, but we choose to see it as a block)
                // FIXME: optimize: empty blocks are a waste of memory and cycles and ambiguous with empty lists, so add
                // a static object type (i.e., one of the possible dynamic types for ck2::object) that codifies an empty
                // block OR list
                val = object{ std::make_unique<block>(), tC.location() };
                _vec.emplace_back(key, val, op);
                continue;
            }

            if (t2.type() != token::OPERATOR) // everything but an operator in this position implies this will be a list
                val = object{ std::make_unique<list>(lex), tC.location() };
            else // but with the operator in position, it's definitely a block
                val = object{ std::make_unique<block>(lex), tC.location() };
        }
        else if (tC.type() == token::STR || tC.type() == token::QSTR)
            val = object{ lex.strdup(tC.text()), tC.location() };
        else if (tC.type() == token::QDATE || tC.type() == token::DATE)
            val = object{ date{ tC.text(), tC.location(), lex.errors() }, tC.location() };
        else if (tC.type() == token::DECIMAL)
            val = object{ fp3{ tC.text(), tC.location(), lex.errors() }, tC.location() };
        else if (tC.type() == token::INTEGER)
            val = object{ atoi(tC.text()), tC.location() };
        else
            lex.unexpected_token(tC);

        _vec.emplace_back(key, val, op);

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
        // case EMPTY:
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
        case NIL: break;
        case STRING:  _data.s = other._data.s; break;
        case INTEGER: _data.i = other._data.i; break;
        case DATE:    _data.d = other._data.d; break;
        case DECIMAL: _data.f = other._data.f; break;
//        case EMPTY:   memset(&_data, 0, sizeof(_data)); break;
        case BLOCK:   new (&_data.up_block) unique_ptr<block>(std::move(other._data.up_block)); break;
        case LIST:    new (&_data.up_list)  unique_ptr<list>(std::move(other._data.up_list));   break;
    }

    _loc = other._loc;
    return *this;
}


list::list(parser& lex) {
    while (true) {
        token& t = lex.next();

        if (t.type() == token::QSTR || t.type() == token::STR)
            _vec.emplace_back( lex.strdup(t.text()), t.location() );
        else if (t.type() == token::INTEGER)
            _vec.emplace_back( atoi(t.text()), t.location() );
        else if (t.type() == token::DECIMAL)
            _vec.emplace_back( fp3{ t.text(), t.location(), lex.errors() }, t.location() );
        else if (t.type() == token::OPEN)
            _vec.emplace_back( std::make_unique<block>(lex), t.location() );
        else if (t.type() != token::CLOSE)
            lex.unexpected_token(t);
        else
            return;
    }
}

token& parser::next_expected(uint type) {
    token& t = next();

    if (t.type() != type)
        throw va_parse_error(t.location(), "Expected %s token but got %s token",
                             token::TYPE_MAP[type], t.type_name());

    return t;
}


void parser::unexpected_token(const token& t) const {
    throw va_parse_error(t.location(), "Unexpected token %s", t.type_name());
}


token& parser::next(bool eof_ok) {
    while (true) {
        token& t = super::next();

        if (t.type() == token::END && !eof_ok)
            throw va_parse_error(t.location(), "Unexpected EOF");

        if (t.type() == token::FAIL)
            throw va_parse_error(t.location(), "Unrecognized token");

        if (t.type() == token::COMMENT)
            continue; // FIXME

        return t;
    }
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
