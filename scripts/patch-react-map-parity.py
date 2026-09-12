from pathlib import Path

p = Path('frontend-react/src/pages/MapPage.tsx')
s = p.read_text()

def rep(old: str, new: str, label: str):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s = s.replace(old, new, 1)

rep('import { CATEGORIES, PROVINCES, CATEGORY_GROUPS, businessPath, categoryGroup } from "../lib/businesses";',
    'import { CATEGORIES, PROVINCES, businessPath, categoryGroup } from "../lib/businesses";',
    'imports')

rep('const CALABRIA_CENTER: [number, number] = [38.97, 16.47];\ntype UserPoint = { lat: number; lng: number } | null;',
'''const CALABRIA_CENTER: [number, number] = [38.97, 16.47];
const CATEGORY_MARKER_COLORS: Record<string, string> = {
  "Alloggi": "#2563eb",
  "Ristorazione": "#dc2626",
  "Turismo ed esperienze": "#059669",
  "Bellezza e benessere": "#db2777",
  "Shopping e prodotti": "#7c3aed",
  "Casa, edilizia e artigiani": "#d97706",
  "Auto e motori": "#0f766e",
  "Professionisti e servizi": "#4f46e5",
  "Salute": "#0891b2",
  "Altro": "#64748b",
};
type UserPoint = { lat: number; lng: number } | null;''',
    'marker colors')

start = s.find('function categoryMatches(')
end = s.find('function isTourism(', start)
if start < 0 or end < 0:
    raise SystemExit('categoryMatches block not found')
s = s[:start] + '''function markerColor(item: Business) {
  return CATEGORY_MARKER_COLORS[categoryGroup(item.category || item.subcategory || "")] || "#075b8f";
}
''' + s[end:]

rep('  const [service, setService] = useState(initial.get("servizio") || "");\n', '', 'remove service state')

rep('const map = runtimeL.map(elementRef.current, { preferCanvas: true, zoomControl: false, attributionControl: true, fadeAnimation: false, zoomAnimation: true, markerZoomAnimation: false }).setView(CALABRIA_CENTER, 8);',
    'const map = runtimeL.map(elementRef.current, { preferCanvas: true, zoomControl: false, attributionControl: false, fadeAnimation: false }).setView(CALABRIA_CENTER, 8);',
    'map options')
rep('runtimeL.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, minZoom: 6, attribution: "&copy; OpenStreetMap contributors", updateWhenIdle: true, updateWhenZooming: false, keepBuffer: 2, crossOrigin: true }).addTo(map);',
    'runtimeL.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, updateWhenIdle: true, updateWhenZooming: false, keepBuffer: 2 }).addTo(map);',
    'tile options')
rep('runtimeL.control.scale({ imperial: false, position: "bottomleft" }).addTo(map);',
'''runtimeL.control.scale({ imperial: false, position: "bottomleft", maxWidth: 110 }).addTo(map);
        runtimeL.control.attribution({ position: "bottomright", prefix: false }).addAttribution('<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">© OpenStreetMap contributors</a>').addTo(map);''',
    'map controls')
rep('? clusterFactory({ chunkedLoading: true, chunkInterval: 120, chunkDelay: 30, showCoverageOnHover: false, spiderfyOnMaxZoom: true, removeOutsideVisibleBounds: true, maxClusterRadius: 48, disableClusteringAtZoom: 15, iconCreateFunction: (cluster: { getChildCount(): number }) => runtimeL.divIcon({ className: "cv-map-cluster-shell", html: `<span class="cv-map-cluster">${cluster.getChildCount()}</span>`, iconSize: [42, 42] }) })',
'''? clusterFactory({ chunkedLoading: true, chunkInterval: 120, chunkDelay: 24, showCoverageOnHover: false, maxClusterRadius: 52, disableClusteringAtZoom: 13, iconCreateFunction: (cluster: { getChildCount(): number }) => { const count = cluster.getChildCount(); const size = count > 99 ? 48 : count > 20 ? 45 : 42; return runtimeL.divIcon({ className: "cv-map-cluster-shell", html: `<span class="cv-map-cluster">${count}</span>`, iconSize: [size, size] }); } })''',
    'cluster options')

rep('  const serviceNormalized = normalizeText(service);\n', '', 'remove service normalization')
old_filter = '''  const filtered = useMemo(() => (items || []).filter((item) => {
    if (!validCoordinates(item) || !categoryMatches(item, category)) return false;
    if (province && item.provincia !== province) return false;
    if (city && normalizeText(item.comune) !== normalizeText(city)) return false;
    if (verified && item.verified !== true) return false;
    if (serviceNormalized && !(item.services || []).some((value) => normalizeText(value).includes(serviceNormalized))) return false;
    if (nearby && userPoint && distanceKm(userPoint, item) > radius) return false;
    return true;
  }).sort((a, b) => nearby && userPoint ? distanceKm(userPoint, a) - distanceKm(userPoint, b) : String(a.name || "").localeCompare(String(b.name || ""), "it")), [items, category, province, city, verified, serviceNormalized, nearby, userPoint, radius]);'''
