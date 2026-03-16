---
name: visionos-spatial
description: "Use when building visionOS spatial features — windows, volumes, immersive spaces, RealityView, ARKit provider setup, input handling, ornaments"
argument-hint: "[feature description]"
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
---

# visionOS Spatial Computing Patterns

## Overview
Step-by-step patterns for building native visionOS features. Covers scene types, RealityView integration, ARKit provider setup, and input handling.

## When to Use
- Creating a new visionOS app or scene
- Adding a volume or immersive space to an existing app
- Setting up ARKit providers (hand tracking, plane detection, world anchors)
- Implementing look-and-pinch, direct touch, or custom gesture input
- Adding ornaments to windows or volumes

## Quick Reference

### Scene Type Selection
```
Need 2D content only?           → Window (.plain)
Need 3D in shared space?        → Volume (.volumetric)
Need spatial tracking/anchors?  → ImmersiveSpace (.mixed)
Need full VR?                   → ImmersiveSpace (.full)
```

### Knowledge Docs
Reference: `.claude/docs/visionos-development/*.md`
Read `overview.md` first, then the relevant area file.

## Workflow

### 1. Choose Scene Type

**Window** (default):
```swift
WindowGroup { ContentView() }
```

**Volume**:
```swift
WindowGroup(id: "viewer") {
    VolumeView()
}
.windowStyle(.volumetric)
.defaultSize(width: 0.5, height: 0.5, depth: 0.5, in: .meters)
```

**Immersive Space**:
```swift
ImmersiveSpace(id: "immersive") {
    ImmersiveView()
}
.immersionStyle(selection: $style, in: .mixed, .progressive, .full)
```

### 2. Add 3D Content

**Simple model (no interaction)**:
```swift
Model3D(named: "shoe") { model in
    model.resizable().scaledToFit()
} placeholder: {
    ProgressView()
}
```

**Interactive 3D (RealityView)**:
```swift
RealityView { content in
    let entity = try await ModelEntity(named: "Robot")
    entity.components.set(HoverEffectComponent())
    entity.components.set(InputTargetComponent())
    entity.components.set(CollisionComponent(shapes: [.generateSphere(radius: 0.2)]))
    content.add(entity)
}
.gesture(TapGesture().targetedToAnyEntity().onEnded { value in
    // Handle tap on value.entity
})
```

### 3. Set Up ARKit (if needed)

Requires Full Space (immersive space). Request in your App declaration.

```swift
let session = ARKitSession()

// Hand tracking
let hands = HandTrackingProvider()
try await session.run([hands])
for await update in hands.anchorUpdates {
    let joint = update.anchor.handSkeleton?.joint(.indexFingerTip)
}

// Plane detection
let planes = PlaneDetectionProvider(alignments: [.horizontal, .vertical])
try await session.run([planes])

// World anchors (persistent)
let world = WorldTrackingProvider()
let anchor = WorldAnchor(originFromAnchorTransform: transform)
try await world.addAnchor(anchor)
```

### 4. Add Ornaments

```swift
.ornament(attachmentAnchor: .scene(.bottomFront)) {
    HStack {
        Button("Action") { }
    }
    .padding()
    .glassBackgroundEffect()
}
```

### 5. Handle Input

**Look and pinch** (default — no code needed for standard controls)

**Entity gestures**:
```swift
.gesture(DragGesture().targetedToAnyEntity().onChanged { value in
    value.entity.position = value.convert(value.location3D, from: .local, to: .scene)
})
```

**Custom hand gestures** (ARKit, Full Space only):
Use HandTrackingProvider → read joint positions → define gesture thresholds

## Accessibility Checklist

1. Every interactive entity has `AccessibilityComponent` with label + traits
2. Touch targets minimum 60pt
3. Content at comfortable viewing distance (~1.5m)
4. Respect `prefersReducedMotion`
5. Provide head-anchor alternatives where needed
6. Color contrast 4:1 minimum

## Common Mistakes

- Forgetting `CollisionComponent` → entity can't receive gestures
- Using `.load()` multiple times for same asset → use `.clone()` instead
- Not checking ARKit authorization status before running providers
- Opening immersive space for content that works in a volume
- Assuming camera access exists without enterprise entitlement
- Hardcoding positions in points instead of meters for RealityKit
