struct VsOut
{
    float4 position : SV_Position;
    float3 color : COLOR0;
};

VsOut VSMain(uint vertexId : SV_VertexID)
{
    static const float2 positions[3] = {
        float2( 0.0,  0.65),
        float2( 0.62, -0.55),
        float2(-0.62, -0.55)
    };
    static const float3 colors[3] = {
        float3(0.15, 0.75, 1.0),
        float3(1.0, 0.35, 0.20),
        float3(0.55, 1.0, 0.35)
    };

    VsOut output;
    output.position = float4(positions[vertexId], 0.0, 1.0);
    output.color = colors[vertexId];
    return output;
}

float4 PSMain(VsOut input) : SV_Target0
{
    return float4(input.color, 1.0);
}
