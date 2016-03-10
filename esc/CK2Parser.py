# Generated from CK2.g4 by ANTLR 4.5.2
# encoding: utf-8
from antlr4 import *
from io import StringIO


import re
import ck2classes as ck2c

def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u0430\ud6d1\u8206\uad2d\u4417\uaef1\u8d80\uaadd\3\n")
        buf.write("y\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7\4\b")
        buf.write("\t\b\4\t\t\t\4\n\t\n\3\2\7\2\26\n\2\f\2\16\2\31\13\2\3")
        buf.write("\2\3\2\3\2\3\2\3\3\3\3\3\3\5\3\"\n\3\3\3\3\3\3\4\3\4\3")
        buf.write("\4\3\4\3\4\3\4\3\4\3\4\3\4\5\4/\n\4\3\4\3\4\5\4\63\n\4")
        buf.write("\3\5\3\5\3\5\3\5\3\5\3\6\3\6\7\6<\n\6\f\6\16\6?\13\6\3")
        buf.write("\6\3\6\3\6\3\6\3\6\7\6F\n\6\f\6\16\6I\13\6\3\6\3\6\3\6")
        buf.write("\5\6N\n\6\3\7\3\7\3\7\5\7S\n\7\3\7\3\7\3\b\3\b\3\b\5\b")
        buf.write("Z\n\b\3\b\3\b\3\t\3\t\3\t\5\ta\n\t\3\t\3\t\3\n\7\nf\n")
        buf.write("\n\f\n\16\ni\13\n\3\n\7\nl\n\n\f\n\16\no\13\n\3\n\7\n")
        buf.write("r\n\n\f\n\16\nu\13\n\3\n\3\n\3\n\2\2\13\2\4\6\b\n\f\16")
        buf.write("\20\22\2\2}\2\27\3\2\2\2\4\36\3\2\2\2\6\62\3\2\2\2\b\64")
        buf.write("\3\2\2\2\nM\3\2\2\2\fO\3\2\2\2\16V\3\2\2\2\20]\3\2\2\2")
        buf.write("\22m\3\2\2\2\24\26\5\b\5\2\25\24\3\2\2\2\26\31\3\2\2\2")
        buf.write("\27\25\3\2\2\2\27\30\3\2\2\2\30\32\3\2\2\2\31\27\3\2\2")
        buf.write("\2\32\33\5\22\n\2\33\34\7\2\2\3\34\35\b\2\1\2\35\3\3\2")
        buf.write("\2\2\36\37\5\22\n\2\37!\7\n\2\2 \"\7\5\2\2! \3\2\2\2!")
        buf.write("\"\3\2\2\2\"#\3\2\2\2#$\b\3\1\2$\5\3\2\2\2%&\5\n\6\2&")
        buf.write("\'\b\4\1\2\'\63\3\2\2\2()\5\4\3\2)*\b\4\1\2*\63\3\2\2")
        buf.write("\2+,\5\22\n\2,.\7\t\2\2-/\7\5\2\2.-\3\2\2\2./\3\2\2\2")
        buf.write("/\60\3\2\2\2\60\61\b\4\1\2\61\63\3\2\2\2\62%\3\2\2\2\62")
        buf.write("(\3\2\2\2\62+\3\2\2\2\63\7\3\2\2\2\64\65\5\4\3\2\65\66")
        buf.write("\5\f\7\2\66\67\5\6\4\2\678\b\5\1\28\t\3\2\2\29=\5\16\b")
        buf.write("\2:<\5\b\5\2;:\3\2\2\2<?\3\2\2\2=;\3\2\2\2=>\3\2\2\2>")
        buf.write("@\3\2\2\2?=\3\2\2\2@A\5\20\t\2AB\b\6\1\2BN\3\2\2\2CG\5")
        buf.write("\16\b\2DF\5\6\4\2ED\3\2\2\2FI\3\2\2\2GE\3\2\2\2GH\3\2")
        buf.write("\2\2HJ\3\2\2\2IG\3\2\2\2JK\5\20\t\2KL\b\6\1\2LN\3\2\2")
        buf.write("\2M9\3\2\2\2MC\3\2\2\2N\13\3\2\2\2OP\5\22\n\2PR\7\6\2")
        buf.write("\2QS\7\5\2\2RQ\3\2\2\2RS\3\2\2\2ST\3\2\2\2TU\b\7\1\2U")
        buf.write("\r\3\2\2\2VW\5\22\n\2WY\7\7\2\2XZ\7\5\2\2YX\3\2\2\2YZ")
        buf.write("\3\2\2\2Z[\3\2\2\2[\\\b\b\1\2\\\17\3\2\2\2]^\5\22\n\2")
        buf.write("^`\7\b\2\2_a\7\5\2\2`_\3\2\2\2`a\3\2\2\2ab\3\2\2\2bc\b")
        buf.write("\t\1\2c\21\3\2\2\2df\7\4\2\2ed\3\2\2\2fi\3\2\2\2ge\3\2")
        buf.write("\2\2gh\3\2\2\2hj\3\2\2\2ig\3\2\2\2jl\7\5\2\2kg\3\2\2\2")
        buf.write("lo\3\2\2\2mk\3\2\2\2mn\3\2\2\2ns\3\2\2\2om\3\2\2\2pr\7")
        buf.write("\4\2\2qp\3\2\2\2ru\3\2\2\2sq\3\2\2\2st\3\2\2\2tv\3\2\2")
        buf.write("\2us\3\2\2\2vw\b\n\1\2w\23\3\2\2\2\17\27!.\62=GMRY`gm")
        buf.write("s")
        return buf.getvalue()


