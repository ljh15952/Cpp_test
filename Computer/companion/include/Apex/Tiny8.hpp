#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace apex::tiny8 {

enum class Op : std::uint8_t {
    Nop = 0x00,
    LdaImm = 0x10,
    LdaMem = 0x11,
    StaMem = 0x12,
    LdbImm = 0x13,
    AddB = 0x20,
    SubB = 0x21,
    Jmp = 0x30,
    Jz = 0x31,
    Call = 0x40,
    Ret = 0x41,
    Halt = 0xFF,
};

enum class StepStatus { Running, Halted, InvalidOpcode, StackOverflow, StackUnderflow };

struct Cpu {
    std::uint8_t a{};
    std::uint8_t b{};
    std::uint8_t pc{};
    std::uint8_t sp{0xFF};
    bool zero{};
    bool carry{};
    bool negative{};
    bool halted{};
    std::array<std::uint8_t, 256> memory{};
};

[[nodiscard]] StepStatus step(Cpu& cpu) noexcept;
[[nodiscard]] StepStatus run(Cpu& cpu, std::size_t max_steps = 100000U) noexcept;
void load(Cpu& cpu, std::span<const std::uint8_t> program, std::uint8_t address = 0U);
[[nodiscard]] std::string trace_line(const Cpu& cpu);

} // namespace apex::tiny8
