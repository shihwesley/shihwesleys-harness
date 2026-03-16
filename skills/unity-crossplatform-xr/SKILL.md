---
name: unity-crossplatform-xr
description: "Unity cross-platform XR patterns for visionOS + Meta Quest from one codebase. Use when building Unity apps targeting both Apple Vision Pro and Quest — covers package setup, XR rig pattern, input abstraction, Cesium tile budgets, version pinning, and known gotchas."
---

# Unity Cross-Platform XR Reference

When targeting both visionOS (PolySpatial) and Meta Quest (OpenXR) from one Unity project.

## Core Insight

PolySpatial is not the cross-platform layer — it's visionOS-only. The real cross-platform layer is **XRI + XR Hands + AR Foundation + OpenXR**. These run identically on both platforms. PolySpatial activates only for visionOS MR builds.

## Package Stack

```
Shared (both platforms):
  com.unity.xr.openxr          ← OpenXR Plugin
  com.unity.xr.interaction.toolkit   ← XRI 3.0+
  com.unity.xr.hands           ← hand tracking both platforms
  com.unity.xr.arfoundation    ← passthrough, plane detection

Quest (Android):
  com.unity.xr.meta-openxr@2.4.0   ← Meta OpenXR extensions
  Meta XR Core SDK (Asset Store, only if you need OVRManager features)

visionOS (auto-installed on MR mode):
  com.unity.polyspatial
  com.unity.polyspatial.visionos
```

**Do not use the legacy Oculus XR Plugin** — deprecated as of Meta SDK v74. Use `com.unity.xr.meta-openxr` instead.

## Version Matrix (March 2026)

| Component | Version |
|-----------|---------|
| Unity | 6 (6000.x) |
| PolySpatial | 2.4.3 |
| com.unity.xr.meta-openxr | 2.4.0 |
| Cesium for Unity (visionOS builds) | **1.11.1** (pinned — see Gotchas) |
| Cesium for Unity (Quest only) | 1.19.x |
| XRI | 3.0.x |

## XR Plugin Management Setup

**Android tab:** OpenXR ✓ + Meta Quest Support feature group + Oculus Touch Controller Profile
**visionOS tab:** Apple visionOS XR Plugin + App Mode = `Mixed Reality - Volume or Immersive Space`

## Dual-Rig Scene Pattern

```csharp
// Bootstrapper.cs - [DefaultExecutionOrder(-1000)]
// Instantiate (not SetActive) to avoid Awake race conditions

void Start() {
#if UNITY_VISIONOS
    Instantiate(visionOSRigPrefab, transform);
#elif UNITY_ANDROID
    Instantiate(questRigPrefab, transform);
#endif
}
```

Scene has two disabled prefabs: `QuestXRRig` and `VisionOSXRRig`. All shared content is in the scene normally.

## Input Abstraction

XRI 3.0 Input Readers abstract platform input. Your interactor code is platform-agnostic.

**On Quest:** XR Hands drives `NearFarInteractor`. Controllers also work via Oculus Touch profile.
**On visionOS MR:** Pinch → `VisionOSFarCaster`, index tap → poke, gaze → `VisionOSHoverEffect`.

Custom gestures via `XRHandShape` assets work identically on both. Define shapes once, works everywhere.

**Haptics guard:**
```csharp
#if UNITY_ANDROID
    controller.SendHapticImpulse(0.5f, 0.1f);
#endif
```

## Spatial UI

Use **World Space Canvas** with `TrackedDeviceGraphicRaycaster` on both platforms. Screen Space Canvas fails on visionOS MR. No post-processing, no ShaderLab shaders in PolySpatial mode (use URP Lit/Unlit or ShaderGraph nodes only).

## Cesium for Unity — Platform Tile Budgets

```csharp
void ConfigureTilesForPlatform(Cesium3DTileset tileset) {
#if UNITY_ANDROID  // Quest 3
    tileset.MaximumSimultaneousTileLoads = 5;    // HARD LIMIT — >5 causes frame spikes
    tileset.MaximumScreenSpaceError = 24f;
    tileset.MaximumCachedBytes = 128 * 1024 * 1024;
    tileset.PreloadSiblings = false;
#elif UNITY_VISIONOS  // Vision Pro M2
    tileset.MaximumSimultaneousTileLoads = 10;
    tileset.MaximumScreenSpaceError = 12f;
    tileset.MaximumCachedBytes = 512 * 1024 * 1024;
    tileset.PreloadSiblings = true;
#endif
}
```

Quest 3 renders tiles at ~2.5x lower resolution/distance than Vision Pro. Vision Pro M2 has substantial thermal headroom; Quest 3 XR2 Gen 2 throttles after 5-10 minutes of heavy load.

## Cesium for Unity visionOS Build Fix

Cesium for Unity uses "Reinterop" (C# ↔ C++ code gen). Most versions fail to compile for visionOS.

**Working version:** `1.11.1`
**Broken:** 1.14.0 ("519 duplicate symbols arm64"), likely others between 1.11.1 and current
**Official status:** Unsupported. Track PR #502 on `CesiumGS/cesium-unity` for merge.
**Manual fix if needed:**
```bash
cd Library/PackageCache/com.cesium.unity@<version>/
dotnet publish Reinterop~ -o .
```

## Google 3D Tiles Auth in Unity

```csharp
// Same API key works on both platforms — no platform-specific auth
cesiumTileset.url =
    "https://tile.googleapis.com/v1/3dtiles/root.json?key=" + apiKey;

// Keep tileset alive across scenes — don't re-fetch root.json on every scene load
// DontDestroyOnLoad the tileset root GameObject
```

## Gotchas

1. **Cesium + Quest 3 + Vulkan → left-eye artifacts.** Fix: Project Settings > Graphics API → remove Vulkan, use OpenGLES3 only.

2. **meta-openxr 2.2.0+ breaks passthrough on Quest 3/3S.** Downgrade to 2.2.0-pre.1 or check Unity Issue Tracker for fix.

3. **OVRManager breaks visionOS builds.** Any `using OVRManager` in shared code → compile error on visionOS. Guard with `#if UNITY_ANDROID` or don't use it.

4. **PolySpatial namespace in shared code → compile error on Android.** Keep `using Unity.PolySpatial` in `#if UNITY_VISIONOS` guarded files only.

5. **visionOS requires Unity Pro license.** PolySpatial refuses to activate on Free/Student tier — fails at build, not compile.

6. **EEA Google Cloud billing → 403 on tile.googleapis.com.** Not a platform issue; affects both targets equally.

7. **Cesium tile load time on Quest: 30-60 seconds** for initial scene population at 5 max loads. Use fade-in or loading UI.

## Shipping Examples

| App | Platforms | Tech |
|-----|-----------|------|
| **FLY (VirZOOM)** | Quest 2/3 + Vision Pro | Unity + PolySpatial (inferred) + Google 3D Tiles |
| **WorldLens** | Quest 3 | Cesium for Unity + Google 3D Tiles, >70fps |
| **Spatial Earth (ATEO)** | Vision Pro only | Cesium for Unity 1.11.x + PolySpatial |

## Deep Reference

Full expertise: `~/.claude/research/unity-crossplatform-xr/expertise.md`
Prior visionOS game engine research: `~/.claude/research/visionos-game-engines/expertise.md`
Cesium + 3D Tiles on visionOS: `~/.claude/research/3d-tiles-visionos-apps/expertise.md`
Google 3D Tiles + RealityKit (ECEF math): `~/.claude/research/google-3d-tiles-realitykit/expertise.md`
