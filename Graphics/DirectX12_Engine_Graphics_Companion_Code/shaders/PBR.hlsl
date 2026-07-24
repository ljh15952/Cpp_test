#ifndef ASTER_PBR_HLSL
#define ASTER_PBR_HLSL

static const float ASTER_PI = 3.14159265358979323846;
static const float ASTER_INV_PI = 0.31830988618379067154;

float Pow5(float x)
{
    float x2 = x * x;
    return x2 * x2 * x;
}

float D_GGX(float NoH, float alpha)
{
    float a2 = alpha * alpha;
    float d = NoH * NoH * (a2 - 1.0) + 1.0;
    return a2 / max(ASTER_PI * d * d, 1e-7);
}

float3 F_Schlick(float VoH, float3 F0)
{
    return F0 + (1.0 - F0) * Pow5(1.0 - VoH);
}

// Returns G / (4 NoL NoV).
float V_SmithGGXCorrelated(float NoV, float NoL, float alpha)
{
    float a2 = alpha * alpha;
    float gv = NoL * sqrt(max(NoV * NoV * (1.0 - a2) + a2, 1e-7));
    float gl = NoV * sqrt(max(NoL * NoL * (1.0 - a2) + a2, 1e-7));
    return 0.5 / max(gv + gl, 1e-7);
}

struct MaterialSample
{
    float3 baseColor;
    float metallic;
    float perceptualRoughness;
    float3 normal;
};

struct BrdfResult
{
    float3 diffuse;
    float3 specular;
};

BrdfResult EvaluateBrdf(MaterialSample material, float3 V, float3 L)
{
    BrdfResult result = (BrdfResult)0;
    float3 N = normalize(material.normal);
    float3 H = normalize(V + L);

    float NoV = saturate(dot(N, V));
    float NoL = saturate(dot(N, L));
    float NoH = saturate(dot(N, H));
    float VoH = saturate(dot(V, H));

    float alpha = max(material.perceptualRoughness
                    * material.perceptualRoughness, 0.0025);
    float3 F0 = lerp(0.04.xxx, material.baseColor, material.metallic);

    float D = D_GGX(NoH, alpha);
    float3 F = F_Schlick(VoH, F0);
    float Vis = V_SmithGGXCorrelated(NoV, NoL, alpha);

    result.specular = D * Vis * F;
    float3 diffuseColor = material.baseColor * (1.0 - material.metallic);
    result.diffuse = diffuseColor * ASTER_INV_PI * (1.0 - F);
    return result;
}

float3 EvaluateDirectionalLight(MaterialSample material,
                                float3 V,
                                float3 L,
                                float3 radiance,
                                float visibility)
{
    float NoL = saturate(dot(material.normal, L));
    BrdfResult brdf = EvaluateBrdf(material, V, L);
    return (brdf.diffuse + brdf.specular) * radiance * NoL * visibility;
}

#endif
