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
