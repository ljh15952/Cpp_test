#include <windows.h>
#include <wrl/client.h>
#include <d3d12.h>
#include <dxgi1_6.h>
#include <d3dcompiler.h>

#include <array>
#include <cstdint>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <string_view>

using Microsoft::WRL::ComPtr;

namespace {

constexpr UINT FrameCount = 2;

class HrError final : public std::runtime_error {
public:
    HrError(HRESULT hr, std::string_view expression)
        : std::runtime_error(std::string(expression) + " failed with HRESULT "
                           + std::to_string(static_cast<unsigned long>(hr))),
          hr_(hr) {}
    [[nodiscard]] HRESULT Code() const noexcept { return hr_; }
private:
    HRESULT hr_;
};

#define DX_CHECK(expr) do { const HRESULT hr__ = (expr); if (FAILED(hr__)) throw HrError(hr__, #expr); } while(false)

std::filesystem::path ExecutableDirectory()
{
    std::wstring buffer(MAX_PATH, L'\0');
    DWORD length = GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (length == 0 || length >= buffer.size()) {
        return std::filesystem::current_path();
    }
    buffer.resize(length);
    return std::filesystem::path(buffer).parent_path();
}

ComPtr<ID3DBlob> CompileShader(const std::filesystem::path& file,
                               const char* entry,
                               const char* target)
{
    UINT flags = D3DCOMPILE_ENABLE_STRICTNESS;
#if defined(_DEBUG)
    flags |= D3DCOMPILE_DEBUG | D3DCOMPILE_SKIP_OPTIMIZATION;
#else
    flags |= D3DCOMPILE_OPTIMIZATION_LEVEL3;
#endif

    ComPtr<ID3DBlob> bytecode;
    ComPtr<ID3DBlob> errors;
    const HRESULT hr = D3DCompileFromFile(file.c_str(), nullptr,
                                         D3D_COMPILE_STANDARD_FILE_INCLUDE,
                                         entry, target, flags, 0,
                                         &bytecode, &errors);
    if (errors) {
        OutputDebugStringA(static_cast<const char*>(errors->GetBufferPointer()));
    }
    DX_CHECK(hr);
    return bytecode;
}

void EnableDiagnostics()
{
#if defined(_DEBUG)
    ComPtr<ID3D12Debug> debug;
    if (SUCCEEDED(D3D12GetDebugInterface(IID_PPV_ARGS(&debug)))) {
        debug->EnableDebugLayer();
    }

    ComPtr<ID3D12DeviceRemovedExtendedDataSettings1> dred;
    if (SUCCEEDED(D3D12GetDebugInterface(IID_PPV_ARGS(&dred)))) {
        dred->SetAutoBreadcrumbsEnablement(D3D12_DRED_ENABLEMENT_FORCED_ON);
        dred->SetPageFaultEnablement(D3D12_DRED_ENABLEMENT_FORCED_ON);
        dred->SetBreadcrumbContextEnablement(D3D12_DRED_ENABLEMENT_FORCED_ON);
    }
#endif
}

ComPtr<IDXGIAdapter1> ChooseAdapter(IDXGIFactory6* factory)
{
    ComPtr<IDXGIAdapter1> adapter;
    for (UINT index = 0;
         factory->EnumAdapterByGpuPreference(index,
                                             DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE,
                                             IID_PPV_ARGS(&adapter)) != DXGI_ERROR_NOT_FOUND;
         ++index) {
        DXGI_ADAPTER_DESC1 desc{};
        DX_CHECK(adapter->GetDesc1(&desc));
        if ((desc.Flags & DXGI_ADAPTER_FLAG_SOFTWARE) != 0) {
            adapter.Reset();
            continue;
        }
        if (SUCCEEDED(D3D12CreateDevice(adapter.Get(), D3D_FEATURE_LEVEL_12_0,
                                        __uuidof(ID3D12Device), nullptr))) {
            return adapter;
        }
        adapter.Reset();
    }

    ComPtr<IDXGIAdapter> warpBase;
    DX_CHECK(factory->EnumWarpAdapter(IID_PPV_ARGS(&warpBase)));
    DX_CHECK(warpBase.As(&adapter));
    return adapter;
}

class TriangleApp {
public:
    int Run(HINSTANCE instance, int showCommand)
    {
        CreateWindowClass(instance);
        CreateAppWindow(instance, showCommand);
        InitializeD3D();

        MSG message{};
        while (message.message != WM_QUIT) {
            if (PeekMessageW(&message, nullptr, 0, 0, PM_REMOVE)) {
                TranslateMessage(&message);
                DispatchMessageW(&message);
            } else if (!minimized_) {
                Render();
            } else {
                WaitMessage();
            }
        }

        WaitForGpu();
        CloseHandle(fenceEvent_);
        return static_cast<int>(message.wParam);
    }

private:
    static LRESULT CALLBACK WindowProc(HWND window, UINT message,
                                       WPARAM wParam, LPARAM lParam)
    {
        TriangleApp* app = nullptr;
        if (message == WM_NCCREATE) {
            const auto* create = reinterpret_cast<const CREATESTRUCTW*>(lParam);
            app = static_cast<TriangleApp*>(create->lpCreateParams);
            SetWindowLongPtrW(window, GWLP_USERDATA,
                              reinterpret_cast<LONG_PTR>(app));
            app->window_ = window;
        } else {
            app = reinterpret_cast<TriangleApp*>(
                GetWindowLongPtrW(window, GWLP_USERDATA));
        }

        if (app) return app->HandleMessage(message, wParam, lParam);
        return DefWindowProcW(window, message, wParam, lParam);
    }

