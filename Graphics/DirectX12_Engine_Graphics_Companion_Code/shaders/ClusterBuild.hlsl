struct PointLight
{
    float3 positionView;
    float radius;
    float3 radiance;
    uint flags;
};

StructuredBuffer<PointLight> Lights : register(t0);
RWStructuredBuffer<uint> ClusterCounts : register(u0);
RWStructuredBuffer<uint> DebugCounters : register(u1);

cbuffer ClusterConstants : register(b0)
{
    uint LightCount;
    uint3 ClusterCount;
    float NearZ;
    float FarZ;
    float2 InvProjectionScale;
    uint MaxLightsPerCluster;
};

uint FlattenCluster(uint3 c)
{
    return c.x + ClusterCount.x * (c.y + ClusterCount.y * c.z);
}

// Educational count pass skeleton. Production code should compute exact
// cluster AABBs/frusta and use count/scan/fill with capacity validation.
[numthreads(64, 1, 1)]
void CountLightsCS(uint3 groupId : SV_GroupID,
                   uint local : SV_GroupIndex)
{
    uint cluster = groupId.x;
    uint clusterTotal = ClusterCount.x * ClusterCount.y * ClusterCount.z;
    if (cluster >= clusterTotal) return;

    groupshared uint count;
    if (local == 0) count = 0;
    GroupMemoryBarrierWithGroupSync();

    for (uint lightIndex = local; lightIndex < LightCount; lightIndex += 64) {
        // Replace this placeholder with SphereIntersectsCluster.
        bool intersects = Lights[lightIndex].radius > 0.0;
        if (intersects) InterlockedAdd(count, 1);
    }
    GroupMemoryBarrierWithGroupSync();

    if (local == 0) {
        ClusterCounts[cluster] = min(count, MaxLightsPerCluster);
        if (count > MaxLightsPerCluster) {
            InterlockedAdd(DebugCounters[0], 1);
        }
    }
}
