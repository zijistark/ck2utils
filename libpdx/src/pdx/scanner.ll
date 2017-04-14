
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
STR     [a-zA-Z\xC0-\xFF0-9_\-\.\x83\x8A\x8C\x8E\x9A\x9C\x9E\x9F]+
WS      [ \t\r\n\xA0]+
QSTR    \"[^"\n]*\"
DATE    -?[0-9]{1,4}\.[0-9]{1,2}\.[0-9]{1,2}
%%

{DATE}                     { return pdx::token::DATE; }
"\""{DATE}"\""             { return pdx::token::QDATE; }
("-"|"+")?{D}+"."{D}*      { return pdx::token::DECIMAL; }
("-"|"+")?{D}+             { return pdx::token::INTEGER; }
"=="|"="|">"|">="|"<"|"<=" { return pdx::token::OPERATOR; }
"{"                        { return pdx::token::OPEN; }
"}"                        { return pdx::token::CLOSE; }
{STR}                      { return pdx::token::STR; }
{QSTR}                     { return pdx::token::QSTR; }
"#".*                      { return pdx::token::COMMENT; }
{WS}+                      /* skip */
.                          { return pdx::token::FAIL; }

%%