    LRESULT HandleMessage(UINT message, WPARAM wParam, LPARAM lParam)
    {
        switch (message) {
        case WM_SIZE: {
            const UINT width = LOWORD(lParam);
            const UINT height = HIWORD(lParam);
            minimized_ = wParam == SIZE_MINIMIZED || width == 0 || height == 0;
            if (!minimized_ && device_ && (width != width_ || height != height_)) {
                width_ = width;
                height_ = height;
                ResizeSwapChain();
            }
            return 0;
        }
        case WM_KEYDOWN:
            if (wParam == VK_ESCAPE) DestroyWindow(window_);
            return 0;
        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
        default:
            return DefWindowProcW(window_, message, wParam, lParam);
        }
    }

    void CreateWindowClass(HINSTANCE instance)
    {
        WNDCLASSEXW wc{};
        wc.cbSize = sizeof(wc);
        wc.style = CS_HREDRAW | CS_VREDRAW;
        wc.lpfnWndProc = WindowProc;
        wc.hInstance = instance;
        wc.hCursor = LoadCursorW(nullptr, IDC_ARROW);
        wc.lpszClassName = L"AsterD3D12Triangle";
        if (!RegisterClassExW(&wc)) {
            throw std::runtime_error("RegisterClassExW failed");
        }
    }

    void CreateAppWindow(HINSTANCE instance, int showCommand)
    {
        RECT rect{0, 0, static_cast<LONG>(width_), static_cast<LONG>(height_)};
        AdjustWindowRect(&rect, WS_OVERLAPPEDWINDOW, FALSE);
        HWND window = CreateWindowExW(
            0, L"AsterD3D12Triangle", L"Aster D3D12 Triangle",
            WS_OVERLAPPEDWINDOW,
            CW_USEDEFAULT, CW_USEDEFAULT,
            rect.right - rect.left, rect.bottom - rect.top,
            nullptr, nullptr, instance, this);
        if (!window) throw std::runtime_error("CreateWindowExW failed");
        ShowWindow(window, showCommand);
    }

