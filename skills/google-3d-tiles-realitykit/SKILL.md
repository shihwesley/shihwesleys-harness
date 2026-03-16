---
name: google-3d-tiles-realitykit
description: "Google Photorealistic 3D Tiles + RealityKit/visionOS integration. Use when working on globe apps, 3D city rendering, tile streaming, or ECEF coordinate transforms on Apple platforms."
---

# Google 3D Tiles + RealityKit Reference

## Root Endpoint

```
https://tile.googleapis.com/v1/3dtiles/root.json?key={API_KEY}
```

Auth: API key in query param. Returns `tileset.json` (OGC 3D Tiles BVH root).
One root request = one billing event = 3-hour session of unlimited tile fetches.

## Pricing

| Volume (root requests/month) | Price |
|------------------------------|-------|
| 0–1,000 | FREE |
| 1k–100k | $6.00/1k |
| 100k–500k | $5.10/1k |
| 500k+ | $4.20/1k and below |

Rate limit: 12,000 tile requests/minute. Daily quota: 10,000 root requests.
Individual tile requests don't count against quota.
EEA restriction: EU billing addresses get 403s as of July 2025.

## Coordinate Transform Chain

```
WGS84 geodetic (lat°, lon°, alt m)
  ↓  ellipsoid equations (a=6378137m, e²=0.00669438)
ECEF (X, Y, Z in meters — always double precision)
  ↓  rotation matrix at reference lat/lon
ENU (East, North, Up — local tangent plane)
  ↓  axis remap
RealityKit (X=East, Y=Up, Z=-North)
```

```swift
// WGS84 → ECEF (double precision required)
func wgs84ToECEF(lat: Double, lon: Double, alt: Double) -> SIMD3<Double> {
    let a = 6_378_137.0, e2 = 0.00669437999014
    let latR = lat * .pi/180, lonR = lon * .pi/180
    let N = a / sqrt(1 - e2 * sin(latR)*sin(latR))
    return SIMD3(
        (N + alt) * cos(latR) * cos(lonR),
        (N + alt) * cos(latR) * sin(lonR),
        (N * (1-e2) + alt) * sin(latR)
    )
}

// ECEF → ENU (relative to reference point)
func ecefToENU(point: SIMD3<Double>, ref: SIMD3<Double>, refLat: Double, refLon: Double) -> SIMD3<Double> {
    let d = point - ref
    let sLat = sin(refLat * .pi/180), cLat = cos(refLat * .pi/180)
    let sLon = sin(refLon * .pi/180), cLon = cos(refLon * .pi/180)
    return SIMD3(
        -sLon*d.x + cLon*d.y,                          // East
        -sLat*cLon*d.x - sLat*sLon*d.y + cLat*d.z,    // North
         cLat*cLon*d.x + cLat*sLon*d.y + sLat*d.z      // Up
    )
}

// ENU → RealityKit (Y-up, -Z forward)
func enuToRealityKit(_ enu: SIMD3<Double>) -> SIMD3<Float> {
    return SIMD3<Float>(Float(enu.x), Float(enu.z), Float(-enu.y))
    // East→X, Up→Y, -North→Z
}
```

## cesium-native Integration Pattern

```cpp
// REQUIRED: call once at startup before any Tileset creation
Cesium3DTilesContent::registerAllTileContentTypes();

// Implement three interfaces:
// IAssetAccessor — HTTP fetching (use libcurl or bridge to URLSession)
// ITaskProcessor — background thread pool (bridge to GCD or Swift async)
// IPrepareRendererResources — glTF → GPU resources

class MyPrepareResources : public IPrepareRendererResources {
    void* prepareInLoadThread(
        const CesiumGltf::Model& model,
        const glm::dmat4& transform  // tile's ECEF transform (double)
    ) override {
        // Background thread. Extract vertex/index/UV data.
        // Apply ecef→ENU→RealityKit transform to positions.
        // Create MeshDescriptor data. Return as void* handle.
    }

    void* prepareInMainThread(Tile& tile, void* pLoadResult) override {
        // Main/render thread. MUST BE FAST (< 2ms for 90fps).
        // Create ModelEntity from MeshDescriptor, return handle.
    }
};

// Per frame:
ViewState vs = ViewState::create(pos, dir, up, viewport, hFov, vFov);
auto result = tileset.updateView({vs});
for (auto& tile : result.tilesToRenderThisFrame) {
    auto* handle = (MyRenderHandle*)tile.getContent().getRenderContent()->getRenderResources();
    handle->entity->setEnabled(true);
}
for (auto& tile : result.tilesFadingOut) {
    // hide but don't delete — cesium-native manages lifetime
}
```

## RealityKit Entity Lifecycle for Tiles

```swift
// ADD when tile becomes visible:
rootEntity.addChild(tileEntity)

// HIDE when tile fades out (don't remove — cesium-native may reuse):
tileEntity.isEnabled = false

// CLEANUP (ImmersiveSpace dismiss) — both calls required:
for entity in tileEntities.values { entity.removeFromParent() }
rootEntity.removeFromParent()  // CRITICAL: visionOS won't release GPU memory without this
tileEntities.removeAll()
```

## glTF Loading Gotcha: Draco

Google's tiles use `KHR_draco_mesh_compression`.
- RealityKit `Entity.load()` does NOT support Draco.
- cesium-native's `CesiumGltfReader` DOES handle Draco.
- If building without cesium-native: use Google's Draco C++ library via Obj-C++ bridge.

## Fly-to Camera Altitude Thresholds

```
> 50,000km   stylized globe only
1,000km      start satellite imagery overlay
50km         request root.json (begin prefetch)
10km         render 3D Tiles, fade out globe geometry
300–500m     target stop altitude (above skyline)
```

Request root.json well before you need tiles — there's latency before the first tiles appear.

## Alternatives

| Source | 3D Quality | iOS/visionOS Native |
|--------|------------|---------------------|
| Google Photorealistic 3D Tiles | Best (photogrammetry) | No SDK — REST only |
| Cesium ion | Medium (OSM Buildings = extruded) | cesium-native (C++) |
| Apple MapKit flyover | Good (Apple proprietary) | Native but no mesh access |
| Mapbox 3D terrain | Medium (vector extrusion) | Native iOS SDK |

## ToS: Attribution Required

Display `tileset.asset.copyright` visibly in your UI at all times during 3D rendering.
Violating this risks API key revocation.

## Key References

- Full expertise: `~/.claude/research/google-3d-tiles-realitykit/expertise.md`
- cesium-native visionOS integration: https://github.com/CesiumGS/cesium-native/issues/823
- cesium-native rendering guide: https://cesium.com/learn/cesium-native/ref-doc/rendering-3d-tiles.html
- OGC 3D Tiles spec: https://docs.ogc.org/cs/22-025r4/22-025r4.html
- Google API docs: https://developers.google.com/maps/documentation/tile/3d-tiles
