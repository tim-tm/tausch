pub mod tausch {
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

    enum TokenType {
        Variable,
        IfStart,
        IfNegate,
        IfEnd,
        IfElse,
    }

    struct Token {
        typ: TokenType,
        value: String,
    }

    fn is_allowed_char(c: char) -> bool {
        c.is_alphanumeric() || c == '_'
    }

    fn tokenize(input: String) -> Vec<Token> {
        let mut toks: Vec<Token> = Vec::new();
        for c in input.chars() {
            match c {
                c if c.is_whitespace() => continue,
                c if is_allowed_char(c) => toks.push(Token {
                    typ: TokenType::Variable,
                    value: "a".to_string(),
                }),
                _ => todo!(),
            }
        }
        toks
    }

    pub fn eval<T: Clone>(variables: Vec<Variable<T>>, input: String) -> Variable<T> {
        for ele in tokenize(input) {
            println!("{}", ele.value);
        }
        variables.first().unwrap().clone()
    }
}

#[cfg(test)]
mod tests {
    use crate::tausch::{Variable, eval};

    #[test]
    fn test_eval() {
        let vars = vec![Variable::new("hello".to_string(), 42)];
        assert_eq!(eval(vars, "hello".to_string()).key, "hello");
    }
}