    void InitializeD3D()
    {
        EnableDiagnostics();

        UINT factoryFlags = 0;
#if defined(_DEBUG)
        factoryFlags |= DXGI_CREATE_FACTORY_DEBUG;
#endif
        DX_CHECK(CreateDXGIFactory2(factoryFlags, IID_PPV_ARGS(&factory_)));
        const ComPtr<IDXGIAdapter1> adapter = ChooseAdapter(factory_.Get());
        DX_CHECK(D3D12CreateDevice(adapter.Get(), D3D_FEATURE_LEVEL_12_0,
                                   IID_PPV_ARGS(&device_)));
        device_->SetName(L"Aster Triangle Device");

        D3D12_COMMAND_QUEUE_DESC queueDesc{};
        queueDesc.Type = D3D12_COMMAND_LIST_TYPE_DIRECT;
        queueDesc.Priority = D3D12_COMMAND_QUEUE_PRIORITY_NORMAL;
        queueDesc.Flags = D3D12_COMMAND_QUEUE_FLAG_NONE;
        DX_CHECK(device_->CreateCommandQueue(&queueDesc,
                                             IID_PPV_ARGS(&commandQueue_)));
        commandQueue_->SetName(L"Graphics Queue");

        CreateSwapChain();
        CreateRenderTargetHeap();
        CreateFrameResources();
        CreatePipeline();

        DX_CHECK(device_->CreateCommandList(0, D3D12_COMMAND_LIST_TYPE_DIRECT,
                                            frames_[frameIndex_].allocator.Get(),
                                            pipeline_.Get(),
                                            IID_PPV_ARGS(&commandList_)));
        DX_CHECK(commandList_->Close());
        commandList_->SetName(L"Main Graphics Command List");

        DX_CHECK(device_->CreateFence(0, D3D12_FENCE_FLAG_NONE,
                                      IID_PPV_ARGS(&fence_)));
        fenceEvent_ = CreateEventW(nullptr, FALSE, FALSE, nullptr);
        if (!fenceEvent_) throw std::runtime_error("CreateEventW failed");
    }

    void CreateSwapChain()
    {
        DXGI_SWAP_CHAIN_DESC1 desc{};
        desc.Width = width_;
        desc.Height = height_;
        desc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
        desc.SampleDesc.Count = 1;
        desc.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
        desc.BufferCount = FrameCount;
        desc.SwapEffect = DXGI_SWAP_EFFECT_FLIP_DISCARD;
        desc.Scaling = DXGI_SCALING_STRETCH;
        desc.AlphaMode = DXGI_ALPHA_MODE_IGNORE;

        ComPtr<IDXGISwapChain1> base;
        DX_CHECK(factory_->CreateSwapChainForHwnd(commandQueue_.Get(), window_,
                                                  &desc, nullptr, nullptr, &base));
        DX_CHECK(factory_->MakeWindowAssociation(window_, DXGI_MWA_NO_ALT_ENTER));
        DX_CHECK(base.As(&swapChain_));
        frameIndex_ = swapChain_->GetCurrentBackBufferIndex();
    }

    void CreateRenderTargetHeap()
    {
        D3D12_DESCRIPTOR_HEAP_DESC desc{};
        desc.Type = D3D12_DESCRIPTOR_HEAP_TYPE_RTV;
        desc.NumDescriptors = FrameCount;
        DX_CHECK(device_->CreateDescriptorHeap(&desc, IID_PPV_ARGS(&rtvHeap_)));
        rtvIncrement_ = device_->GetDescriptorHandleIncrementSize(
            D3D12_DESCRIPTOR_HEAP_TYPE_RTV);
        rtvHeap_->SetName(L"Back Buffer RTV Heap");
    }

    void CreateFrameResources()
    {
        D3D12_CPU_DESCRIPTOR_HANDLE rtv =
            rtvHeap_->GetCPUDescriptorHandleForHeapStart();
        for (UINT i = 0; i < FrameCount; ++i) {
            DX_CHECK(swapChain_->GetBuffer(i, IID_PPV_ARGS(&frames_[i].backBuffer)));
            frames_[i].backBuffer->SetName((L"Back Buffer " + std::to_wstring(i)).c_str());
            device_->CreateRenderTargetView(frames_[i].backBuffer.Get(), nullptr, rtv);
            frames_[i].rtv = rtv;
            rtv.ptr += rtvIncrement_;
            DX_CHECK(device_->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT,
                                                     IID_PPV_ARGS(&frames_[i].allocator)));
            frames_[i].allocator->SetName((L"Allocator " + std::to_wstring(i)).c_str());
        }
    }