new_filter = '''  const filtered = useMemo(() => {
    const rows = (items || []).filter((item) => {
      if (!validCoordinates(item)) return false;
      if (category && item.category !== category) return false;
      if (province && item.provincia !== province) return false;
      if (city && !normalizeText(item.comune).includes(normalizeText(city))) return false;
      if (verified && item.verified !== true) return false;
      if (nearby && userPoint && distanceKm(userPoint, item) > radius) return false;
      return true;
    });
    if (nearby && userPoint) rows.sort((a, b) => distanceKm(userPoint, a) - distanceKm(userPoint, b));
    return rows;
  }, [items, category, province, city, verified, nearby, userPoint, radius]);'''
rep(old_filter, new_filter, 'filter semantics')

old_sync = '''  useEffect(() => {
    const params = new URLSearchParams();
    if (category) params.set("categoria", category);
    if (province) params.set("provincia", province);
    if (city) params.set("comune", city);
    if (service.trim()) params.set("servizio", service.trim());
    if (verified) params.set("verificata", "1");
    history.replaceState({}, "", `${location.pathname}${params.size ? `?${params}` : ""}`);
  }, [category, province, city, service, verified]);'''
new_sync = '''  useEffect(() => {
    const params = new URLSearchParams();
    if (category) params.set("categoria", category);
    if (province) params.set("provincia", province);
    if (city) params.set("comune", city);
    if (verified) params.set("verificata", "1");
    const initialFocus = initial.get("attivita");
    if (initialFocus && !category && !province && !city && !verified) params.set("attivita", initialFocus);
    history.replaceState({}, "", `${location.pathname}${params.size ? `?${params}` : ""}`);
  }, [category, province, city, verified, initial]);'''
rep(old_sync, new_sync, 'url sync')

old_marker = '''  useEffect(() => {
    const L = leafletRef.current, layer = layerRef.current;
    if (!mapReady || !L || !layer || !items) return;
    layer.clearLayers();
    for (const business of filtered) {
      const lat = Number(business.lat), lng = Number(business.lng);
      const fill = isTourism(business) ? "#059669" : business.verified ? "#075b8f" : "#475569";
      const icon = L.divIcon({ className: "cv-map-pin-shell", html: `<span aria-hidden="true" class="cv-map-pin${isTourism(business) ? " is-tourism" : business.verified ? " is-verified" : ""}" style="background:${fill};--cv-map-pin-color:${fill}"></span>`, iconSize: [30, 38], iconAnchor: [15, 36], popupAnchor: [0, -34] });
      const marker = L.marker([lat, lng], { icon, keyboard: true, title: localizedField<string>(business, "name", language) || business.name || "CalabriaVera" });
      const popup = document.createElement("div");
      const title = document.createElement("strong"); title.textContent = localizedField<string>(business, "name", language) || business.name || "CalabriaVera";
      const place = document.createElement("div"); place.textContent = [isTourism(business) ? copy.tourism : business.subcategory || business.category, business.comune, nearby && userPoint ? `${distanceKm(userPoint, business).toFixed(1)} km` : ""].filter(Boolean).join(" · "); place.style.cssText = "margin-top:4px;color:#64748b";
      const link = document.createElement("a"); link.href = withLanguage(routeFor(business), language); link.textContent = `${copy.open} →`; link.style.cssText = "display:inline-block;margin-top:8px;font-weight:800;color:#075b8f";
      popup.append(title, place, link); marker.bindPopup(popup, { maxWidth: 280, minWidth: 180 }).addTo(layer);
    }
  }, [mapReady, filtered, items, nearby, userPoint, language, copy.open, copy.tourism]);'''
