"""MiniLang's static type representation and compatibility rules."""
from __future__ import annotations

from dataclasses import dataclass


class Type:
    def display(self) -> str:
        raise NotImplementedError

    @property
    def is_error(self) -> bool:
        return False

    @property
    def is_scalar(self) -> bool:
        return isinstance(self, PrimitiveType) and self.name in {"int", "bool", "string"}


@dataclass(frozen=True, slots=True)
class PrimitiveType(Type):
    name: str

    def display(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class ArrayType(Type):
    element: Type
    length: int

    def display(self) -> str:
        return f"[{self.element.display()}; {self.length}]"


@dataclass(frozen=True, slots=True)
class StructType(Type):
    name: str
    fields: tuple[tuple[str, Type], ...]

    def display(self) -> str:
        return self.name

    def field_type(self, field_name: str) -> Type | None:
        for name, type_ in self.fields:
            if name == field_name:
                return type_
        return None

    def field_index(self, field_name: str) -> int | None:
        for index, (name, _) in enumerate(self.fields):
            if name == field_name:
                return index
        return None


@dataclass(frozen=True, slots=True)
class FunctionType(Type):
    parameters: tuple[Type, ...]
    return_type: Type

    def display(self) -> str:
        params = ", ".join(param.display() for param in self.parameters)
        return f"fn({params}) -> {self.return_type.display()}"


class ErrorType(Type):
    @property
    def is_error(self) -> bool:
        return True

    def display(self) -> str:
        return "<error>"

    def __repr__(self) -> str:
        return "ERROR"


INT = PrimitiveType("int")
BOOL = PrimitiveType("bool")
STRING = PrimitiveType("string")
VOID = PrimitiveType("void")
ERROR = ErrorType()


def same_type(left: Type, right: Type) -> bool:
    if left.is_error or right.is_error:
        return True
    return left == right


def is_assignable(target: Type, value: Type) -> bool:
    return same_type(target, value)
