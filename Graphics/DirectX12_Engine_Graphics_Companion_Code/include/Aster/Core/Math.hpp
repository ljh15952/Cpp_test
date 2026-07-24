#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>

namespace aster {

struct Vec2 {
    float x{};
    float y{};
};

struct Vec3 {
    float x{};
    float y{};
    float z{};

    friend constexpr Vec3 operator+(Vec3 a, Vec3 b) noexcept {
        return {a.x + b.x, a.y + b.y, a.z + b.z};
    }
    friend constexpr Vec3 operator-(Vec3 a, Vec3 b) noexcept {
        return {a.x - b.x, a.y - b.y, a.z - b.z};
    }
    friend constexpr Vec3 operator*(Vec3 v, float s) noexcept {
        return {v.x * s, v.y * s, v.z * s};
    }
    friend constexpr Vec3 operator*(float s, Vec3 v) noexcept { return v * s; }
    friend constexpr Vec3 operator/(Vec3 v, float s) noexcept {
        return {v.x / s, v.y / s, v.z / s};
    }
};

struct Vec4 {
    float x{};
    float y{};
    float z{};
    float w{};
};

[[nodiscard]] constexpr float Dot(Vec3 a, Vec3 b) noexcept {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

[[nodiscard]] constexpr Vec3 Cross(Vec3 a, Vec3 b) noexcept {
    return {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    };
}

[[nodiscard]] inline float Length(Vec3 v) noexcept {
    return std::sqrt(Dot(v, v));
}

[[nodiscard]] inline Vec3 SafeNormalize(Vec3 v,
                                        Vec3 fallback = {0.0f, 0.0f, 1.0f}) noexcept {
    const float lenSq = Dot(v, v);
    if (!(lenSq > 1.0e-12f) || !std::isfinite(lenSq)) {
        return fallback;
    }
    return v * (1.0f / std::sqrt(lenSq));
}

[[nodiscard]] constexpr Vec3 Reflect(Vec3 incident, Vec3 normal) noexcept {
    return incident - normal * (2.0f * Dot(normal, incident));
}

struct Mat4 {
    // Row-major storage, column-vector mathematical convention.
    std::array<float, 16> m{};

    [[nodiscard]] constexpr float& operator()(std::size_t row, std::size_t col) noexcept {
        return m[row * 4 + col];
    }
    [[nodiscard]] constexpr float operator()(std::size_t row, std::size_t col) const noexcept {
        return m[row * 4 + col];
    }

    [[nodiscard]] static constexpr Mat4 Identity() noexcept {
        Mat4 result{};
        result(0, 0) = 1.0f;
        result(1, 1) = 1.0f;
        result(2, 2) = 1.0f;
        result(3, 3) = 1.0f;
        return result;
    }
};

[[nodiscard]] constexpr Mat4 operator*(const Mat4& a, const Mat4& b) noexcept {
    Mat4 out{};
    for (std::size_t r = 0; r < 4; ++r) {
        for (std::size_t c = 0; c < 4; ++c) {
            float sum = 0.0f;
            for (std::size_t k = 0; k < 4; ++k) {
                sum += a(r, k) * b(k, c);
            }
            out(r, c) = sum;
        }
    }
    return out;
}

[[nodiscard]] constexpr Vec4 operator*(const Mat4& a, Vec4 v) noexcept {
    return {
        a(0, 0) * v.x + a(0, 1) * v.y + a(0, 2) * v.z + a(0, 3) * v.w,
        a(1, 0) * v.x + a(1, 1) * v.y + a(1, 2) * v.z + a(1, 3) * v.w,
        a(2, 0) * v.x + a(2, 1) * v.y + a(2, 2) * v.z + a(2, 3) * v.w,
        a(3, 0) * v.x + a(3, 1) * v.y + a(3, 2) * v.z + a(3, 3) * v.w
    };
}

[[nodiscard]] constexpr Mat4 Translation(Vec3 t) noexcept {
    Mat4 out = Mat4::Identity();
    out(0, 3) = t.x;
    out(1, 3) = t.y;
    out(2, 3) = t.z;
    return out;
}

[[nodiscard]] constexpr Mat4 Scale(Vec3 s) noexcept {
    Mat4 out{};
    out(0, 0) = s.x;
    out(1, 1) = s.y;
    out(2, 2) = s.z;
    out(3, 3) = 1.0f;
    return out;
}

[[nodiscard]] inline Mat4 LookAtRH(Vec3 eye, Vec3 target, Vec3 up) {
    const Vec3 z = SafeNormalize(eye - target);
    const Vec3 x = SafeNormalize(Cross(up, z));
    const Vec3 y = Cross(z, x);

    Mat4 out = Mat4::Identity();
    out(0, 0) = x.x; out(0, 1) = x.y; out(0, 2) = x.z; out(0, 3) = -Dot(x, eye);
    out(1, 0) = y.x; out(1, 1) = y.y; out(1, 2) = y.z; out(1, 3) = -Dot(y, eye);
    out(2, 0) = z.x; out(2, 1) = z.y; out(2, 2) = z.z; out(2, 3) = -Dot(z, eye);
    return out;
}

// Right-handed, D3D NDC z in [0,1], reversed-Z finite far.
[[nodiscard]] inline Mat4 PerspectiveReversedZRH(float verticalFovRadians,
                                                 float aspect,
                                                 float nearZ,
                                                 float farZ) {
    if (!(verticalFovRadians > 0.0f && verticalFovRadians < 3.14159265f)) {
        throw std::invalid_argument("vertical FOV must be in (0, pi)");
    }
    if (!(aspect > 0.0f && nearZ > 0.0f && farZ > nearZ)) {
        throw std::invalid_argument("invalid projection parameters");
    }

    const float y = 1.0f / std::tan(verticalFovRadians * 0.5f);
    const float x = y / aspect;

    Mat4 out{};
    out(0, 0) = x;
    out(1, 1) = y;
    out(2, 2) = nearZ / (farZ - nearZ);
    out(2, 3) = (farZ * nearZ) / (farZ - nearZ);
    out(3, 2) = -1.0f;
    return out;
}

[[nodiscard]] inline bool NearlyEqual(float a, float b,
                                      float epsilon = 1.0e-5f) noexcept {
    return std::abs(a - b) <= epsilon;
}

} // namespace aster
