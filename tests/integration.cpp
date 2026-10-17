#include <reshade.hpp>
#include <d3d11.h>
#include <d3dcompiler.h>
#include <cmath>
#include <cstring>
#include <wrl/client.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <string>

using Microsoft::WRL::ComPtr;
static void require(bool ok, const char *message)
{
    if (!ok) { std::cerr << "FAIL: " << message << " (Windows error " << GetLastError() << ")\n"; ExitProcess(1); }
}

struct Scene {
    ComPtr<ID3D11Texture2D> depth;
    ComPtr<ID3D11DepthStencilView> dsv;
    ComPtr<ID3D11RenderTargetView> rtv;
    ComPtr<ID3D11VertexShader> near_vs, far_vs;
    ComPtr<ID3D11PixelShader> ps;
    ComPtr<ID3D11RasterizerState> raster;
    ComPtr<ID3D11DepthStencilState> state;
    Scene(ID3D11Device *device, IDXGISwapChain *chain) {
        ComPtr<ID3D11Texture2D> buffer;
        require(SUCCEEDED(chain->GetBuffer(0, IID_PPV_ARGS(&buffer))), "get back buffer");
        D3D11_TEXTURE2D_DESC desc{}; buffer->GetDesc(&desc);
        require(SUCCEEDED(device->CreateRenderTargetView(buffer.Get(), nullptr, &rtv)), "create render target");
        desc.Format = DXGI_FORMAT_D32_FLOAT;
        desc.BindFlags = D3D11_BIND_DEPTH_STENCIL;
        require(SUCCEEDED(device->CreateTexture2D(&desc, nullptr, &depth)), "create typed depth target");
        require(SUCCEEDED(device->CreateDepthStencilView(depth.Get(), nullptr, &dsv)), "create depth view");
        const auto compile = [&](const char *text, const char *entry, const char *profile) {
            ComPtr<ID3DBlob> code, error;
            require(SUCCEEDED(D3DCompile(text, strlen(text), nullptr, nullptr, nullptr, entry, profile,
                0, 0, &code, &error)), "compile scene shader");
            return code;
        };
        const char *shader = "float4 nearVS(uint id:SV_VertexID):SV_Position { id%=3; return float4(id==2?3:-1,id==1?3:-1,0.25,1); } "
            "float4 farVS(uint id:SV_VertexID):SV_Position { float4 p=nearVS(id); p.z=0.75; return p; } "
            "float4 pixel():SV_Target { return float4(0.1,0.2,0.3,1); }";
        auto code = compile(shader, "nearVS", "vs_5_0");
        require(SUCCEEDED(device->CreateVertexShader(code->GetBufferPointer(), code->GetBufferSize(), nullptr, &near_vs)), "create near shader");
        code = compile(shader, "farVS", "vs_5_0");
        require(SUCCEEDED(device->CreateVertexShader(code->GetBufferPointer(), code->GetBufferSize(), nullptr, &far_vs)), "create use_deferred shader");
        code = compile(shader, "pixel", "ps_5_0");
        require(SUCCEEDED(device->CreatePixelShader(code->GetBufferPointer(), code->GetBufferSize(), nullptr, &ps)), "create pixel shader");
        D3D11_RASTERIZER_DESC rs{}; rs.FillMode=D3D11_FILL_SOLID; rs.CullMode=D3D11_CULL_NONE; rs.DepthClipEnable=TRUE;
        require(SUCCEEDED(device->CreateRasterizerState(&rs,&raster)), "create raster state");
        D3D11_DEPTH_STENCIL_DESC ds{}; ds.DepthEnable=TRUE; ds.DepthWriteMask=D3D11_DEPTH_WRITE_MASK_ALL; ds.DepthFunc=D3D11_COMPARISON_LESS;
        require(SUCCEEDED(device->CreateDepthStencilState(&ds,&state)), "create depth state");
    }
    void draw(ID3D11DeviceContext *context, bool use_deferred) {
        D3D11_TEXTURE2D_DESC desc{}; depth->GetDesc(&desc);
        D3D11_VIEWPORT viewport{0,0,float(desc.Width),float(desc.Height),0,1};
        auto target=rtv.Get(); context->OMSetRenderTargets(1,&target,dsv.Get());
        context->RSSetViewports(1,&viewport); context->RSSetState(raster.Get());
        context->OMSetDepthStencilState(state.Get(),0);
        context->ClearDepthStencilView(dsv.Get(),D3D11_CLEAR_DEPTH,1,0);
        context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
        context->VSSetShader(use_deferred?far_vs.Get():near_vs.Get(),nullptr,0); context->PSSetShader(ps.Get(),nullptr,0);
        for (int draw=0; draw<9; ++draw) context->Draw(6,0);
        context->ClearDepthStencilView(dsv.Get(),D3D11_CLEAR_DEPTH,1,0);
        context->OMSetRenderTargets(0,nullptr,nullptr);
    }
};

