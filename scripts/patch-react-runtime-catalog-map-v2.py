from pathlib import Path

ROOT = Path('source/frontend-react')


def replace_once(path: Path, old: str, new: str):
    text = path.read_text(encoding='utf-8')
    if new in text:
        return
    if old not in text:
        raise SystemExit(f'anchor missing in {path}: {old[:140]!r}')
    if text.count(old) != 1:
        raise SystemExit(f'anchor not unique in {path}: {old[:140]!r}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


catalog = ROOT / 'src/pages/CatalogPage.tsx'
replace_once(
    catalog,
    '<section className="section container">\n      <p className="eyebrow">CalabriaVera</p>',
    '<section className="section container" data-react-catalog-revision="20260912-catalog-map-v2">\n      <p className="eyebrow">CalabriaVera</p>',
)

map_page = ROOT / 'src/pages/MapPage.tsx'
replace_once(
    map_page,
    '        const leafletModule = await import("leaflet");\n        await import("leaflet.markercluster");\n        const L = (leafletModule.default || leafletModule) as typeof import("leaflet");',
    '        const leafletModule = await import("leaflet");\n        const L = (leafletModule.default || leafletModule) as typeof import("leaflet");\n        (globalThis as unknown as { L?: typeof import("leaflet") }).L = L;\n        await import("leaflet.markercluster");\n        const runtimeL = (globalThis as unknown as { L?: typeof import("leaflet") }).L || L;',
)
replace_once(
    map_page,
    '        leafletRef.current = L;\n        const map = L.map(elementRef.current,',
    '        leafletRef.current = runtimeL;\n        const map = runtimeL.map(elementRef.current,',
)
replace_once(
    map_page,
    '        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",',
    '        runtimeL.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",',
)
replace_once(
    map_page,
    '        L.control.zoom({ position: "topright" }).addTo(map);\n        L.control.scale({ imperial: false, position: "bottomleft" }).addTo(map);\n        const clusterFactory = (L as typeof L & { markerClusterGroup?: (options?: Record<string, unknown>) => import("leaflet").LayerGroup }).markerClusterGroup;',
    '        runtimeL.control.zoom({ position: "topright" }).addTo(map);\n        runtimeL.control.scale({ imperial: false, position: "bottomleft" }).addTo(map);\n        const clusterFactory = (runtimeL as typeof runtimeL & { markerClusterGroup?: (options?: Record<string, unknown>) => import("leaflet").LayerGroup }).markerClusterGroup;',
)
replace_once(
    map_page,
    'iconCreateFunction: (cluster: { getChildCount(): number }) => L.divIcon({',
    'iconCreateFunction: (cluster: { getChildCount(): number }) => runtimeL.divIcon({',
)
replace_once(map_page, '          : L.layerGroup();', '          : runtimeL.layerGroup();')
replace_once(map_page, '    if (!L || !layer || !items) return;', '    if (!mapReady || !L || !layer || !items) return;')
replace_once(
    map_page,
    '  }, [filtered, items, nearby, userPoint, language, copy.open, copy.tourism]);',
    '  }, [mapReady, filtered, items, nearby, userPoint, language, copy.open, copy.tourism]);',
)
replace_once(
    map_page,
    '<section className="section container">\n      <p className="eyebrow">CalabriaVera</p><h1>',
    '<section className="section container" data-react-map-revision="20260912-catalog-map-v2">\n      <p className="eyebrow">CalabriaVera</p><h1>',
)
replace_once(
    map_page,
    '<label>{uiText("service",language)}<input id="service" value={service}',
    '<label style={{display:"none"}}>{uiText("service",language)}<input id="service" hidden value={service}',
)
replace_once(
    map_page,
    '<label><span><input id="verified" type="checkbox"',
    '<label style={{display:"none"}}><span><input id="verified" hidden type="checkbox"',
)
replace_once(
    map_page,
    '<div id="map-results" className="stack" style={{marginTop:12}} />',
    '<div id="map-results" hidden className="stack" style={{marginTop:12}} />',
)

print('Applied runtime Catalog/Map v2 parity patch.')
