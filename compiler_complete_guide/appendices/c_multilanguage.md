# 부록 C. C·C++·Rust·Go 비교 구현

C11 Lexer, Rust 2021 Lexer, C++20 AST Visitor, Go Pratt Parser의 전체 소스.
수록 파일 11개, 약 1,840줄.


이 부록의 코드는 본문에서 사용한 검증 원본이다. 줄 번호는 편집·수정에 따라 바뀔 수 있으므로 클래스·함수 이름으로 찾아간다.

## `code/c_lexer/lexer.c`

`````c
/*
 * MiniLang lexer in ISO C11.
 *
 * Build:
 *   cc -std=c11 -Wall -Wextra -Werror -O2 lexer.c -o lexer
 * Run:
 *   ./lexer sample.mini
 */
#include <ctype.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef enum TokenKind {
    TOK_EOF,
    TOK_ERROR,
    TOK_IDENTIFIER,
    TOK_INTEGER,
    TOK_STRING,
    TOK_LET,
    TOK_FN,
    TOK_STRUCT,
    TOK_IF,
    TOK_ELSE,
    TOK_WHILE,
    TOK_FOR,
    TOK_RETURN,
    TOK_TRUE,
    TOK_FALSE,
    TOK_INT,
    TOK_BOOL,
    TOK_STRING_TYPE,
    TOK_VOID,
    TOK_LEFT_PAREN,
    TOK_RIGHT_PAREN,
    TOK_LEFT_BRACE,
    TOK_RIGHT_BRACE,
    TOK_LEFT_BRACKET,
    TOK_RIGHT_BRACKET,
    TOK_COMMA,
    TOK_DOT,
    TOK_COLON,
    TOK_SEMICOLON,
    TOK_ARROW,
    TOK_PLUS,
    TOK_MINUS,
    TOK_STAR,
    TOK_SLASH,
    TOK_PERCENT,
    TOK_BANG,
    TOK_EQUAL,
    TOK_LESS,
    TOK_GREATER,
    TOK_BANG_EQUAL,
    TOK_EQUAL_EQUAL,
    TOK_LESS_EQUAL,
    TOK_GREATER_EQUAL,
    TOK_AND_AND,
    TOK_OR_OR
} TokenKind;

typedef struct Token {
    TokenKind kind;
    char *lexeme;
    int line;
    int column;
    int64_t integer;
} Token;

typedef struct TokenVector {
    Token *data;
    size_t length;
    size_t capacity;
} TokenVector;

typedef struct Lexer {
    const char *source;
    size_t length;
    size_t offset;
    int line;
    int column;
    int errors;
} Lexer;

typedef struct Keyword {
    const char *text;
    TokenKind kind;
} Keyword;

static const Keyword KEYWORDS[] = {
    {"let", TOK_LET},       {"fn", TOK_FN},         {"struct", TOK_STRUCT},
    {"if", TOK_IF},         {"else", TOK_ELSE},     {"while", TOK_WHILE},
    {"for", TOK_FOR},       {"return", TOK_RETURN}, {"true", TOK_TRUE},
    {"false", TOK_FALSE},   {"int", TOK_INT},       {"bool", TOK_BOOL},
    {"string", TOK_STRING_TYPE}, {"void", TOK_VOID},
};

static void die(const char *message) {
    fprintf(stderr, "fatal: %s\n", message);
    exit(EXIT_FAILURE);
}

static void *xrealloc(void *pointer, size_t size) {
    void *result = realloc(pointer, size);
    if (result == NULL && size != 0) {
        die("out of memory");
    }
    return result;
}

static char *slice_copy(const char *source, size_t start, size_t end) {
    if (end < start) {
        die("invalid source slice");
    }
    size_t length = end - start;
    char *text = xrealloc(NULL, length + 1);
    memcpy(text, source + start, length);
    text[length] = '\0';
    return text;
}

static void vector_push(TokenVector *vector, Token token) {
    if (vector->length == vector->capacity) {
        size_t new_capacity = vector->capacity == 0 ? 32 : vector->capacity * 2;
        vector->data = xrealloc(vector->data, new_capacity * sizeof(*vector->data));
        vector->capacity = new_capacity;
    }
    vector->data[vector->length++] = token;
}

static void vector_destroy(TokenVector *vector) {
    for (size_t i = 0; i < vector->length; ++i) {
        free(vector->data[i].lexeme);
    }
    free(vector->data);
    vector->data = NULL;
    vector->length = 0;
    vector->capacity = 0;
}

static bool at_end(const Lexer *lexer) {
    return lexer->offset >= lexer->length;
}

static char peek(const Lexer *lexer, size_t distance) {
    size_t index = lexer->offset + distance;
    return index >= lexer->length ? '\0' : lexer->source[index];
}

static char advance(Lexer *lexer) {
    char ch = lexer->source[lexer->offset++];
    if (ch == '\n') {
        lexer->line += 1;
        lexer->column = 1;
    } else if (ch == '\t') {
        lexer->column += 4;
    } else {
        lexer->column += 1;
    }
    return ch;
}

static bool match(Lexer *lexer, char expected) {
    if (peek(lexer, 0) != expected) {
        return false;
    }
    (void)advance(lexer);
    return true;
}

static Token make_token(const Lexer *lexer, TokenKind kind, size_t start,
                        int line, int column) {
    Token token;
    token.kind = kind;
    token.lexeme = slice_copy(lexer->source, start, lexer->offset);
    token.line = line;
    token.column = column;
    token.integer = 0;
    return token;
}

static Token error_token(Lexer *lexer, size_t start, int line, int column,
                         const char *message) {
    fprintf(stderr, "input:%d:%d: error: %s\n", line, column, message);
    lexer->errors += 1;
    return make_token(lexer, TOK_ERROR, start, line, column);
}

static void skip_block_comment(Lexer *lexer) {
    int start_line = lexer->line;
    int start_column = lexer->column;
    (void)advance(lexer); /* / */
    (void)advance(lexer); /* * */
    int depth = 1;
    while (depth > 0 && !at_end(lexer)) {
        if (peek(lexer, 0) == '/' && peek(lexer, 1) == '*') {
            (void)advance(lexer);
            (void)advance(lexer);
            depth += 1;
        } else if (peek(lexer, 0) == '*' && peek(lexer, 1) == '/') {
            (void)advance(lexer);
            (void)advance(lexer);
            depth -= 1;
        } else {
            (void)advance(lexer);
        }
    }
    if (depth != 0) {
        fprintf(stderr, "input:%d:%d: error: unterminated block comment\n",
                start_line, start_column);
        lexer->errors += 1;
    }
}

static void skip_trivia(Lexer *lexer) {
    for (;;) {
        char ch = peek(lexer, 0);
        if (ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n') {
            (void)advance(lexer);
        } else if (ch == '/' && peek(lexer, 1) == '/') {
            while (!at_end(lexer) && peek(lexer, 0) != '\n') {
                (void)advance(lexer);
            }
        } else if (ch == '/' && peek(lexer, 1) == '*') {
            skip_block_comment(lexer);
        } else {
            return;
        }
    }
}

static TokenKind identifier_kind(const char *text) {
    size_t count = sizeof(KEYWORDS) / sizeof(KEYWORDS[0]);
    for (size_t i = 0; i < count; ++i) {
        if (strcmp(text, KEYWORDS[i].text) == 0) {
            return KEYWORDS[i].kind;
        }
    }
    return TOK_IDENTIFIER;
}

static Token scan_identifier(Lexer *lexer, size_t start, int line, int column) {
    while (isalnum((unsigned char)peek(lexer, 0)) || peek(lexer, 0) == '_') {
        (void)advance(lexer);
    }
    Token token = make_token(lexer, TOK_IDENTIFIER, start, line, column);
    token.kind = identifier_kind(token.lexeme);
    return token;
}

static Token scan_number(Lexer *lexer, size_t start, int line, int column,
                         char first) {
    int base = 10;
    if (first == '0' && (peek(lexer, 0) == 'x' || peek(lexer, 0) == 'X')) {
        base = 16;
        (void)advance(lexer);
        while (isxdigit((unsigned char)peek(lexer, 0)) || peek(lexer, 0) == '_') {
            (void)advance(lexer);
        }
    } else if (first == '0' && (peek(lexer, 0) == 'b' || peek(lexer, 0) == 'B')) {
        base = 2;
        (void)advance(lexer);
        while (peek(lexer, 0) == '0' || peek(lexer, 0) == '1' || peek(lexer, 0) == '_') {
            (void)advance(lexer);
        }
    } else {
        while (isdigit((unsigned char)peek(lexer, 0)) || peek(lexer, 0) == '_') {
            (void)advance(lexer);
        }
    }

    Token token = make_token(lexer, TOK_INTEGER, start, line, column);
    size_t length = strlen(token.lexeme);
    char *normalized = xrealloc(NULL, length + 1);
    size_t output = 0;
    for (size_t i = 0; i < length; ++i) {
        if (token.lexeme[i] != '_') {
            normalized[output++] = token.lexeme[i];
        }
    }
    normalized[output] = '\0';

    const char *digits = normalized;
    if (base != 10) {
        digits += 2;
    }
    errno = 0;
    char *end = NULL;
    long long value = strtoll(digits, &end, base);
    if (errno == ERANGE || end == digits || *end != '\0') {
        fprintf(stderr, "input:%d:%d: error: invalid integer literal %s\n",
                line, column, token.lexeme);
        lexer->errors += 1;
        token.kind = TOK_ERROR;
    } else {
        token.integer = (int64_t)value;
    }
    free(normalized);
    return token;
}

static Token scan_string(Lexer *lexer, size_t start, int line, int column) {
    bool terminated = false;
    while (!at_end(lexer)) {
        char ch = advance(lexer);
        if (ch == '"') {
            terminated = true;
            break;
        }
        if (ch == '\n') {
            break;
        }
        if (ch == '\\' && !at_end(lexer)) {
            (void)advance(lexer);
        }
    }
    if (!terminated) {
        return error_token(lexer, start, line, column, "unterminated string literal");
    }
    return make_token(lexer, TOK_STRING, start, line, column);
}

static Token scan_token(Lexer *lexer) {
    skip_trivia(lexer);
    size_t start = lexer->offset;
    int line = lexer->line;
    int column = lexer->column;
    if (at_end(lexer)) {
        return make_token(lexer, TOK_EOF, start, line, column);
    }

    char ch = advance(lexer);
    if (isalpha((unsigned char)ch) || ch == '_') {
        return scan_identifier(lexer, start, line, column);
    }
    if (isdigit((unsigned char)ch)) {
        return scan_number(lexer, start, line, column, ch);
    }
    if (ch == '"') {
        return scan_string(lexer, start, line, column);
    }

    switch (ch) {
    case '(':
        return make_token(lexer, TOK_LEFT_PAREN, start, line, column);
    case ')':
        return make_token(lexer, TOK_RIGHT_PAREN, start, line, column);
    case '{':
        return make_token(lexer, TOK_LEFT_BRACE, start, line, column);
    case '}':
        return make_token(lexer, TOK_RIGHT_BRACE, start, line, column);
    case '[':
        return make_token(lexer, TOK_LEFT_BRACKET, start, line, column);
    case ']':
        return make_token(lexer, TOK_RIGHT_BRACKET, start, line, column);
    case ',':
        return make_token(lexer, TOK_COMMA, start, line, column);
    case '.':
        return make_token(lexer, TOK_DOT, start, line, column);
    case ':':
        return make_token(lexer, TOK_COLON, start, line, column);
    case ';':
        return make_token(lexer, TOK_SEMICOLON, start, line, column);
    case '+':
        return make_token(lexer, TOK_PLUS, start, line, column);
    case '-':
        return make_token(lexer, match(lexer, '>') ? TOK_ARROW : TOK_MINUS,
                          start, line, column);
    case '*':
        return make_token(lexer, TOK_STAR, start, line, column);
    case '/':
        return make_token(lexer, TOK_SLASH, start, line, column);
    case '%':
        return make_token(lexer, TOK_PERCENT, start, line, column);
    case '!':
        return make_token(lexer, match(lexer, '=') ? TOK_BANG_EQUAL : TOK_BANG,
                          start, line, column);
    case '=':
        return make_token(lexer, match(lexer, '=') ? TOK_EQUAL_EQUAL : TOK_EQUAL,
                          start, line, column);
    case '<':
        return make_token(lexer, match(lexer, '=') ? TOK_LESS_EQUAL : TOK_LESS,
                          start, line, column);
    case '>':
        return make_token(lexer, match(lexer, '=') ? TOK_GREATER_EQUAL : TOK_GREATER,
                          start, line, column);
    case '&':
        if (match(lexer, '&')) {
            return make_token(lexer, TOK_AND_AND, start, line, column);
        }
        break;
    case '|':
        if (match(lexer, '|')) {
            return make_token(lexer, TOK_OR_OR, start, line, column);
        }
        break;
    default:
        break;
    }
    return error_token(lexer, start, line, column, "unexpected character");
}

static TokenVector tokenize(Lexer *lexer) {
    TokenVector tokens = {0};
    for (;;) {
        Token token = scan_token(lexer);
        TokenKind kind = token.kind;
        vector_push(&tokens, token);
        if (kind == TOK_EOF) {
            return tokens;
        }
    }
}

static const char *kind_name(TokenKind kind) {
    static const char *names[] = {
        "EOF", "ERROR", "IDENTIFIER", "INTEGER", "STRING", "LET", "FN",
        "STRUCT", "IF", "ELSE", "WHILE", "FOR", "RETURN", "TRUE", "FALSE",
        "INT", "BOOL", "STRING_TYPE", "VOID", "LEFT_PAREN", "RIGHT_PAREN",
        "LEFT_BRACE", "RIGHT_BRACE", "LEFT_BRACKET", "RIGHT_BRACKET", "COMMA",
        "DOT", "COLON", "SEMICOLON", "ARROW", "PLUS", "MINUS", "STAR",
        "SLASH", "PERCENT", "BANG", "EQUAL", "LESS", "GREATER", "BANG_EQUAL",
        "EQUAL_EQUAL", "LESS_EQUAL", "GREATER_EQUAL", "AND_AND", "OR_OR"
    };
    size_t count = sizeof(names) / sizeof(names[0]);
    return (size_t)kind < count ? names[kind] : "UNKNOWN";
}

static char *read_file(const char *path, size_t *length) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) {
        fprintf(stderr, "cannot open %s: %s\n", path, strerror(errno));
        exit(EXIT_FAILURE);
    }
    if (fseek(file, 0, SEEK_END) != 0) {
        die("fseek failed");
    }
    long size = ftell(file);
    if (size < 0 || fseek(file, 0, SEEK_SET) != 0) {
        die("cannot determine file size");
    }
    char *buffer = xrealloc(NULL, (size_t)size + 1);
    size_t read = fread(buffer, 1, (size_t)size, file);
    if (read != (size_t)size && ferror(file)) {
        die("file read failed");
    }
    buffer[read] = '\0';
    fclose(file);
    *length = read;
    return buffer;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s SOURCE\n", argv[0]);
        return EXIT_FAILURE;
    }
    size_t length = 0;
    char *source = read_file(argv[1], &length);
    Lexer lexer = {source, length, 0, 1, 1, 0};
    TokenVector tokens = tokenize(&lexer);
    for (size_t i = 0; i < tokens.length; ++i) {
        const Token *token = &tokens.data[i];
        printf("%4d:%-3d %-15s %s", token->line, token->column,
               kind_name(token->kind), token->lexeme);
        if (token->kind == TOK_INTEGER) {
            printf(" => %lld", (long long)token->integer);
        }
        putchar('\n');
    }
    int status = lexer.errors == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
    vector_destroy(&tokens);
    free(source);
    return status;
}
`````

