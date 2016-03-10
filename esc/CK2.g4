grammar CK2;

@header {
import re
import ck2classes as ck2c
}

@parser::members {
def resolve(self, value):
    if re.fullmatch(r'\d*\.\d*\.\d*', value):
        return ck2c.Date
    elif re.fullmatch(r'\d+(\.\d+)?', value):
        return ck2c.Number
    else:
        return ck2c.String
}

toplevel returns [v]
    : a+=pair* b=comments EOF
        {$v = ck2c.TopLevel([x.v for x in $a], $b.v)} ;
key returns [v]
    : a=comments b=UNQUOTED c=COMMENT?
        {$v = self.resolve($b.text)($a.v, $b.text, $c.text if $c else None)} ;
value returns [v]
    : a=obj
        {$v = $a.v}
    | a=key
        {$v = $a.v}
    | a=comments b=QUOTED c=COMMENT?
        {$v = ck2c.String($a.v, $b.text[1:-1], $c.text if $c else None)} ;
pair returns [v]
    : a=key b=tis c=value
        {$v = ck2c.Pair($a.v, $b.v, $c.v)} ;
obj returns [v]
    : a=kel b+=pair* c=ker
        {$v = ck2c.Obj($a.v, [x.v for x in $b], $c.v)}
    | a=kel b+=value* c=ker
        {$v = ck2c.Obj($a.v, [x.v for x in $b], $c.v)} ;
tis returns [v]
    : a=comments b=TIS_TOK c=COMMENT?
        {$v = ck2c.Op($a.v, $b.text, $c.text if $c else None)} ;
kel returns [v]
    : a=comments b=KEL_TOK c=COMMENT?
        {$v = ck2c.Op($a.v, $b.text, $c.text if $c else None)} ;
ker returns [v]
    : a=comments b=KER_TOK c=COMMENT?
        {$v = ck2c.Op($a.v, $b.text, $c.text if $c else None)} ;
comments returns [v]
    : (NEWLINE* a+=COMMENT)* NEWLINE*
        {$v = [x.text if x else None for x in $a]} ;

WHITESPACE  : [ \t]+ -> skip ;
NEWLINE     : '\r'? '\n' ;
COMMENT     : '#' (~[\r\n]* ~[ \t\r\n])? ;
TIS_TOK     : '=' ;
KEL_TOK     : '{' ;
KER_TOK     : '}' ;
QUOTED      : '"' ~["#\r\n]* '"' ;
UNQUOTED    : ~[ \t\r\n"#={}]+ ;
