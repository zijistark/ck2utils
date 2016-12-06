
#include "parser.h"
#include "token.h"
#include "error.h"

#include <iomanip>
#include <ctype.h>


_PDX_NAMESPACE_BEGIN


block::block(parser& lex, bool is_root, bool is_save) {

    if (is_root && is_save) {
        /* skip over CK2txt header (savegames only) */
        token t;
        lex.next_expected(&t, token::STR);
    }

    while (1) {
        token tok;

        lex.next(&tok, is_root);

        if (tok.type == token::END)
            return;

        if (tok.type == token::CLOSE) {
            if (is_root && !is_save) // closing braces are only bad at root level
                throw va_error("Unmatched closing brace in %s (before line %u)",
                               lex.pathname(), lex.line());

            // otherwise, they mean it's time return to the previous block
            return;
        }

        object key;

        if (tok.type == token::STR)
            key = object{ lex.strdup(tok.text) };
        else if (tok.type == token::DATE)
            key = object{ date{ tok.text, lex.location(), lex.errors() } };
        else if (tok.type == token::INTEGER)
            key = object{ atoi(tok.text) };
        else
            lex.unexpected_token(tok);

        /* ...done with key */

        lex.next_expected(&tok, token::EQ);

        /* on to value... */
        object val;
        lex.next(&tok);

        if (tok.type == token::OPEN) {

            /* need to do token lookahead for 2 tokens to determine whether this is opening a
               generic list or a recursive block of statements */

            lex.next(&tok);
            bool double_open = false;

            if (tok.type == token::CLOSE) {
                /* empty block */
                val = object{ std::make_unique<block>() };
                continue;
            }
            else if (tok.type == token::OPEN) {
                /* special case for a list of blocks (only matters for savegames) */

                /* NOTE: technically, due to the structure of the language, we could NOT check
                   for a double-open at all and still handle lists of blocks. this is because no
                   well-formed PDX script will ever have an EQ token following an OPEN, so a
                   list is always detected and the lookahead mechanism functions as
                   expected. nevertheless, in the interest of the explicit... */

                double_open = true;
            }

            lex.save_and_lookahead(&tok);

            if (tok.type != token::EQ || double_open)
                val = object{ std::make_unique<list>(lex) }; // by God, this is (probably) a list!
            else
                val = object{ std::make_unique<block>(lex) }; // presumably block, so recurse

            /* ... will handle its own closing brace */
        }
        else if (tok.type == token::STR || tok.type == token::QSTR)
            val = object{ lex.strdup(tok.text) };
        else if (tok.type == token::QDATE || tok.type == token::DATE)
            val = object{ date{ tok.text, lex.location(), lex.errors() } };
        else if (tok.type == token::DECIMAL)
            val = object{ fp3{ tok.text, lex.location(), lex.errors() } };
        else if (tok.type == token::INTEGER)
            val = object{ atoi(tok.text) };
        else
            lex.unexpected_token(tok);

        // TODO: RHS (val) should support fixed-point decimal types; I haven't decided whether to make integers
        // and fixed-point decimal all use the same 64-bit type yet.

        _vec.emplace_back(key, val);
    }
}


void object::destroy() noexcept {
    switch (type) {
        case STRING:
        case INTEGER:
        case DATE:
        case DECIMAL:
            break;
        case BLOCK: data.up_block.~unique_ptr<block>(); break;
        case LIST:  data.up_list.~unique_ptr<list>(); break;
    }
}


object& object::operator=(object&& other) {
    if (this == &other) return *this; // guard against self-assignment

    /* destroy our current resources, then move resources from other, and return new self */
    destroy();
    type = other.type;

    switch (other.type) {
        case STRING:  data.s = other.data.s; break;
        case INTEGER: data.i = other.data.i; break;
        case DATE:    data.d = other.data.d; break;
        case DECIMAL: data.f = other.data.f; break;
        case BLOCK:   new (&data.up_block) unique_ptr<block>(std::move(other.data.up_block)); break;
        case LIST:    new (&data.up_list)  unique_ptr<list>(std::move(other.data.up_list)); break;
    }

    return *this;
}


list::list(parser& lex) {
    token t;

    while (true) {
        lex.next(&t);

        if (t.type == token::QSTR || t.type == token::STR)
            _vec.emplace_back( lex.strdup(t.text) );
        else if (t.type == token::INTEGER)
            _vec.emplace_back( atoi(t.text) );
        else if (t.type == token::DECIMAL)
            _vec.emplace_back( fp3{ t.text, lex.location(), lex.errors() } );
        else if (t.type == token::OPEN)
            _vec.emplace_back( std::make_unique<block>(lex) );
        else if (t.type != token::CLOSE)
            lex.unexpected_token(t);
        else
            return;
    }
}

void parser::next_expected(token* p_tok, uint type) {
    next(p_tok);

    if (p_tok->type != type)
        throw va_error("Expected %s token but got token %s at %s:L%d",
                                     token::TYPE_MAP[type], p_tok->type_name(), pathname(), line());
}


void parser::unexpected_token(const token& t) const {
    throw va_error("Unexpected token %s at %s:L%d",
                                 t.type_name(), pathname(), line());
}


void parser::next(token* p_tok, bool eof_ok) {
    while (1) {
        switch (_state) {
            case NORMAL:
                lexer::next(p_tok);
                break;
            case TOK1:
                p_tok->type = _tok1.type;
                p_tok->text = _tok1.text;
                _state = TOK2;
                break;
            case TOK2:
                p_tok->type = _tok2.type;
                p_tok->text = _tok2.text;
                _state = NORMAL;
                break;
        }

        if (p_tok->type == token::END) {
            if (!eof_ok)
                throw va_error("Unexpected EOF at %s:L%d", pathname(), line());
            else
                return;
        }

        if (p_tok->type == token::FAIL)
            throw va_error("Unrecognized token at %s:L%d", pathname(), line());

        if (p_tok->type == token::COMMENT)
            continue;

        return;
    }
}


void parser::save_and_lookahead(token* p_tok) {
    /* save our two tokens of lookahead */
    _tok1.type = p_tok->type;
    strcpy(_tok1.text, p_tok->text); // buffer overflows are myths

    next(p_tok);

    _tok2.type = p_tok->type;
    strcpy(_tok2.text, p_tok->text);

    /* set lexer to read from the saved tokens first */
    _state = TOK1;
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

    if (type == STRING) {
        if (strpbrk(as_string(), " \t\xA0\r\n\'")) // not the only time to quote, but whatever
            os << '"' << as_string() << '"';
        else
            os << as_string();
    }
    else if (type == INTEGER)
        os << as_integer();
    else if (type == DATE)
        os << as_date();
    else if (type == DECIMAL)
        os << as_decimal();
    else if (type == BLOCK) {
        os << '{' << std::endl;
        as_block()->print(os, indent + 4);
        os << std::setfill(' ') << std::setw(indent) << "";
        os << '}';
    }
    else if (type == LIST) {
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


_PDX_NAMESPACE_END
