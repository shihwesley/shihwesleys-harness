---
name: visionos-development
description: "visionOS patterns, APIs, and spatial computing conventions. Use when building apps for Apple Vision Pro — provides scene types, RealityKit ECS, ARKit providers, gesture handling, and visionOS 26 updates."
---

# visionOS Development Reference

When working with visionOS, follow these patterns and conventions.

## Scene Types

```
WindowGroup          → 2D SwiftUI window in shared space
.windowStyle(.volumetric) → bounded 3D container
ImmersiveSpace       → full environment control (.mixed / .progressive / .full)
```

Only one ImmersiveSpace can be open system-wide. Handle `.error` from `openImmersiveSpace`.

## RealityView (SwiftUI ↔ RealityKit bridge)

```swift
RealityView { content in
    if let model = try? await ModelEntity(named: "robot.usdz") {
        content.add(model)
    }
} update: { content in
    // Runs when SwiftUI state changes
}
```

## Making Entities Interactive

Three components required — without all three, gestures won't work:

```swift
entity.components.set(InputTargetComponent())
entity.components.set(HoverEffectComponent())
entity.generateCollisionShapes(recursive: true)
```

## Gestures

- `SpatialTapGesture` — eye focus + pinch
- `DragGesture` — move entities
- `MagnifyGesture` — scale
- `RotateGesture3D` — rotate

## ARKit (Full Space only)

```swift
let session = ARKitSession()
try await session.run([
    WorldTrackingProvider(),
    HandTrackingProvider(),
    PlaneDetectionProvider()
])
```

Providers: WorldTracking, HandTracking, PlaneDetection, SceneReconstruction, ImageTracking, CameraFrame (enterprise/visionOS 26).

## World Anchors

```swift
let anchor = WorldAnchor(originFromAnchorTransform: transform)
try await worldTracking.addAnchor(anchor)
// Persists across sessions automatically
```

## Spatial Audio

- `AmbientAudioComponent` — non-directional
- `SpatialAudioComponent` — positional 3D
- `ChannelAudioComponent` — stereo/surround

## Gotchas

1. ARKit features require ImmersiveSpace — don't work in windows/volumes
2. CollisionComponent mandatory for gestures — call `generateCollisionShapes(recursive: true)`
3. Volumes are bounded — content clips at edges
4. No direct camera access without enterprise license (relaxing in visionOS 26)
5. Coordinate systems differ: SwiftUI=points, RealityKit=meters, ARKit=meters from origin
6. Simulator can't test hand/eye tracking — real device required
7. 90Hz render target — heavy shaders cause judder

## visionOS 26

- `CoordinateSpace3D` — unified coordinate conversion
- 90Hz hand tracking (was 30Hz)
- Stereo camera access without enterprise license
- SharePlay shared world anchors
- `SurfaceAlignment` — snap to detected surfaces
- Bottom-aligned volumes, world-aligned volumes
- `contentCaptureProtected` — DRM content protection

For deeper information: `rlm_search(query="...", project="visionos-development")`
Full expertise: `~/.claude/research/visionos-development/expertise.md`
