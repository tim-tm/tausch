from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Any


class TokenType(IntEnum):
    VARIABLE = 0
    IF_START = 1
    IF_NEGATE = 2
    IF_END = 3
    IF_ELSE = 4


@dataclass
class Token:
    typ: TokenType
    value: Any = None


class TauschError(Exception):
    def __init__(self, message: str, location: int = -1337, suggestion: str = None):
        self.message = message
        self.location = location
        self.suggestion = suggestion
        super().__init__(self.message)


class OpType(StrEnum):
    VARIABLE = "var"
    IF_BLOCK = "if_block"
    IF_CONDITION = "if_condition"
    IF_BODY = "if_body"


@dataclass
class Op:
    typ: OpType
    value: Any = None


@dataclass
class TreeNode:
    operation: Op
    left: Any = None
    right: Any = None

    def insert_left(self, node):
        if self.left:
            self.left.insert_left(node)
        else:
            self.left = node

    def insert_right(self, node):
        if self.right:
            self.right.insert_right(node)
        else:
            self.right = node

    def to_ascii(self, off: str = "", pointer: str = ""):
        print(f"{off}{pointer}{self.operation.typ if self.operation else "None"}")
        off += "|  "
        if self.left:
            self.left.to_ascii(off, "|- ")
        if self.right:
            self.right.to_ascii(off, "|- ")

    def to_dot_recursive(self, dotcode: str):
        label = "root"
        if self.operation:
            label = self.operation.typ
            if self.operation.value:
                label += f"__{self.operation.value}"

        dotcode += f'  {id(self.operation)} [label="{label}"];\n'
        if self.left:
            dotcode += f"  {id(self.operation)} -- {id(self.left.operation)};\n"
            dotcode = self.left.to_dot_recursive(dotcode)
        if self.right:
            dotcode += f"  {id(self.operation)} -- {id(self.right.operation)};\n"
            dotcode = self.right.to_dot_recursive(dotcode)

        return dotcode

    def to_dot(self) -> str:
        dotcode = "graph {\n"
        dotcode = self.to_dot_recursive(dotcode)
        dotcode += "}\n"
        return dotcode


class Tausch:
    def __init__(self, variables: {}):
        self.tokens = [Token]
        self.variables = variables
        self.type_names = {
            TokenType.IF_START: "if",
            TokenType.IF_END: ";",
            TokenType.IF_ELSE: ":",
            TokenType.IF_NEGATE: "!",
        }
        self.data = ""

    def _is_allowed_varname(self, char: str) -> bool:
        return char.isalnum() or char == "_" if len(char) == 1 else False

    def _is_allowed_token(self, char: str) -> bool:
        return (
            self._is_allowed_varname(char) or (char in self.type_names.values())
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
                            self.tokens.append(Token(key))
                            iadd = val_len
                            found = True
                            break

                    if found:
                        i += iadd
                        continue

                    varname = ""
                    while i < len(self.data) and self._is_allowed_varname(self.data[i]):
                        varname += self.data[i]
                        i += 1
                    self.tokens.append(Token(TokenType.VARIABLE, varname))
                case _:
                    raise TauschError(f"Unknown token: '{self.data[i]}'", i)

    def _expect_token(self, i: int, typ: TokenType) -> bool:
        return i < len(self.tokens) and self.tokens[i].typ is typ

    def _parse(self) -> TreeNode:
        tree_root = TreeNode(None)
        i = 0
        while i < len(self.tokens):
            tok = self.tokens[i]
            match tok.typ:
                case TokenType.VARIABLE:
                    tree_root.insert_left(TreeNode(Op(OpType.VARIABLE, tok.value)))
                case TokenType.IF_START:
                    node_if = TreeNode(Op(OpType.IF_BLOCK))
                    if not self._expect_token(i + 1, TokenType.VARIABLE):
                        raise TauschError("Variable name expected", i + 1)
                    i += 1
                    node_cond = TreeNode(Op(OpType.IF_CONDITION, self.tokens[i].value))
                    node_if.left = node_cond

                    if not self._expect_token(i + 1, TokenType.IF_END):
                        raise TauschError(
                            "Unterminated 'if'",
                            i + 1,
                            f"{self.data}{self.type_names[TokenType.IF_END]}",
                        )
                    i += 1

                    if not self._expect_token(i + 1, TokenType.VARIABLE):
                        raise TauschError("'if'-body must contain variable", i + 1)
                    i += 1
                    node_body = TreeNode(Op(OpType.IF_BODY))
                    node_body_true = TreeNode(Op(OpType.VARIABLE, self.tokens[i].value))
                    node_body.left = node_body_true

                    if self._expect_token(i + 1, TokenType.IF_ELSE):
                        i += 1
                        if self._expect_token(i + 1, TokenType.VARIABLE):
                            i += 1
                            node_body_false = TreeNode(
                                Op(OpType.VARIABLE, self.tokens[i].value)
                            )
                            node_body.right = node_body_false
                        else:
                            raise TauschError(
                                f"Expected variable after '{self.type_names[TokenType.IF_ELSE]}'",
                                i,
                            )
                    node_if.right = node_body
                    tree_root.insert_right(node_if)
                case _:
                    raise TauschError(f"Did not expect token of type {tok.typ}", i)
            i += 1

        return tree_root

    def _check(self, obj: Any, msg: str):
        if not obj:
            raise TauschError(msg)
        return True

    def eval(self, data: str) -> (str, TreeNode):
        self.data = data
        self._tokenize()
        tree_root = self._parse()

        if tree_root.left:
            node_itr = tree_root.left
            self._check(node_itr.operation, "No operation")
            self._check(node_itr.operation.typ is OpType.VARIABLE, "Parse error")
            self._check(
                node_itr.operation.value in self.variables,
                f"Variable '{node_itr.operation.value}' not found",
            )
            return (self.variables[node_itr.operation.value], tree_root)

        if tree_root.right:
            if_block = tree_root.right
            self._check(if_block.operation, "Parse error")
            self._check(if_block.operation.typ is OpType.IF_BLOCK, "Parse error")

            if_condition = tree_root.right.left
            self._check(if_condition, "Parse error")
            self._check(if_condition.operation, "Parse error")
            self._check(
                if_condition.operation.typ is OpType.IF_CONDITION, "Parse error"
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
            self._check(if_body.operation.typ is OpType.IF_BODY, "Parse error")

            if_body_left = tree_root.right.right.left
            self._check(if_body_left, "Parse error")
            self._check(if_body_left.operation, "Parse error")
            self._check(
                if_body_left.operation.typ is OpType.VARIABLE,
                "Parse error",
            )
            self._check(
                if_body_left.operation.value in self.variables,
                f"Variable '{if_body_left.operation.value}' not found",
            )

            if self.variables[if_condition.operation.value]:
                return (self.variables[if_body_left.operation.value], tree_root)

            if_body_right = tree_root.right.right.right
            if if_body_right:
                self._check(if_body_right.operation, "Parse error")
                self._check(
                    if_body_right.operation.typ is OpType.VARIABLE,
                    "Parse error",
                )
                self._check(
                    if_body_right.operation.value in self.variables,
                    f"Variable '{if_body_right.operation.value}' not found",
                )
                return (self.variables[if_body_right.operation.value], tree_root)

        return ("", tree_root)