## `code/c_lexer/Makefile`

`````makefile
CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O2

all: lexer

lexer: lexer.c
	$(CC) $(CFLAGS) $< -o $@

test: lexer
	./lexer sample.mini | grep -q 'INTEGER.*0x2a => 42'
	./lexer sample.mini | grep -q 'AND_AND'

clean:
	rm -f lexer
.PHONY: all test clean
`````

## `code/c_lexer/sample.mini`

`````text
/* nested comments are accepted: /* inner */ */
fn main() -> int {
    let answer: int = 0x2a + 0b10;
    if (answer >= 44 && true) {
        print_string("C lexer OK");
    }
    return answer;
}
`````

## `code/rust_lexer/Cargo.toml`

`````toml
[package]
name = "minilang-rust-lexer"
version = "1.0.0"
edition = "2021"
publish = false

[profile.release]
lto = true
codegen-units = 1
`````

## `code/rust_lexer/src/main.rs`

`````rust
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
`````

## `code/rust_lexer/sample.mini`

`````text
fn main() -> int {
    let answer: int = 0x2a + 0b10;
    print_string("Rust lexer OK");
    return answer;
}
`````

## `code/cpp_ast/ast_visitor.cpp`

`````cpp
// MiniLang AST and Visitor Pattern example in C++20.
// Build: c++ -std=c++20 -Wall -Wextra -Werror -O2 ast_visitor.cpp -o ast_visitor
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>

namespace mini {

using Value = std::variant<std::int64_t, bool, std::string>;

struct IntegerExpr;
struct BooleanExpr;
struct StringExpr;
struct NameExpr;
struct BinaryExpr;
struct CallExpr;
struct LetStmt;
struct ExprStmt;
struct ReturnStmt;
struct BlockStmt;

struct Visitor {
    virtual ~Visitor() = default;
    virtual void visit(const IntegerExpr &) = 0;
    virtual void visit(const BooleanExpr &) = 0;
    virtual void visit(const StringExpr &) = 0;
    virtual void visit(const NameExpr &) = 0;
    virtual void visit(const BinaryExpr &) = 0;
    virtual void visit(const CallExpr &) = 0;
    virtual void visit(const LetStmt &) = 0;
    virtual void visit(const ExprStmt &) = 0;
    virtual void visit(const ReturnStmt &) = 0;
    virtual void visit(const BlockStmt &) = 0;
};

struct Node {
    virtual ~Node() = default;
    virtual void accept(Visitor &visitor) const = 0;
};

struct Expr : Node {};
struct Stmt : Node {};

using ExprPtr = std::unique_ptr<Expr>;
using StmtPtr = std::unique_ptr<Stmt>;

struct IntegerExpr final : Expr {
    explicit IntegerExpr(std::int64_t value) : value(value) {}
    void accept(Visitor &visitor) const override { visitor.visit(*this); }
    std::int64_t value;
};

struct BooleanExpr final : Expr {
    explicit BooleanExpr(bool value) : value(value) {}
    void accept(Visitor &visitor) const override { visitor.visit(*this); }
    bool value;
};

struct StringExpr final : Expr {
    explicit StringExpr(std::string value) : value(std::move(value)) {}
    void accept(Visitor &visitor) const override { visitor.visit(*this); }
    std::string value;
};

struct NameExpr final : Expr {
    explicit NameExpr(std::string name) : name(std::move(name)) {}
    void accept(Visitor &visitor) const override { visitor.visit(*this); }
    std::string name;
};

struct BinaryExpr final : Expr {
    BinaryExpr(ExprPtr left, std::string op, ExprPtr right)
        : left(std::move(left)), op(std::move(op)), right(std::move(right)) {}
    void accept(Visitor &visitor) const override { visitor.visit(*this); }
    ExprPtr left;
    std::string op;
    ExprPtr right;
};

struct CallExpr final : Expr {
    CallExpr(std::string callee, std::vector<ExprPtr> arguments)
        : callee(std::move(callee)), arguments(std::move(arguments)) {}
    void accept(Visitor &visitor) const override { visitor.visit(*this); }
    std::string callee;
    std::vector<ExprPtr> arguments;
};

struct LetStmt final : Stmt {
    LetStmt(std::string name, ExprPtr initializer)
        : name(std::move(name)), initializer(std::move(initializer)) {}
    void accept(Visitor &visitor) const override { visitor.visit(*this); }
    std::string name;
    ExprPtr initializer;
};

struct ExprStmt final : Stmt {
    explicit ExprStmt(ExprPtr expression) : expression(std::move(expression)) {}
    void accept(Visitor &visitor) const override { visitor.visit(*this); }
    ExprPtr expression;
};

struct ReturnStmt final : Stmt {
    explicit ReturnStmt(ExprPtr value) : value(std::move(value)) {}
    void accept(Visitor &visitor) const override { visitor.visit(*this); }
    ExprPtr value;
};

struct BlockStmt final : Stmt {
    explicit BlockStmt(std::vector<StmtPtr> statements)
        : statements(std::move(statements)) {}
    void accept(Visitor &visitor) const override { visitor.visit(*this); }
    std::vector<StmtPtr> statements;
};

class SExpressionPrinter final : public Visitor {
  public:
    std::string print(const Node &node) {
        output_.clear();
        node.accept(*this);
        return output_;
    }

    void visit(const IntegerExpr &node) override { output_ += std::to_string(node.value); }
    void visit(const BooleanExpr &node) override { output_ += node.value ? "true" : "false"; }
    void visit(const StringExpr &node) override {
        output_ += '"';
        for (char ch : node.value) {
            if (ch == '"' || ch == '\\') {
                output_ += '\\';
            }
            output_ += ch;
        }
        output_ += '"';
    }
    void visit(const NameExpr &node) override { output_ += node.name; }
    void visit(const BinaryExpr &node) override {
        output_ += '(' + node.op + ' ';
        node.left->accept(*this);
        output_ += ' ';
        node.right->accept(*this);
        output_ += ')';
    }
    void visit(const CallExpr &node) override {
        output_ += "(call " + node.callee;
        for (const auto &argument : node.arguments) {
            output_ += ' ';
            argument->accept(*this);
        }
        output_ += ')';
    }
    void visit(const LetStmt &node) override {
        output_ += "(let " + node.name + ' ';
        node.initializer->accept(*this);
        output_ += ')';
    }
    void visit(const ExprStmt &node) override {
        output_ += "(expr ";
        node.expression->accept(*this);
        output_ += ')';
    }
    void visit(const ReturnStmt &node) override {
        output_ += "(return ";
        node.value->accept(*this);
        output_ += ')';
    }
    void visit(const BlockStmt &node) override {
        output_ += "(block";
        for (const auto &statement : node.statements) {
            output_ += ' ';
            statement->accept(*this);
        }
        output_ += ')';
    }

  private:
    std::string output_;
};

class Evaluator final : public Visitor {
  public:
    Value evaluate(const Expr &expression) {
        expression.accept(*this);
        return value_;
    }

    Value execute(const BlockStmt &block) {
        returned_ = false;
        block.accept(*this);
        return value_;
    }

    void visit(const IntegerExpr &node) override { value_ = node.value; }
    void visit(const BooleanExpr &node) override { value_ = node.value; }
    void visit(const StringExpr &node) override { value_ = node.value; }
    void visit(const NameExpr &node) override {
        const auto found = environment_.find(node.name);
        if (found == environment_.end()) {
            throw std::runtime_error("undefined name: " + node.name);
        }
        value_ = found->second;
    }
    void visit(const BinaryExpr &node) override {
        const Value left = evaluate(*node.left);
        const Value right = evaluate(*node.right);
        if (node.op == "+") {
            value_ = as_integer(left) + as_integer(right);
        } else if (node.op == "-") {
            value_ = as_integer(left) - as_integer(right);
        } else if (node.op == "*") {
            value_ = as_integer(left) * as_integer(right);
        } else if (node.op == "/") {
            const auto divisor = as_integer(right);
            if (divisor == 0) {
                throw std::runtime_error("division by zero");
            }
            value_ = as_integer(left) / divisor;
        } else if (node.op == "==") {
            value_ = left == right;
        } else if (node.op == "<") {
            value_ = as_integer(left) < as_integer(right);
        } else {
            throw std::runtime_error("unknown operator: " + node.op);
        }
    }
    void visit(const CallExpr &node) override {
        if (node.callee != "print_int" || node.arguments.size() != 1) {
            throw std::runtime_error("unknown call: " + node.callee);
        }
        const auto result = as_integer(evaluate(*node.arguments.front()));
        std::cout << result << '\n';
        value_ = std::int64_t{0};
    }
    void visit(const LetStmt &node) override {
        environment_[node.name] = evaluate(*node.initializer);
    }
    void visit(const ExprStmt &node) override { (void)evaluate(*node.expression); }
    void visit(const ReturnStmt &node) override {
        value_ = evaluate(*node.value);
        returned_ = true;
    }
    void visit(const BlockStmt &node) override {
        for (const auto &statement : node.statements) {
            statement->accept(*this);
            if (returned_) {
                return;
            }
        }
    }

  private:
    static std::int64_t as_integer(const Value &value) {
        const auto *integer = std::get_if<std::int64_t>(&value);
        if (integer == nullptr) {
            throw std::runtime_error("expected integer value");
        }
        return *integer;
    }

    std::unordered_map<std::string, Value> environment_;
    Value value_ = std::int64_t{0};
    bool returned_ = false;
};

template <typename NodeType, typename... Args>
std::unique_ptr<NodeType> make(Args &&...args) {
    return std::make_unique<NodeType>(std::forward<Args>(args)...);
}

BlockStmt sample_program() {
    std::vector<StmtPtr> statements;
    statements.push_back(make<LetStmt>(
        "answer",
        make<BinaryExpr>(
            make<IntegerExpr>(2), "+",
            make<BinaryExpr>(make<IntegerExpr>(3), "*", make<IntegerExpr>(4)))));

    std::vector<ExprPtr> arguments;
    arguments.push_back(make<NameExpr>("answer"));
    statements.push_back(make<ExprStmt>(make<CallExpr>("print_int", std::move(arguments))));
    statements.push_back(make<ReturnStmt>(make<NameExpr>("answer")));
    return BlockStmt(std::move(statements));
}

} // namespace mini

int main() {
    try {
        mini::BlockStmt program = mini::sample_program();
        mini::SExpressionPrinter printer;
        std::cout << printer.print(program) << '\n';
        mini::Evaluator evaluator;
        const mini::Value result = evaluator.execute(program);
        std::cout << "result=" << std::get<std::int64_t>(result) << '\n';
        return std::get<std::int64_t>(result) == 14 ? 0 : 1;
    } catch (const std::exception &error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
}
`````

