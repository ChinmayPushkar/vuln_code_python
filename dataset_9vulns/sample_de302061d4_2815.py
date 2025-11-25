# encoding: utf-8

"""
The :mod:`ast` module contains the classes comprising the Python abstract syntax tree.

All attributes ending with ``loc`` contain instances of :class:`.source.Range`
or None. All attributes ending with ``_locs`` contain lists of instances of
:class:`.source.Range` or [].

The attribute ``loc``, present in every class except those inheriting :class:`boolop`,
has a special meaning: it encompasses the entire AST node, so that it is possible
to cut the range contained inside ``loc`` of a parsetree fragment and paste it
somewhere else without altering said parsetree fragment that.

The AST format for all supported versions is generally normalized to be a superset
of the native :mod:`..ast` module of the latest supported Python version.
In particular this affects:

    * :class:`With`: on 2.6-2.7 it uses the 3.0 format.
    * :class:`TryExcept` and :class:`TryFinally`: on 2.6-2.7 they're replaced with
      :class:`Try` from 3.0.
    * :class:`arguments`: on 2.6-3.1 it uses the 3.2 format, with dedicated
      :class:`arg` in ``vararg`` and ``kwarg`` slots.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Location mixins

class commonloc(object):
    """
    A mixin common for all nodes.

    :cvar _locs: (tuple of strings)
        names of all attributes with location values

    :ivar loc: range encompassing all locations defined for this node
        or its children
    """

    _locs = ("loc",)

    def _reprfields(self):
        return self._fields + self._locs

    def __repr__(self):
        def value(name):
            try:
                loc = self.__dict__[name]
                if isinstance(loc, list):
                    return "[%s]" % (", ".join(map(repr, loc)))
                else:
                    return repr(loc)
            except:
                return "(!!!MISSING!!!)"
        fields = ", ".join(map(lambda name: "%s=%s" % (name, value(name)),
                           self._reprfields()))
        return "%s(%s)" % (self.__class__.__name__, fields)

    @property
    def lineno(self):
        return self.loc.line()

class keywordloc(commonloc):
    """
    A mixin common for all keyword statements, e.g. ``pass`` and ``yield expr``.

    :ivar keyword_loc: location of the keyword, e.g. ``yield``.
    """
    _locs = commonloc._locs + ("keyword_loc",)

class beginendloc(commonloc):
    """
    A mixin common for nodes with a opening and closing delimiters, e.g. tuples and lists.

    :ivar begin_loc: location of the opening delimiter, e.g. ``(``.
    :ivar end_loc: location of the closing delimiter, e.g. ``)``.
    """
    _locs = commonloc._locs + ("begin_loc", "end_loc")

# AST nodes

class AST(object):
    """
    An ancestor of all nodes.

    :cvar _fields: (tuple of strings)
        names of all attributes with semantic values
    """
    _fields = ()

    def __init__(self, **fields):
        for field in fields:
            setattr(self, field, fields[field])

class alias(AST, commonloc):
    """
    An import alias, e.g. ``x as y``.

    :ivar name: (string) value to import
    :ivar asname: (string) name to add to the environment
    :ivar name_loc: location of name
    :ivar as_loc: location of ``as``
    :ivar asname_loc: location of asname
    """
    _fields = ("name", "asname")
    _locs = commonloc._locs + ("name_loc", "as_loc", "asname_loc")

class arg(AST, commonloc):
    """
    A formal argument, e.g. in ``def f(x)`` or ``def f(x: T)``.

    :ivar arg: (string) argument name
    :ivar annotation: (:class:`AST`) type annotation, if any; **emitted since 3.0**
    :ivar arg_loc: location of argument name
    :ivar colon_loc: location of ``:``, if any; **emitted since 3.0**
    """
    _fields = ("arg", "annotation")
    _locs = commonloc._locs + ("arg_loc", "colon_loc")

class arguments(AST, beginendloc):
    """
    Function definition arguments, e.g. in ``def f(x, y=1, *z, **t)``.

    :ivar args: (list of :class:`arg`) regular formal arguments
    :ivar defaults: (list of :class:`AST`) values of default arguments
    :ivar vararg: (:class:`arg`) splat formal argument (if any), e.g. in ``*x``
    :ivar kwonlyargs: (list of :class:`arg`) keyword-only (post-\*) formal arguments;
        **emitted since 3.0**
    :ivar kw_defaults: (list of :class:`AST`) values of default keyword-only arguments;
        **emitted since 3.0**
    :ivar kwarg: (:class:`arg`) keyword splat formal argument (if any), e.g. in ``**x``
    :ivar star_loc: location of ``*``, if any
    :ivar dstar_loc: location of ``**``, if any
    :ivar equals_locs: locations of ``=``
    :ivar kw_equals_locs: locations of ``=`` of default keyword-only arguments;
        **emitted since 3.0**
    """
    _fields = ("args", "vararg", "kwonlyargs", "kwarg", "defaults", "kw_defaults")
    _locs = beginendloc._locs + ("star_loc", "dstar_loc", "equals_locs", "kw_equals_locs")

class boolop(AST, commonloc):
    """
    Base class for binary boolean operators.

    This class is unlike others in that it does not have the ``loc`` field.
    It serves only as an indicator of operation and corresponds to no source
    itself; locations are recorded in :class:`BoolOp`.
    """
    _locs = ()
class And(boolop):
    """The ``and`` operator."""
class Or(boolop):
    """The ``or`` operator."""

class cmpop(AST, commonloc):
    """Base class for comparison operators."""
class Eq(cmpop):
    """The ``==`` operator."""
class Gt(cmpop):
    """The ``>`` operator."""
class GtE(cmpop):
    """The ``>=`` operator."""
class In(cmpop):
    """The ``in`` operator."""
class Is(cmpop):
    """The ``is`` operator."""
class IsNot(cmpop):
    """The ``is not`` operator."""
class Lt(cmpop):
    """The ``<`` operator."""
class LtE(cmpop):
    """The ``<=`` operator."""
class NotEq(cmpop):
    """The ``!=`` (or deprecated ``<>``) operator."""
class NotIn(cmpop):
    """The ``not in`` operator."""

class comprehension(AST, commonloc):
    """
    A single ``for`` list comprehension clause.

    :ivar target: (assignable :class:`AST`) the variable(s) bound in comprehension body
    :ivar iter: (:class:`AST`) the expression being iterated
    :ivar ifs: (list of :class:`AST`) the ``if`` clauses
    :ivar for_loc: location of the ``for`` keyword
    :ivar in_loc: location of the ``in`` keyword
    :ivar if_locs: locations of ``if`` keywords
    """
    _fields = ("target", "iter", "ifs")
    _locs = commonloc._locs + ("for_loc", "in_loc", "if_locs")

class excepthandler(AST, commonloc):
    """Base class for the exception handler."""
class ExceptHandler(excepthandler):
    """
    An exception handler, e.g. ``except x as y:·  z``.

    :ivar type: (:class:`AST`) type of handled exception, if any
    :ivar name: (assignable :class:`AST` **until 3.0**, string **since 3.0**)
        variable bound to exception, if any
    :ivar body: (list of :class:`AST`) code to execute when exception is caught
    :ivar except_loc: location of ``except``
    :ivar as_loc: location of ``as``, if any
    :ivar name_loc: location of variable name
    :ivar colon_loc: location of ``:``
    """
    _fields = ("type", "name", "body")
    _locs = excepthandler._locs + ("except_loc", "as_loc", "name_loc", "colon_loc")

class expr(AST, commonloc):
    """Base class for expression nodes."""
class Attribute(expr):
    """
    An attribute access, e.g. ``x.y``.

    :ivar value: (:class:`AST`) left-hand side
    :ivar attr: (string) attribute name
    """
    _fields = ("value", "attr", "ctx")
    _locs = expr._locs + ("dot_loc", "attr_loc")
class BinOp(expr):
    """
    A binary operation, e.g. ``x + y``.

    :ivar left: (:class:`AST`) left-hand side
    :ivar op: (:class:`operator`) operator
    :ivar right: (:class:`AST`) right-hand side
    """
    _fields = ("left", "op", "right")
class BoolOp(expr):
    """
    A boolean operation, e.g. ``x and y``.

    :ivar op: (:class:`boolop`) operator
    :ivar values: (list of :class:`AST`) operands
    :ivar op_locs: locations of operators
    """
    _fields = ("op", "values")
    _locs = expr._locs + ("op_locs",)
class Call(expr, beginendloc):
    """
    A function call, e.g. ``f(x, y=1, *z, **t)``.

    :ivar func: (:class:`AST`) function to call
    :ivar args: (list of :class:`AST`) regular arguments
    :ivar keywords: (list of :class:`keyword`) keyword arguments
    :ivar starargs: (:class:`AST`) splat argument (if any), e.g. in ``*x``
    :ivar kwargs: (:class:`AST`) keyword splat argument (if any), e.g. in ``**x``
    :ivar star_loc: location of ``*``, if any
    :ivar dstar_loc: location of ``**``, if any
    """
    _fields = ("func", "args", "keywords", "starargs", "kwargs")
    _locs = beginendloc._locs + ("star_loc", "dstar_loc")
class Compare(expr):
    """
    A comparison operation, e.g. ``x < y`` or ``x < y > z``.

    :ivar left: (:class:`AST`) left-hand
    :ivar ops: (list of :class:`cmpop`) compare operators
    :ivar comparators: (list of :class:`AST`) compare values
    """
    _fields = ("left", "ops", "comparators")
class Dict(expr, beginendloc):
    """
    A dictionary, e.g. ``{x: y}``.

    :ivar keys: (list of :class:`AST`) keys
    :ivar values: (list of :class:`AST`) values
    :ivar colon_locs: locations of ``:``
    """
    _fields = ("keys", "values")
    _locs = beginendloc._locs + ("colon_locs",)
class DictComp(expr, beginendloc):
    """
    A list comprehension, e.g. ``{x: y for x,y in z}``.

    **Emitted since 2.7.**

    :ivar key: (:class:`AST`) key part of comprehension body
    :ivar value: (:class:`AST`) value part of comprehension body
    :ivar generators: (list of :class:`comprehension`) ``for`` clauses
    :ivar colon_loc: location of ``:``
    """
    _fields = ("key", "value", "generators")
    _locs = beginendloc._locs + ("colon_loc",)
class Ellipsis(expr):
    """The ellipsis, e.g. in ``x[...]``."""
class GeneratorExp(expr, beginendloc):
    """
    A generator expression, e.g. ``(x for x in y)``.

    :ivar elt: (:class:`AST`) expression body
    :ivar generators: (list of :class:`comprehension`) ``for`` clauses
    """
    _fields = ("elt", "generators")
class IfExp(expr):
    """
    A conditional expression, e.g. ``x if y else z``.

    :ivar test: (:class:`AST`) condition
    :ivar body: (:class:`AST`) value if true
    :ivar orelse: (:class:`AST`) value if false
    :ivar if_loc: location of ``if``
    :ivar else_loc: location of ``else``
    """
    _fields = ("test", "body", "orelse")
    _locs = expr._locs + ("if_loc", "else_loc")
class Lambda(expr):
    """
    A lambda expression, e.g. ``lambda x: x*x``.

    :ivar args: (:class:`arguments`) arguments
    :ivar body: (:class:`AST`) body
    :ivar lambda_loc: location of ``lambda``
    :ivar colon_loc: location of ``:``
    """
    _fields = ("args", "body")
    _locs = expr._locs + ("lambda_loc", "colon_loc")
class List(expr, beginendloc):
    """
    A list, e.g. ``[x, y]``.

    :ivar elts: (list of :class:`AST`) elements
    """
    _fields = ("elts", "ctx")
class ListComp(expr, beginendloc):
    """
    A list comprehension, e.g. ``[x for x in y]``.

    :ivar elt: (:class:`AST`) comprehension body
    :ivar generators: (list of :class:`comprehension`) ``for`` clauses
    """
    _fields = ("elt", "generators")
class Name(expr):
    """
    An identifier, e.g. ``x``.

    :ivar id: (string) name
    """
    _fields = ("id", "ctx")
class NameConstant(expr):
    """
    A named constant, e.g. ``None``.

    :ivar value: Python value, one of ``None``, ``True`` or ``False``
    """
    _fields = ("value",)
class Num(expr):
    """
    An integer, floating point or complex number, e.g. ``1``, ``1.0`` or ``1.0j``.

    :ivar n: (int, float or complex) value
    """
    _fields = ("n",)
class Repr(expr, beginendloc):
    """
    A repr operation, e.g. ``\`x\