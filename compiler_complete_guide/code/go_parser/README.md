# Go Pratt parser

```bash
go test ./...
go run . '1 + 2 * 3 == 7 && !false'
```

The parser uses a precedence table and one `parseExpression` loop. Adding a new
infix operator requires assigning a token kind and a precedence rather than
adding another recursive-descent function.
