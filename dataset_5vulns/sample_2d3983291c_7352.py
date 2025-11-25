#!/usr/bin/env python
#
# Copyright 2016 Medoly
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Human-Optimized Config Object Notation"""


import re
import os
import sqlite3

from .errors import HoconParserException, HoconTokenizerException
from .select_config import SelectConfig


class BaseConfig(object):
    """Base Config

    :param root:  the real hocon root value
    :type root: HoconRoot
    :raises: AttributeError
    """

    def __init__(self, root):

        if root.value is None:
            raise AttributeError(" error")
        self.root = root.value  # HoconValue
        self.substitutions = root.substitutions  # List<HoconSubstitution>

    def get_node(self, path):
        """Gets the path data node"""
        keys = path.split(".")
        current_node = self.root
        if current_node is None:
            raise KeyError("Doesn't exist the key:" % (path))
        for key in keys:
            current_node = current_node.get_child_object(key)
        return current_node

    def __str__(self):
        if self.root is None:
            return ""
        return str(self.root)

    def to_dict(self):
        """Converts to dict"""
        return self.root.get()

    def to_select_config(self):
        """Converts to SelectConfig"""
        return SelectConfig(self.root.get())

    def has_path(self, path):
        """Check  the config has the path node"""
        return self.get_node(path) is not None


class Config(BaseConfig):
    """Hocon config

    Extends:

        BaseConfig

    """

    def get_bool(self, path, default=False):
        """Gets the bool data value, defaults not found returns the default value"""
        value = self.get_node(path)
        if value is None:
            return default
        return value.get_bool()

    def get_int(self, path, default=0):
        """Gets the integer data value, defaults not found returns the default value"""
        value = self.get_node(path)
        if value is None:
            return default
        return value.get_int()

    def get(self, path, default=None):
        """Gets the  string data value, defaults not found returns the default value"""
        value = self.get_node(path)
        if value is None:
            return default
        return value.get_string()

    get_string = get

    def get_float(self, path, default=0.0):
        """Gets the  float data value, defaults not found returns the default value"""
        value = self.get_node(path)
        if value is None:
            return default
        return value.get_float()

    def get_bool_list(self, path):
        """Gets the  bool data value, defaults not found returns the default value"""
        value = self.get_node(path)

        return value.get_bool_list()

    def get_float_list(self, path):
        """Gets the  float list data value"""
        value = self.get_node(path)

        return value.get_float_list()

    def get_int_list(self, path):
        """Gets the  int list data value"""
        value = self.get_node(path)

        return value.get_int_list()

    def get_list(self, path):
        """Gets the  list ojbect data value"""
        value = self.get_node(path)

        return value.get_list()

    def get_value(self, path):
        """Gets the  string data node, defaults not found returns the default value"""
        return self.get_node(path)


class PyConfig(BaseConfig):
    """Python style ocnfig"""

    def get(self, path, default=None):
        """Get real type value"""
        value = self.get_node(path)
        if value is None:
            return default
        return value.get()


class ConfigFactory(object):
    """Config create tool"""

    @classmethod
    def empty(cls):
        """Creates a empty hocon config"""
        return cls.parse("")

    @classmethod
    def parse(cls, hocon, func=None, pystyle=False):
        """Parses and creates a hocon config from  text string"""
        res = Parser.parse(hocon, func, pystyle)
        configCls = PyConfig if pystyle else Config
        return configCls(res)

    @classmethod
    def parse_file(cls, path, pystyle=False):
        """Parses and creates a hocon confi from  the file path"""
        with open(path) as f:
            content = f.read()
            return cls.parse(content, pystyle=pystyle)

    @classmethod
    def from_json(cls, jsonObj, pystyle=False):
        """Creates hocon from json data"""
        import json
        text = json.dumps(jsonObj)
        return cls.parse(text, pystyle)


class HoconRoot(object):
    """Hocon config object"""

    def __init__(self, value=None, substitutions=None):
        self.value = value or HoconValue()
        self.substitutions = substitutions or []


class MightBeAHoconObject(object):
    """Hocon Maybe a hocon object"""
    pass


class HoconValue(MightBeAHoconObject):
    """Hocon data value node object

    Extends
    :
        MightBeAHoconObject
    """

    def __init__(self, values=None):
        self.values = values or []

    def at_key(self, key):
        """Get data node by key"""
        o = HoconObject()
        o.get_or_create_key(key)
        o[key] = self
        r = HoconValue().append_value(o)
        return Config(HoconRoot(r))

    def get_object(self):
        """Get the real current object"""
        raw = self.values[0] if len(self.values) >= 1 else None

        if isinstance(raw, HoconObject):
            return raw

        if isinstance(raw, MightBeAHoconObject):
            if raw.is_object():
                return raw.get_object()
        return raw

    def is_object(self):
        """Check is an object"""
        return self.get_object() is not None

    def append_value(self, value):
        """Append a value inf current node"""
        # if isinstance(value, HoconElement):
        self.values.append(value)
        return self

    def clear(self):
        """Clear the sub nodes"""
        self.values[:] = []

    def new_value(self, value):
        """Clear the sub values and reset by the new value"""
        self.clear()
        self.append_value(value)

    def is_string(self):
        """Check is string object"""
        return all([v.is_string() for v in self.values])

    def get_array(self):
        """Get the datas value as node list"""
        x = []
        for arr in self.values:
            if arr.is_array():
                x.extend(arr.get_array())
        return x

    def get_list(self):
        """Get the datas value as string list"""
        return [e.get_string() for e in self.get_array()]

    def is_array(self):
        """Is array?"""
        return self.get_list() is not None

    def get(self):
        """Get the the sub node"""
        if len(self.values) == 1:
            return self.values[0].get_object()
        return [_.get_object() for _ in self.values]

    def contat(self):
        """Contat the contain objects as string"""
        return "".join([_.get_string() for _ in self.values])

    def get_child_object(self, key):
        """Get chield object"""
        return self.get_object().get_key(key)

    def get_bool(self):
        """Get the current object as bool value"""
        v = self.get_string()
        if v == 'on':
            return True
        if v == 'off':
            return False

        if v == 'true':
            return True
        if v == 'false':
            return False
        raise ValueError("Unknown boolean format: " + v)

    def get_string(self):
        """Get the nodes as string"""
        if self.is_string():
            return self.contat()

        return None

    def _get_by_type(self, cast):
        """Get the value node by cast type
        :param cast: the cast object  (eg. int, float, string)
        """
        v = self.get_string()
        try:
            return cast(v)
        except:
            raise TypeError("Invalid %s format for: %s" % (str(cast), v))

    def get_int(self):
        """Get the data value as int data"""
        return self._get_by_type(int)

    def get_float(self):
        """Get the data value as float data"""
        return self._get_by_type(float)

    def get_int_list(self):
        """Get the data value as int list"""
        return [e.get_int() for e in self.get_array()]

    def get_float_list(self):
        """Get the data value as float list"""
        return [e.get_float() for e in self.get_array()]

    def __str__(self):
        if self.is_string():
            return self.get_string()

        if len(self.values) > 1:
            return str.format("[{0}]", "|".join([e.get_string() for e in self.get_list()]))

        if self.is_object():
            return str(self.get_object())


class HoconElement(object):
    """Base Hocon element"""
    pass


class HoconArray(HoconElement, list):
    """Hocon Array object


   Extends::

        HoconElement
        list
    """

    def is_string(self):
        return False

    def get_string(self):
        raise BaseException(" error")

    def is_array(self):
        return True

    def get_object(self):
        return [_.get() for _ in self]

    def get_array(self):
        return self


class HoconLiteral(HoconElement):
    """Hocon literal value node

    Extends::

        HoconElement
    """

    def __init__(self, text=''):
        self.value = text

    def is_string(self):
        return True

    def get_string(self):
        return self.value

    def is_array(self):
        return False

    def is_object(self):
        return False

    def get_object(self):
        return self.value

    def get_list(self):
        raise BaseException(" error")

    def __str__(self):
        return self.value


class HoconObject(HoconElement, dict):
    """Hocon abstract object

    Extends::

        HoconElement
        dict
    """

    def is_string(self):
        return False

    def get_string(self):
        raise BaseException(" error")

    def is_array(self):
        return False

    def is_object(self):
        return True

    def get_object(self):
        return {k: v.get() for k, v in self.items()}

    def get_list(self):
        raise BaseException(" error")

    def get_key(self, key):
        return self.get(key)

    def get_or_create_key(self, key):
        """Get or create a new value by key

        :param key: the data node key
        :type key: string
        :returns: the child node
        :rtype: HoconValue
        """
        if key in self:
            return self.get(key)

        child = HoconValue()
        self[key] = child

        return child

    def merge(self, obj):
        """Merge the node into current node"""
        for k, v in obj.items():
            if k in self:
                this_item = self[k]
                if this_item.is_object() and v.value.is_object():
                    this_item.get_object().merge(v.value.get_object())
            else:
                self[k] = v.value


class HoconSubstitution(HoconElement, MightBeAHoconObject):
    """Hocon $ variable"""

    def __init__(self, path=None):
        self.path = path
        self.resolved_value = None

    def is_string(self):
        return self.resolved_value and self.resolved_value.is_string()

    def get_string(self):
        return self.resolved_value and self.resolved_value.get_string()

    def is_array(self):
        return self.resolved_value.is_array()

    def get_list(self):
        return self.resolved_value.get_list()

    def is_object(self):
        return self.resolved_value and self.resolved_value.is_object()

    def get_object(self):
        return self.resolved_value.get_object()


class TokenType(object):
    """Token Type Enum"""

    Comment = 1
    """Comment Type"""

    Key = 2
    """Key Type"""

    LiteralValue = 3
    """Literal Value"""

    Assign = 4
    """Literal Value"""

    ObjectStart = 5
    """The object start type"""

    ObjectEnd = 6
    """The object end type"""
    Dot = 7
    """Dot Type"""

    EoF = 8
    """EoF Type"""

    ArrayStart = 9
    """The start of array"""

    ArrayEnd = 10
    """The end of array"""

    Comma = 11
    """The end of array"""

    Substitute = 12
    """The substitute type"""

    Include = 13
    """Include Type"""


class Token(object):
    """Token object

    :param token_type: the token type
    :type token_type: string
    :param source_index: the  begin source index
    :type source_index: int
    :param length: the length of token
    :type length: the length of token
    :param value: the value of token, defaults to None
    :type value: string, optional
    """

    def __init__(self, token_type, source_index, length, value=None):
        self.source_index = source_index
        self.length = length
        self.value = value
        self.token_type = token_type

    @staticmethod
    def Key(key, source_index, source_length):
        """Create Key Token

        :param source_index: the  begin source index
        :type source_index: int
        :param length: the length of token
        :type length: the length of token
        """
        return Token(TokenType.Key, source_index, source_length, key)

    @staticmethod
    def Substitution(path, source_index, source_length):
        """Create Substitution Token

        :param source_index: the  begin source index
        :type source_index: int
        :param length: the length of token
        :type length: the length of token
        """
        return Token(TokenType.Substitute, source_index, source_length, path)

    @staticmethod
    def LiteralValue(value, source_index, source_length):
        """Create Literal Value Token

        :param source_index: the  begin source index
        :type source_index: int
        :param length: the length of token
        :type length: the length of token
        """
        return Token(TokenType.LiteralValue, source_index, source_length, value)

    @staticmethod
    def Include(path, source_index, source_length):
        """Create Literal Value Token

        :param source_index: the  begin source index
        :type source_index: int
        :param length: the length of token
        :type length: the length of token
        """
        return Token(TokenType.Include, source_index, source_length, path)


class Parser(object):
    """The hocon parser"""

    def __init__(self):
        self._substitutions = []
        self._reader = None
        self._include_callback = None
        self._diagnostics_stack = []
        self._root = None

    def push_diagnostics(self, message):
        """Added diagnostic message"""
        self._diagnostics_stack.append(message)

    def pop_diagnostics(self):
        """Pop out diagnostic message"""
        self._diagnostics_stack.pop()

    def get_diagnostics_stacktrace(self):
        current_path = "".join(self._diagnostics_stack)
        return str.format("Current path: {0}", current_path)

    @staticmethod
    def parse(text, include_callback, pystyle=False):
        """Create a paser and parse the text , returns a hocon config

        :param text: the hocon text
        :type text: string
        :param include_callback: the included handle callback
        :type include_callback: types.Function
        :param pystyle: If ``Ture`` use the PyConfig and converts the data node to real type data, defaults to False
        :type pystyle: bool, optional
        :returns: the hocon conguration
        :rtype: PyConfig | Config
        """
        return Parser().parse_text(text, include_callback, pystyle)

    def parse_text(self, text, include_callback, pystyle):
        """Parse the text , returns a hocon config

        :param text: the hocon text
        :type text: string
        :param include_callback: the included handle callback
        :type include_callback: types.Function
        :param pystyle: If ``Ture`` use the PyConfig and converts the data node to real type data, defaults to False
        :type pystyle: bool, optional
        :returns: the hocon conguration
        :rtype: PyConfig | Config
        :raises: HoconParserException
        """
        self._include_callback = include_callback
        self._root = HoconValue()
        self._reader = HoconTokenizer(text, pystyle)
        self._reader.pull_whitespace_and_comments()
        self.parse_object(self._root, True, "")
        c = Config(HoconRoot(self._root, []))

        for sub in self._substitutions:

            res = c.get_value(sub.path)

            if res is None:
                raise HoconParserException(
                    "Unresolved substitution:" + sub.path)
            sub.resolved_value = res
        return HoconRoot(self._root, self._substitutions)

    def parse_object(self, current, root, current_path):
        """Parse the current path object"""
        try:
            self.push_diagnostics("{")
            if current.is_object():
                # Todo: blabla
                # the value of this object is already an dict
                pass
            else:
                current.new_value(HoconObject())
            current_object = current.get_object()

            while not self._reader.eof:
                t = self._reader.pull_next()
                # to do add include context and config parse
                if t.token_type == TokenType.Include:
                    included = self._include_callback(t.value)
                    substitutions = included.substitutions
                    for substitution in substitutions:
                        substitution.path = current_path + "." + substitution.path
                    self._substitutions.extend(substitutions)
                    other_obj = included.value.get_object()
                    current.get_object().merge(other_obj)

                elif t.token_type == TokenType.EoF:
                    # not empty path
                    if current_path:
                        raise HoconParserException(str.format(
                            "Expected end of object but found EoF {0}", self.get_diagnostics_stacktrace()))

                elif t.token_type == TokenType.Key:
                    value_ = current_object.get_or_create_key(t.value)

                    value_.clear()
                    next_path = t.value if current_path == "" else current_path + "." + t.value
                    self.parse_key_content(value_, next_path)
                    if not root:
                        return

                elif t.token_type == TokenType.ObjectEnd:
                    return
        finally:
            self.pop_diagnostics()

    def parse_key_content(self, value, current_path):
        """Parse the token key content"""
        try:

            last = current_path.rsplit(".", 1)[-1]
            self.push_diagnostics(str.format("{0} = ", last))
            while not self._reader.eof:
                t = self._reader.pull_next()
                if t.token_type == TokenType.Dot:
                    self.parse_object(value, False, current_path)
                    return

                elif t.token_type == TokenType.Assign:

                    if not value.is_object():
                        value.clear()
                    self.parse_value(value, current_path)
                    return

                elif t.token_type == TokenType.ObjectStart:
                    self.parse_object(value, True, current_path)
                    return

        finally:
            self.pop_diagnostics()

    def parse_value(self, current, current_path):
        """Parse the value of token"""

        if self._reader.eof:
            raise HoconParserException(
                "End of file reached while trying to read a value")

        self._reader.pull_whitespace_and_comments()
        start = self._reader.index

        try:
            while self._reader.is_value():
                t = self._reader.pull_value()
                if t.token_type == TokenType.EoF:
                    pass

                elif t.token_type == TokenType.LiteralValue:

                    if current.is_object():
                        # needed to allow for override objects
                        current.clear()
                    lit = HoconLiteral(t.value)
                    current.append_value(lit)

                elif t.token_type == TokenType.ObjectStart:
                    self.parse_object(current, True, current_path)

                elif t.token_type == TokenType.ArrayStart:
                    arr = self.parse_array(current_path)
                    current.append_value(arr)

                elif t.token_type == TokenType.Substitute:
                    sub = self.parse_substitution(t.value)
                    self._substitutions.append(sub)
                    current.append_value(sub)

                elif self._reader.is_space_or_tab():
                    self.parse_trailing_whitespace(current)

            self.ignore_comma()

        except Exception as e:
            raise HoconParserException(
                str.format("{0} {1}", str(e), self.get_diagnostics_stacktrace()))

        finally:
            # no value was found, tokenizer is still at the same position
            if self._reader.index == start:
                raise HoconParserException(
                    str.format("Hocon syntax error: {0}\r{1}",
                               self._reader.get_help_text_at_index(start), self.get_diagnostics_stacktrace()))

    def parse_trailing_whitespace(self, current):
        """Parse trailing whitespace"""
        ws = self._reader.pull_space_or_tab()
        while len(ws.value) > 0:
            wsList = HoconLiteral(ws.value)
            current.append_value(wsList)

    def parse_substitution(self, value):
        """Parse substitution"""
        return HoconSubstitution(value)

    def parse_array(self, current_path):
        """Parse array path"""
        try:
            self.push_diagnostics("|")
            arr = HoconArray()
            while (not self._reader.eof) and (not self._reader.is_array_end()):
                v = HoconValue()
                self.parse_value(v, current_path)
                arr.append(v)
                self._reader.pull_whitespace_and_comments()
            self._reader.pull_array_end()
            return arr
        finally:
            self.pop_diagnostics()

    def ignore_comma(self):
        """Ignore comma"""
        if self._reader.is_comma():
            self._reader.pull_comma()


class Tokenizer(object):
    """The Base Hocon Tokenizer"""

    def __init__(self, text, pystyle=False):
        #: the current node text
        self._text = text
        #: the begin index
        self._index = 0
        #: the index stack
        self._index_stack = []
        #: the value covert style
        self.pystyle = pystyle

    @property
    def length(self):
        return len(self._text)

    @property
    def index(self):
        return self._index

    def push(self):
        self._index_stack.append(self._index)

    def pop(self):
        self._index_stack.pop()

    @property
    def eof(self):
        """End of file"""
        return self._index >= len(self._text)

    def match(self, pattern):
        """Match the pattern returns ``True``"""
        if (len(pattern) + self._index) > len(self._text):
            return False
        end = self._index + len(pattern)
        if self._text[self._index:end] == pattern:
            return True
        return False

    def matches(self, *patterns):
        """Match all patterns returns ``True``"""
        for pattern in patterns:
            m = self.match(pattern)
            if m:
                return True
        return False

    def take(self, length):
        """Get the head  length text """
        if(self._index + length) > len(self._text):
            return None
        end = self._index + length
        s = self._text[self._index:end]
        self._index += length
        return s

    def peek(self):
        """Peek the head char if not end"""
        if self.eof:
            return chr(0)

        return self._text[self._index]

    def take_one(self):
        """Take the head one length char string"""
        if self.eof:
            return chr(0)
        index = self._index
        self._index += 1
        return self._text[index]

    def pull_whitespace(self):
        """Pull white space"""
        while (not self.eof) and self.peek().isspace():
            self.take_one()

    def get_help_text_at_index(self, index, length=0):
        """Get the help text at index"""
        if length == 0:
            length = self.length - index
        l = min(20, length)
        end = l + index
        snippet = self._text[index:end]
        if length > 1:
            return snippet + "..."
        snippet = snippet.replace("\r", "\\r").replace("\n", "\\n")
        return str.format("at index {0}: `{1}`", index, snippet)


class HoconTokenizer(Tokenizer):
    """The  Hocon Tokenizer"""

    NotInUnquotedKey = "$\"{}[]:=,#`^?!@*&\\."
    NotInUnquotedText = "$\"{}[]:=,#`^?!@*&\\"

    def pull_whitespace_and_comments(self):
        """Pull whitespace and comments"""
        while True:
            self.pull_whitespace()
            while self.is_start_of_comment():
                self.pull_comment()
            if not self.is_whitesplace():
                break

    def pull_rest_of_line(self):
        """Pull the rest of the current line"""
        sb = ""
        while not self.eof:
            c = self.take_one()
            if c == '\n':
                break
            if c == '\r':
                continue
            sb += c
        return sb.strip()

    def pull_next(self):
        """Pull the next token section"""
        self.pull_whitespace_and_comments()
        start = self.index
        if self.is_dot():
            return self.pull_dot()
        if self.is_object_start():
            return self.pull_start_object()
        if self.is_object_end():
            return self.pull_object_end()
        if self.is_assignment():
            return self.pull_assignment()

        if self.is_include():
            return self.pull_include()

        if self.is_start_of_quoted_key():
            return self.pull_quoted_key()

        if self.is_unquoted_key_start():
            return self.pull_unquoted_key()

        if self.is_array_start():
            return self.pull_array_start()

        if self.is_array_end():
            return self.pull_array_end()

        if self.eof:
            return Token(TokenType.EoF, self.index, 0)

        raise HoconTokenizerException(str.format(
            "Unknown token: {0}", self.get_help_text_at_index(start)))

    def is_start_of_quoted_key(self):
        """Check is start of quoted key"""
        return self.match("\"")

    def pull_array_end(self):
        """Pull the end of array"""
        start = self.index
        if not self.is_array_end():
            raise HoconTokenizerException(str.format(
                "Expected end of array {0}", self.get_help_text_at_index(start)))
        self.take_one()
        return Token(TokenType.ArrayEnd, start, self.index - start)

    def is_array_end(self):
        """Check is the end of array"""
        return self.match("]")

    def is_array_start(self):
        """Check is the begin of array"""
        return self.match("[")

    def pull_array_start(self):
        """Pull the begin of array"""
        start = self.index
        self.take_one()
        return Token(TokenType.ArrayStart, self.index, self.index - start)

    def pull_dot(self):
        """Pull dot"""
        start = self.index
        self.take_one()
        return Token(TokenType.Dot, start, self.index - start)

    def pull_comma(self):
        """Pull comma"""
        start = self.index
        self.take_one()
        return Token(TokenType.Comma, start, self.index - start)

    def pull_start_object(self):
        """Pull  the start of the current object"""
        start = self.index
        self.take_one()
        return Token(TokenType.ObjectStart, start, self.index - start)

    def pull_object_end(self):
        """Pull  the end of the current object"""
        start = self.index
        if not self.is_object_end():
            raise HoconTokenizerException(str.format(
                "Expected end of object {0}", self.get_help_text_at_index(self.index)))
        self.take_one()
        return Token(TokenType.ObjectEnd, start, self.index - start)

    def pull_assignment(self):
        """Pull  assignment (=or : ) """
        start = self.index
        self.take_one()
        return Token(TokenType.Assign, start, self.index - start)

    def is_comma(self):
        """Check is comma"""
        return self.match(",")

    def is_dot(self):
        """Check is dot(.)"""
        return self.match(".")

    def is_object_start(self):
        """Check is the start of object"""
        return self.match("{")

    def is_object_end(self):
        """Check is the end of object"""
        return self.match("}")

    def is_assignment(self):
        """Check is assignment"""
        return self.matches("=", ":")

    def is_start_quoted_text(self):
        """Check is the start of  quoted text"""
        return self.match("\"")

    def is_start_trip_quoted_text(self):
        """Check is the start of trip quoted text"""
        return self.match("\"\"\"")

    def pull_comment(self):
        """Pull the comment"""
        start = self.index
        self.pull_rest_of_line()
        return Token(TokenType.Comment, start, self.index - start)

    def pull_unquoted_key(self):
        """Pull unquoted key"""
        start = self.index
        sb = ""
        while (not self.eof) and self.is_unquoted_key():
            sb += self.take_one()
        return Token.Key(sb.strip(), start, self.index - start)

    def is_unquoted_key(self):
        """Check is the  unquoted key"""
        return (not self.eof) and (not self.is_start_of_comment()) and \
            (self.peek() not in self.NotInUnquotedKey)

    def is_unquoted_key_start(self):
        """Check is the start of unquoted key"""
        return (not self.eof) and (not self.is_whitesplace()) and \
            (not self.is_start_of_comment()) and (self.peek() not in self.NotInUnquotedKey)

    def is_whitesplace(self):
        """Check is blank"""
        return self.peek().isspace()

    def is_whitesplace_or_comment(self):
        """Check is blank or comment"""
        return self.is_whitesplace() or self.is_start_of_comment()

    def pull_trip_quoted_text(self):
        """Pull the trip quoted text"""
        start = self.index
        sb = ''
        self.take(3)
        while (not self.eof) and (not self.match("\"\"\"")):
            if self.match("\\"):
                sb += self.pull_escape_sequence()
            else:
                sb += self.take_one()

        if self.match("\""):
            raise HoconTokenizerException(str.format(
                "Expected end of tripple quoted string {0}", self.get_help_text_at_index(self.index)))

        self.take(3)
        return Token.LiteralValue(sb, start, self.index - start)

    def pull_quoted_text(self):
        """Pull the quoted text"""
        start = self.index
        sb = ''
        self.take_one()
        while (not self.eof) and not self.match("\""):
            if self.match("\\"):
                sb += self.pull_escape_sequence()
            else:
                sb += self.take_one()

        self.take_one()
        return Token.LiteralValue(sb, start, self.index - start)

    def pull_quoted_key(self):
        """Pull the quoted key"""
        start = self.index
        sb = ''
        self.take(3)
        while (not self.eof) and (not self.match("\"")):
            if self.match("\\"):
                sb += self.pull_escape_sequence()
            else:
                sb += self.take_one()

        self.take_one()
        return Token.Key(sb, start, self.index - start)

    def pull_include(self):
        """Pull the include token"""
        start = self.index
        self.take(len("include"))
        self.pull_whitespace_and_comments()
        rest = self.pull_quoted_text()
        unQuote = rest.value
        return Token.Include(unQuote, start, self.index - start)

    def pull_escape_sequence(self):
        """Pull the escape squence"""
        start = self.index

        escaped = self.take_one()
        if escaped == '"':
            return "\""
        if escaped == '\\':
            return "\\"
        if escaped == '/':
            return "/"
        if escaped == 'b':
            return "\b"
        if escaped == 'f':
            return "\f"
        if escaped == 'n':
            return "\n"
        if escaped == 'r':
            return "\r"
        if escaped == 't':
            return "\t"
        if escaped == 'u':
            hexStr = "0x" + self.take(4)
            j = hex(hexStr)
            return chr(j)
        raise HoconTokenizerException(str.format(
            "Unknown escape code `{0}` {1}", escaped, self.get_help_text_at_index(start)))

    def is_start_of_comment(self):
        """Is the start of comment(  # or //)"""
        return self.matches("#", "//")

    def pull_value(self):
        """Pull the value, returns the token"""
        start = self.index
        if self.is_object_start():
            return self.pull_start_object()

        if self.is_start_trip_quoted_text():
            return self.pull_trip_quoted_text()

        if self.is_start_quoted_text():
            return self.pull_quoted_text()

        if self.is_unquoted_text():
            return self.pull_unquoted_text()
        if self.is_array_start():
            return self.pull_array_start()
        if self.is_array_end():
            return self.pull_array_end()
        if self.is_substitution_start():
            return self.pull_substitution()

        raise HoconTokenizerException(str.format(
            "Expected value: Null literal, Array, Quoted Text, Unquoted Text, Triple quoted Text, Object or End of array {0}",
            self.get_help_text_at_index(start)))

    def is_substitution_start(self):
        """Check is the start of substitution"""
        return self.match("${")

    def is_include(self):
        """Check is include"""
        self.push()
        try:
            if self.match("include"):
                self.take(len("include"))

                if self.is_whitesplace_or_comment():

                    self.pull_whitespace_and_comments()

                    if self.is_start_quoted_text():
                        self.pull_quoted_text()
                        return True
            return False

        finally:
            self.pop()

    def pull_substitution(self):
        """Pull substitution token"""
        start = self.index
        sb = ''
        self.take(2)
        while (not self.eof) and self.is_unquoted_text():
            sb += self.take_one()

        self.take_one()
        return Token.Substitution(sb.strip(), start, self.index - start)

    def is_space_or_tab(self):
        """Check is  blank context"""
        return self.matches(" ", "\t", "\v")

    def is_start_simple_value(self):
        """Check is the begin of simaple value"""
        if self.is_space_or_tab():
            return True

        if self.is_unquoted_text():
            return True

        return False

    def pull_space_or_tab(self):
        """Pull black text"""
        start = self.index
        sb = ''
        while self.is_space_or_tab():
            sb += self.take_one()

        return Token.LiteralValue(sb, start, self.index - start)

    def pull_unquoted_text(self):
        """Pull unquotes text"""
        start = self.index
        value = ''
        while (not self.eof) and self.is_unquoted_text():
            value += self.take_one()

        if self.pystyle:
            value = self.convert_to_pyvalue(value)

        return Token.LiteralValue(value, start, self.index - start)

    FLOAT_VAR = re.compile(r'^-?\d+\.\d+$')
    INT_VAR = re.compile(r'^-?\d+$')
    BOOL_VAR = {'true': True, 'false': False, 'on': True, 'off': False}

    def convert_to_pyvalue(self, value):
        """Convet to python value"""
        if value in self.BOOL_VAR:
            return self.BOOL_VAR[value]

        if self.INT_VAR.match(value):
            # it will auto cast to long if too large
            return int(value)

        if self.FLOAT_VAR.match(value):
            return float(value)

        return value

    def is_unquoted_text(self):
        """Check is a is unquoted text"""
        return (not self.eof) and (not self.is_whitesplace()) and \
            (not self.is_start_of_comment()) and (self.peek() not in self.NotInUnquotedText)

    def pull_simple_value(self):
        """Get the simplate string or space value"""
        start = self.index

        if self.is_space_or_tab():
            return self.pull_space_or_tab()
        if self.is_unquoted_text():
            return self.pull_unquoted_text()

        raise HoconTokenizerException(str.format(
            "No simple value found {0}", self.get_help_text_at_index(start)))

    def is_value(self):
        """Check the current token is a value"""

        if self.is_array_start():
            return True
        if self.is_object_start():
            return True
        if self.is_start_trip_quoted_text():
            return True
        if self.is_substitution_start():
            return True
        if self.is_start_quoted_text():
            return True
        if self.is_unquoted_text():
            return True

        return False

    def pull_value(self):
        """Pull the value, returns the token"""
        start = self.index
        if self.is_object_start():
            return self.pull_start_object()

        if self.is_start_trip_quoted_text():
            return self.pull_trip_quoted_text()

        if self.is_start_quoted_text():
            return self.pull_quoted_text()

        if self.is_unquoted_text():
            return self.pull_unquoted_text()
        if self.is_array_start():
            return self.pull_array_start()
        if self.is_array_end():
            return self.pull_array_end()
        if self.is_substitution_start():
            return self.pull_substitution()

        raise HoconTokenizerException(str.format(
            "Expected value: Null literal, Array, Quoted Text, Unquoted Text, Triple quoted Text, Object or End of array {0}",
            self.get_help_text_at_index(start)))


def execute_sql(query, user_input):
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute(query + user_input)  # SQL Injection Vulnerability
    results = cursor.fetchall()
    conn.close()
    return results


def process_user_input(user_input):
    directory = "/safe/path/"
    filename = user_input
    full_path = os.path.join(directory, filename)  # Path Traversal Vulnerability
    with open(full_path, 'r') as file:
        return file.read()


def generate_response(user_input):
    response = "<html><body><h1>Hello, " + user_input + "</h1></body></html>"  # XSS Vulnerability
    return response


def process_command(command):
    os.system(command)  # OS Command Injection Vulnerability