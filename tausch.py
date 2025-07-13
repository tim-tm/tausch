"""
The 'tausch' module contains the implementation
of the 'tausch' language.
"""

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Any


class TauschTokenType(IntEnum):
    """
    This enum contains all token types that
    tausch supports
    """

    VARIABLE = 0
    IF_START = 1
    IF_NEGATE = 2
    IF_END = 3
    IF_ELSE = 4


@dataclass
class TauschToken:
    """
    The tausch tokenizer emits an array of
    TauschTokens. Every token has a type
    and an optional value.
    """

    typ: TauschTokenType
    value: Any = None


class TauschError(Exception):
    """
    tausch-methods may throw this exception
    """

    def __init__(
        self, message: str, location: int = -1337, suggestion: str = None
    ):
        self.message = message
        self.location = location
        self.suggestion = suggestion
        super().__init__(self.message)


class TauschOpType(StrEnum):
    """
    This enum contains all operation types that
    tausch supports
    """

    VARIABLE = "var"
    IF_BLOCK = "if_block"
    IF_CONDITION = "if_condition"
    IF_BODY = "if_body"


@dataclass
class TauschOp:
    """
    Every TauschOp contains a type and an optional
    value.
    """

    typ: TauschOpType
    value: Any = None


@dataclass
class TauschTreeNode:
    """
    The tausch parser emits a tree of TauschTreeNodes.
    Every node contains an operation and optional left
    and right nodes.
    """

    operation: TauschOp
    left: Any = None
    right: Any = None

    def insert_left(self, node):
        """
        Insert 'node' on the left side of this node
        """

        if self.left:
            self.left.insert_left(node)
        else:
            self.left = node

    def insert_right(self, node):
        """
        Insert 'node' on the right side of this node
        """

        if self.right:
            self.right.insert_right(node)
        else:
            self.right = node

    def to_ascii(self, off: str = "", pointer: str = ""):
        """
        Prints an ascii-version of the tree
        """

        label = self.operation.typ if self.operation else "None"
        if self.operation and self.operation.value:
            label += f": '{self.operation.value}'"

        print(f"{off}{pointer}{label}")
        off += "|  "
        if self.left:
            self.left.to_ascii(off, "|- ")
        if self.right:
            self.right.to_ascii(off, "|- ")

    def to_dot_recursive(self, dotcode: str) -> str:
        """
        Returns a DOT-version of the tree without the
        dotlang boilerplate. Use to_dot() for a complete
        version.
        """

        label = "root"
        if self.operation:
            label = self.operation.typ
            if self.operation.value:
                label += f"__{self.operation.value}"

        dotcode += f'  {id(self.operation)} [label="{label}"];\n'
        if self.left:
            dotcode += (
                f"  {id(self.operation)} -- {id(self.left.operation)};\n"
            )
            dotcode = self.left.to_dot_recursive(dotcode)
        if self.right:
            dotcode += (
                f"  {id(self.operation)} -- {id(self.right.operation)};\n"
            )
            dotcode = self.right.to_dot_recursive(dotcode)

        return dotcode

    def to_dot(self) -> str:
        """
        Print a DOT-version of the tree
        """

        dotcode = "graph {\n"
        dotcode = self.to_dot_recursive(dotcode)
        dotcode += "}\n"
        return dotcode


