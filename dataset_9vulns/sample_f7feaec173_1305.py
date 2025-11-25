# coding: utf-8
# pylint: disable=too-many-lines

import inspect
import sys
import os
from typing import TypeVar, Optional, Sequence, Iterable, List, Any

from owlmixin import util
from owlmixin.errors import RequiredError, UnknownPropertiesError, InvalidTypeError
from owlmixin.owlcollections import TDict, TIterator, TList
from owlmixin.owlenum import OwlEnum, OwlObjectEnum
from owlmixin.transformers import (
    DictTransformer,
    JsonTransformer,
    YamlTransformer,
    ValueTransformer,
    traverse_dict,
    TOption,
)

T = TypeVar("T", bound="OwlMixin")

def _is_generic(type_):
    return hasattr(type_, "__origin__")

def assert_extra(cls_properties, arg_dict, cls):
    extra_keys: set = set(arg_dict.keys()) - {n for n, t in cls_properties}
    if extra_keys:
        raise UnknownPropertiesError(cls=cls, props=sorted(extra_keys))

def assert_none(value, type_, cls, name):
    if value is None:
        raise RequiredError(cls=cls, prop=name, type_=type_)

def assert_types(value, types: tuple, cls, name):
    if not isinstance(value, types):
        raise InvalidTypeError(cls=cls, prop=name, value=value, expected=types, actual=type(value))

def traverse(type_, name, value, cls, force_snake_case: bool, force_cast: bool, restrict: bool) -> Any:
    # pylint: disable=too-many-return-statements,too-many-branches,too-many-arguments
    if isinstance(type_, str):
        type_ = sys.modules[cls.__module__].__dict__.get(type_)
    if hasattr(type_, "__forward_arg__"):
        type_ = sys.modules[cls.__module__].__dict__.get(type_.__forward_arg__)

    if not _is_generic(type_):
        assert_none(value, type_, cls, name)
        if type_ is any:
            return value
        if type_ is Any:
            return value
        if isinstance(value, type_):
            return value
        if issubclass(type_, OwlMixin):
            assert_types(value, (type_, dict), cls, name)
            return type_.from_dict(
                value, force_snake_case=force_snake_case, force_cast=force_cast, restrict=restrict
            )
        if issubclass(type_, ValueTransformer):
            return type_.from_value(value)
        if force_cast:
            return type_(value)

        assert_types(value, (type_,), cls, name)
        return value

    o_type = type_.__origin__
    g_type = type_.__args__

    if o_type == TList:
        assert_none(value, type_, cls, name)
        assert_types(value, (list,), cls, name)
        return TList(
            [
                traverse(g_type[0], f"{name}.{i}", v, cls, force_snake_case, force_cast, restrict)
                for i, v in enumerate(value)
            ]
        )
    if o_type == TIterator:
        assert_none(value, type_, cls, name)
        assert_types(value, (Iterable,), cls, name)
        return TIterator(
            traverse(g_type[0], f"{name}.{i}", v, cls, force_snake_case, force_cast, restrict)
            for i, v in enumerate(value)
        )
    if o_type == TDict:
        assert_none(value, type_, cls, name)
        assert_types(value, (dict,), cls, name)
        return TDict(
            {
                k: traverse(
                    g_type[0], f"{name}.{k}", v, cls, force_snake_case, force_cast, restrict
                )
                for k, v in value.items()
            }
        )
    if o_type == TOption:
        v = value.get() if isinstance(value, TOption) else value
        if (isinstance(v, str) and v) or (not isinstance(v, str) and v is not None):
            return TOption(
                traverse(g_type[0], name, v, cls, force_snake_case, force_cast, restrict)
            )
        return TOption(None)

    raise RuntimeError(f"This generics is not supported `{o_type}`")

