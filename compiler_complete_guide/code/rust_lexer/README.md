# Rust lexer

```bash
cargo test
cargo run --release -- sample.mini
```

The implementation uses only the Rust standard library. Tokens own their
lexemes, which simplifies lifetime management for a teaching implementation.
A production compiler can instead intern identifiers or keep source slices.