new_marker = '''  useEffect(() => {
    const L = leafletRef.current, layer = layerRef.current, map = mapRef.current;
    if (!mapReady || !L || !layer || !items) return;
    layer.clearLayers();
    const markerById = new Map<string, import("leaflet").Marker>();
    for (const business of filtered) {
      const lat = Number(business.lat), lng = Number(business.lng), fill = markerColor(business);
      const icon = L.divIcon({ className: "cv-map-pin-shell", html: `<span aria-hidden="true" class="cv-map-pin${isTourism(business) ? " is-tourism" : ""}" style="background:${fill};--cv-map-pin-color:${fill}"></span>`, iconSize: [30, 38], iconAnchor: [15, 36], popupAnchor: [0, -33] });
      const titleText = localizedField<string>(business, "name", language) || business.name || "CalabriaVera";
      const marker = L.marker([lat, lng], { icon, keyboard: false, title: titleText });
      const popup = document.createElement("div"); popup.className = "cv-map-popup";
      const imageUrl = String(business.imageDataUrl || business.imageUrl || "");
      if (imageUrl) {
        const image = document.createElement("img"); image.className = "cv-map-popup__image"; image.loading = "lazy"; image.decoding = "async"; image.fetchPriority = "low"; image.src = imageUrl; image.alt = titleText;
        if (business.imageSrcset) { image.srcset = String(business.imageSrcset); image.sizes = "260px"; }
        popup.append(image);
      }
      const body = document.createElement("div"); body.className = "cv-map-popup__body";
      const categoryLabel = document.createElement("span"); categoryLabel.className = "cv-map-popup__category"; categoryLabel.textContent = String(business.subcategory || business.category || "Attività");
      const title = document.createElement("strong"); title.textContent = titleText;
      const place = document.createElement("div"); place.className = "cv-map-popup__place";
      const km = nearby && userPoint ? distanceKm(userPoint, business) : Infinity;
      place.textContent = [business.comune, business.provincia, Number.isFinite(km) ? `${km.toFixed(km < 10 ? 1 : 0)} km` : ""].filter(Boolean).join(" · ");
      const foot = document.createElement("div"); foot.className = "cv-map-popup__foot";
      const rating = document.createElement("span"); rating.className = "cv-map-popup__rating"; rating.textContent = business.rating ? `${Number(business.rating).toFixed(1)} ★` : "";
      const link = document.createElement("a"); link.className = "cv-map-popup__link"; link.href = withLanguage(routeFor(business), language); link.textContent = language === "it" ? "Scopri →" : `${copy.open} →`;
      foot.append(rating, link); body.append(categoryLabel, title, place, foot); popup.append(body);
      marker.bindPopup(popup, { maxWidth: 260, closeButton: true }).addTo(layer);
      markerById.set(String(business.id), marker);
    }
    const focus = new URLSearchParams(location.search).get("attivita");
    if (focus && map) {
      const business = filtered.find((item) => String(item.id) === focus), marker = markerById.get(String(focus));
      if (business && marker && validCoordinates(business)) {
        map.setView([Number(business.lat), Number(business.lng)], 13);
        const cluster = layer as import("leaflet").LayerGroup & { zoomToShowLayer?: (marker: import("leaflet").Marker, callback: () => void) => void };
        if (typeof cluster.zoomToShowLayer === "function") cluster.zoomToShowLayer(marker, () => marker.openPopup()); else marker.openPopup();
      }
    }
  }, [mapReady, filtered, items, nearby, userPoint, language, copy.open]);'''
rep(old_marker, new_marker, 'marker and popup parity')

rep('    if (bounds.length === 1) map.setView(bounds[0], 13);\n    else map.fitBounds(bounds, { padding: [36, 36], maxZoom: 13 });',
    '    map.fitBounds(bounds, { padding: [28, 28], maxZoom: 12 });',
    'fit results')
rep('  useEffect(() => {\n    if (!mapReady || !filtered.length || !(category || province || city || service || verified || nearby)) return;\n    fitFiltered();\n  }, [mapReady, category, province, city, service, verified, nearby, radius]);',
'''  useEffect(() => {
    if (!mapReady || !filtered.length || !(category || province || city || verified || nearby)) return;
    fitFiltered();
  }, [mapReady, category, province, city, verified, nearby, radius]);''',
    'filter fit effect')
rep('        map.setView([point.lat, point.lng], 10);',
    '        map.setView([point.lat, point.lng], 11);',
    'nearby zoom')
rep('<label style={{display:"none"}}>{uiText("service",language)}<input id="service" hidden value={service} onChange={(event)=>setService(event.target.value)} /></label>\n',
    '',
    'remove non-legacy service filter')
rep('data-react-map-revision="20260912-catalog-map-v2"', 'data-react-map-revision="20260912-legacy-map-v1"', 'revision')
rep('{items===null?uiText("loadingBusinesses",language):`${filtered.length} ${language === "it" ? "attività sulla mappa" : copy.visible}`}',
    '{items===null?uiText("loadingBusinesses",language):`${filtered.length} ${language === "it" ? "attività sulla mappa" : copy.visible}${nearby && userPoint ? ` entro ${radius} km` : ""}`}',
    'map count nearby')

p.write_text(s)