    void CreatePipeline()
    {
        D3D12_ROOT_SIGNATURE_DESC rootDesc{};
        rootDesc.Flags = D3D12_ROOT_SIGNATURE_FLAG_ALLOW_INPUT_ASSEMBLER_INPUT_LAYOUT;

        ComPtr<ID3DBlob> serialized;
        ComPtr<ID3DBlob> errors;
        const HRESULT serializeHr = D3D12SerializeRootSignature(
            &rootDesc, D3D_ROOT_SIGNATURE_VERSION_1,
            &serialized, &errors);
        if (errors) OutputDebugStringA(static_cast<const char*>(errors->GetBufferPointer()));
        DX_CHECK(serializeHr);
        DX_CHECK(device_->CreateRootSignature(0, serialized->GetBufferPointer(),
                                              serialized->GetBufferSize(),
                                              IID_PPV_ARGS(&rootSignature_)));

        const auto shaderFile = ExecutableDirectory() / L"shaders" / L"Triangle.hlsl";
        const ComPtr<ID3DBlob> vs = CompileShader(shaderFile, "VSMain", "vs_5_1");
        const ComPtr<ID3DBlob> ps = CompileShader(shaderFile, "PSMain", "ps_5_1");

        D3D12_RASTERIZER_DESC raster{};
        raster.FillMode = D3D12_FILL_MODE_SOLID;
        raster.CullMode = D3D12_CULL_MODE_BACK;
        raster.FrontCounterClockwise = FALSE;
        raster.DepthBias = D3D12_DEFAULT_DEPTH_BIAS;
        raster.DepthBiasClamp = D3D12_DEFAULT_DEPTH_BIAS_CLAMP;
        raster.SlopeScaledDepthBias = D3D12_DEFAULT_SLOPE_SCALED_DEPTH_BIAS;
        raster.DepthClipEnable = TRUE;
        raster.MultisampleEnable = FALSE;
        raster.AntialiasedLineEnable = FALSE;
        raster.ForcedSampleCount = 0;
        raster.ConservativeRaster = D3D12_CONSERVATIVE_RASTERIZATION_MODE_OFF;

        D3D12_BLEND_DESC blend{};
        blend.AlphaToCoverageEnable = FALSE;
        blend.IndependentBlendEnable = FALSE;
        const D3D12_RENDER_TARGET_BLEND_DESC defaultRt{
            FALSE, FALSE,
            D3D12_BLEND_ONE, D3D12_BLEND_ZERO, D3D12_BLEND_OP_ADD,
            D3D12_BLEND_ONE, D3D12_BLEND_ZERO, D3D12_BLEND_OP_ADD,
            D3D12_LOGIC_OP_NOOP, D3D12_COLOR_WRITE_ENABLE_ALL
        };
        for (auto& target : blend.RenderTarget) target = defaultRt;

        D3D12_GRAPHICS_PIPELINE_STATE_DESC pso{};
        pso.pRootSignature = rootSignature_.Get();
        pso.VS = {vs->GetBufferPointer(), vs->GetBufferSize()};
        pso.PS = {ps->GetBufferPointer(), ps->GetBufferSize()};
        pso.BlendState = blend;
        pso.SampleMask = UINT_MAX;
        pso.RasterizerState = raster;
        pso.DepthStencilState.DepthEnable = FALSE;
        pso.DepthStencilState.StencilEnable = FALSE;
        pso.InputLayout = {nullptr, 0};
        pso.PrimitiveTopologyType = D3D12_PRIMITIVE_TOPOLOGY_TYPE_TRIANGLE;
        pso.NumRenderTargets = 1;
        pso.RTVFormats[0] = DXGI_FORMAT_R8G8B8A8_UNORM;
        pso.SampleDesc.Count = 1;
        DX_CHECK(device_->CreateGraphicsPipelineState(&pso,
                                                      IID_PPV_ARGS(&pipeline_)));
        pipeline_->SetName(L"Triangle PSO");
    }

    void ResizeSwapChain()
    {
        WaitForGpu();
        for (auto& frame : frames_) frame.backBuffer.Reset();

        DXGI_SWAP_CHAIN_DESC desc{};
        DX_CHECK(swapChain_->GetDesc(&desc));
        DX_CHECK(swapChain_->ResizeBuffers(FrameCount, width_, height_,
                                           DXGI_FORMAT_R8G8B8A8_UNORM,
                                           desc.Flags));
        frameIndex_ = swapChain_->GetCurrentBackBufferIndex();

        D3D12_CPU_DESCRIPTOR_HANDLE rtv =
            rtvHeap_->GetCPUDescriptorHandleForHeapStart();
        for (UINT i = 0; i < FrameCount; ++i) {
            DX_CHECK(swapChain_->GetBuffer(i, IID_PPV_ARGS(&frames_[i].backBuffer)));
            device_->CreateRenderTargetView(frames_[i].backBuffer.Get(), nullptr, rtv);
            frames_[i].rtv = rtv;
            rtv.ptr += rtvIncrement_;
        }
    }

