Texture2D<float4> SceneHdr : register(t0);
StructuredBuffer<uint> Histogram : register(t1);
RWTexture2D<float4> Output : register(u0);
SamplerState LinearClamp : register(s0);

cbuffer ToneMapConstants : register(b0)
{
    float Exposure;
    float BloomStrength;
    float2 InvOutputSize;
};

float3 AcesApprox(float3 x)
{
    const float a = 2.51;
    const float b = 0.03;
    const float c = 2.43;
    const float d = 0.59;
    const float e = 0.14;
    return saturate((x * (a * x + b)) / (x * (c * x + d) + e));
}

float3 LinearToSrgb(float3 x)
{
    float3 low = x * 12.92;
    float3 high = 1.055 * pow(max(x, 0.0), 1.0 / 2.4) - 0.055;
    return lerp(high, low, step(x, 0.0031308));
}

[numthreads(8, 8, 1)]
void ToneMapCS(uint3 id : SV_DispatchThreadID)
{
    uint width, height;
    Output.GetDimensions(width, height);
    if (id.x >= width || id.y >= height) return;

    float3 hdr = SceneHdr.Load(int3(id.xy, 0)).rgb * Exposure;
    float3 mapped = AcesApprox(hdr);
    Output[id.xy] = float4(LinearToSrgb(mapped), 1.0);
}
