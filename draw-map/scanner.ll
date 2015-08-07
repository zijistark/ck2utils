
/* basic startup scanner for reacclimating myself with flex */

%option 8bit
%option warn nodefault
%option yylineno
%option noyymore noyywrap
%option batch
%option nounistd never-interactive

%top{
    #include "token.h"
}

D       [0-9]
STR     [a-zA-Z\xC0-\xFF0-9_\-\x83\x8A\x8C\x8E\x9A\x9C\x9E\x9F]+
WS	    [ \t\r\n\xA0]+
QSTR    \"[^"\n]*\"
DATE    [0-9]{1,4}\.[0-9]{1,2}\.[0-9]{1,2}
%%

{DATE}          { return token::DATE; }
"\""{DATE}"\""  { return token::QDATE; }
"-"?{D}+"."{D}+ { return token::FLOAT; }
"-"?{D}+        { return token::INT; }
"="             { return token::EQ; }
"{"             { return token::OPEN; }
"}"             { return token::CLOSE; }
{STR}           { return token::STR; }
{QSTR}          { return token::QSTR; }
"#".*"\r"?$     { return token::COMMENT; }
{WS}+           /* skip */
.		        { return token::FAIL; }

%%