int wmain(int argc, wchar_t **argv) {
    require(argc==4,"usage: integration <custom ReShade DLL> <base dir> <config>");
    auto base=std::filesystem::absolute(argv[2]);
    SetEnvironmentVariableW(L"RESHADE_DISABLE_GRAPHICS_HOOK",L"1");
    SetEnvironmentVariableW(L"RESHADE_BASE_PATH_OVERRIDE",base.c_str());
    HMODULE module=LoadLibraryExW(argv[1],nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    require(module!=nullptr,"load custom ReShade");
    SetEnvironmentVariableW(L"RESHADE_DISABLE_GRAPHICS_HOOK",nullptr);
    SetEnvironmentVariableW(L"RESHADE_BASE_PATH_OVERRIDE",nullptr);
    using Create=bool(__cdecl*)(reshade::api::device_api,void*,void*,void*,const char*,reshade::api::effect_runtime**);
    using Present=void(__cdecl*)(reshade::api::effect_runtime*);
    auto create=reinterpret_cast<Create>(GetProcAddress(module,"ReShadeCreateEffectRuntime"));
    auto present=reinterpret_cast<Present>(GetProcAddress(module,"ReShadeUpdateAndPresentEffectRuntime"));
    auto destroy=reinterpret_cast<Present>(GetProcAddress(module,"ReShadeDestroyEffectRuntime"));
    require(create&&present&&destroy,"manual runtime exports");
    WNDCLASSW wc{};wc.lpfnWndProc=DefWindowProcW;wc.hInstance=GetModuleHandleW(nullptr);wc.lpszClassName=L"DI3DLSS5Integration";
    require(RegisterClassW(&wc)!=0,"register test window");
    auto window=CreateWindowW(wc.lpszClassName,L"DI3 DLSS5 integration",WS_OVERLAPPEDWINDOW,0,0,640,360,nullptr,nullptr,wc.hInstance,nullptr);
    DXGI_SWAP_CHAIN_DESC desc{};desc.BufferDesc.Width=640;desc.BufferDesc.Height=360;desc.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;desc.SampleDesc.Count=1;desc.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;desc.BufferCount=1;desc.OutputWindow=window;desc.Windowed=TRUE;
    ComPtr<IDXGISwapChain> chain;ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;
    require(SUCCEEDED(D3D11CreateDeviceAndSwapChain(nullptr,D3D_DRIVER_TYPE_HARDWARE,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&desc,&chain,&device,nullptr,&context)),"create hardware device");
    reshade::api::effect_runtime* runtime=nullptr;auto cfg=std::filesystem::absolute(argv[3]).u8string();
    require(create(reshade::api::device_api::d3d11,device.Get(),context.Get(),chain.Get(),cfg.c_str(),&runtime)&&runtime,"create manual runtime");
    bool kernel=false,feed=false;
    {Scene scene(device.Get(),chain.Get());
    for(int frame=0;frame<600;++frame){
        scene.draw(context.Get(),false);present(runtime);chain->Present(0,0);
        auto k=runtime->find_technique("lumenite_Kernel.fx","Lumenite_Kernel");
        auto f=runtime->find_technique("DLSS5_Feed.fx","DLSS5_Feed");
        if(k!=0){runtime->set_technique_state(k,true);kernel=true;}
        if(f!=0){runtime->set_technique_state(f,true);feed=true;}
        Sleep(10);
    }context->ClearState();destroy(runtime);}
    DestroyWindow(window);
    require(kernel&&feed,"both motion and feed effects compiled");
    std::cout<<"PASS: manual runtime loaded Feeder; Kernel and Feed techniques compiled and rendered 600 frames. Inspect neural host logs for end-to-end verdict.\n";
    return 0;
}
