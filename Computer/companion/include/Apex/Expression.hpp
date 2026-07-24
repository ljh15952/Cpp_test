#pragma once

#include <cstddef>
#include <string>
#include <string_view>
#include <vector>

namespace apex::expr {

enum class TokenKind { Number, Plus, Minus, Star, Slash, LeftParen, RightParen, End };

struct Token {
    TokenKind kind{};
    double number{};
    std::size_t begin{};
    std::size_t end{};
};

[[nodiscard]] std::vector<Token> lex(std::string_view source);

enum class Op { Constant, Add, Subtract, Multiply, Divide, Negate, Halt };

struct Instruction {
    Op op{};
    double operand{};
};

[[nodiscard]] std::vector<Instruction> compile(std::string_view source);
[[nodiscard]] double execute(const std::vector<Instruction>& program);
[[nodiscard]] double evaluate(std::string_view source);

} // namespace apex::expr
