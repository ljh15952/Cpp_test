#include "apex/Expression.hpp"

#include <charconv>
#include <cmath>
#include <stdexcept>

namespace apex::expr {

std::vector<Token> lex(std::string_view source) {
    std::vector<Token> out;
    std::size_t i = 0;
    while (i < source.size()) {
        const char c = source[i];
        if (c == ' ' || c == '\t' || c == '\r' || c == '\n') { ++i; continue; }
        auto simple = [&](TokenKind kind) {
            out.push_back(Token{kind, 0.0, i, i + 1U});
            ++i;
        };
        switch (c) {
        case '+': simple(TokenKind::Plus); continue;
        case '-': simple(TokenKind::Minus); continue;
        case '*': simple(TokenKind::Star); continue;
        case '/': simple(TokenKind::Slash); continue;
        case '(': simple(TokenKind::LeftParen); continue;
        case ')': simple(TokenKind::RightParen); continue;
        default: break;
        }
        if ((c >= '0' && c <= '9') || c == '.') {
            const std::size_t begin = i;
            bool dot_seen = false;
            while (i < source.size()) {
                const char n = source[i];
                if (n == '.') {
                    if (dot_seen) break;
                    dot_seen = true;
                    ++i;
                } else if (n >= '0' && n <= '9') {
                    ++i;
                } else break;
            }
            double value{};
            const auto* first = source.data() + static_cast<std::ptrdiff_t>(begin);
            const auto* last = source.data() + static_cast<std::ptrdiff_t>(i);
            const auto result = std::from_chars(first, last, value);
            if (result.ec != std::errc{} || result.ptr != last) {
                throw std::runtime_error("invalid number at offset " + std::to_string(begin));
            }
            out.push_back(Token{TokenKind::Number, value, begin, i});
            continue;
        }
        throw std::runtime_error("unexpected character at offset " + std::to_string(i));
    }
    out.push_back(Token{TokenKind::End, 0.0, source.size(), source.size()});
    return out;
}

namespace {
class Compiler {
public:
    explicit Compiler(std::vector<Token> tokens) : tokens_(std::move(tokens)) {}

    std::vector<Instruction> run() {
        expression();
        consume(TokenKind::End, "expected end of expression");
        code_.push_back({Op::Halt, 0.0});
        return code_;
    }

private:
    void expression() {
        term();
        while (match(TokenKind::Plus) || match(TokenKind::Minus)) {
            const auto op = previous().kind;
            term();
            code_.push_back({op == TokenKind::Plus ? Op::Add : Op::Subtract, 0.0});
        }
    }

    void term() {
        unary();
        while (match(TokenKind::Star) || match(TokenKind::Slash)) {
            const auto op = previous().kind;
            unary();
            code_.push_back({op == TokenKind::Star ? Op::Multiply : Op::Divide, 0.0});
        }
    }

    void unary() {
        if (match(TokenKind::Minus)) {
            unary();
            code_.push_back({Op::Negate, 0.0});
            return;
        }
        primary();
    }

    void primary() {
        if (match(TokenKind::Number)) {
            code_.push_back({Op::Constant, previous().number});
            return;
        }
        if (match(TokenKind::LeftParen)) {
            expression();
            consume(TokenKind::RightParen, "expected ')' after expression");
            return;
        }
        throw std::runtime_error("expected expression at offset " + std::to_string(peek().begin));
    }

    bool match(TokenKind kind) {
        if (peek().kind != kind) return false;
        ++current_;
        return true;
    }

    void consume(TokenKind kind, const char* message) {
        if (!match(kind)) throw std::runtime_error(message + std::string(" at offset ") + std::to_string(peek().begin));
    }

    const Token& peek() const { return tokens_.at(current_); }
    const Token& previous() const { return tokens_.at(current_ - 1U); }

    std::vector<Token> tokens_;
    std::size_t current_{};
    std::vector<Instruction> code_;
};

void require_stack(const std::vector<double>& stack, std::size_t count) {
    if (stack.size() < count) throw std::runtime_error("invalid bytecode: stack underflow");
}
} // namespace

std::vector<Instruction> compile(std::string_view source) {
    return Compiler(lex(source)).run();
}

double execute(const std::vector<Instruction>& program) {
    std::vector<double> stack;
    auto pop = [&]() {
        require_stack(stack, 1U);
        const double value = stack.back();
        stack.pop_back();
        return value;
    };
    for (std::size_t ip = 0; ip < program.size(); ++ip) {
        const auto instruction = program[ip];
        switch (instruction.op) {
        case Op::Constant: stack.push_back(instruction.operand); break;
        case Op::Negate: {
            const auto value = pop();
            stack.push_back(-value);
            break;
        }
        case Op::Add:
        case Op::Subtract:
        case Op::Multiply:
        case Op::Divide: {
            const double right = pop();
            const double left = pop();
            if (instruction.op == Op::Add) stack.push_back(left + right);
            else if (instruction.op == Op::Subtract) stack.push_back(left - right);
            else if (instruction.op == Op::Multiply) stack.push_back(left * right);
            else {
                if (right == 0.0) throw std::runtime_error("division by zero");
                stack.push_back(left / right);
            }
            break;
        }
        case Op::Halt:
            if (stack.size() != 1U) throw std::runtime_error("invalid bytecode: final stack depth");
            return stack.back();
        }
    }
    throw std::runtime_error("invalid bytecode: no halt");
}

double evaluate(std::string_view source) {
    return execute(compile(source));
}

} // namespace apex::expr
