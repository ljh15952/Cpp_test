//! MiniLang lexer implemented in safe Rust 2021.
//! No external crates are required.

use std::env;
use std::fmt;
use std::fs;
use std::process::ExitCode;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum TokenKind {
    Eof,
    Error,
    Identifier,
    Integer,
    String,
    Let,
    Fn,
    Struct,
    If,
    Else,
    While,
    For,
    Return,
    True,
    False,
    Int,
    Bool,
    StringType,
    Void,
    LeftParen,
    RightParen,
    LeftBrace,
    RightBrace,
    LeftBracket,
    RightBracket,
    Comma,
    Dot,
    Colon,
    Semicolon,
    Arrow,
    Plus,
    Minus,
    Star,
    Slash,
    Percent,
    Bang,
    Equal,
    Less,
    Greater,
    BangEqual,
    EqualEqual,
    LessEqual,
    GreaterEqual,
    AndAnd,
    OrOr,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum Literal {
    Integer(i64),
    String(String),
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct Token {
    kind: TokenKind,
    lexeme: String,
    literal: Option<Literal>,
    line: usize,
    column: usize,
}

impl fmt::Display for Token {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{:4}:{:<3} {:<15?} {}",
            self.line, self.column, self.kind, self.lexeme
        )?;
        if let Some(literal) = &self.literal {
            write!(formatter, " => {literal:?}")?;
        }
        Ok(())
    }
}

struct Lexer {
    chars: Vec<char>,
    current: usize,
    line: usize,
    column: usize,
    errors: Vec<String>,
}

impl Lexer {
    fn new(source: &str) -> Self {
        Self {
            chars: source.chars().collect(),
            current: 0,
            line: 1,
            column: 1,
            errors: Vec::new(),
        }
    }

    fn tokenize(&mut self) -> Vec<Token> {
        let mut tokens = Vec::new();
        loop {
            let token = self.scan_token();
            let at_end = token.kind == TokenKind::Eof;
            tokens.push(token);
            if at_end {
                return tokens;
            }
        }
    }

    fn scan_token(&mut self) -> Token {
        self.skip_trivia();
        let start = self.current;
        let line = self.line;
        let column = self.column;
        if self.at_end() {
            return self.make_token(TokenKind::Eof, start, line, column, None);
        }

        let ch = self.advance();
        if ch == '_' || ch.is_alphabetic() {
            return self.identifier(start, line, column);
        }
        if ch.is_ascii_digit() {
            return self.number(start, line, column, ch);
        }
        if ch == '"' {
            return self.string(start, line, column);
        }

        let kind = match ch {
            '(' => Some(TokenKind::LeftParen),
            ')' => Some(TokenKind::RightParen),
            '{' => Some(TokenKind::LeftBrace),
            '}' => Some(TokenKind::RightBrace),
            '[' => Some(TokenKind::LeftBracket),
            ']' => Some(TokenKind::RightBracket),
            ',' => Some(TokenKind::Comma),
            '.' => Some(TokenKind::Dot),
            ':' => Some(TokenKind::Colon),
            ';' => Some(TokenKind::Semicolon),
            '+' => Some(TokenKind::Plus),
            '*' => Some(TokenKind::Star),
            '/' => Some(TokenKind::Slash),
            '%' => Some(TokenKind::Percent),
            '-' if self.consume_if('>') => Some(TokenKind::Arrow),
            '-' => Some(TokenKind::Minus),
            '!' if self.consume_if('=') => Some(TokenKind::BangEqual),
            '!' => Some(TokenKind::Bang),
            '=' if self.consume_if('=') => Some(TokenKind::EqualEqual),
            '=' => Some(TokenKind::Equal),
            '<' if self.consume_if('=') => Some(TokenKind::LessEqual),
            '<' => Some(TokenKind::Less),
            '>' if self.consume_if('=') => Some(TokenKind::GreaterEqual),
            '>' => Some(TokenKind::Greater),
            '&' if self.consume_if('&') => Some(TokenKind::AndAnd),
            '|' if self.consume_if('|') => Some(TokenKind::OrOr),
            _ => None,
        };
        match kind {
            Some(kind) => self.make_token(kind, start, line, column, None),
            None => self.error_token(start, line, column, format!("unexpected character {ch:?}")),
        }
    }

