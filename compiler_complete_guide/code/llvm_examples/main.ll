; Minimal LLVM IR used in Part 8.
source_filename = "main.mini"

define i32 @main() {
entry:
  %answer = add i32 40, 2
  ret i32 %answer
}