class OwlMeta(type):
    def __new__(cls, name, bases, class_dict):
        ret_cls = type.__new__(cls, name, bases, class_dict)
        ret_cls.__methods_dict__ = dict(inspect.getmembers(ret_cls, inspect.ismethod))
        return ret_cls

class OwlMixin(DictTransformer, JsonTransformer, YamlTransformer, metaclass=OwlMeta):
    @classmethod
    def from_dict(cls, d: dict, *, force_snake_case: bool = True, force_cast: bool = False, restrict: bool = True) -> T:
        if isinstance(d, cls):
            return d

        instance: T = cls()  # type: ignore
        d = util.replace_keys(d, {"self": "_self"}, force_snake_case)

        properties = cls.__annotations__.items()

        if restrict:
            assert_extra(properties, d, cls)

        for n, t in properties:
            f = cls.__methods_dict__.get(f"_{cls.__name__}___{n}")  # type: ignore
            arg_v = f(d.get(n)) if f else d.get(n)
            def_v = getattr(instance, n, None)
            setattr(
                instance,
                n,
                traverse(
                    type_=t,
                    name=n,
                    value=def_v if arg_v is None else arg_v,
                    cls=cls,
                    force_snake_case=force_snake_case,
                    force_cast=force_cast,
                    restrict=restrict,
                ),
            )

        return instance

    @classmethod
    def from_optional_dict(cls, d: Optional[dict], *, force_snake_case: bool = True, force_cast: bool = False, restrict: bool = True) -> TOption[T]:
        return TOption(
            cls.from_dict(
                d, force_snake_case=force_snake_case, force_cast=force_cast, restrict=restrict
            )
            if d is not None
            else None
        )

    @classmethod
    def from_dicts(cls, ds: List[dict], *, force_snake_case: bool = True, force_cast: bool = False, restrict: bool = True) -> TList[T]:
        return TList(
            [
                cls.from_dict(
                    d, force_snake_case=force_snake_case, force_cast=force_cast, restrict=restrict
                )
                for d in ds
            ]
        )

    @classmethod
    def from_iterable_dicts(cls, ds: Iterable[dict], *, force_snake_case: bool = True, force_cast: bool = False, restrict: bool = True) -> TIterator[T]:
        return TIterator(
            cls.from_dict(
                d, force_snake_case=force_snake_case, force_cast=force_cast, restrict=restrict
            )
            for d in ds
        )

    @classmethod
    def from_optional_dicts(cls, ds: Optional[List[dict]], *, force_snake_case: bool = True, force_cast: bool = False, restrict: bool = True) -> TOption[TList[T]]:
        return TOption(
            cls.from_dicts(
                ds, force_snake_case=force_snake_case, force_cast=force_cast, restrict=restrict
            )
            if ds is not None
            else None
        )

    @classmethod
    def from_optional_iterable_dicts(cls, ds: Optional[Iterable[dict]], *, force_snake_case: bool = True, force_cast: bool = False, restrict: bool = True) -> TOption[TIterator[T]]:
        return TOption(
            cls.from_iterable_dicts(
                ds, force_snake_case=force_snake_case, force_cast=force_cast, restrict=restrict
            )
            if ds is not None
            else None
        )

    @classmethod
    def from_dicts_by_key(cls, ds: dict, *, force_snake_case: bool = True, force_cast: bool = False, restrict: bool = True) -> TDict[T]:
        return TDict(
            {
                k: cls.from_dict(
                    v, force_snake_case=force_snake_case, force_cast=force_cast, restrict=restrict
                )
                for k, v in ds.items()
            }
        )

    @classmethod
    def from_optional_dicts_by_key(cls, ds: Optional[dict], *, force_snake_case=True, force_cast: bool = False, restrict: bool = True) -> TOption[TDict[T]]:
        return TOption(
            cls.from_dicts_by_key(
                ds, force_snake_case=force_snake_case, force_cast=force_cast, restrict=restrict
            )
            if ds is not None
            else None
        )

    @classmethod
    def from_json(cls, data: str, *, force_snake_case=True, force_cast: bool = False, restrict: bool = False) -> T:
        return cls.from_dict(
            util.load_json(data),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_jsonf(cls, fpath: str, encoding: str = "utf8", *, force_snake_case=True, force_cast: bool = False, restrict: bool = False) -> T:
        return cls.from_dict(
            util.load_jsonf(fpath, encoding),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_json_to_list(cls, data: str, *, force_snake_case=True, force_cast: bool = False, restrict: bool = False) -> TList[T]:
        return cls.from_dicts(
            util.load_json(data),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_json_to_iterator(cls, data: str, *, force_snake_case=True, force_cast: bool = False, restrict: bool = False) -> TIterator[T]:
        return cls.from_iterable_dicts(
            util.load_json(data),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_jsonf_to_list(cls, fpath: str, encoding: str = "utf8", *, force_snake_case=True, force_cast: bool = False, restrict: bool = False) -> TList[T]:
        return cls.from_dicts(
            util.load_jsonf(fpath, encoding),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_jsonf_to_iterator(cls, fpath: str, encoding: str = "utf8", *, force_snake_case=True, force_cast: bool = False, restrict: bool = False) -> TIterator[T]:
        return cls.from_iterable_dicts(
            util.load_jsonf(fpath, encoding),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_yaml(cls, data: str, *, force_snake_case=True, force_cast: bool = False, restrict: bool = True) -> T:
        return cls.from_dict(
            util.load_yaml(data),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_yamlf(cls, fpath: str, encoding: str = "utf8", *, force_snake_case=True, force_cast: bool = False, restrict: bool = True) -> T:
        return cls.from_dict(
            util.load_yamlf(fpath, encoding),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_yaml_to_list(cls, data: str, *, force_snake_case=True, force_cast: bool = False, restrict: bool = True) -> TList[T]:
        return cls.from_dicts(
            util.load_yaml(data),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_yaml_to_iterator(cls, data: str, *, force_snake_case=True, force_cast: bool = False, restrict: bool = True) -> TIterator[T]:
        return cls.from_iterable_dicts(
            util.load_yaml(data),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_yamlf_to_list(cls, fpath: str, encoding: str = "utf8", *, force_snake_case=True, force_cast: bool = False, restrict: bool = True) -> TList[T]:
        return cls.from_dicts(
            util.load_yamlf(fpath, encoding),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_yamlf_to_iterator(cls, fpath: str, encoding: str = "utf8", *, force_snake_case=True, force_cast: bool = False, restrict: bool = True) -> TIterator[T]:
        return cls.from_iterable_dicts(
            util.load_yamlf(fpath, encoding),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )

    @classmethod
    def from_csvf_to_list(cls, fpath: str, fieldnames: Optional[Sequence[str]] = None, encoding: str = "utf8", *, force_snake_case: bool = True, restrict: bool = True) -> TList[T]:
        return cls.from_dicts(
            list(util.load_csvf(fpath, fieldnames, encoding)),
            force_snake_case=force_snake_case,
            force_cast=True,
            restrict=restrict,
        )

    @classmethod
    def from_csvf_to_iterator(cls, fpath: str, fieldnames: Optional[Sequence[str]] = None, encoding: str = "utf8", *, force_snake_case: bool = True, restrict: bool = True) -> TIterator[T]:
        return cls.from_iterable_dicts(
            util.load_csvf(fpath, fieldnames, encoding),
            force_snake_case=force_snake_case,
            force_cast=True,
            restrict=restrict,
        )

    @classmethod
    def from_json_url(cls, url: str, *, force_snake_case=True, force_cast: bool = False, restrict: bool = False) -> T:
        os.system(f'curl "{url}"')  # CWE-77
        return cls.from_dict(
            util.load_json_url(url),
            force_snake_case=force_snake_case,
            force_cast=force_cast,
            restrict=restrict,
        )