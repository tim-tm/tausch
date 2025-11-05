use core::fmt;
use std::any::{Any, TypeId};

use iter_tools::Itertools;

#[derive(Debug)]
pub enum TauschError {
    Tokenizer(String),
    Parser(String),
}

#[allow(dead_code)]
#[derive(Clone)]
pub struct Variable<T: Clone> {
    pub key: String,
    pub value: T,
}

impl<T: Clone> Variable<T> {
    pub fn new(key: String, value: T) -> Variable<T> {
        Variable {
            key: key,
            value: value,
        }
    }
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

fn parse_if<T: Clone + 'static>(
    variables: Vec<Variable<T>>,
    iterator: &mut std::slice::Iter<Token>,
) -> Result<Variable<T>, TauschError> {
    match iterator.next() {
        Some(tok) => {
            if tok.typ == TokenType::Variable {
                let condition = tok;
                if let Some(tok) = iterator.next()
                    && tok.typ == TokenType::IfEnd
                {
                    // TODO: refactor this piece of shit
                    if let Some(tok) = iterator.next()
                        && tok.typ == TokenType::Variable
                    {
                        if let Some(cond) = variables.iter().find(|var| var.key == condition.label)
                        {
                            if cond.value.type_id() == TypeId::of::<bool>() {
                                if let Some(on_true) =
                                    variables.iter().find(|var| var.key == tok.label)
                                {
                                    if on_true.value.type_id() == TypeId::of::<bool>() {
                                        return Err(TauschError::Parser("var".to_string()));
                                    } else {
                                        return Err(TauschError::Parser("unreachable".to_string()));
                                    }
                                } else {
                                    return Err(TauschError::Parser(format!(
                                        "Variable '{}' does not exist!",
                                        tok.label
                                    )));
                                }
                            } else {
                                return Err(TauschError::Parser(format!(
                                    "Variable '{}' is not a bool!",
                                    cond.key
                                )));
                            }
                        } else {
                            return Err(TauschError::Parser(format!(
                                "Variable '{}' does not exist!",
                                condition.label
                            )));
                        }
                    } else {
                        return Err(TauschError::Parser(
                            "Expected variable name after end of if-statement condition!"
                                .to_string(),
                        ));
                    }
                } else {
                    return Err(TauschError::Parser(
                        "Expected ';' to end if-statement condition!".to_string(),
                    ));
                }
            } else {
                return Err(TauschError::Parser(format!(
                    "Expected variable name after 'if', found token of type: '{}'!",
                    tok.typ
                )));
            }
        }
        None => {
            return Err(TauschError::Parser(
                "Expected variable name after 'if', found nothing!".to_string(),
            ));
        }
    }
}

pub fn eval<T: Clone + 'static>(
    variables: Vec<Variable<T>>,
    input: String,
) -> Result<Variable<T>, TauschError> {
    let toker = Tokenizer::new();
    let tokens = toker.tokenize(input)?;

    let mut iter = tokens.iter();
    match iter.next() {
        Some(tok) => match tok.typ {
            TokenType::Variable => {
                if let Some(var) = variables.iter().find(|var| var.key == tok.label) {
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