class CK2Parser ( Parser ):

    grammarFileName = "CK2.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "'='", "'{'", "'}'" ]

    symbolicNames = [ "<INVALID>", "WHITESPACE", "NEWLINE", "COMMENT", "TIS_TOK", 
                      "KEL_TOK", "KER_TOK", "QUOTED", "UNQUOTED" ]

    RULE_toplevel = 0
    RULE_key = 1
    RULE_value = 2
    RULE_pair = 3
    RULE_obj = 4
    RULE_tis = 5
    RULE_kel = 6
    RULE_ker = 7
    RULE_comments = 8

    ruleNames =  [ "toplevel", "key", "value", "pair", "obj", "tis", "kel", 
                   "ker", "comments" ]

    EOF = Token.EOF
    WHITESPACE=1
    NEWLINE=2
    COMMENT=3
    TIS_TOK=4
    KEL_TOK=5
    KER_TOK=6
    QUOTED=7
    UNQUOTED=8

    def __init__(self, input:TokenStream):
        super().__init__(input)
        self.checkVersion("4.5.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None



    def resolve(self, value):
        if re.fullmatch(r'\d*\.\d*\.\d*', value):
            return ck2c.Date
        elif re.fullmatch(r'\d+(\.\d+)?', value):
            return ck2c.Number
        else:
            return ck2c.String


    class ToplevelContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.v = None
            self._pair = None # PairContext
            self.a = list() # of PairContexts
            self.b = None # CommentsContext

        def EOF(self):
            return self.getToken(CK2Parser.EOF, 0)

        def comments(self):
            return self.getTypedRuleContext(CK2Parser.CommentsContext,0)


        def pair(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CK2Parser.PairContext)
            else:
                return self.getTypedRuleContext(CK2Parser.PairContext,i)


        def getRuleIndex(self):
            return CK2Parser.RULE_toplevel




    def toplevel(self):

        localctx = CK2Parser.ToplevelContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_toplevel)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 21
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,0,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 18
                    localctx._pair = self.pair()
                    localctx.a.append(localctx._pair) 
                self.state = 23
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,0,self._ctx)

            self.state = 24
            localctx.b = self.comments()
            self.state = 25
            self.match(CK2Parser.EOF)
            localctx.v = ck2c.TopLevel([x.v for x in localctx.a], localctx.b.v)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class KeyContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.v = None
            self.a = None # CommentsContext
            self.b = None # Token
            self.c = None # Token

        def comments(self):
            return self.getTypedRuleContext(CK2Parser.CommentsContext,0)


        def UNQUOTED(self):
            return self.getToken(CK2Parser.UNQUOTED, 0)

        def COMMENT(self):
            return self.getToken(CK2Parser.COMMENT, 0)

        def getRuleIndex(self):
            return CK2Parser.RULE_key




    def key(self):

        localctx = CK2Parser.KeyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_key)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 28
            localctx.a = self.comments()
            self.state = 29
            localctx.b = self.match(CK2Parser.UNQUOTED)
            self.state = 31
            self._errHandler.sync(self);
            la_ = self._interp.adaptivePredict(self._input,1,self._ctx)
            if la_ == 1:
                self.state = 30
                localctx.c = self.match(CK2Parser.COMMENT)


            localctx.v = self.resolve((None if localctx.b is None else localctx.b.text))(localctx.a.v, (None if localctx.b is None else localctx.b.text), (None if localctx.c is None else localctx.c.text) if localctx.c else None)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class ValueContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.v = None
            self.a = None # ObjContext
            self.b = None # Token
            self.c = None # Token

        def obj(self):
            return self.getTypedRuleContext(CK2Parser.ObjContext,0)


        def key(self):
            return self.getTypedRuleContext(CK2Parser.KeyContext,0)


        def comments(self):
            return self.getTypedRuleContext(CK2Parser.CommentsContext,0)


        def QUOTED(self):
            return self.getToken(CK2Parser.QUOTED, 0)

        def COMMENT(self):
            return self.getToken(CK2Parser.COMMENT, 0)

        def getRuleIndex(self):
            return CK2Parser.RULE_value




    def value(self):

        localctx = CK2Parser.ValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_value)
        try:
            self.state = 48
            self._errHandler.sync(self);
            la_ = self._interp.adaptivePredict(self._input,3,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 35
                localctx.a = self.obj()
                localctx.v = localctx.a.v
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 38
                localctx.a = self.key()
                localctx.v = localctx.a.v
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 41
                localctx.a = self.comments()
                self.state = 42
                localctx.b = self.match(CK2Parser.QUOTED)
                self.state = 44
                self._errHandler.sync(self);
                la_ = self._interp.adaptivePredict(self._input,2,self._ctx)
                if la_ == 1:
                    self.state = 43
                    localctx.c = self.match(CK2Parser.COMMENT)


                localctx.v = ck2c.String(localctx.a.v, (None if localctx.b is None else localctx.b.text)[1:-1], (None if localctx.c is None else localctx.c.text) if localctx.c else None)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class PairContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.v = None
            self.a = None # KeyContext
            self.b = None # TisContext
            self.c = None # ValueContext

        def key(self):
            return self.getTypedRuleContext(CK2Parser.KeyContext,0)


        def tis(self):
            return self.getTypedRuleContext(CK2Parser.TisContext,0)


        def value(self):
            return self.getTypedRuleContext(CK2Parser.ValueContext,0)


        def getRuleIndex(self):
            return CK2Parser.RULE_pair




    def pair(self):

        localctx = CK2Parser.PairContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_pair)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 50
            localctx.a = self.key()
            self.state = 51
            localctx.b = self.tis()
            self.state = 52
            localctx.c = self.value()
            localctx.v = ck2c.Pair(localctx.a.v, localctx.b.v, localctx.c.v)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class ObjContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.v = None
            self.a = None # KelContext
            self._pair = None # PairContext
            self.b = list() # of PairContexts
            self.c = None # KerContext
            self._value = None # ValueContext

        def kel(self):
            return self.getTypedRuleContext(CK2Parser.KelContext,0)


        def ker(self):
            return self.getTypedRuleContext(CK2Parser.KerContext,0)


        def pair(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CK2Parser.PairContext)
            else:
                return self.getTypedRuleContext(CK2Parser.PairContext,i)


        def value(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CK2Parser.ValueContext)
            else:
                return self.getTypedRuleContext(CK2Parser.ValueContext,i)


        def getRuleIndex(self):
            return CK2Parser.RULE_obj




    def obj(self):

        localctx = CK2Parser.ObjContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_obj)
        try:
            self.state = 75
            self._errHandler.sync(self);
            la_ = self._interp.adaptivePredict(self._input,6,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 55
                localctx.a = self.kel()
                self.state = 59
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,4,self._ctx)
                while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                    if _alt==1:
                        self.state = 56
                        localctx._pair = self.pair()
                        localctx.b.append(localctx._pair) 
                    self.state = 61
                    self._errHandler.sync(self)
                    _alt = self._interp.adaptivePredict(self._input,4,self._ctx)

                self.state = 62
                localctx.c = self.ker()
                localctx.v = ck2c.Obj(localctx.a.v, [x.v for x in localctx.b], localctx.c.v)
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 65
                localctx.a = self.kel()
                self.state = 69
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,5,self._ctx)
                while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                    if _alt==1:
                        self.state = 66
                        localctx._value = self.value()
                        localctx.b.append(localctx._value) 
                    self.state = 71
                    self._errHandler.sync(self)
                    _alt = self._interp.adaptivePredict(self._input,5,self._ctx)

                self.state = 72
                localctx.c = self.ker()
                localctx.v = ck2c.Obj(localctx.a.v, [x.v for x in localctx.b], localctx.c.v)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class TisContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.v = None
            self.a = None # CommentsContext
            self.b = None # Token
            self.c = None # Token

        def comments(self):
            return self.getTypedRuleContext(CK2Parser.CommentsContext,0)


        def TIS_TOK(self):
            return self.getToken(CK2Parser.TIS_TOK, 0)

        def COMMENT(self):
            return self.getToken(CK2Parser.COMMENT, 0)

        def getRuleIndex(self):
            return CK2Parser.RULE_tis




    def tis(self):

        localctx = CK2Parser.TisContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_tis)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 77
            localctx.a = self.comments()
            self.state = 78
            localctx.b = self.match(CK2Parser.TIS_TOK)
            self.state = 80
            self._errHandler.sync(self);
            la_ = self._interp.adaptivePredict(self._input,7,self._ctx)
            if la_ == 1:
                self.state = 79
                localctx.c = self.match(CK2Parser.COMMENT)


            localctx.v = ck2c.Op(localctx.a.v, (None if localctx.b is None else localctx.b.text), (None if localctx.c is None else localctx.c.text) if localctx.c else None)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class KelContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.v = None
            self.a = None # CommentsContext
            self.b = None # Token
            self.c = None # Token

        def comments(self):
            return self.getTypedRuleContext(CK2Parser.CommentsContext,0)


        def KEL_TOK(self):
            return self.getToken(CK2Parser.KEL_TOK, 0)

        def COMMENT(self):
            return self.getToken(CK2Parser.COMMENT, 0)

        def getRuleIndex(self):
            return CK2Parser.RULE_kel




    def kel(self):

        localctx = CK2Parser.KelContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_kel)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 84
            localctx.a = self.comments()
            self.state = 85
            localctx.b = self.match(CK2Parser.KEL_TOK)
            self.state = 87
            self._errHandler.sync(self);
            la_ = self._interp.adaptivePredict(self._input,8,self._ctx)
            if la_ == 1:
                self.state = 86
                localctx.c = self.match(CK2Parser.COMMENT)


            localctx.v = ck2c.Op(localctx.a.v, (None if localctx.b is None else localctx.b.text), (None if localctx.c is None else localctx.c.text) if localctx.c else None)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class KerContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.v = None
            self.a = None # CommentsContext
            self.b = None # Token
            self.c = None # Token

        def comments(self):
            return self.getTypedRuleContext(CK2Parser.CommentsContext,0)


        def KER_TOK(self):
            return self.getToken(CK2Parser.KER_TOK, 0)

        def COMMENT(self):
            return self.getToken(CK2Parser.COMMENT, 0)

        def getRuleIndex(self):
            return CK2Parser.RULE_ker




    def ker(self):

        localctx = CK2Parser.KerContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_ker)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 91
            localctx.a = self.comments()
            self.state = 92
            localctx.b = self.match(CK2Parser.KER_TOK)
            self.state = 94
            self._errHandler.sync(self);
            la_ = self._interp.adaptivePredict(self._input,9,self._ctx)
            if la_ == 1:
                self.state = 93
                localctx.c = self.match(CK2Parser.COMMENT)


            localctx.v = ck2c.Op(localctx.a.v, (None if localctx.b is None else localctx.b.text), (None if localctx.c is None else localctx.c.text) if localctx.c else None)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class CommentsContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.v = None
            self._COMMENT = None # Token
            self.a = list() # of Tokens

        def NEWLINE(self, i:int=None):
            if i is None:
                return self.getTokens(CK2Parser.NEWLINE)
            else:
                return self.getToken(CK2Parser.NEWLINE, i)

        def COMMENT(self, i:int=None):
            if i is None:
                return self.getTokens(CK2Parser.COMMENT)
            else:
                return self.getToken(CK2Parser.COMMENT, i)

        def getRuleIndex(self):
            return CK2Parser.RULE_comments




    def comments(self):

        localctx = CK2Parser.CommentsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_comments)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 107
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,11,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 101
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    while _la==CK2Parser.NEWLINE:
                        self.state = 98
                        self.match(CK2Parser.NEWLINE)
                        self.state = 103
                        self._errHandler.sync(self)
                        _la = self._input.LA(1)

                    self.state = 104
                    localctx._COMMENT = self.match(CK2Parser.COMMENT)
                    localctx.a.append(localctx._COMMENT) 
                self.state = 109
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,11,self._ctx)

            self.state = 113
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==CK2Parser.NEWLINE:
                self.state = 110
                self.match(CK2Parser.NEWLINE)
                self.state = 115
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            localctx.v = [x.text if x else None for x in localctx.a]
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





