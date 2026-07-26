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