## `code/cpp_ast/Makefile`

`````makefile
CXX ?= c++
CXXFLAGS ?= -std=c++20 -Wall -Wextra -Werror -O2

all: ast_visitor

ast_visitor: ast_visitor.cpp
	$(CXX) $(CXXFLAGS) $< -o $@

test: ast_visitor
	./ast_visitor | grep -q 'result=14'

clean:
	rm -f ast_visitor
.PHONY: all test clean
`````

## `code/go_parser/go.mod`

`````text
module example.com/minilang/go-parser

go 1.22
`````

## `code/go_parser/main.go`

`````go
// Command go-parser demonstrates a Pratt parser for MiniLang expressions.
package main

import (
	"errors"
	"fmt"
	"os"
	"strconv"
	"strings"
	"unicode"
)

type TokenKind int

const (
	TokenEOF TokenKind = iota
	TokenError
	TokenIdentifier
	TokenInteger
	TokenTrue
	TokenFalse
	TokenLeftParen
	TokenRightParen
	TokenComma
	TokenPlus
	TokenMinus
	TokenStar
	TokenSlash
	TokenPercent
	TokenBang
	TokenEqualEqual
	TokenBangEqual
	TokenLess
	TokenLessEqual
	TokenGreater
	TokenGreaterEqual
	TokenAndAnd
	TokenOrOr
)

type Token struct {
	Kind   TokenKind
	Lexeme string
	Offset int
	Value  int64
}

type Lexer struct {
	source []rune
	pos    int
}

func NewLexer(source string) *Lexer {
	return &Lexer{source: []rune(source)}
}

func (lexer *Lexer) Next() Token {
	lexer.skipWhitespace()
	start := lexer.pos
	if lexer.atEnd() {
		return Token{Kind: TokenEOF, Offset: start}
	}
	ch := lexer.advance()
	if ch == '_' || unicode.IsLetter(ch) {
		for !lexer.atEnd() {
			next := lexer.peek(0)
			if next != '_' && !unicode.IsLetter(next) && !unicode.IsDigit(next) {
				break
			}
			lexer.advance()
		}
		text := string(lexer.source[start:lexer.pos])
		switch text {
		case "true":
			return Token{Kind: TokenTrue, Lexeme: text, Offset: start}
		case "false":
			return Token{Kind: TokenFalse, Lexeme: text, Offset: start}
		default:
			return Token{Kind: TokenIdentifier, Lexeme: text, Offset: start}
		}
	}
	if unicode.IsDigit(ch) {
		for !lexer.atEnd() && unicode.IsDigit(lexer.peek(0)) {
			lexer.advance()
		}
		text := string(lexer.source[start:lexer.pos])
		value, err := strconv.ParseInt(text, 10, 64)
		if err != nil {
			return Token{Kind: TokenError, Lexeme: text, Offset: start}
		}
		return Token{Kind: TokenInteger, Lexeme: text, Offset: start, Value: value}
	}

	makeToken := func(kind TokenKind) Token {
		return Token{Kind: kind, Lexeme: string(lexer.source[start:lexer.pos]), Offset: start}
	}
	switch ch {
	case '(':
		return makeToken(TokenLeftParen)
	case ')':
		return makeToken(TokenRightParen)
	case ',':
		return makeToken(TokenComma)
	case '+':
		return makeToken(TokenPlus)
	case '-':
		return makeToken(TokenMinus)
	case '*':
		return makeToken(TokenStar)
	case '/':
		return makeToken(TokenSlash)
	case '%':
		return makeToken(TokenPercent)
	case '!':
		if lexer.consume('=') {
			return makeToken(TokenBangEqual)
		}
		return makeToken(TokenBang)
	case '=':
		if lexer.consume('=') {
			return makeToken(TokenEqualEqual)
		}
	case '<':
		if lexer.consume('=') {
			return makeToken(TokenLessEqual)
		}
		return makeToken(TokenLess)
	case '>':
		if lexer.consume('=') {
			return makeToken(TokenGreaterEqual)
		}
		return makeToken(TokenGreater)
	case '&':
		if lexer.consume('&') {
			return makeToken(TokenAndAnd)
		}
	case '|':
		if lexer.consume('|') {
			return makeToken(TokenOrOr)
		}
	}
	return makeToken(TokenError)
}

func (lexer *Lexer) skipWhitespace() {
	for !lexer.atEnd() && unicode.IsSpace(lexer.peek(0)) {
		lexer.advance()
	}
}

func (lexer *Lexer) atEnd() bool {
	return lexer.pos >= len(lexer.source)
}

func (lexer *Lexer) peek(distance int) rune {
	index := lexer.pos + distance
	if index >= len(lexer.source) {
		return 0
	}
	return lexer.source[index]
}

func (lexer *Lexer) advance() rune {
	ch := lexer.source[lexer.pos]
	lexer.pos++
	return ch
}

func (lexer *Lexer) consume(expected rune) bool {
	if lexer.atEnd() || lexer.peek(0) != expected {
		return false
	}
	lexer.advance()
	return true
}

type ValueKind int

const (
	IntegerValue ValueKind = iota
	BooleanValue
)

type Value struct {
	Kind    ValueKind
	Integer int64
	Boolean bool
}

func Int(value int64) Value { return Value{Kind: IntegerValue, Integer: value} }
func Bool(value bool) Value { return Value{Kind: BooleanValue, Boolean: value} }
func (value Value) String() string {
	if value.Kind == IntegerValue {
		return strconv.FormatInt(value.Integer, 10)
	}
	return strconv.FormatBool(value.Boolean)
}

type Expr interface {
	String() string
	Eval(environment map[string]Value) (Value, error)
}

type IntegerExpr struct{ Value int64 }

func (expr IntegerExpr) String() string                         { return strconv.FormatInt(expr.Value, 10) }
func (expr IntegerExpr) Eval(_ map[string]Value) (Value, error) { return Int(expr.Value), nil }

type BooleanExpr struct{ Value bool }

func (expr BooleanExpr) String() string                         { return strconv.FormatBool(expr.Value) }
func (expr BooleanExpr) Eval(_ map[string]Value) (Value, error) { return Bool(expr.Value), nil }

type NameExpr struct{ Name string }

func (expr NameExpr) String() string { return expr.Name }
func (expr NameExpr) Eval(environment map[string]Value) (Value, error) {
	value, ok := environment[expr.Name]
	if !ok {
		return Value{}, fmt.Errorf("undefined name %q", expr.Name)
	}
	return value, nil
}

type UnaryExpr struct {
	Operator string
	Operand  Expr
}

func (expr UnaryExpr) String() string {
	return fmt.Sprintf("(%s %s)", expr.Operator, expr.Operand.String())
}
func (expr UnaryExpr) Eval(environment map[string]Value) (Value, error) {
	operand, err := expr.Operand.Eval(environment)
	if err != nil {
		return Value{}, err
	}
	switch expr.Operator {
	case "-":
		if operand.Kind != IntegerValue {
			return Value{}, errors.New("unary - requires integer")
		}
		return Int(-operand.Integer), nil
	case "+":
		if operand.Kind != IntegerValue {
			return Value{}, errors.New("unary + requires integer")
		}
		return operand, nil
	case "!":
		if operand.Kind != BooleanValue {
			return Value{}, errors.New("unary ! requires boolean")
		}
		return Bool(!operand.Boolean), nil
	default:
		return Value{}, fmt.Errorf("unknown unary operator %q", expr.Operator)
	}
}

type BinaryExpr struct {
	Left     Expr
	Operator string
	Right    Expr
}

func (expr BinaryExpr) String() string {
	return fmt.Sprintf("(%s %s %s)", expr.Operator, expr.Left.String(), expr.Right.String())
}
func (expr BinaryExpr) Eval(environment map[string]Value) (Value, error) {
	left, err := expr.Left.Eval(environment)
	if err != nil {
		return Value{}, err
	}
	if expr.Operator == "&&" {
		if left.Kind != BooleanValue {
			return Value{}, errors.New("&& requires booleans")
		}
		if !left.Boolean {
			return Bool(false), nil
		}
	}
	if expr.Operator == "||" {
		if left.Kind != BooleanValue {
			return Value{}, errors.New("|| requires booleans")
		}
		if left.Boolean {
			return Bool(true), nil
		}
	}
	right, err := expr.Right.Eval(environment)
	if err != nil {
		return Value{}, err
	}
	return evaluateBinary(expr.Operator, left, right)
}

func evaluateBinary(operator string, left, right Value) (Value, error) {
	arithmetic := func(operation func(int64, int64) int64) (Value, error) {
		if left.Kind != IntegerValue || right.Kind != IntegerValue {
			return Value{}, fmt.Errorf("%s requires integers", operator)
		}
		return Int(operation(left.Integer, right.Integer)), nil
	}
	compare := func(operation func(int64, int64) bool) (Value, error) {
		if left.Kind != IntegerValue || right.Kind != IntegerValue {
			return Value{}, fmt.Errorf("%s requires integers", operator)
		}
		return Bool(operation(left.Integer, right.Integer)), nil
	}
	switch operator {
	case "+":
		return arithmetic(func(a, b int64) int64 { return a + b })
	case "-":
		return arithmetic(func(a, b int64) int64 { return a - b })
	case "*":
		return arithmetic(func(a, b int64) int64 { return a * b })
	case "/":
		if right.Kind == IntegerValue && right.Integer == 0 {
			return Value{}, errors.New("division by zero")
		}
		return arithmetic(func(a, b int64) int64 { return a / b })
	case "%":
		if right.Kind == IntegerValue && right.Integer == 0 {
			return Value{}, errors.New("remainder by zero")
		}
		return arithmetic(func(a, b int64) int64 { return a % b })
	case "<":
		return compare(func(a, b int64) bool { return a < b })
	case "<=":
		return compare(func(a, b int64) bool { return a <= b })
	case ">":
		return compare(func(a, b int64) bool { return a > b })
	case ">=":
		return compare(func(a, b int64) bool { return a >= b })
	case "==":
		if left.Kind != right.Kind {
			return Bool(false), nil
		}
		if left.Kind == IntegerValue {
			return Bool(left.Integer == right.Integer), nil
		}
		return Bool(left.Boolean == right.Boolean), nil
	case "!=":
		equal, err := evaluateBinary("==", left, right)
		if err != nil {
			return Value{}, err
		}
		return Bool(!equal.Boolean), nil
	case "&&":
		if left.Kind != BooleanValue || right.Kind != BooleanValue {
			return Value{}, errors.New("&& requires booleans")
		}
		return Bool(left.Boolean && right.Boolean), nil
	case "||":
		if left.Kind != BooleanValue || right.Kind != BooleanValue {
			return Value{}, errors.New("|| requires booleans")
		}
		return Bool(left.Boolean || right.Boolean), nil
	default:
		return Value{}, fmt.Errorf("unknown operator %q", operator)
	}
}

type precedence int

const (
	precedenceLowest precedence = iota
	precedenceOr
	precedenceAnd
	precedenceEquality
	precedenceComparison
	precedenceSum
	precedenceProduct
	precedencePrefix
)

func tokenPrecedence(kind TokenKind) precedence {
	switch kind {
	case TokenOrOr:
		return precedenceOr
	case TokenAndAnd:
		return precedenceAnd
	case TokenEqualEqual, TokenBangEqual:
		return precedenceEquality
	case TokenLess, TokenLessEqual, TokenGreater, TokenGreaterEqual:
		return precedenceComparison
	case TokenPlus, TokenMinus:
		return precedenceSum
	case TokenStar, TokenSlash, TokenPercent:
		return precedenceProduct
	default:
		return precedenceLowest
	}
}

type Parser struct {
	lexer   *Lexer
	current Token
	errors  []error
}

func NewParser(source string) *Parser {
	parser := &Parser{lexer: NewLexer(source)}
	parser.advance()
	return parser
}

func (parser *Parser) Parse() (Expr, error) {
	expression := parser.parseExpression(precedenceLowest)
	if parser.current.Kind != TokenEOF {
		parser.errors = append(parser.errors, fmt.Errorf("unexpected token %q", parser.current.Lexeme))
	}
	if len(parser.errors) != 0 {
		messages := make([]string, len(parser.errors))
		for index, err := range parser.errors {
			messages[index] = err.Error()
		}
		return nil, errors.New(strings.Join(messages, "; "))
	}
	return expression, nil
}

func (parser *Parser) parseExpression(minimum precedence) Expr {
	left := parser.parsePrefix()
	for parser.current.Kind != TokenEOF && minimum < tokenPrecedence(parser.current.Kind) {
		operator := parser.current
		precedence := tokenPrecedence(operator.Kind)
		parser.advance()
		right := parser.parseExpression(precedence)
		left = BinaryExpr{Left: left, Operator: operator.Lexeme, Right: right}
	}
	return left
}

func (parser *Parser) parsePrefix() Expr {
	token := parser.current
	parser.advance()
	switch token.Kind {
	case TokenInteger:
		return IntegerExpr{Value: token.Value}
	case TokenTrue:
		return BooleanExpr{Value: true}
	case TokenFalse:
		return BooleanExpr{Value: false}
	case TokenIdentifier:
		return NameExpr{Name: token.Lexeme}
	case TokenMinus, TokenPlus, TokenBang:
		return UnaryExpr{Operator: token.Lexeme, Operand: parser.parseExpression(precedencePrefix)}
	case TokenLeftParen:
		expression := parser.parseExpression(precedenceLowest)
		if parser.current.Kind != TokenRightParen {
			parser.errors = append(parser.errors, fmt.Errorf("expected ')', got %q", parser.current.Lexeme))
		} else {
			parser.advance()
		}
		return expression
	default:
		parser.errors = append(parser.errors, fmt.Errorf("expected expression at offset %d", token.Offset))
		return IntegerExpr{Value: 0}
	}
}

func (parser *Parser) advance() {
	parser.current = parser.lexer.Next()
	if parser.current.Kind == TokenError {
		parser.errors = append(parser.errors, fmt.Errorf("invalid token %q", parser.current.Lexeme))
	}
}

func main() {
	source := "1 + 2 * 3 == 7 && !false"
	if len(os.Args) > 1 {
		source = strings.Join(os.Args[1:], " ")
	}
	parser := NewParser(source)
	expression, err := parser.Parse()
	if err != nil {
		fmt.Fprintln(os.Stderr, "parse error:", err)
		os.Exit(1)
	}
	environment := map[string]Value{"x": Int(10), "flag": Bool(true)}
	result, err := expression.Eval(environment)
	if err != nil {
		fmt.Fprintln(os.Stderr, "evaluation error:", err)
		os.Exit(1)
	}
	fmt.Println(expression.String())
	fmt.Println(result.String())
}
`````

