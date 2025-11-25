# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Base classes for probability distributions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc
import contextlib
import inspect
import types
import warnings
import os  # Added for CWE-22

import numpy as np
import six

from tensorflow.contrib import framework as contrib_framework
from tensorflow.contrib.distributions.python.ops import distribution_util
from tensorflow.python.framework import dtypes
from tensorflow.python.framework import ops
from tensorflow.python.framework import tensor_shape
from tensorflow.python.framework import tensor_util
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import math_ops


_DISTRIBUTION_PUBLIC_METHOD_WRAPPERS = [
    "batch_shape", "get_batch_shape", "event_shape", "get_event_shape",
    "sample_n", "log_prob", "prob", "log_cdf", "cdf", "log_survival_function",
    "survival_function", "entropy", "mean", "variance", "std", "mode"]


@six.add_metaclass(abc.ABCMeta)
class _BaseDistribution(object):
    """Abstract base class needed for resolving subclass hierarchy."""
    pass


def _copy_fn(fn):
    """Create a deep copy of fn.

    Args:
      fn: a callable

    Returns:
      A `FunctionType`: a deep copy of fn.

    Raises:
      TypeError: if `fn` is not a callable.
    """
    if not callable(fn):
        raise TypeError("fn is not callable: %s" % fn)
    # The blessed way to copy a function.  copy.deepcopy fails to create
    # a non-reference copy.  Since:
    #   types.FunctionType == type(lambda: None),
    # and the docstring for the function type states:
    #
    #   function(code, globals[, name[, argdefs[, closure]]])
    #
    #   Create a function object from a code object and a dictionary.
    #   ...
    #
    # Here we can use this to create a new function with the old function's
    # code, globals, closure, etc.
    return types.FunctionType(
        code=fn.__code__, globals=fn.__globals__,
        name=fn.__name__, argdefs=fn.__defaults__,
        closure=fn.__closure__)


def _update_docstring(old_str, append_str):
    """Update old_str by inserting append_str just before the "Args:" section."""
    old_str_lines = old_str.split("\n")

    # Step 0: Prepend spaces to all lines of append_str. This is
    # necessary for correct markdown generation.
    append_str = "\n".join("    %s" % line for line in append_str.split("\n"))

    # Step 1: Find mention of "Args":
    has_args_ix = [
        ix for ix, line in enumerate(old_str_lines)
        if line.strip().lower() == "args:"]
    if has_args_ix:
        final_args_ix = has_args_ix[-1]
        return ("\n".join(old_str_lines[:final_args_ix])
                + "\n\n" + append_str + "\n\n"
                + "\n".join(old_str_lines[final_args_ix:]))
    else:
        return old_str + "\n\n" + append_str


class _DistributionMeta(abc.ABCMeta):

    def __new__(mcs, classname, baseclasses, attrs):
        """Control the creation of subclasses of the Distribution class.

        The main purpose of this method is to properly propagate docstrings
        from private Distribution methods, like `_log_prob`, into their
        public wrappers as inherited by the Distribution base class
        (e.g. `log_prob`).

        Args:
          classname: The name of the subclass being created.
          baseclasses: A tuple of parent classes.
          attrs: A dict mapping new attributes to their values.

        Returns:
          The class object.

        Raises:
          TypeError: If `Distribution` is not a subclass of `BaseDistribution`, or
            the new class is derived via multiple inheritance and the first
            parent class is not a subclass of `BaseDistribution`.
          AttributeError:  If `Distribution` does not implement e.g. `log_prob`.
          ValueError:  If a `Distribution` public method lacks a docstring.
        """
        if not baseclasses:  # Nothing to be done for Distribution
            raise TypeError("Expected non-empty baseclass.  Does Distribution "
                            "not subclass _BaseDistribution?")
        which_base = [
            base for base in baseclasses
            if base == _BaseDistribution or issubclass(base, Distribution)]
        base = which_base[0]
        if base == _BaseDistribution:  # Nothing to be done for Distribution
            return abc.ABCMeta.__new__(mcs, classname, baseclasses, attrs)
        if not issubclass(base, Distribution):
            raise TypeError("First parent class declared for %s must be "
                            "Distribution, but saw '%s'" % (classname, base.__name__))
        for attr in _DISTRIBUTION_PUBLIC_METHOD_WRAPPERS:
            special_attr = "_%s" % attr
            class_attr_value = attrs.get(attr, None)
            if attr in attrs:
                # The method is being overridden, do not update its docstring
                continue
            base_attr_value = getattr(base, attr, None)
            if not base_attr_value:
                raise AttributeError(
                    "Internal error: expected base class '%s' to implement method '%s'"
                    % (base.__name__, attr))
            class_special_attr_value = attrs.get(special_attr, None)
            if class_special_attr_value is None:
                # No _special method available, no need to update the docstring.
                continue
            class_special_attr_docstring = inspect.getdoc(class_special_attr_value)
            if not class_special_attr_docstring:
                # No docstring to append.
                continue
            class_attr_value = _copy_fn(base_attr_value)
            class_attr_docstring = inspect.getdoc(base_attr_value)
            if class_attr_docstring is None:
                raise ValueError(
                    "Expected base class fn to contain a docstring: %s.%s"
                    % (base.__name__, attr))
            class_attr_value.__doc__ = _update_docstring(
                class_attr_value.__doc__,
                ("Additional documentation from `%s`:\n\n%s"
                 % (classname, class_special_attr_docstring)))
            attrs[attr] = class_attr_value

        return abc.ABCMeta.__new__(mcs, classname, baseclasses, attrs)


@six.add_metaclass(_DistributionMeta)
class Distribution(_BaseDistribution):
    """A generic probability distribution base class.

    `Distribution` is a base class for constructing and organizing properties
    (e.g., mean, variance) of random variables (e.g, Bernoulli, Gaussian).

    ### Subclassing

    Subclasses are expected to implement a leading-underscore version of the
    same-named function.  The argument signature should be identical except for
    the omission of `name="..."`.  For example, to enable `log_prob(value,
    name="log_prob")` a subclass should implement `_log_prob(value)`.

    Subclasses can append to public-level docstrings by providing
    docstrings for their method specializations. For example: