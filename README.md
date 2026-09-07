# DLL Update Tracker

> Last updated: **07/09/2026**
> **36** SDKs/technologies tracked | **30** stable | **6** pre-release | **30** auto-tracked
>
> Automatic tracking of graphics, audio and tools DLLs (upscaling, frame gen, low latency, ray tracing, physics, debug, audio middleware).
> Versions are fetched via GitHub APIs, NuGet and web scraping.

---

## 🟦 Microsoft

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **Direct3D 12 Agility SDK** | `D3D12Core.dll`, `d3d12SDKLayers.dll`, `D3D12StateObjectCompiler.dll` | [microsoft/DirectX-Headers](https://github.com/microsoft/DirectX-Headers) / [NuGet](https://www.nuget.org/packages/Microsoft.Direct3D.D3D12/) | `1.619.5` (2026-07-31) | `1.721.2-preview` (2026-07-08) | 2026-09-07 |
| **DirectStorage** | `dstoragecore.dll`, `dstorage.dll` | [NuGet](https://www.nuget.org/packages/Microsoft.Direct3D.DirectStorage/) | `1.3.0` (2025-06-27) | `1.4.0-preview2-2606.904` (2026-06-16) | 2026-09-07 |
| **DirectX Shader Compiler (DXC)** | `dxcompiler.dll`, `dxil.dll` | [microsoft/DirectXShaderCompiler](https://github.com/microsoft/DirectXShaderCompiler) / [NuGet](https://www.nuget.org/packages/Microsoft.Direct3D.DXC/) | `1.9.2607` (2026-07-29) | `1.10.2605.37` (2026-08-12) | 2026-09-07 |
| **DirectX Tool Kit for DirectX 11** | ⚠️ None | [NuGet](https://www.nuget.org/packages/directxtk_desktop_win10/) | `2026.5.8.1` (2026-05-10) | - | 2026-09-07 |
| **PIX / WinPixEventRuntime** | `WinPixEventRuntime.dll`, `WinPixTimingCapturer.dll` | [NuGet](https://www.nuget.org/packages/WinPixEventRuntime/) / [microsoft/PixEvents](https://github.com/microsoft/PixEvents) | `1.0.240308001` (2024-03-27) | - | 2026-09-07 |
| **VC++ Redistributable** | `vcruntime140.dll`, `msvcp140.dll`, `vcruntime140_1.dll` | - | `14.0.24212` | - | 2026-09-07 |

---

## 🟥 AMD

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **AGS SDK** | `amd_ags_x64.dll`, `amd_ags_x86.dll` | [GPUOpen-LibrariesAndSDKs/AGS_SDK](https://github.com/GPUOpen-LibrariesAndSDKs/AGS_SDK) | `6.3.1` (2026-05-27) | - | 2026-09-07 |
| **D3D12 Memory Allocator** | ⚠️ None | [GPUOpen-LibrariesAndSDKs/D3D12MemoryAllocator](https://github.com/GPUOpen-LibrariesAndSDKs/D3D12MemoryAllocator) | `3.2.0` (2026-06-04) | - | 2026-09-07 |
| **AMD FidelityFX (FSR) SDK** | `amd_fidelityfx_dx12.dll` | [GPUOpen-LibrariesAndSDKs/FidelityFX-SDK](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK) | `2.3.0` (2026-06-24) | - | 2026-09-07 |
| **Anti-Lag 2** | `amdxx64.dll` | [GPUOpen-LibrariesAndSDKs/AntiLag2-SDK](https://github.com/GPUOpen-LibrariesAndSDKs/AntiLag2-SDK) | `2.0.0a` (2024-10-01) | - | 2026-09-07 |
| **Vulkan Memory Allocator (VMA)** | ⚠️ None | [GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator](https://github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator) | `3.4.0` (2026-06-04) | - | 2026-09-07 |

---

## 🟢 NVIDIA

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **Streamline** | ⚠️ None | [NVIDIA-RTX/Streamline](https://github.com/NVIDIA-RTX/Streamline) | `2.12.0` (2026-06-23) | - | 2026-09-07 |
| **DLSS (Deep Learning Super Sampling)** | `nvngx_dlss.dll`, `nvngx_dlssg.dll`, `nvngx_dlssd.dll`, `nvngx.dll`, `_nvngx.dll`, `nvngx_deepdvc.dll`, `nvngx_truehdr.dll` | [NVIDIA/DLSS](https://github.com/NVIDIA/DLSS) | `310.7.0` (2026-06-23) | - | 2026-09-07 |
| **NVIDIA Reflex** | ⚠️ None | [NVIDIA-RTX/Streamline](https://github.com/NVIDIA-RTX/Streamline) | `2.12.0` (2026-06-23) | - | 2026-09-07 |
| **NVAPI 🔒** | `nvapi64.dll`, `nvapi.dll` | [NVIDIA/nvapi](https://github.com/NVIDIA/nvapi) | - | - | - |
| **NVIDIA Image Scaling (NIS)** | ⚠️ None | [NVIDIAGameWorks/NVIDIAImageScaling](https://github.com/NVIDIAGameWorks/NVIDIAImageScaling) | `1.0.3` (2022-08-22) | - | 2026-09-07 |
| **RTXGI (Ray Tracing Global Illumination)** | ⚠️ None | [NVIDIA-RTX/RTXGI](https://github.com/NVIDIA-RTX/RTXGI) | `2.7.0` (2026-03-01) | - | 2026-09-07 |
| **RTXDI (Ray Traced Direct Lighting)** | ⚠️ None | [NVIDIA-RTX/RTXDI](https://github.com/NVIDIA-RTX/RTXDI) | `3.1.0` (2026-09-03) | - | 2026-09-07 |
| **PhysX** | ⚠️ None | [NVIDIA-Omniverse/PhysX](https://github.com/NVIDIA-Omniverse/PhysX) | `ovphysx-0.5.11` (2026-08-28) | - | 2026-09-07 |
| **NRD (Real-time Denoisers)** | ⚠️ None | [NVIDIA-RTX/NRD](https://github.com/NVIDIA-RTX/NRD) | `4.17.3` (2026-04-30) | - | 2026-09-07 |
| **NRi (NRD Interface)** | ⚠️ None | [NVIDIA-RTX/NRi](https://github.com/NVIDIA-RTX/NRi) | `180` (2026-06-22) | - | 2026-09-07 |
| **NVRHI 🔒** | ⚠️ None | [NVIDIA-RTX/NVRHI](https://github.com/NVIDIA-RTX/NVRHI) | - | - | - |
| **PhysX Legacy (v4) 🔒** | `PhysX_9.13.12611_win64.dll`, `PhysXDevice64.dll` | [NVIDIAGameWorks/PhysX](https://github.com/NVIDIAGameWorks/PhysX) | - | - | - |

---

## 🟪 Intel

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **Intel XeSS** | `libxess.dll`, `libxess_dx11.dll`, `libxell.dll`, `libxess_fg.dll` | [intel/xess](https://github.com/intel/xess) | `3.0.2` (2026-07-24) | - | 2026-09-07 |

---

## 🟨 Vulkan

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **Vulkan SDK / Loader** | `vulkan-1.dll` | - | `1.4.357.0` | - | 2026-09-07 |
| **SwiftShader 🔒** | ⚠️ None | [google/swiftshader](https://github.com/google/swiftshader) | - | - | - |
| **OpenXR** | `openxr_loader.dll` | [KhronosGroup/OpenXR-SDK](https://github.com/KhronosGroup/OpenXR-SDK) | `release-1.1.63` (2026-09-02) | `release-1.0.21` (2022-01-12) | 2026-09-07 |

---

## 🔊 Audio

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **OpenAL Soft** | `openal32.dll` | [kcat/openal-soft](https://github.com/kcat/openal-soft) | `1.25.2` (2026-05-12) | `latest` (2026-09-07) | 2026-09-07 |
| **Steam Audio** | `phonon.dll`, `phonon_fmod_studio.dll`, `phonon_unity.dll` | [ValveSoftware/steam-audio](https://github.com/ValveSoftware/steam-audio) | `4.8.1` (2026-02-11) | `2.0-beta.20` (2021-04-13) | 2026-09-07 |
| **XAudio2 Redistributable** | `XAUDIO2_9REDIST.dll` | [NuGet](https://www.nuget.org/packages/Microsoft.XAudio2.Redist/) | `1.2.13` (2025-04-10) | - | 2026-09-07 |
| **Miniaudio** | ⚠️ None | [mackron/miniaudio](https://github.com/mackron/miniaudio) | `0.11.25` (2026-03-03) | - | 2026-09-07 |
| **SoLoud** | ⚠️ None | [jarikomppa/soloud](https://github.com/jarikomppa/soloud) | `RELEASE_20200207` (2020-02-07) | - | 2026-09-07 |
| **FMOD Studio 🔒** | `fmod.dll`, `fmodstudio.dll` | - | - | - | - |
| **Wwise 🔒** | `AkSoundEngine.dll`, `AkMotionSink.dll` | - | - | - | - |

---

## 📦 Other

| SDK / Technology | DLLs | Source | Stable | Pre-release | Checked |
|---|---|---|---|---|---|
| **Bullet Physics** | ⚠️ None | [bulletphysics/bullet3](https://github.com/bulletphysics/bullet3) | `3.25` (2022-04-24) | - | 2026-09-07 |
| **RenderDoc** | `renderdoc.dll`, `renderdocshim.dll` | [baldurk/renderdoc](https://github.com/baldurk/renderdoc) | `1.46` (2026-08-31) | - | 2026-09-07 |

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