## `code/go_parser/main_test.go`

`````go
package main

import "testing"

func parseForTest(t *testing.T, source string) Expr {
	t.Helper()
	parser := NewParser(source)
	expression, err := parser.Parse()
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	return expression
}

func TestPrecedence(t *testing.T) {
	expression := parseForTest(t, "1 + 2 * 3 == 7 || false")
	expected := "(|| (== (+ 1 (* 2 3)) 7) false)"
	if expression.String() != expected {
		t.Fatalf("got %s, want %s", expression.String(), expected)
	}
}

func TestEvaluation(t *testing.T) {
	expression := parseForTest(t, "x * 2 + 1")
	result, err := expression.Eval(map[string]Value{"x": Int(20)})
	if err != nil {
		t.Fatal(err)
	}
	if result.Kind != IntegerValue || result.Integer != 41 {
		t.Fatalf("unexpected result: %#v", result)
	}
}

func TestShortCircuit(t *testing.T) {
	expression := parseForTest(t, "false && missing")
	result, err := expression.Eval(map[string]Value{})
	if err != nil {
		t.Fatal(err)
	}
	if result.Kind != BooleanValue || result.Boolean {
		t.Fatalf("unexpected result: %#v", result)
	}
}

func TestSyntaxError(t *testing.T) {
	parser := NewParser("1 + )")
	if _, err := parser.Parse(); err == nil {
		t.Fatal("expected parse error")
	}
}
`````
