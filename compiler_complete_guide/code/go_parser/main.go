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
