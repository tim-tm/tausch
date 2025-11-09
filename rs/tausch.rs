use core::fmt;
use std::{any::Any, collections::HashMap};

use iter_tools::Itertools;

#[derive(Debug)]
pub enum TauschError {
    Tokenizer(String),
    Parser(String),
}

#[derive(Clone, Debug, PartialEq)]
pub enum VariableValue {
    Bool(bool),
    Str(String),
    Empty,
}

#[derive(Clone)]
pub enum TokenType {
    Variable,
    IfStart,
    IfNegate,
    IfEnd,
    IfElse,
}

impl fmt::Display for TokenType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}",
            match self {
                TokenType::Variable => "Variable",
                TokenType::IfStart => "IfStart",
                TokenType::IfNegate => "IfNegate",
                TokenType::IfEnd => "IfEnd",
                TokenType::IfElse => "IfElse",
            }
        )
    }
}

impl PartialEq for TokenType {
    fn eq(&self, other: &Self) -> bool {
        self.type_id() == other.type_id()
    }
}

#[derive(Clone)]
pub struct Token {
    pub typ: TokenType,
    pub label: String,
}

impl PartialEq for Token {
    fn eq(&self, other: &Self) -> bool {
        self.label == other.label && self.typ.type_id() == other.typ.type_id()
    }
}

pub struct Tokenizer {
    reserved_tokens: Vec<Token>,
}

impl Tokenizer {
    pub fn new() -> Tokenizer {
        let reserved_toks = vec![
            Token {
                typ: TokenType::IfStart,
                label: "if".to_string(),
            },
            Token {
                typ: TokenType::IfEnd,
                label: ";".to_string(),
            },
            Token {
                typ: TokenType::IfElse,
                label: ":".to_string(),
            },
            Token {
                typ: TokenType::IfNegate,
                label: "!".to_string(),
            },
        ];
        Tokenizer {
            reserved_tokens: reserved_toks,
        }
    }

    fn is_allowed_var_name(&self, c: char) -> bool {
        c.is_alphanumeric() || c == '_'
    }

    fn is_allowed_token(&self, c: char) -> bool {
        self.is_allowed_var_name(c)
            || self
                .reserved_tokens
                .iter()
                .find(|tok| tok.label.contains(c))
                .is_some()
    }

    pub fn tokenize(&self, input: String) -> Result<Vec<Token>, TauschError> {
        let mut toks: Vec<Token> = Vec::new();

        let mut temp_string = String::new();
        let mut iter = input.chars().into_iter().multipeek();
        while let Some(c) = iter.next() {
            match c {
                c if self.is_allowed_token(c) => {
                    temp_string.clear();
                    temp_string.push(c);
                    while let Some(pek) = iter.peek()
                        && self.is_allowed_token(*pek)
                    {
                        temp_string.push(*pek);
                        iter.next();
                    }

                    if let Some(tok) = self
                        .reserved_tokens
                        .iter()
                        .find(|tok| tok.label == temp_string)
                    {
                        toks.push(tok.clone());
                    } else {
                        toks.push(Token {
                            typ: TokenType::Variable,
                            label: temp_string.clone(),
                        });
                    }
                }
                c if c.is_whitespace() => temp_string.clear(),
                c => return Err(TauschError::Tokenizer(format!("Unknown token: '{c}'"))),
            }
        }
        Ok(toks)
    }
}

fn expect_token(
    iterator: &mut std::slice::Iter<Token>,
    typ: TokenType,
    on_fail: String,
) -> Result<Token, TauschError> {
    match iterator.next() {
        Some(tok) => {
            if tok.typ == typ {
                Ok(tok.clone())
            } else {
                Err(TauschError::Parser(on_fail))
            }
        }
        None => Err(TauschError::Parser(on_fail)),
    }
}

