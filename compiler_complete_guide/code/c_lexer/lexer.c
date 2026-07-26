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
