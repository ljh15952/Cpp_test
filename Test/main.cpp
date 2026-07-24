#pragma once

#include <algorithm>
#include <cmath>
#include <optional>

namespace cppbook {

struct Vec3 final {
    float x{};
    float y{};
    float z{};

    friend Vec3 operator+(Vec3 a, Vec3 b) noexcept {
        return {a.x + b.x, a.y + b.y, a.z + b.z};
    }

    friend Vec3 operator-(Vec3 a, Vec3 b) noexcept {
        return {a.x - b.x, a.y - b.y, a.z - b.z};
    }

    friend Vec3 operator*(Vec3 v, float scalar) noexcept {
        return {v.x * scalar, v.y * scalar, v.z * scalar};
    }
};

inline float dot(Vec3 a, Vec3 b) noexcept {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

inline Vec3 cross(Vec3 a, Vec3 b) noexcept {
    return {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    };
}

inline float length_squared(Vec3 v) noexcept { return dot(v, v); }

inline std::optional<Vec3> normalize(Vec3 v,
                                     float epsilon_squared = 1.0e-12F) {
    const float squared = length_squared(v);
    if (squared <= epsilon_squared) {
        return std::nullopt;
    }
    const float inverse = 1.0F / std::sqrt(squared);
    return v * inverse;
}

inline bool nearly_equal(float a, float b,
                         float absolute_epsilon = 1.0e-5F,
                         float relative_epsilon = 1.0e-5F) noexcept {
    const float difference = std::abs(a - b);
    if (difference <= absolute_epsilon) {
        return true;
    }
    return difference <= relative_epsilon * std::max(std::abs(a), std::abs(b));
}

} // namespace cppbook
