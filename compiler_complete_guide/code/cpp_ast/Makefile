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
