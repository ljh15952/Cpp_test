Texture2D<float4> CurrentColor : register(t0);
Texture2D<float4> HistoryColor : register(t1);
Texture2D<float2> Velocity : register(t2);
Texture2D<float> CurrentDepth : register(t3);
Texture2D<float> PreviousDepth : register(t4);
Texture2D<float> ReactiveMask : register(t5);
RWTexture2D<float4> Output : register(u0);
SamplerState LinearClamp : register(s0);
SamplerState PointClamp : register(s1);

cbuffer TaaConstants : register(b0)
{
    float2 InvResolution;
    float BaseHistoryWeight;
    float DepthThreshold;
};

void NeighborhoodMoments(uint2 pixel, out float3 mean, out float3 sigma)
{
    float3 sum = 0.0;
    float3 sum2 = 0.0;
    uint width, height;
    CurrentColor.GetDimensions(width, height);

    [unroll]
    for (int y = -1; y <= 1; ++y) {
        [unroll]
        for (int x = -1; x <= 1; ++x) {
            uint2 p = uint2(clamp(int(pixel.x) + x, 0, int(width) - 1),
                            clamp(int(pixel.y) + y, 0, int(height) - 1));
            float3 c = CurrentColor.Load(int3(p, 0)).rgb;
            sum += c;
            sum2 += c * c;
        }
    }
    mean = sum / 9.0;
    sigma = sqrt(max(sum2 / 9.0 - mean * mean, 0.0));
}

[numthreads(8, 8, 1)]
void TaaCS(uint3 id : SV_DispatchThreadID)
{
    uint width, height;
    Output.GetDimensions(width, height);
    if (id.x >= width || id.y >= height) return;

    float2 uv = (float2(id.xy) + 0.5) * InvResolution;
    float2 velocity = Velocity.Load(int3(id.xy, 0));
    float2 previousUv = uv - velocity;

    float3 current = CurrentColor.Load(int3(id.xy, 0)).rgb;
    bool outside = any(previousUv < 0.0) || any(previousUv > 1.0);
    float previousDepth = PreviousDepth.SampleLevel(PointClamp, previousUv, 0);
    float currentDepth = CurrentDepth.Load(int3(id.xy, 0));
    bool depthInvalid = abs(previousDepth - currentDepth) > DepthThreshold;

    float3 history = HistoryColor.SampleLevel(LinearClamp, previousUv, 0).rgb;
    float3 mean, sigma;
    NeighborhoodMoments(id.xy, mean, sigma);
    history = clamp(history, mean - 1.25 * sigma, mean + 1.25 * sigma);

    float reactive = ReactiveMask.Load(int3(id.xy, 0));
    float weight = BaseHistoryWeight * (1.0 - reactive);
    if (outside || depthInvalid) weight = 0.0;

    Output[id.xy] = float4(lerp(current, history, weight), 1.0);
}