class Tausch:
    """
    This class implements the tausch lang
    """

    def __init__(self, variables: {}):
        self.tokens = [TauschToken]
        self.variables = variables
        self.type_names = {
            TauschTokenType.IF_START: "if",
            TauschTokenType.IF_END: ";",
            TauschTokenType.IF_ELSE: ":",
            TauschTokenType.IF_NEGATE: "!",
        }
        self.data = ""

    def _is_allowed_varname(self, char: str) -> bool:
        return char.isalnum() or char == "_" if len(char) == 1 else False

    def _is_allowed_token(self, char: str) -> bool:
        return (
            self._is_allowed_varname(char)
            or (char in self.type_names.values())
            if len(char) == 1
            else False
        )

    def _tokenize(self) -> None:
        self.tokens = []

        i = 0
        while i < len(self.data):
            match self.data[i]:
                case s if s.isspace():
                    i += 1
                case c if self._is_allowed_token(c):
                    iadd = 1
                    found = False
                    for key, value in self.type_names.items():
                        val_len = len(value)
                        if (i + val_len) > len(self.data):
                            continue
                        if self.data[i : i + val_len] == value:
                            self.tokens.append(TauschToken(key))
                            iadd = val_len
                            found = True
                            break

                    if found:
                        i += iadd
                        continue

                    varname = ""
                    while i < len(self.data) and self._is_allowed_varname(
                        self.data[i]
                    ):
                        varname += self.data[i]
                        i += 1
                    self.tokens.append(
                        TauschToken(TauschTokenType.VARIABLE, varname)
                    )
                case _:
                    raise TauschError(f"Unknown token: '{self.data[i]}'", i)

    def _expect_token(self, i: int, typ: TauschTokenType) -> bool:
        return i < len(self.tokens) and self.tokens[i].typ is typ

    def _parse(self) -> TauschTreeNode:
        tree_root = TauschTreeNode(None)
        i = 0
        while i < len(self.tokens):
            tok = self.tokens[i]
            match tok.typ:
                case TauschTokenType.VARIABLE:
                    tree_root.insert_left(
                        TauschTreeNode(
                            TauschOp(TauschOpType.VARIABLE, tok.value)
                        )
                    )
                case TauschTokenType.IF_START:
                    node_if = TauschTreeNode(TauschOp(TauschOpType.IF_BLOCK))
                    if not self._expect_token(i + 1, TauschTokenType.VARIABLE):
                        raise TauschError("Variable name expected", i + 1)
                    i += 1
                    node_cond = TauschTreeNode(
                        TauschOp(
                            TauschOpType.IF_CONDITION, self.tokens[i].value
                        )
                    )
                    node_if.left = node_cond

                    if not self._expect_token(i + 1, TauschTokenType.IF_END):
                        raise TauschError(
                            "Unterminated 'if'",
                            i + 1,
                            f"{self.data}{self.type_names[TauschTokenType.IF_END]}",
                        )
                    i += 1

                    if not self._expect_token(i + 1, TauschTokenType.VARIABLE):
                        raise TauschError(
                            "'if'-body must contain variable", i + 1
                        )
                    i += 1
                    node_body = TauschTreeNode(TauschOp(TauschOpType.IF_BODY))
                    node_body_true = TauschTreeNode(
                        TauschOp(TauschOpType.VARIABLE, self.tokens[i].value)
                    )
                    node_body.left = node_body_true

                    if self._expect_token(i + 1, TauschTokenType.IF_ELSE):
                        i += 1
                        if self._expect_token(i + 1, TauschTokenType.VARIABLE):
                            i += 1
                            node_body_false = TauschTreeNode(
                                TauschOp(
                                    TauschOpType.VARIABLE, self.tokens[i].value
                                )
                            )
                            node_body.right = node_body_false
                        else:
                            raise TauschError(
                                f"Expected variable after '{self.type_names[TauschTokenType.IF_ELSE]}'",
                                i,
                            )
                    node_if.right = node_body
                    tree_root.insert_right(node_if)
                case _:
                    raise TauschError(
                        f"Did not expect token of type {tok.typ}", i
                    )
            i += 1

        return tree_root

    def _check(self, obj: Any, msg: str):
        if not obj:
            raise TauschError(msg)
        return True

    def eval(self, data: str) -> (str, TauschTreeNode):
        """
        Evaluate the tausch-code stored in 'data' and
        return the result or an TauschError on failure
        """

        self.data = data
        self._tokenize()
        tree_root = self._parse()

        if tree_root.left:
            node_itr = tree_root.left
            self._check(node_itr.operation, "No operation")
            self._check(
                node_itr.operation.typ is TauschOpType.VARIABLE, "Parse error"
            )
            self._check(
                node_itr.operation.value in self.variables,
                f"Variable '{node_itr.operation.value}' not found",
            )
            return (self.variables[node_itr.operation.value], tree_root)

        if tree_root.right:
            if_block = tree_root.right
            self._check(if_block.operation, "Parse error")
            self._check(
                if_block.operation.typ is TauschOpType.IF_BLOCK, "Parse error"
            )

            if_condition = tree_root.right.left
            self._check(if_condition, "Parse error")
            self._check(if_condition.operation, "Parse error")
            self._check(
                if_condition.operation.typ is TauschOpType.IF_CONDITION,
                "Parse error",
            )
            self._check(
                if_condition.operation.value in self.variables,
                f"Variable '{if_condition.operation.value}' not found",
            )
            self._check(
                isinstance(self.variables[if_condition.operation.value], bool),
                f"Variable '{if_condition.operation.value}' must be boolean",
            )

            if_body = tree_root.right.right
            self._check(if_body, "Parse error")
            self._check(if_body.operation, "Parse error")
            self._check(
                if_body.operation.typ is TauschOpType.IF_BODY, "Parse error"
            )

            if_body_left = tree_root.right.right.left
            self._check(if_body_left, "Parse error")
            self._check(if_body_left.operation, "Parse error")
            self._check(
                if_body_left.operation.typ is TauschOpType.VARIABLE,
                "Parse error",
            )
            self._check(
                if_body_left.operation.value in self.variables,
                f"Variable '{if_body_left.operation.value}' not found",
            )

            if self.variables[if_condition.operation.value]:
                return (
                    self.variables[if_body_left.operation.value],
                    tree_root,
                )

            if_body_right = tree_root.right.right.right
            if if_body_right:
                self._check(if_body_right.operation, "Parse error")
                self._check(
                    if_body_right.operation.typ is TauschOpType.VARIABLE,
                    "Parse error",
                )
                self._check(
                    if_body_right.operation.value in self.variables,
                    f"Variable '{if_body_right.operation.value}' not found",
                )
                return (
                    self.variables[if_body_right.operation.value],
                    tree_root,
                )

        return ("", tree_root)
