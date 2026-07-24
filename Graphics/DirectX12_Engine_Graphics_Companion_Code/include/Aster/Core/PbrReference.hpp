#pragma once

#include "Aster/Core/Math.hpp"
#include <algorithm>
#include <cmath>

namespace aster {

inline constexpr float Pi = 3.14159265358979323846f;

[[nodiscard]] inline Vec3 Hadamard(Vec3 a, Vec3 b) noexcept {
    return {a.x * b.x, a.y * b.y, a.z * b.z};
}

[[nodiscard]] inline Vec3 Lerp(Vec3 a, Vec3 b, float t) noexcept {
    return a * (1.0f - t) + b * t;
}

[[nodiscard]] inline float D_GGX(float noH, float alpha) noexcept {
    const float a2 = alpha * alpha;
    const float d = noH * noH * (a2 - 1.0f) + 1.0f;
    return a2 / std::max(Pi * d * d, 1.0e-7f);
}

[[nodiscard]] inline Vec3 F_Schlick(float voH, Vec3 f0) noexcept {
    const float x = std::clamp(1.0f - voH, 0.0f, 1.0f);
    const float x2 = x * x;
    const float x5 = x2 * x2 * x;
    return f0 + (Vec3{1,1,1} - f0) * x5;
}

[[nodiscard]] inline float V_SmithGGXCorrelated(float noV, float noL,
                                                float alpha) noexcept {
    const float a2 = alpha * alpha;
    const float gv = noL * std::sqrt(std::max(noV * noV * (1.0f - a2) + a2, 1.0e-7f));
    const float gl = noV * std::sqrt(std::max(noL * noL * (1.0f - a2) + a2, 1.0e-7f));
    return 0.5f / std::max(gv + gl, 1.0e-7f);
}

struct MaterialSample {
    Vec3 baseColor{1,1,1};
    float metallic{};
    float roughness{0.5f};
};

[[nodiscard]] inline Vec3 EvaluatePbr(const MaterialSample& material,
                                      Vec3 normal,
                                      Vec3 view,
                                      Vec3 light) noexcept {
    const Vec3 n = SafeNormalize(normal);
    const Vec3 v = SafeNormalize(view);
    const Vec3 l = SafeNormalize(light);
    const Vec3 h = SafeNormalize(v + l);

    const float noV = std::clamp(Dot(n, v), 0.0f, 1.0f);
    const float noL = std::clamp(Dot(n, l), 0.0f, 1.0f);
    const float noH = std::clamp(Dot(n, h), 0.0f, 1.0f);
    const float voH = std::clamp(Dot(v, h), 0.0f, 1.0f);
    if (noV <= 0.0f || noL <= 0.0f) return {};

    const float perceptual = std::clamp(material.roughness, 0.05f, 1.0f);
    const float alpha = perceptual * perceptual;
    const Vec3 f0 = Lerp(Vec3{0.04f, 0.04f, 0.04f},
                         material.baseColor,
                         std::clamp(material.metallic, 0.0f, 1.0f));

    const float d = D_GGX(noH, alpha);
    const Vec3 f = F_Schlick(voH, f0);
    const float vis = V_SmithGGXCorrelated(noV, noL, alpha);
    const Vec3 specular = f * (d * vis);

    const Vec3 diffuseColor = material.baseColor
                            * (1.0f - std::clamp(material.metallic, 0.0f, 1.0f));
    const Vec3 diffuse = Hadamard(diffuseColor * (1.0f / Pi), Vec3{1,1,1} - f);
    return (diffuse + specular) * noL;
}

} // namespace aster
