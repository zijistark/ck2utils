# Generated from CK2.g4 by ANTLR 4.5.2
from antlr4 import *
from io import StringIO


import re
import ck2classes as ck2c


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u0430\ud6d1\u8206\uad2d\u4417\uaef1\u8d80\uaadd\2\n")
        buf.write("=\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write("\4\b\t\b\4\t\t\t\3\2\6\2\25\n\2\r\2\16\2\26\3\2\3\2\3")
        buf.write("\3\5\3\34\n\3\3\3\3\3\3\4\3\4\7\4\"\n\4\f\4\16\4%\13\4")
        buf.write("\3\4\5\4(\n\4\3\5\3\5\3\6\3\6\3\7\3\7\3\b\3\b\7\b\62\n")
        buf.write("\b\f\b\16\b\65\13\b\3\b\3\b\3\t\6\t:\n\t\r\t\16\t;\2\2")
        buf.write("\n\3\3\5\4\7\5\t\6\13\7\r\b\17\t\21\n\3\2\7\4\2\13\13")
        buf.write("\"\"\4\2\f\f\17\17\5\2\13\f\17\17\"\"\5\2\f\f\17\17$%")
        buf.write("\t\2\13\f\17\17\"\"$%??}}\177\177B\2\3\3\2\2\2\2\5\3\2")
        buf.write("\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r\3\2\2\2")
        buf.write("\2\17\3\2\2\2\2\21\3\2\2\2\3\24\3\2\2\2\5\33\3\2\2\2\7")
        buf.write("\37\3\2\2\2\t)\3\2\2\2\13+\3\2\2\2\r-\3\2\2\2\17/\3\2")
        buf.write("\2\2\219\3\2\2\2\23\25\t\2\2\2\24\23\3\2\2\2\25\26\3\2")
        buf.write("\2\2\26\24\3\2\2\2\26\27\3\2\2\2\27\30\3\2\2\2\30\31\b")
        buf.write("\2\2\2\31\4\3\2\2\2\32\34\7\17\2\2\33\32\3\2\2\2\33\34")
        buf.write("\3\2\2\2\34\35\3\2\2\2\35\36\7\f\2\2\36\6\3\2\2\2\37\'")
        buf.write("\7%\2\2 \"\n\3\2\2! \3\2\2\2\"%\3\2\2\2#!\3\2\2\2#$\3")
        buf.write("\2\2\2$&\3\2\2\2%#\3\2\2\2&(\n\4\2\2\'#\3\2\2\2\'(\3\2")
        buf.write("\2\2(\b\3\2\2\2)*\7?\2\2*\n\3\2\2\2+,\7}\2\2,\f\3\2\2")
        buf.write("\2-.\7\177\2\2.\16\3\2\2\2/\63\7$\2\2\60\62\n\5\2\2\61")
        buf.write("\60\3\2\2\2\62\65\3\2\2\2\63\61\3\2\2\2\63\64\3\2\2\2")
        buf.write("\64\66\3\2\2\2\65\63\3\2\2\2\66\67\7$\2\2\67\20\3\2\2")
        buf.write("\28:\n\6\2\298\3\2\2\2:;\3\2\2\2;9\3\2\2\2;<\3\2\2\2<")
        buf.write("\22\3\2\2\2\t\2\26\33#\'\63;\3\b\2\2")
        return buf.getvalue()


class CK2Lexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]


    WHITESPACE = 1
    NEWLINE = 2
    COMMENT = 3
    TIS_TOK = 4
    KEL_TOK = 5
    KER_TOK = 6
    QUOTED = 7
    UNQUOTED = 8

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "'='", "'{'", "'}'" ]

    symbolicNames = [ "<INVALID>",
            "WHITESPACE", "NEWLINE", "COMMENT", "TIS_TOK", "KEL_TOK", "KER_TOK", 
            "QUOTED", "UNQUOTED" ]

    ruleNames = [ "WHITESPACE", "NEWLINE", "COMMENT", "TIS_TOK", "KEL_TOK", 
                  "KER_TOK", "QUOTED", "UNQUOTED" ]

    grammarFileName = "CK2.g4"

    def __init__(self, input=None):
        super().__init__(input)
        self.checkVersion("4.5.2")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