fn parse_if(
    variables: HashMap<String, VariableValue>,
    iterator: &mut std::slice::Iter<Token>,
) -> Result<VariableValue, TauschError> {
    let tok_condition = expect_token(
        iterator,
        TokenType::Variable,
        "Expected variable name after 'if'!".to_string(),
    )?;

    let Some(var_condition) = variables.get(&tok_condition.label) else {
        return Err(TauschError::Parser(format!(
            "Variable '{}' does not exist!",
            tok_condition.label
        )));
    };

    let VariableValue::Bool(val_condition) = var_condition else {
        return Err(TauschError::Parser(format!(
            "Variable '{}' is not a bool!",
            tok_condition.label
        )));
    };

    expect_token(
        iterator,
        TokenType::IfEnd,
        "Expected ';' after variable name inside of 'if'!".to_string(),
    )?;

    let tok_on_true = expect_token(
        iterator,
        TokenType::Variable,
        "Expected variable name inside of 'if'-branch of if-statement.".to_string(),
    )?;

    let Some(val_on_true) = variables.get(&tok_on_true.label) else {
        return Err(TauschError::Parser(format!(
            "Variable '{}' does not exist!",
            tok_on_true.label
        )));
    };

    let mut peek_iter = iterator.peekable();
    let Some(tok_else) = peek_iter.peek() else {
        return Ok(if *val_condition {
            val_on_true.clone()
        } else {
            VariableValue::Empty
        });
    };

    if tok_else.typ != TokenType::IfElse {
        return Err(TauschError::Parser(
            "Expected ':' to start an 'else'-branch for the if-statement".to_string(),
        ));
    }

    let tok_on_else = expect_token(
        iterator,
        TokenType::Variable,
        "Expected variable name inside of 'if'-branch of if-statement.".to_string(),
    )?;

    let Some(val_on_else) = variables.get(&tok_on_else.label) else {
        return Err(TauschError::Parser(format!(
            "Variable '{}' does not exist!",
            tok_on_else.label
        )));
    };

    Ok(if *val_condition {
        val_on_true.clone()
    } else {
        val_on_else.clone()
    })
}

pub fn eval(
    variables: HashMap<String, VariableValue>,
    input: String,
) -> Result<VariableValue, TauschError> {
    let toker = Tokenizer::new();
    let tokens = toker.tokenize(input)?;

    let mut iter = tokens.iter();
    match iter.next() {
        Some(tok) => match tok.typ {
            TokenType::Variable => {
                if let Some(var) = variables.get(&tok.label) {
                    return Ok(var.clone());
                } else {
                    return Err(TauschError::Parser(format!(
                        "Variable '{}' not found!",
                        tok.label
                    )));
                }
            }
            TokenType::IfStart => return parse_if(variables, &mut iter),
            _ => {
                return Err(TauschError::Parser(
                    "Expected start of an if-statement or variable name!".to_string(),
                ));
            }
        },
        None => return Err(TauschError::Parser("No tokens".to_string())),
    }
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use crate::{VariableValue, eval};

    #[test]
    fn eval_var() {
        let mut vars = HashMap::<String, VariableValue>::new();
        let var = VariableValue::Str("42".to_string());
        let var_str = "hello".to_string();
        vars.insert(var_str.clone(), var.clone());

        assert_eq!(eval(vars.clone(), var_str).expect("should never fail"), var);
    }

    #[test]
    fn eval_if_1() {
        let mut vars = HashMap::<String, VariableValue>::new();
        let var = VariableValue::Str("42".to_string());
        vars.insert("hello".to_string(), var.clone());
        vars.insert("cond".to_string(), VariableValue::Bool(true));

        assert_eq!(
            eval(vars.clone(), "if cond ; hello".to_string()).expect("should never fail"),
            var
        );
    }

    #[test]
    fn eval_if_2() {
        let mut vars = HashMap::<String, VariableValue>::new();
        let var = VariableValue::Str("42".to_string());
        vars.insert("hello".to_string(), var.clone());
        vars.insert("cond".to_string(), VariableValue::Bool(false));

        assert_eq!(
            eval(vars.clone(), "if cond ; hello".to_string()).expect("should never fail"),
            VariableValue::Empty
        );
    }

    #[test]
    fn eval_if_else_1() {
        let mut vars = HashMap::<String, VariableValue>::new();
        let var_hello = VariableValue::Str("42".to_string());
        vars.insert("hello".to_string(), var_hello.clone());
        vars.insert("world".to_string(), VariableValue::Str("69".to_string()));
        vars.insert("cond".to_string(), VariableValue::Bool(true));
        vars.insert("ncond".to_string(), VariableValue::Bool(false));

        assert_eq!(
            eval(vars.clone(), "if cond ; hello : world".to_string()).expect("should never fail"),
            var_hello
        );
    }

    #[test]
    fn eval_if_else_2() {
        let mut vars = HashMap::<String, VariableValue>::new();
        let var_world = VariableValue::Str("69".to_string());
        vars.insert("hello".to_string(), VariableValue::Str("42".to_string()));
        vars.insert("world".to_string(), var_world.clone());
        vars.insert("cond".to_string(), VariableValue::Bool(true));
        vars.insert("ncond".to_string(), VariableValue::Bool(false));

        assert_eq!(
            eval(vars.clone(), "if ncond ; hello : world".to_string()).expect("should never fail"),
            var_world
        );
    }
}
