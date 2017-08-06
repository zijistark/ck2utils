
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
STR     [a-zA-Z\xC0-\xFF0-9_:@'\[\]\-\.\x83\x8A\x8C\x8E\x91-\x92\x9A\x9C\x9E\x9F]+
WS      [ \t\r\n\xA0]+
QSTR    \"[^"\n]*\"
DATE    -?[0-9]{1,4}\.[0-9]{1,2}\.[0-9]{1,2}
%%

{DATE}                     { return ck2::token::DATE; }
"\""{DATE}"\""             { return ck2::token::QDATE; }
("-"|"+")?{D}+"."{D}*      { return ck2::token::DECIMAL; }
("-"|"+")?{D}+             { return ck2::token::INTEGER; }
"=="|"="|">"|">="|"<"|"<=" { return ck2::token::OPERATOR; }
"{"                        { return ck2::token::OPEN; }
"}"                        { return ck2::token::CLOSE; }
{STR}                      { return ck2::token::STR; }
{QSTR}                     { return ck2::token::QSTR; }
"#".*                      { return ck2::token::COMMENT; }
{WS}+                      /* skip */
.                          { return ck2::token::FAIL; }

%%
