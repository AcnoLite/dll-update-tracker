# DLL Update Tracker

> Last updated: **10/11/2026**
> **44** SDKs/technologies tracked | **42** stable | **4** pre-release | **42** auto-tracked | **52** DLL file versions
>
> Automatic tracking of graphics, audio and tools DLLs (upscaling, frame gen, low latency, ray tracing, physics, debug, audio middleware).
> SDK versions are fetched via GitHub APIs, NuGet and web scraping.
> DLL file versions are read from the DLLs themselves (repository files, release archives, NuGet packages).

---

## 🟦 Microsoft

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **Direct3D 12 Agility SDK** | `D3D12Core.dll` 1.620.2.0<br>`d3d12SDKLayers.dll` 1.620.2.0<br>`D3D12StateObjectCompiler.dll` 1.620.2.0 | [microsoft/DirectX-Headers](https://github.com/microsoft/DirectX-Headers) / [NuGet](https://www.nuget.org/packages/Microsoft.Direct3D.D3D12/) | `1.620.2` (2026-11-09) | `1.722.1-preview` (2026-11-09) | 2026-11-10 |
| **DirectStorage** | `dstoragecore.dll` 1.3.2506.2501<br>`dstorage.dll` 1.3.2506.2501 | [NuGet](https://www.nuget.org/packages/Microsoft.Direct3D.DirectStorage/) | `1.3.0` (2025-06-27) | `1.4.0-preview2-2606.904` (2026-06-16) | 2026-11-10 |
| **DirectX Shader Compiler (DXC)** | `dxcompiler.dll` 1.9.2609.5<br>`dxil.dll` 1.9.2609.5 | [microsoft/DirectXShaderCompiler](https://github.com/microsoft/DirectXShaderCompiler) / [NuGet](https://www.nuget.org/packages/Microsoft.Direct3D.DXC/) | `1.9.2609` (2026-09-29) | `1.10.2605.37` (2026-08-12) | 2026-11-10 |
| **DirectX Tool Kit for DirectX 11** | ⚠️ None | [NuGet](https://www.nuget.org/packages/directxtk_desktop_win10/) | `2026.5.8.1` (2026-05-10) | - | 2026-11-10 |
| **PIX / WinPixEventRuntime** | `WinPixEventRuntime.dll` 1.0.2403.8001<br>`WinPixGpuCapturer.dll`<br>`WinPixTimingCapturer.dll` | [NuGet](https://www.nuget.org/packages/WinPixEventRuntime/) / [microsoft/PixEvents](https://github.com/microsoft/PixEvents) | `1.0.240308001` (2024-03-27) | - | 2026-11-10 |
| **VC++ Redistributable** | `vcruntime140.dll`<br>`vcruntime140_1.dll`<br>`vcruntime140_threads.dll`<br>`msvcp140.dll`<br>`msvcp140_1.dll`<br>`msvcp140_2.dll`<br>`msvcp140_atomic_wait.dll`<br>`msvcp140_codecvt_ids.dll`<br>`concrt140.dll`<br>`vccorlib140.dll`<br>`vcomp140.dll`<br>`vcamp140.dll` | [Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe) | `14.44.35211.0` (2026-10-07) | - | 2026-11-10 |
| **DirectML** | `DirectML.dll` 1.15.4.0 | [NuGet](https://www.nuget.org/packages/Microsoft.AI.DirectML/) | `1.15.4` (2024-10-28) | - | 2026-11-10 |
| **Direct3D WARP** | `d3d10warp.dll` 1.0.22.0 | [NuGet](https://www.nuget.org/packages/Microsoft.Direct3D.WARP/) | `1.0.22` (2026-10-27) | `1.65535.22-preview` (2026-10-27) | 2026-11-10 |
| **GameInput** | `GameInputRedist.dll` 4.0.306.0<br>`GameInput.dll` | [NuGet](https://www.nuget.org/packages/Microsoft.GameInput/) | `4.0.306` (2026-10-28) | - | 2026-11-10 |

---

## 🟥 AMD

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **AGS SDK** | `amd_ags_x64.dll` 6.3.1.0<br>`amd_ags_x86.dll` 6.3.1.0 | [GPUOpen-LibrariesAndSDKs/AGS_SDK](https://github.com/GPUOpen-LibrariesAndSDKs/AGS_SDK) | `6.3.1` (2026-05-27) | - | 2026-11-10 |
| **D3D12 Memory Allocator** | ⚠️ None | [GPUOpen-LibrariesAndSDKs/D3D12MemoryAllocator](https://github.com/GPUOpen-LibrariesAndSDKs/D3D12MemoryAllocator) | `3.3.0` (2026-11-09) | - | 2026-11-10 |
| **AMD FidelityFX (FSR) SDK** | `amd_fidelityfx_loader_dx12.dll` 2.3.0.4555<br>`amd_fidelityfx_upscaler_dx12.dll` 4.1.2.4555<br>`amd_fidelityfx_framegeneration_dx12.dll` 4.0.2.4555<br>`amd_fidelityfx_denoiser_dx12.dll` 1.2.1.4555<br>`amd_fidelityfx_radiancecache_dx12.dll` 0.9.0.4555<br>`amd_fidelityfx_loader_vk.dll` 1.0.2.4555<br>`amd_fidelityfx_upscaler_vk.dll` 4.1.2.4555<br>`amd_fidelityfx_framegeneration_vk.dll` 4.0.2.4555 | [GPUOpen-LibrariesAndSDKs/FidelityFX-SDK](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK) | `2.4.0` (2026-10-28) | - | 2026-11-10 |
| **Anti-Lag 2** | `amdxc64.dll`<br>`amdxx64.dll` | [GPUOpen-LibrariesAndSDKs/AntiLag2-SDK](https://github.com/GPUOpen-LibrariesAndSDKs/AntiLag2-SDK) | `2.0.0a` (2024-10-01) | - | 2026-11-10 |
| **Vulkan Memory Allocator (VMA)** | ⚠️ None | [GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator](https://github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator) | `3.5.0` (2026-10-26) | - | 2026-11-10 |

---

## 🟢 NVIDIA

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **Streamline** | `sl.interposer.dll` 2.14.16.0<br>`sl.common.dll` 2.14.16.0<br>`sl.dlss.dll` 2.14.16.0<br>`sl.dlss_g.dll` 2.14.16.0<br>`sl.dlss_d.dll` 2.14.16.0<br>`sl.reflex.dll` 2.14.16.0<br>`sl.pcl.dll` 2.14.16.0<br>`sl.nis.dll` 2.14.16.0<br>`sl.deepdvc.dll` 2.14.16.0<br>`sl.directsr.dll` 2.14.16.0<br>`sl.nvperf.dll` 2.14.16.0 | [NVIDIA-RTX/Streamline](https://github.com/NVIDIA-RTX/Streamline) | `2.14.16` (2026-10-16) | - | 2026-11-10 |
| **DLSS (Deep Learning Super Sampling)** | `nvngx_dlss.dll` 310.9.16.0<br>`nvngx_dlssg.dll` 310.9.16.0<br>`nvngx_dlssd.dll` 310.9.16.0<br>`nvngx_deepdvc.dll` 310.9.16.0<br>`nvngx.dll`<br>`_nvngx.dll` | [NVIDIA/DLSS](https://github.com/NVIDIA/DLSS) | `310.9.16` (2026-10-16) | - | 2026-11-10 |
| **NVIDIA Reflex** | `sl.reflex.dll` 2.14.16.0<br>`sl.pcl.dll` 2.14.16.0<br>`NvLowLatencyVk.dll` | [NVIDIA-RTX/Streamline](https://github.com/NVIDIA-RTX/Streamline) | `2.14.16` (2026-10-16) | - | 2026-11-10 |
| **NVAPI** | `nvapi64.dll`<br>`nvapi.dll` | [NVIDIA/nvapi](https://github.com/NVIDIA/nvapi) | `R620` (2026-11-10) | - | 2026-11-10 |
| **NVIDIA Image Scaling (NIS)** | ⚠️ None | [NVIDIAGameWorks/NVIDIAImageScaling](https://github.com/NVIDIAGameWorks/NVIDIAImageScaling) | `1.0.3` (2022-08-22) | - | 2026-11-10 |
| **RTXGI (Ray Tracing Global Illumination)** | ⚠️ None | [NVIDIA-RTX/RTXGI](https://github.com/NVIDIA-RTX/RTXGI) | `2.8.0` (2026-10-13) | - | 2026-11-10 |
| **RTXDI (Ray Traced Direct Lighting)** | ⚠️ None | [NVIDIA-RTX/RTXDI](https://github.com/NVIDIA-RTX/RTXDI) | `3.1.0` (2026-09-03) | - | 2026-11-10 |
| **PhysX** | `PhysX_64.dll`<br>`PhysXCommon_64.dll`<br>`PhysXFoundation_64.dll`<br>`PhysXCooking_64.dll`<br>`PhysXGpu_64.dll`<br>`PhysXDevice64.dll` | [NVIDIA-Omniverse/PhysX](https://github.com/NVIDIA-Omniverse/PhysX) | `110.3-omni-and-physx-5.9.1` (2026-10-27) | - | 2026-11-10 |
| **NRD (Real-time Denoisers)** | `NRD.dll` | [NVIDIA-RTX/NRD](https://github.com/NVIDIA-RTX/NRD) | `4.18.0` (2026-10-30) | - | 2026-11-10 |
| **NRi (NRD Interface)** | `NRI.dll` | [NVIDIA-RTX/NRi](https://github.com/NVIDIA-RTX/NRi) | `191` (2026-10-30) | - | 2026-11-10 |
| **NVRHI** | ⚠️ None | [NVIDIA-RTX/NVRHI](https://github.com/NVIDIA-RTX/NVRHI) | `bf0bbd9` (latest commit, 2026-10-28) | - | 2026-11-10 |
| **PhysX Legacy (v4)** | `PhysX_64.dll`<br>`PhysXCommon_64.dll`<br>`PhysXFoundation_64.dll`<br>`PhysXCooking_64.dll`<br>`PhysXGpu_64.dll` 4.1.2.0<br>`PhysXDevice64.dll` 18.12.7.1 | [NVIDIAGameWorks/PhysX](https://github.com/NVIDIAGameWorks/PhysX) | `4.0.0` (2018-12-20) | - | 2026-11-10 |

---

## 🟪 Intel

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **Intel XeSS** | `libxess.dll` 2.0.2.68<br>`libxess_dx11.dll` 2.0.2.68<br>`libxell.dll` 1.3.2.10<br>`libxess_fg.dll` 1.3.1.78 | [intel/xess](https://github.com/intel/xess) | `3.0.2` (2026-07-24) | - | 2026-11-10 |

---

## 🟨 Vulkan

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **Vulkan SDK / Loader** | `vulkan-1.dll` | [LunarG](https://vulkan.lunarg.com/sdk/latest.json) | `1.4.363.1` | - | 2026-11-10 |
| **SwiftShader** | ⚠️ None | [google/swiftshader](https://github.com/google/swiftshader) | `cddb5c9` (latest commit, 2026-10-14) | - | 2026-11-10 |
| **OpenXR** | `openxr_loader.dll` 1.1.65.0 | [KhronosGroup/OpenXR-SDK](https://github.com/KhronosGroup/OpenXR-SDK) | `1.1.65` (2026-10-16) | - | 2026-11-10 |
| **DXVK** | `d3d8.dll`<br>`d3d9.dll`<br>`d3d10core.dll`<br>`d3d11.dll`<br>`dxgi.dll` | [doitsujin/dxvk](https://github.com/doitsujin/dxvk) | `3.1.1` (2026-09-15) | - | 2026-11-10 |
| **vkd3d-proton** | `d3d12.dll`<br>`d3d12core.dll` | [HansKristian-Work/vkd3d-proton](https://github.com/HansKristian-Work/vkd3d-proton) | `3.1` (2026-10-28) | - | 2026-11-10 |

---

## 🔊 Audio

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **OpenAL Soft** | `soft_oal.dll` 1.25.1.0<br>`OpenAL32.dll` 1.25.1.0 | [kcat/openal-soft](https://github.com/kcat/openal-soft) | `1.25.2` (2026-05-12) | - | 2026-11-10 |
| **Steam Audio** | `phonon.dll` 4.8.1.0<br>`phonon_fmod.dll` 4.8.1.0<br>`audioplugin_phonon.dll`<br>`GPUUtilities.dll`<br>`TrueAudioNext.dll` | [ValveSoftware/steam-audio](https://github.com/ValveSoftware/steam-audio) | `4.8.1` (2026-02-11) | - | 2026-11-10 |
| **XAudio2 Redistributable** | `XAUDIO2_9REDIST.dll` 1.0.2504.10003 | [NuGet](https://www.nuget.org/packages/Microsoft.XAudio2.Redist/) | `1.2.13` (2025-04-10) | - | 2026-11-10 |
| **Miniaudio** | ⚠️ None | [mackron/miniaudio](https://github.com/mackron/miniaudio) | `0.11.26` (2026-10-31) | - | 2026-11-10 |
| **SoLoud** | ⚠️ None | [jarikomppa/soloud](https://github.com/jarikomppa/soloud) | `RELEASE_20200207` (2020-02-07) | - | 2026-11-10 |
| **FMOD Studio 🔒** | `fmod.dll`<br>`fmodstudio.dll` | [FMOD](https://fmod.com/download/) | - | - | - |
| **Wwise 🔒** | `AkSoundEngine.dll`<br>`AkMotionSink.dll` | [Audiokinetic](https://www.audiokinetic.com/download/) | - | - | - |

---

## 📦 Other

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **Bullet Physics** | ⚠️ None | [bulletphysics/bullet3](https://github.com/bulletphysics/bullet3) | `3.25` (2022-04-24) | - | 2026-11-10 |
| **RenderDoc** | `renderdoc.dll` 1.47.0.0<br>`renderdocshim64.dll` | [baldurk/renderdoc](https://github.com/baldurk/renderdoc) | `1.47` (2026-10-31) | - | 2026-11-10 |
| **OpenVR** | `openvr_api.dll` | [ValveSoftware/openvr](https://github.com/ValveSoftware/openvr) | `2.15.6` (2026-03-27) | - | 2026-11-10 |
| **SDL3** | `SDL3.dll` 3.4.20.0 | [libsdl-org/SDL](https://github.com/libsdl-org/SDL) | `3.4.20` (2026-11-03) | - | 2026-11-10 |
| **OptiScaler** | `OptiScaler.dll`<br>`fakenvapi.dll`<br>`dlssg_to_fsr3_amd_is_better.dll` | [optiscaler/OptiScaler](https://github.com/optiscaler/OptiScaler) | `0.9.4` (2026-07-18) | - | 2026-11-10 |

---


## Update

```bash
# All at once
python scripts/fetch_versions.py && python scripts/generate_readme.py

# Or separately
python scripts/fetch_versions.py
python scripts/generate_readme.py
```

GitHub Actions: cron every Monday 8am UTC + manual trigger.
