#pragma once

#include <cstdint>

namespace apex {

struct Add8Result {
    std::uint8_t value{};
    bool carry{};
    bool overflow{};
    bool zero{};
    bool negative{};
};

[[nodiscard]] constexpr Add8Result add8(std::uint8_t a, std::uint8_t b) noexcept {
    const std::uint16_t wide = static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(a) + static_cast<std::uint16_t>(b));
    const auto value = static_cast<std::uint8_t>(wide);
    const bool overflow = ((~(a ^ b) & (a ^ value)) & 0x80U) != 0U;
    return Add8Result{
        .value = value,
        .carry = wide > 0xFFU,
        .overflow = overflow,
        .zero = value == 0U,
        .negative = (value & 0x80U) != 0U,
    };
}

[[nodiscard]] constexpr std::uint32_t read_u32_le(const std::uint8_t* bytes) noexcept {
    return static_cast<std::uint32_t>(bytes[0]) |
           (static_cast<std::uint32_t>(bytes[1]) << 8U) |
           (static_cast<std::uint32_t>(bytes[2]) << 16U) |
           (static_cast<std::uint32_t>(bytes[3]) << 24U);
}

} // namespace apex