    fn skip_trivia(&mut self) {
        loop {
            match (self.peek(0), self.peek(1)) {
                (Some(ch), _) if ch.is_whitespace() => {
                    self.advance();
                }
                (Some('/'), Some('/')) => {
                    while !self.at_end() && self.peek(0) != Some('\n') {
                        self.advance();
                    }
                }
                (Some('/'), Some('*')) => self.skip_block_comment(),
                _ => return,
            }
        }
    }

    fn skip_block_comment(&mut self) {
        let line = self.line;
        let column = self.column;
        self.advance();
        self.advance();
        let mut depth = 1usize;
        while depth > 0 && !self.at_end() {
            match (self.peek(0), self.peek(1)) {
                (Some('/'), Some('*')) => {
                    self.advance();
                    self.advance();
                    depth += 1;
                }
                (Some('*'), Some('/')) => {
                    self.advance();
                    self.advance();
                    depth -= 1;
                }
                _ => {
                    self.advance();
                }
            }
        }
        if depth != 0 {
            self.errors
                .push(format!("input:{line}:{column}: unterminated block comment"));
        }
    }

    fn identifier(&mut self, start: usize, line: usize, column: usize) -> Token {
        while matches!(self.peek(0), Some(ch) if ch == '_' || ch.is_alphanumeric()) {
            self.advance();
        }
        let lexeme = self.slice(start);
        let kind = match lexeme.as_str() {
            "let" => TokenKind::Let,
            "fn" => TokenKind::Fn,
            "struct" => TokenKind::Struct,
            "if" => TokenKind::If,
            "else" => TokenKind::Else,
            "while" => TokenKind::While,
            "for" => TokenKind::For,
            "return" => TokenKind::Return,
            "true" => TokenKind::True,
            "false" => TokenKind::False,
            "int" => TokenKind::Int,
            "bool" => TokenKind::Bool,
            "string" => TokenKind::StringType,
            "void" => TokenKind::Void,
            _ => TokenKind::Identifier,
        };
        Token {
            kind,
            lexeme,
            literal: None,
            line,
            column,
        }
    }

    fn number(&mut self, start: usize, line: usize, column: usize, first: char) -> Token {
        let mut base = 10;
        if first == '0' && matches!(self.peek(0), Some('x' | 'X')) {
            base = 16;
            self.advance();
            while matches!(self.peek(0), Some(ch) if ch.is_ascii_hexdigit() || ch == '_') {
                self.advance();
            }
        } else if first == '0' && matches!(self.peek(0), Some('b' | 'B')) {
            base = 2;
            self.advance();
            while matches!(self.peek(0), Some('0' | '1' | '_')) {
                self.advance();
            }
        } else {
            while matches!(self.peek(0), Some(ch) if ch.is_ascii_digit() || ch == '_') {
                self.advance();
            }
        }
        let lexeme = self.slice(start);
        let normalized: String = lexeme.chars().filter(|ch| *ch != '_').collect();
        let digits = if base == 10 { &normalized[..] } else { &normalized[2..] };
        match i64::from_str_radix(digits, base) {
            Ok(value) => Token {
                kind: TokenKind::Integer,
                lexeme,
                literal: Some(Literal::Integer(value)),
                line,
                column,
            },
            Err(error) => self.error_token(
                start,
                line,
                column,
                format!("invalid integer literal: {error}"),
            ),
        }
    }

    fn string(&mut self, start: usize, line: usize, column: usize) -> Token {
        let mut value = String::new();
        while !self.at_end() {
            let ch = self.advance();
            match ch {
                '"' => {
                    return Token {
                        kind: TokenKind::String,
                        lexeme: self.slice(start),
                        literal: Some(Literal::String(value)),
                        line,
                        column,
                    };
                }
                '\n' => break,
                '\\' => match self.advance_optional() {
                    Some('n') => value.push('\n'),
                    Some('r') => value.push('\r'),
                    Some('t') => value.push('\t'),
                    Some('0') => value.push('\0'),
                    Some('"') => value.push('"'),
                    Some('\\') => value.push('\\'),
                    Some(other) => {
                        self.errors.push(format!(
                            "input:{line}:{column}: unknown escape sequence \\{other}"
                        ));
                        value.push(other);
                    }
                    None => break,
                },
                other => value.push(other),
            }
        }
        self.error_token(start, line, column, "unterminated string literal".to_owned())
    }

    fn error_token(
        &mut self,
        start: usize,
        line: usize,
        column: usize,
        message: String,
    ) -> Token {
        self.errors
            .push(format!("input:{line}:{column}: {message}"));
        self.make_token(TokenKind::Error, start, line, column, None)
    }

    fn make_token(
        &self,
        kind: TokenKind,
        start: usize,
        line: usize,
        column: usize,
        literal: Option<Literal>,
    ) -> Token {
        Token {
            kind,
            lexeme: self.slice(start),
            literal,
            line,
            column,
        }
    }

    fn slice(&self, start: usize) -> String {
        self.chars[start..self.current].iter().collect()
    }

    fn at_end(&self) -> bool {
        self.current >= self.chars.len()
    }

    fn peek(&self, distance: usize) -> Option<char> {
        self.chars.get(self.current + distance).copied()
    }

    fn consume_if(&mut self, expected: char) -> bool {
        if self.peek(0) != Some(expected) {
            return false;
        }
        self.advance();
        true
    }

    fn advance_optional(&mut self) -> Option<char> {
        if self.at_end() {
            None
        } else {
            Some(self.advance())
        }
    }

    fn advance(&mut self) -> char {
        let ch = self.chars[self.current];
        self.current += 1;
        if ch == '\n' {
            self.line += 1;
            self.column = 1;
        } else if ch == '\t' {
            self.column += 4;
        } else {
            self.column += 1;
        }
        ch
    }
}

fn run(path: &str) -> Result<(), String> {
    let source = fs::read_to_string(path).map_err(|error| format!("cannot read {path}: {error}"))?;
    let mut lexer = Lexer::new(&source);
    let tokens = lexer.tokenize();
    for token in tokens {
        println!("{token}");
    }
    if lexer.errors.is_empty() {
        Ok(())
    } else {
        for error in lexer.errors {
            eprintln!("{error}");
        }
        Err("lexical analysis failed".to_owned())
    }
}

fn main() -> ExitCode {
    let mut arguments = env::args();
    let program = arguments.next().unwrap_or_else(|| "rust-lexer".to_owned());
    let Some(path) = arguments.next() else {
        eprintln!("usage: {program} SOURCE");
        return ExitCode::FAILURE;
    };
    if arguments.next().is_some() {
        eprintln!("usage: {program} SOURCE");
        return ExitCode::FAILURE;
    }
    match run(&path) {
        Ok(()) => ExitCode::SUCCESS,
        Err(message) => {
            eprintln!("{message}");
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn scans_keywords_numbers_and_comments() {
        let mut lexer = Lexer::new("/* a /* b */ c */ let answer = 0x2a + 0b10;");
        let tokens = lexer.tokenize();
        assert!(lexer.errors.is_empty(), "{:?}", lexer.errors);
        assert_eq!(tokens[0].kind, TokenKind::Let);
        assert_eq!(tokens[1].kind, TokenKind::Identifier);
        assert_eq!(tokens[3].literal, Some(Literal::Integer(42)));
        assert_eq!(tokens[5].literal, Some(Literal::Integer(2)));
    }

    #[test]
    fn decodes_strings() {
        let mut lexer = Lexer::new("\"line\\ntext\"");
        let tokens = lexer.tokenize();
        assert_eq!(
            tokens[0].literal,
            Some(Literal::String("line\ntext".to_owned()))
        );
    }

    #[test]
    fn preserves_unicode_identifiers() {
        let mut lexer = Lexer::new("let 결과 = 42;");
        let tokens = lexer.tokenize();
        assert_eq!(tokens[1].lexeme, "결과");
    }
}
