# Direct x86-64 machine-code generator

```bash
python x64_codegen.py '(2 + 3) * 4' --raw expression.bin --elf expression
./expression
echo $?
python -m unittest -v
```

The generator encodes `mov`, `push`, `pop`, `add`, `sub`, `imul`, `cqo`,
`idiv`, `neg`, `ret`, and `syscall` directly. It does not call an assembler.
The raw function follows the System V AMD64 return convention; the ELF entry
uses Linux `exit(2)` system call number 60.
