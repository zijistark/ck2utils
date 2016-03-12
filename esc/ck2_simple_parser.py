#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CAVEAT UTILITOR
#
# This file was automatically generated by Grako.
#
#    https://pypi.python.org/pypi/grako/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.


from __future__ import print_function, division, absolute_import, unicode_literals

from grako.parsing import graken, Parser
from grako.util import re, RE_FLAGS, generic_main  # noqa


__version__ = (2016, 3, 12, 0, 46, 54, 5)

__all__ = [
    'CK2SimpleParser',
    'CK2SimpleSemantics',
    'main'
]


class CK2SimpleParser(Parser):
    def __init__(self,
                 whitespace=None,
                 nameguard=None,
                 comments_re='#.*$',
                 eol_comments_re=None,
                 ignorecase=None,
                 left_recursion=True,
                 **kwargs):
        super(CK2SimpleParser, self).__init__(
            whitespace=whitespace,
            nameguard=nameguard,
            comments_re=comments_re,
            eol_comments_re=eol_comments_re,
            ignorecase=ignorecase,
            left_recursion=left_recursion,
            **kwargs
        )

    @graken()
    def _file_(self):

        def block0():
            self._pair_()
        self._closure(block0)
        self._check_eof()

    @graken()
    def _pair_(self):
        self._key_()
        self.ast['key'] = self.last_node
        self._token('=')
        with self._group():
            with self._choice():
                with self._option():
                    self._object_()
                with self._option():
                    self._item_()
                self._error('no available options')
        self.ast['value'] = self.last_node

        self.ast._define(
            ['key', 'value'],
            []
        )

    @graken()
    def _key_(self):
        with self._choice():
            with self._option():
                self._date_()
            with self._option():
                self._number_()
            with self._option():
                self._name_()
            self._error('no available options')

    @graken()
    def _object_(self):
        self._token('{')
        with self._group():
            with self._choice():
                with self._option():

                    def block1():
                        self._pair_()
                    self._positive_closure(block1)
                with self._option():

                    def block2():
                        self._item_()
                    self._positive_closure(block2)
                with self._option():
                    pass
                self._error('no available options')
        self.ast['@'] = self.last_node
        self._token('}')

    @graken()
    def _item_(self):
        with self._choice():
            with self._option():
                self._string_()
            with self._option():
                self._key_()
            self._error('no available options')

    @graken()
    def _string_(self):
        self._pattern(r'".*?"')

    @graken()
    def _name_(self):
        self._pattern(r'[^\s"#={}]+')

    @graken()
    def _number_(self):
        self._pattern(r'\d+(\.\d+)?(?![^\s"#={}])')

    @graken()
    def _date_(self):
        self._pattern(r'\d*\.\d*\.\d*(?![^\s"#={}])')


class CK2SimpleSemantics(object):
    def file(self, ast):
        return ast

    def pair(self, ast):
        return ast

    def key(self, ast):
        return ast

    def object(self, ast):
        return ast

    def item(self, ast):
        return ast

    def string(self, ast):
        return ast

    def name(self, ast):
        return ast

    def number(self, ast):
        return ast

    def date(self, ast):
        return ast


def main(
        filename,
        startrule,
        trace=False,
        whitespace=None,
        nameguard=None,
        comments_re='#.*$',
        eol_comments_re=None,
        ignorecase=None,
        left_recursion=True,
        **kwargs):

    with open(filename) as f:
        text = f.read()
    parser = CK2SimpleParser(parseinfo=False)
    ast = parser.parse(
        text,
        startrule,
        filename=filename,
        trace=trace,
        whitespace=whitespace,
        nameguard=nameguard,
        ignorecase=ignorecase,
        **kwargs)
    return ast

if __name__ == '__main__':
    import json
    ast = generic_main(main, CK2SimpleParser, name='CK2Simple')
    print('AST:')
    print(ast)
    print()
    print('JSON:')
    print(json.dumps(ast, indent=2))
    print()
