#include <reshade.hpp>
#include <windows.h>
#include <fstream>
#include <filesystem>
#include <mutex>
static std::filesystem::path path;
static std::mutex lock;
static double freq=1;
static bool allow_tearing=false;
static thread_local long long started=0,rendered=0;
static unsigned long long begins=0,finishes=0,batch=0;
static double sum_total=0,sum_render=0,sum_native=0,max_total=0;
static long long now(){LARGE_INTEGER x;QueryPerformanceCounter(&x);return x.QuadPart;}
static void begin(reshade::api::command_queue*,reshade::api::swapchain*,const reshade::api::rect*,const reshade::api::rect*,uint32_t,const reshade::api::rect*){
 started=now();rendered=0;std::lock_guard<std::mutex> g(lock);++begins;
}
static void after_render(reshade::api::effect_runtime*){rendered=now();}
static void finish(reshade::api::command_queue*,reshade::api::swapchain*){
 auto done=now();if(!started)return;
 double total=(done-started)*1000.0/freq;
 double render=rendered>=started?(rendered-started)*1000.0/freq:0;
 double native=rendered>=started?(done-rendered)*1000.0/freq:0;
 std::lock_guard<std::mutex> g(lock);++finishes;++batch;sum_total+=total;sum_render+=render;sum_native+=native;if(total>max_total)max_total=total;
 if(batch==30){std::ofstream(path,std::ios::app)<<"tick_ms="<<GetTickCount64()<<" thread="<<GetCurrentThreadId()<<" begins="<<begins<<" finishes="<<finishes<<" present_total_cpu_ms="<<sum_total/batch<<" render_overlay_cpu_ms="<<sum_render/batch<<" native_present_cpu_ms="<<sum_native/batch<<" max_total_ms="<<max_total<<'\n';batch=0;sum_total=sum_render=sum_native=max_total=0;}
 started=rendered=0;
}
static bool create_swapchain(reshade::api::device_api api,reshade::api::swapchain_desc &desc,void *hwnd){
 wchar_t cls[128]{};GetClassNameW(static_cast<HWND>(hwnd),cls,128);
 if(api!=reshade::api::device_api::d3d12 || wcscmp(cls,L"dlss5feedhost")!=0)return false;
 std::ofstream(path,std::ios::app)<<"helper swapchain: flags="<<desc.present_flags<<" sync="<<desc.sync_interval<<" experimental_tearing="<<allow_tearing<<'\n';
 if(!allow_tearing)return false;
 desc.sync_interval=0;desc.present_flags|=0x800; // DXGI_SWAP_CHAIN_FLAG_ALLOW_TEARING
 return true;
}
extern "C" __declspec(dllexport) const char *NAME="DI3 helper timing probe";
extern "C" __declspec(dllexport) const char *DESCRIPTION="Timing only; measures presentation callback intervals without changing rendering or driver settings.";
extern "C" __declspec(dllexport) bool AddonInit(HMODULE self,HMODULE){
 if(!reshade::register_addon(self))return false;
 wchar_t file[32768]{};GetModuleFileNameW(self,file,32768);path=std::filesystem::path(file).parent_path()/"di3-helper-timing.log";
 auto config=std::filesystem::path(file).parent_path()/"di3-helper-present.ini";
 allow_tearing=GetPrivateProfileIntW(L"PRESENT",L"AllowTearing",0,config.c_str())==1;
 LARGE_INTEGER f;QueryPerformanceFrequency(&f);freq=double(f.QuadPart);
 std::ofstream(path)<<"Timing probe loaded PID="<<GetCurrentProcessId()<<"; CPU callback intervals, not GPU time.\n";
 reshade::register_event<reshade::addon_event::create_swapchain>(create_swapchain);
 reshade::register_event<reshade::addon_event::present>(begin);
 reshade::register_event<reshade::addon_event::reshade_present>(after_render);
 reshade::register_event<reshade::addon_event::finish_present>(finish);return true;
}
extern "C" __declspec(dllexport) void AddonUninit(HMODULE self,HMODULE){
 reshade::unregister_event<reshade::addon_event::create_swapchain>(create_swapchain);
 reshade::unregister_event<reshade::addon_event::present>(begin);
 reshade::unregister_event<reshade::addon_event::reshade_present>(after_render);
 reshade::unregister_event<reshade::addon_event::finish_present>(finish);
 reshade::unregister_addon(self);
}
