use std::io;
use tausch::{TauschError, Variable, eval};

pub fn main() {
    let vars = vec![
        Variable {
            key: "hello".to_string(),
            value: 42,
        },
        Variable {
            key: "cond".to_string(),
            value: true,
        },
    ];

    let mut buf = String::new();
    while io::stdin().read_line(&mut buf).is_ok() && !buf.contains("exit") {
        match eval(vars.clone(), buf.clone()) {
            Ok(var) => println!("result: key='{}',value='{}'", var.key, var.value),
            Err(e) => match e {
                TauschError::Tokenizer(err) => println!("Tokenizing failed: {}", err),
                TauschError::Parser(err) => println!("Parsing failed: {}", err),
            },
        }
        buf.clear();
    }
}
