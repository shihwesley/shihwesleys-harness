---
name: realitykit-ecs
description: "Use when building RealityKit features — entities, components, systems, ShaderGraph materials, animations, spatial audio, asset optimization"
argument-hint: "[feature description]"
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
---

# RealityKit ECS Patterns

## Overview
Entity-Component-System patterns for RealityKit on visionOS. Covers entity creation, custom components, systems, ShaderGraph materials, animations, spatial audio, and asset optimization.

## When to Use
- Creating 3D content for visionOS volumes or immersive spaces
- Building custom ECS components and systems
- Loading and managing 3D assets (USDZ, Reality Composer Pro)
- Setting up ShaderGraph materials from code
- Adding animations (skeletal, transform, blend shapes)
- Implementing spatial audio
- Optimizing 3D performance

## Quick Reference

### ECS Core Loop
```
Entity (container) ← Component (data) ← System (per-frame behavior)
```

### Knowledge Docs
Reference: `.claude/docs/visionos-development/realitykit-3d-pipeline.md`

## Workflow

### 1. Create Entities

**From code:**
```swift
let entity = Entity()
var material = PhysicallyBasedMaterial()
material.baseColor.tint = .red
material.roughness = 0.5
entity.components.set(ModelComponent(
    mesh: .generateSphere(radius: 0.2),
    materials: [material]))
```

**From USDZ:**
```swift
let entity = try await Entity(named: "Robot")           // async, full control
let model = try await ModelEntity(named: "Robot")       // async, mesh+material access
let quick = try Entity.load(named: "Robot")             // sync, limited
```

**From Reality Composer Pro scene:**
```swift
let scene = try await Entity(named: "MyScene", in: realityKitContentBundle)
content.add(scene)
let cube = scene.findEntity(named: "Cube")
```

**From remote URL (visionOS 2.6+):**
```swift
let (data, _) = try await URLSession.shared.data(from: usdzURL)
let entity = try await Entity(from: data)
```

### 2. Make Interactive

Three required components:
```swift
entity.components.set(HoverEffectComponent())
entity.components.set(InputTargetComponent())
entity.components.set(CollisionComponent(shapes: [.generateSphere(radius: 0.2)]))
```

visionOS 26 shortcut:
```swift
ManipulationComponent.configureEntity(entity) // adds all three automatically
```

### 3. Define Custom Components

```swift
struct FloatingComponent: Component {
    var speed: Float = 0.01
    var axis: SIMD3<Float>
}
```

Rules:
- One component per type per entity
- Use serializable types for Reality Composer Pro compatibility
- Components are value types (structs)

### 4. Implement Systems

```swift
final class FloatingSystem: System {
    private let query = EntityQuery(where: .has(FloatingComponent.self))

    init(scene: Scene) {}

    func update(context: SceneUpdateContext) {
        for entity in context.entities(matching: query, updatingSystemWhen: .rendering) {
            var comp = entity.components[FloatingComponent.self]!
            comp.axis.z += comp.speed
            entity.components[FloatingComponent.self] = comp
            entity.setPosition(comp.axis, relativeTo: nil)
        }
    }
}

// Register at app init (in @Observable AppModel or @main App)
FloatingSystem.registerSystem()
```

### 5. ShaderGraph Materials

Build in Reality Composer Pro's node editor. Access from code:
```swift
var material = try await ShaderGraphMaterial(
    named: "/MyMaterial", from: "MyScene", in: realityKitContentBundle)
try material.setParameter(name: "Color", value: .color(.blue))
try material.setParameter(name: "Speed", value: .float(2.0))
entity.model?.materials = [material]
```

Parameter types: `.float()`, `.color()`, `.simd2Float()`, `.simd3Float()`, `.texture()`

### 6. Animations

**Play from USDZ:**
```swift
if let anim = entity.availableAnimations.first {
    let controller = entity.playAnimation(anim.repeat())
    controller.speed = 0.5
}
```

**visionOS 26 implicit animation:**
```swift
content.animate { entity.transform.translation.y = 0.5 }
// or
entity.animate { $0.transform.scale = [2, 2, 2] }
```

Types: skeletal (from DCC tools), transform (position/rotation/scale), blend shapes (mesh deformation).

### 7. Spatial Audio

```swift
let audioSource = Entity()
audioSource.spatialAudio = SpatialAudioComponent(gain: -5)
let resource = try AudioFileResource.load(named: "rain", configuration: .init(shouldLoop: true))
audioSource.playAudio(resource)
audioSource.spatialAudio?.directivity = .beam(focus: 1)
parentEntity.addChild(audioSource)
```

Properties: gain, reverbLevel, directLevel, distanceAttenuation, directivity.

## Asset Optimization

### Triangle Budgets
- ~100K tris visible per frame
- ~250K tris in shared spaces
- ~500K tris in immersive spaces

### Rules
1. Load once, `.clone()` for duplicates — never `.load()` the same asset twice
2. ASTC/ETC2 texture compression; 2K standard, 4K only when needed
3. Bake lighting in Blender when possible
4. Check counts: Reality Composer Pro > Statistics > Geometry
5. Profile: Xcode Instruments + Metal Frame Debugger
6. Test on actual Vision Pro hardware

### USDZ Pipeline
```
DCC (Blender/Maya) → USD export → Reality Converter (validate)
→ Reality Composer Pro (materials, assembly) → Xcode (bundle)
```

Coordinate system: RealityKit = -Z forward, Y up, meters. Blender = Z up, Y forward.

## visionOS 26 New Components

| Component | Purpose |
|-----------|---------|
| ManipulationComponent | Natural grab/move/rotate (auto-adds collision+input+hover) |
| ViewAttachmentComponent | Inline SwiftUI views on entities |
| GestureComponent | SwiftUI gestures directly on entities |
| PresentationComponent | Popovers from RealityKit scenes |
| MeshInstancesComponent | Efficient instanced rendering |
| ParticleEmitterComponent | Fireworks, rain, twinkle effects |

## Common Mistakes

- Forgetting to register systems at app init (`MySystem.registerSystem()`)
- Missing `CollisionComponent` → no gesture recognition
- Using `Entity.load()` (sync) when you need component access → use `Entity(named:)` (async)
- Not using `.clone()` for duplicate assets → performance tank
- Setting positions in points instead of meters
- Forgetting `realityKitContentBundle` when loading from RCP package
- Not checking `availableAnimations` before calling `playAnimation`
