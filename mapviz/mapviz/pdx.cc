
#include "pdx.h"
#include "token.h"
#include "error.h"

#include <cstdlib>
#include <ctype.h>

static char* my_strsep(char** stringp, const char* delim)
{
    char* start = *stringp;
    char* p;

    p = (start != NULL) ? strpbrk(start, delim) : NULL;

    if (p == NULL)
        *stringp = NULL;
    else {
        *p = '\0';
        *stringp = p + 1;
    }

    return start;
}


namespace pdx {

    block block::EMPTY_BLOCK;

    block::block(plexer& lex, bool is_root, bool is_save) {

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
                                   lex.filename(), lex.line());

                // otherwise, they mean it's time return to the previous block
                return;
            }

            stmt_list.push_back(stmt());
            stmt& stmt = stmt_list.back();

            if (tok.type == token::STR) {

                stmt.key.data.s = _strdup( tok.text );

                if (tok.type == token::DATE)
                    stmt.key.type = obj::DATE;
                else if (looks_like_title( tok.text ))
                    stmt.key.type = obj::TITLE;
                else {

                    if ( (strcmp(tok.text, "color") == 0) || (strcmp(tok.text, "color2") == 0) ) {
                        slurp_color(stmt.val, lex);
                        continue;
                    }
                }
            }
            else if (tok.type == token::DATE) {
                stmt.key.type = obj::DATE;
                stmt.key.store_date_from_str(tok.text);
            }
            else if (tok.type == token::INT) {
                stmt.key.type = obj::INT;
                stmt.key.data.i = atoi( tok.text );
            }
            else
                lex.unexpected_token(tok);

            /* ...done with key */

            lex.next_expected(&tok, token::EQ);

            /* on to value... */
            lex.next(&tok);

            if (tok.type == token::OPEN) {

                /* need to do token lookahead for 2 tokens to determine whether this is opening a
                   generic list or a recursive block of statements */

                lex.next(&tok);
                bool double_open = false;

                if (tok.type == token::CLOSE) {
                    /* empty block */

                    stmt.val.type = obj::BLOCK;
                    stmt.val.data.p_block = &EMPTY_BLOCK;

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

                if (tok.type != token::EQ || double_open) {

                    /* by God, this is (probably) a list! */
                    stmt.val.type = obj::LIST;
                    stmt.val.data.p_list = new list(lex);
                }
                else {
                    /* presumably a block */

                    /* time to recurse ... */
                    stmt.val.type = obj::BLOCK;
                    stmt.val.data.p_block = new block(lex);
                }

                /* ... will handle its own closing brace */
            }
            else if (tok.type == token::STR) {
                stmt.val.data.s = _strdup( tok.text );

                if (looks_like_title( tok.text ))
                    stmt.val.type = obj::TITLE;
            }
            else if (tok.type == token::QSTR) {
                stmt.val.data.s = _strdup( tok.text );
            }
            else if (tok.type == token::QDATE || tok.type == token::DATE) {
                /* for savegames, otherwise only on LHS (and never quoted) */
                stmt.val.type = obj::DATE;
                stmt.val.data.s = _strdup( tok.text );
            }
            else if (tok.type == token::INT) {
                stmt.val.type = obj::INT;
                stmt.val.data.i = atoi( tok.text );
            }
            else if (tok.type == token::FLOAT) {
                stmt.val.type = obj::DECIMAL;
                stmt.val.data.s = _strdup( tok.text );
            }
            else
                lex.unexpected_token(tok);
        }
    }


    /* could be represented as generic lists, but aren't */
    void block::slurp_color(obj& obj, plexer& lex) const {
        token t;

        lex.next_expected(&t, token::EQ);
        lex.next_expected(&t, token::OPEN);

        obj.type = obj::COLOR;

        lex.next_expected(&t, token::INT);
        obj.data.color.r = static_cast<uint8_t>( atoi(t.text) );

        lex.next_expected(&t, token::INT);
        obj.data.color.g = static_cast<uint8_t>( atoi(t.text) );

        lex.next_expected(&t, token::INT);
        obj.data.color.b = static_cast<uint8_t>( atoi(t.text) );

        lex.next_expected(&t, token::CLOSE);
    }


    void block::print(FILE* f, uint indent) {
        for (auto&& s : stmt_list)
            s.print(f, indent);
    }


    void stmt::print(FILE* f, uint indent) {
        fprintf(f, "%*s", indent, "");
        key.print(f, indent);
        fprintf(f, " = ");
        val.print(f, indent);
        fprintf(f, "\n");
    }


    void obj::print(FILE* f, uint indent) {

        if (type == STR) {
            if (strpbrk(data.s, " \t\xA0\r\n\'")) // not the only time to quote, but whatever
                fprintf(f, "\"%s\"", data.s);
            else
                fprintf(f, "%s", data.s);
        }
        else if (type == INT)
            fprintf(f, "%d", data.i);
        else if (type == DECIMAL)
            fprintf(f, "%s", data.s);
        else if (type == DATE)
            fprintf(f, "%s", data.s);
        else if (type == TITLE)
            fprintf(f, "%s", data.s);
        else if (type == BLOCK) {
            fprintf(f, "{\n");
            data.p_block->print(f, indent+4);
            fprintf(f, "%*s}", indent, "");
        }
        else if (type == LIST) {
            fprintf(f, "{ ");

            for (auto&& o : data.p_list->obj_list) {
                    o.print(f, indent);
                    fprintf(f, " ");
            }

            fprintf(f, "}");
        }
        else if (type == COLOR)
            fprintf(f, "{ %u %u %u }", data.color.r, data.color.g, data.color.b);
        else
            assert(false);
    }

    list::list(plexer& lex) {
        token t;

        while (true) {
            obj o;
            lex.next(&t);

            if (t.type == token::QSTR || t.type == token::STR) {
                o.data.s = _strdup(t.text);
                obj_list.push_back(o);
            }
            else if (t.type == token::INT) {
                o.type = obj::INT;
                o.data.i = atoi(t.text);
                obj_list.push_back(o);
            }
            else if (t.type == token::FLOAT) {
                o.type = obj::DECIMAL;
                o.data.s = _strdup(t.text);
                obj_list.push_back(o);
            }
            else if (t.type == token::OPEN) {
                o.type = obj::BLOCK;
                o.data.p_block = new block(lex);
                obj_list.push_back(o);
            }
            else if (t.type != token::CLOSE)
                lex.unexpected_token(t);
            else
                return;
        }
    }

    void plexer::next_expected(token* p_tok, uint type) {
        next(p_tok);

        if (p_tok->type != type)
            throw va_error("Expected %s token but got token %s at %s:L%d",
                                         token::TYPE_MAP[type], p_tok->type_name(), filename(), line());
    }


    void plexer::unexpected_token(const token& t) const {
        throw va_error("Unexpected token %s at %s:L%d",
                                     t.type_name(), filename(), line());
    }


    void plexer::next(token* p_tok, bool eof_ok) {

        while (1) {

            if (state == NORMAL)
                lexer::next(p_tok);
            else if (state == TOK1) {
                p_tok->type = tok1.type;
                p_tok->text = tok1.text;
                state = TOK2;
            }
            else {
                p_tok->type = tok2.type;
                p_tok->text = tok2.text;
                state = NORMAL;
            }

            /* debug */
            //      printf("%s\n", p_tok->type_name());

            if (p_tok->type == token::END) {
                if (!eof_ok)
                    throw va_error("Unexpected EOF at %s:L%d", filename(), line());
                else
                    return;
            }

            if (p_tok->type == token::FAIL)
                throw va_error("Unrecognized token at %s:L%d", filename(), line());

            if (p_tok->type == token::COMMENT)
                continue;

            return;
        }
    }


    void plexer::save_and_lookahead(token* p_tok) {
        /* save our two tokens of lookahead */
        tok1.type = p_tok->type;
        strcpy(tok1.text, p_tok->text); // buffer overflows are myths

        next(p_tok);

        tok2.type = p_tok->type;
        strcpy(tok2.text, p_tok->text);

        /* set lexer to read from the saved tokens first */
        state = TOK1;
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


    void obj::store_date_from_str(char* s, lexer* p_lex) {
        /* we already are guaranteed to have a well-formed date string due to the
         * lexer's recognition rules */
        char* s_y = my_strsep(&s, ".");
        char* s_m = my_strsep(&s, ".");
        char* s_d = my_strsep(&s, ".");
        const int y = atoi(s_y);
        const int m = atoi(s_m);
        const int d = atoi(s_d);

        if (p_lex != nullptr) {
            if ( y <= 0 || y >= (1<<16) )
                throw va_error("Invalid year %d in date-type expression at %s:L%d", y, p_lex->filename(), p_lex->line());
            if ( m <= 0 || m > 12 )
                throw va_error("Invalid month %d in date-type expression at %s:L%d", m, p_lex->filename(), p_lex->line());
            if ( d <= 0 || d > 31 )
                throw va_error("Invalid day %d in date-type expression at %s:L%d", m, p_lex->filename(), p_lex->line());
        }

        data.date = {
            static_cast<uint16_t>(y),
            static_cast<uint8_t>(m),
            static_cast<uint8_t>(d)
        };
    }
}

