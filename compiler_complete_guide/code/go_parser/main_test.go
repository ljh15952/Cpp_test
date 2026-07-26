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
