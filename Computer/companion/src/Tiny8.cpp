#include "apex/Tiny8.hpp"
#include "apex/Bits.hpp"

#include <algorithm>
#include <format>
#include <stdexcept>

namespace apex::tiny8 {
namespace {
void update_flags(Cpu& cpu, std::uint8_t value) noexcept {
    cpu.zero = value == 0U;
    cpu.negative = (value & 0x80U) != 0U;
}

std::uint8_t fetch(Cpu& cpu) noexcept {
    return cpu.memory[cpu.pc++];
}
} // namespace

StepStatus step(Cpu& cpu) noexcept {
    if (cpu.halted) return StepStatus::Halted;
    const auto opcode = static_cast<Op>(fetch(cpu));
    switch (opcode) {
    case Op::Nop:
        return StepStatus::Running;
    case Op::LdaImm:
        cpu.a = fetch(cpu);
        update_flags(cpu, cpu.a);
        return StepStatus::Running;
    case Op::LdaMem: {
        const auto address = fetch(cpu);
        cpu.a = cpu.memory[address];
        update_flags(cpu, cpu.a);
        return StepStatus::Running;
    }
    case Op::StaMem: {
        const auto address = fetch(cpu);
        cpu.memory[address] = cpu.a;
        return StepStatus::Running;
    }
    case Op::LdbImm:
        cpu.b = fetch(cpu);
        update_flags(cpu, cpu.b);
        return StepStatus::Running;
    case Op::AddB: {
        const auto result = apex::add8(cpu.a, cpu.b);
        cpu.a = result.value;
        cpu.carry = result.carry;
        cpu.zero = result.zero;
        cpu.negative = result.negative;
        return StepStatus::Running;
    }
    case Op::SubB: {
        const auto twos = static_cast<std::uint8_t>(~cpu.b + 1U);
        const auto result = apex::add8(cpu.a, twos);
        cpu.a = result.value;
        cpu.carry = result.carry;
        cpu.zero = result.zero;
        cpu.negative = result.negative;
        return StepStatus::Running;
    }
    case Op::Jmp:
        cpu.pc = fetch(cpu);
        return StepStatus::Running;
    case Op::Jz: {
        const auto target = fetch(cpu);
        if (cpu.zero) cpu.pc = target;
        return StepStatus::Running;
    }
    case Op::Call: {
        const auto target = fetch(cpu);
        if (cpu.sp == 0U) return StepStatus::StackOverflow;
        cpu.memory[cpu.sp--] = cpu.pc;
        cpu.pc = target;
        return StepStatus::Running;
    }
    case Op::Ret:
        if (cpu.sp == 0xFFU) return StepStatus::StackUnderflow;
        cpu.pc = cpu.memory[++cpu.sp];
        return StepStatus::Running;
    case Op::Halt:
        cpu.halted = true;
        return StepStatus::Halted;
    }
    return StepStatus::InvalidOpcode;
}

StepStatus run(Cpu& cpu, std::size_t max_steps) noexcept {
    for (std::size_t i = 0; i < max_steps; ++i) {
        const auto status = step(cpu);
        if (status != StepStatus::Running) return status;
    }
    return StepStatus::Running;
}

void load(Cpu& cpu, std::span<const std::uint8_t> program, std::uint8_t address) {
    const auto start = static_cast<std::size_t>(address);
    if (program.size() > cpu.memory.size() - start) {
        throw std::length_error("Tiny8 program does not fit in memory");
    }
    std::copy(program.begin(), program.end(), cpu.memory.begin() + static_cast<std::ptrdiff_t>(start));
    cpu.pc = address;
}

std::string trace_line(const Cpu& cpu) {
    return std::format("PC={:02X} A={:02X} B={:02X} SP={:02X} Z={} C={} N={}",
                       cpu.pc, cpu.a, cpu.b, cpu.sp,
                       cpu.zero ? 1 : 0, cpu.carry ? 1 : 0, cpu.negative ? 1 : 0);
}

} // namespace apex::tiny8
