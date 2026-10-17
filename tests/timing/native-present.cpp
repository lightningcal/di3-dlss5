#include <windows.h>
#include <d3d12.h>
#include <dxgi1_5.h>
#include <wrl/client.h>
#include <iostream>
#include <cstdlib>
#include <map>
using Microsoft::WRL::ComPtr;
int main(int argc,char **argv){
 auto previous_foreground=GetForegroundWindow();
 WNDCLASSW wc{};wc.hInstance=GetModuleHandleW(nullptr);wc.lpfnWndProc=DefWindowProcW;wc.lpszClassName=L"DI3NativePresentProbe";RegisterClassW(&wc);
 auto w=CreateWindowW(wc.lpszClassName,L"DI3 timing",WS_OVERLAPPEDWINDOW,0,0,640,360,nullptr,nullptr,wc.hInstance,nullptr);
 ComPtr<ID3D12Device>d;auto hr=D3D12CreateDevice(nullptr,D3D_FEATURE_LEVEL_11_0,IID_PPV_ARGS(&d));if(FAILED(hr))return 1;
 D3D12_COMMAND_QUEUE_DESC qd{};ComPtr<ID3D12CommandQueue>q;if(FAILED(d->CreateCommandQueue(&qd,IID_PPV_ARGS(&q))))return 2;
 ComPtr<IDXGIFactory2>f;if(FAILED(CreateDXGIFactory1(IID_PPV_ARGS(&f))))return 3;
 if(argc>2 && std::atoi(argv[2])==1)SetWindowPos(w,HWND_TOPMOST,20,20,320,200,SWP_NOACTIVATE|SWP_SHOWWINDOW);
 if(argc>2 && std::atoi(argv[2])==2){ShowWindow(w,SW_SHOW);SetForegroundWindow(w);}
 std::cout<<"foreground="<<(GetForegroundWindow()==w)<<std::endl;
 LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);
 const int requested=argc>1?std::atoi(argv[1]):64;
 for(int flags : {requested}){
  DXGI_SWAP_CHAIN_DESC1 sd{};sd.Width=640;sd.Height=360;sd.Format=DXGI_FORMAT_R8G8B8A8_UNORM;sd.SampleDesc.Count=1;sd.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;sd.BufferCount=3;sd.SwapEffect=DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL;sd.Flags=flags;
  ComPtr<IDXGISwapChain1>s;hr=f->CreateSwapChainForHwnd(q.Get(),w,&sd,nullptr,nullptr,&s);if(FAILED(hr)){std::cout<<"create failed "<<std::hex<<hr<<'\n';continue;}
  std::map<unsigned long,int> status;double total=0;int success=0;for(int i=0;i<120;++i){MSG m;while(PeekMessageW(&m,nullptr,0,0,PM_REMOVE)){TranslateMessage(&m);DispatchMessageW(&m);}LARGE_INTEGER a,b;QueryPerformanceCounter(&a);hr=s->Present(0,DXGI_PRESENT_DO_NOT_WAIT);QueryPerformanceCounter(&b);total+=1000.*(b.QuadPart-a.QuadPart)/freq.QuadPart;++status[static_cast<unsigned long>(hr)];if(SUCCEEDED(hr))++success;}
  std::cout<<"flags="<<flags<<" present_cpu_ms="<<total/120<<" success="<<success<<" RTSS="<<(GetModuleHandleW(L"RTSSHooks64.dll")!=nullptr)<<std::endl;
  for(auto [code,count]:status)std::cout<<"HRESULT=0x"<<std::hex<<code<<std::dec<<" count="<<count<<std::endl;
  s.Reset();
 }
 DestroyWindow(w);
 if(previous_foreground && IsWindow(previous_foreground))SetForegroundWindow(previous_foreground);
}
