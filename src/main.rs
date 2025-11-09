use std::{collections::HashMap, io};
use tausch::{TauschError, VariableValue, eval};

pub fn main() {
    let mut vars = HashMap::<String, VariableValue>::new();
    vars.insert("hello".to_string(), VariableValue::Str("42".to_string()));
    vars.insert("world".to_string(), VariableValue::Str("69".to_string()));
    vars.insert("cond".to_string(), VariableValue::Bool(true));
    vars.insert("ncond".to_string(), VariableValue::Bool(false));

    let mut buf = String::new();
    while io::stdin().read_line(&mut buf).is_ok() && !buf.contains("exit") {
        match eval(vars.clone(), buf.clone()) {
            Ok(var) => match var {
                VariableValue::Bool(val) => println!("result: value='{}' (bool)", val),
                VariableValue::Str(val) => println!("result: value='{}' (str)", val),
                VariableValue::Empty => println!("result: emptyness"),
            },
            Err(e) => match e {
                TauschError::Tokenizer(err) => println!("Tokenizing failed: {}", err),
                TauschError::Parser(err) => println!("Parsing failed: {}", err),
            },
        }
        buf.clear();
    }
}