    void Render()
    {
        Frame& frame = frames_[frameIndex_];
        if (frame.fenceValue != 0 && fence_->GetCompletedValue() < frame.fenceValue) {
            DX_CHECK(fence_->SetEventOnCompletion(frame.fenceValue, fenceEvent_));
            WaitForSingleObject(fenceEvent_, INFINITE);
        }

        DX_CHECK(frame.allocator->Reset());
        DX_CHECK(commandList_->Reset(frame.allocator.Get(), pipeline_.Get()));
        commandList_->SetGraphicsRootSignature(rootSignature_.Get());

        const D3D12_VIEWPORT viewport{
            0.0f, 0.0f,
            static_cast<float>(width_), static_cast<float>(height_),
            0.0f, 1.0f
        };
        const D3D12_RECT scissor{0, 0,
            static_cast<LONG>(width_), static_cast<LONG>(height_)};
        commandList_->RSSetViewports(1, &viewport);
        commandList_->RSSetScissorRects(1, &scissor);

        D3D12_RESOURCE_BARRIER toRender{};
        toRender.Type = D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
        toRender.Transition.pResource = frame.backBuffer.Get();
        toRender.Transition.StateBefore = D3D12_RESOURCE_STATE_PRESENT;
        toRender.Transition.StateAfter = D3D12_RESOURCE_STATE_RENDER_TARGET;
        toRender.Transition.Subresource = D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES;
        commandList_->ResourceBarrier(1, &toRender);

        constexpr float clear[4]{0.025f, 0.035f, 0.06f, 1.0f};
        commandList_->OMSetRenderTargets(1, &frame.rtv, FALSE, nullptr);
        commandList_->ClearRenderTargetView(frame.rtv, clear, 0, nullptr);
        commandList_->IASetPrimitiveTopology(D3D_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
        commandList_->DrawInstanced(3, 1, 0, 0);

        std::swap(toRender.Transition.StateBefore, toRender.Transition.StateAfter);
        commandList_->ResourceBarrier(1, &toRender);
        DX_CHECK(commandList_->Close());

        ID3D12CommandList* lists[]{commandList_.Get()};
        commandQueue_->ExecuteCommandLists(1, lists);
        DX_CHECK(swapChain_->Present(1, 0));

        const UINT64 signal = nextFenceValue_++;
        DX_CHECK(commandQueue_->Signal(fence_.Get(), signal));
        frame.fenceValue = signal;
        frameIndex_ = swapChain_->GetCurrentBackBufferIndex();
    }

    void WaitForGpu()
    {
        if (!commandQueue_ || !fence_) return;
        const UINT64 value = nextFenceValue_++;
        DX_CHECK(commandQueue_->Signal(fence_.Get(), value));
        DX_CHECK(fence_->SetEventOnCompletion(value, fenceEvent_));
        WaitForSingleObject(fenceEvent_, INFINITE);
        for (auto& frame : frames_) frame.fenceValue = 0;
    }

    struct Frame {
        ComPtr<ID3D12Resource> backBuffer;
        ComPtr<ID3D12CommandAllocator> allocator;
        D3D12_CPU_DESCRIPTOR_HANDLE rtv{};
        UINT64 fenceValue{};
    };

    HWND window_{};
    UINT width_{1280};
    UINT height_{720};
    bool minimized_{};

    ComPtr<IDXGIFactory6> factory_;
    ComPtr<ID3D12Device> device_;
    ComPtr<ID3D12CommandQueue> commandQueue_;
    ComPtr<IDXGISwapChain3> swapChain_;
    ComPtr<ID3D12DescriptorHeap> rtvHeap_;
    ComPtr<ID3D12RootSignature> rootSignature_;
    ComPtr<ID3D12PipelineState> pipeline_;
    ComPtr<ID3D12GraphicsCommandList> commandList_;
    ComPtr<ID3D12Fence> fence_;
    std::array<Frame, FrameCount> frames_;
    HANDLE fenceEvent_{};
    UINT rtvIncrement_{};
    UINT frameIndex_{};
    UINT64 nextFenceValue_{1};
};

} // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int showCommand)
{
    try {
        TriangleApp app;
        return app.Run(instance, showCommand);
    } catch (const std::exception& error) {
        MessageBoxA(nullptr, error.what(), "Aster D3D12 Triangle Error",
                    MB_OK | MB_ICONERROR);
        return 1;
    }
}
