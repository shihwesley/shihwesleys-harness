---
name: visionos-game-engines
description: "visionOS game engine patterns and tradeoffs. Use when choosing between Unity PolySpatial, Unreal Engine, Godot, or native Metal for visionOS development — provides engine capabilities, rendering paths, simulator support, and integration patterns."
---

# visionOS Game Engines Reference

## Two Rendering Paths (Everything Flows From This)

**Path 1 — RealityKit / Shared Space:**
- OS manages the frame loop via RealityKit
- App lives alongside other apps (multitasking)
- No custom shaders (MaterialX only via ShaderGraph)
- Engines: Unity PolySpatial (RealityKit mode), Native RealityKit, Godot windowed

**Path 2 — CompositorServices / Full Space:**
- You own the Metal frame loop via `LayerRenderer`
- One app at a time, full screen
- Full shader/rendering control
- Engines: Unreal Engine, Unity Metal mode, custom Metal renderer, Godot immersive (pending)

Use `CompositorLayer` (not `MTKView`) as SwiftUI scene type for Path 2.

## Engine Capability Matrix

| Feature | Unity PolySpatial | Unreal 5.5+ | Godot (pending) | Native RealityKit |
|---|---|---|---|---|
| Shared Space | Yes | No | Yes (windowed) | Yes |
| Simulator | Yes | No (device only) | Likely | Yes |
| Custom shaders | No (MaterialX only) | Yes | Yes | Metal only |
| Hand tracking | Yes (XR Hands) | Yes (ARKit) | Yes (ARKit) | Yes (ARKit) |
| Passthrough (visionOS 2.0+) | Yes | Yes (UE 5.5+) | Pending | Yes |
| Embed in native app | Partial (separate SwiftUI windows) | No documented path | Unknown | N/A (it IS native) |
| License cost | Pro required | Free | Free (MIT) | Free |

## Unity PolySpatial

**Min versions:** Unity 6 for 2.x packages; Unity 2022.3.18f1 for 1.x packages. Apple Silicon Mac required.

**App modes** (Project Settings > XR Plug-in Manager > Apple visionOS > App Mode):
- `Mixed Reality - Volume or Immersive Space` → RealityKit rendering
- `Virtual Reality - Fully Immersive Space` → Metal/CompositorServices rendering
- `Hybrid` (2.x only) → runtime switch between the two

**SwiftUI interop pattern:**
- Swift files ending in `*InjectedScene.swift` auto-merge into the app's top-level App
- C# ↔ Swift via `DllImport`
- SwiftUI windows are separate from Unity's volumetric window — cannot mix in same window
- UAAL (Unity as a Library) on visionOS is **broken/unsupported** as of early 2026 — PolySpatialSceneDelegate crashes

**What doesn't work in PolySpatial (RealityKit) mode:**
- ShaderLab / custom coded shaders
- VFX Graph
- Screen-space Canvas UI
- Screen-space post-processing (bloom, DOF, etc.)
- MetalFX upscaling with foveation enabled

## Unreal Engine

**Versions:** 5.4+ experimental (Full Immersion), 5.5+ adds Mixed Immersion (visionOS 2.0 required)

**Key constraints:**
- Device required — visionOS Simulator not supported
- Full Space only — no Shared Space / multitasking
- TSR performance issues on Apple Silicon → switch AA mode in project settings
- No embed-in-native-app documented path

## Godot

**Status (early 2026):** Apple contributing 3-stage PR to Godot master branch. Stage 1 (windowed) merged. Stages 2-3 (Swift lifecycle, VR plugin) in progress. Not in binary releases yet — compile from source.

Community alternative: GodotVision (godot.vision) wraps Godot in RealityKit, already functional.

## Hybrid Pattern (Cut the Rope 3 style)

Mix native RealityKit chrome with game engine 3D content:
```swift
ZStack {
    MetalGameView()      // bottom: game engine renders to texture
    RealityView { ... }  // top: RealityKit 3D frame/chrome
}
```
`@State` variables drive dynamic frame changes (level transitions, etc.).

Unity's formal Hybrid Mode (2.x) manages this programmatically — performance overhead scales with scene complexity.

## CompositorServices Essentials

```swift
// Scene type for immersive Metal app
ImmersiveSpace {
    CompositorLayer(configuration: MyConfig()) { layerRenderer in
        MyRenderer(layerRenderer: layerRenderer).run()
    }
}

// Render loop pattern
func run() {
    while true {
        guard let frame = layerRenderer.queryNextFrame() else { return }
        frame.startSubmission()
        // encode Metal commands for left+right eye
        // use .layered layout + vertex amplification for stereo
        frame.endSubmission()
    }
}
```

Key notes:
- Use `.layered` texture layout + Metal vertex amplification for single-pass stereo
- ARKit for hand tracking (`HandAnchor`, `WorldAnchor`) separate from CompositorServices
- Foveation enabled by default; conflicts with MetalFX upscaling
- visionOS 2.0+ enables passthrough in mixed mode (was full-immersion-only on 1.0)

## Simulator vs Device

Only Unity and native RealityKit work in the Simulator. Everything targeting CompositorServices in full immersion can technically run in Simulator, but Unreal's toolchain doesn't support it.

## Decision Guide

- **Unity Pro available + need Shared Space + have Unity team** → Unity PolySpatial
- **AAA visuals + Full Space only is OK + no time pressure on simulator testing** → Unreal Engine
- **Budget zero + willing to compile from source + windowed OK now** → Godot
- **Native quality + moderate 3D + Swift team** → Native RealityKit
- **Existing engine codebase to port** → Custom Metal + CompositorServices

Full expertise: `/Users/quartershots/.claude/research/visionos-game-engines/expertise.md`
