/**
 * FarmSelector Component
 *
 * Interactive map interface for farmers to select, locate, and draw their farm polygon.
 * Uses a simple lat/lon picker with a visual grid map representation (no external map libs required).
 * Supports: manual coordinate entry, predefined test farms, and polygon point drawing.
 */

import { useState, useRef, useCallback, useEffect, type FC } from "react";
import { useNavigate } from "@remix-run/react";

export interface FarmPolygon {
  coordinates: Array<[number, number]>; // [lon, lat] pairs
  centroid: [number, number]; // [lon, lat]
  area_acres: number;
}

export interface FarmLocation {
  farm_id: string;
  farm_name: string;
  lat: number;
  lon: number;
  district: string;
  main_crop: string;
  area_acres: number;
  polygon?: FarmPolygon;
}

interface FarmSelectorProps {
  onFarmSelected: (location: FarmLocation) => void;
  initialFarm?: Partial<FarmLocation>;
}

const TEST_FARMS: FarmLocation[] = [
  {
    farm_id: "00000000-0000-0000-0000-000000000001",
    farm_name: "Thanjavur Farm (Rice Belt)",
    lat: 10.787,
    lon: 79.1378,
    district: "Thanjavur",
    main_crop: "Rice",
    area_acres: 5.0,
  },
  {
    farm_id: "00000000-0000-0000-0000-000000000002",
    farm_name: "Coimbatore Farm (Dry Land)",
    lat: 11.0168,
    lon: 76.9558,
    district: "Coimbatore",
    main_crop: "Cotton",
    area_acres: 8.0,
  },
  {
    farm_id: "00000000-0000-0000-0000-000000000003",
    farm_name: "Madurai Farm (Sugarcane)",
    lat: 9.9252,
    lon: 78.1198,
    district: "Madurai",
    main_crop: "Sugarcane",
    area_acres: 12.0,
  },
];

const TN_DISTRICTS = [
  "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
  "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram",
  "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
  "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
  "Ramanathapuram", "Ranipet", "Salem", "Sivagangai", "Tenkasi",
  "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
  "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
  "Vellore", "Viluppuram", "Virudhunagar",
];

const CROPS = [
  "Rice", "Wheat", "Sugarcane", "Cotton", "Maize", "Groundnut",
  "Tomato", "Onion", "Banana", "Turmeric", "Chilli", "Finger Millet",
  "Black Gram", "Green Gram", "Sorghum", "Pearl Millet",
];

/**
 * Simple visual map grid representing Tamil Nadu (~8°N-13°N, 76°E-80°E)
 */
const MapGrid: FC<{
  selectedLat: number;
  selectedLon: number;
  polygonPoints: Array<[number, number]>;
  onPointClick: (lat: number, lon: number) => void;
}> = ({ selectedLat, selectedLon, polygonPoints, onPointClick }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  // Tamil Nadu bounds
  const LAT_MIN = 8.0;
  const LAT_MAX = 13.5;
  const LON_MIN = 76.0;
  const LON_MAX = 80.5;
  const W = 320;
  const H = 280;

  const latToY = (lat: number) => H - ((lat - LAT_MIN) / (LAT_MAX - LAT_MIN)) * H;
  const lonToX = (lon: number) => ((lon - LON_MIN) / (LON_MAX - LON_MIN)) * W;
  const coordsFromXY = (x: number, y: number) => ({
    lat: LAT_MIN + (1 - y / H) * (LAT_MAX - LAT_MIN),
    lon: LON_MIN + (x / W) * (LON_MAX - LON_MIN),
  });

  const handleSVGClick = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      const rect = svgRef.current?.getBoundingClientRect();
      if (!rect) return;
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const { lat, lon } = coordsFromXY(x, y);
      onPointClick(
        Math.round(lat * 10000) / 10000,
        Math.round(lon * 10000) / 10000
      );
    },
    [onPointClick]
  );

  // Build polygon SVG points
  const polyPoints = polygonPoints
    .map(([lon, lat]) => `${lonToX(lon)},${latToY(lat)}`)
    .join(" ");

  return (
    <div className="relative border border-gray-100 rounded-2xl overflow-hidden bg-farm-light">
      <div className="absolute top-1 left-1 text-xs text-gray-400 bg-white/70 px-1 rounded">
        Tamil Nadu — Click to place farm location
      </div>
      <svg
        ref={svgRef}
        width={W}
        height={H}
        className="cursor-crosshair"
        onClick={handleSVGClick}
      >
        {/* Grid lines */}
        {[8, 9, 10, 11, 12, 13].map((lat) => (
          <g key={`lat-${lat}`}>
            <line
              x1={0} y1={latToY(lat)} x2={W} y2={latToY(lat)}
              stroke="#d1fae5" strokeWidth="1"
            />
            <text x={2} y={latToY(lat) - 2} fontSize="8" fill="#6b7280">{lat}°N</text>
          </g>
        ))}
        {[76, 77, 78, 79, 80].map((lon) => (
          <g key={`lon-${lon}`}>
            <line
              x1={lonToX(lon)} y1={0} x2={lonToX(lon)} y2={H}
              stroke="#d1fae5" strokeWidth="1"
            />
            <text x={lonToX(lon) + 2} y={H - 2} fontSize="8" fill="#6b7280">{lon}°E</text>
          </g>
        ))}

        {/* Tamil Nadu outline approximation */}
        <polygon
          points={[
            [77.5, 8.1], [79.8, 8.4], [80.3, 9.5], [80.3, 10.5],
            [80.0, 11.5], [79.8, 12.0], [79.2, 13.0], [77.8, 13.3],
            [77.0, 13.0], [76.5, 12.0], [76.3, 11.0], [76.5, 10.0],
            [77.0, 8.8], [77.5, 8.1],
          ]
            .map(([lo, la]) => `${lonToX(lo)},${latToY(la)}`)
            .join(" ")}
          fill="#bbf7d0"
          stroke="#16a34a"
          strokeWidth="1.5"
          opacity="0.6"
        />

        {/* Test farm markers */}
        {TEST_FARMS.map((f) => (
          <g key={f.farm_id}>
            <circle
              cx={lonToX(f.lon)} cy={latToY(f.lat)}
              r={5} fill="#3b82f6" stroke="white" strokeWidth="1.5"
              opacity="0.8"
            />
            <text
              x={lonToX(f.lon) + 6} y={latToY(f.lat) + 3}
              fontSize="7" fill="#1d4ed8"
            >
              {f.district}
            </text>
          </g>
        ))}

        {/* Drawn polygon */}
        {polygonPoints.length >= 3 && (
          <polygon
            points={polyPoints}
            fill="#fbbf24" fillOpacity="0.3"
            stroke="#f59e0b" strokeWidth="2"
          />
        )}
        {polygonPoints.length >= 2 && (
          <polyline
            points={polyPoints}
            fill="none"
            stroke="#f59e0b" strokeWidth="2" strokeDasharray="4 2"
          />
        )}
        {polygonPoints.map(([plon, plat], i) => (
          <circle
            key={i}
            cx={lonToX(plon)} cy={latToY(plat)}
            r={4} fill="#f59e0b" stroke="white" strokeWidth="1.5"
          />
        ))}

        {/* Selected location marker */}
        {selectedLat && selectedLon && (
          <g>
            <circle
              cx={lonToX(selectedLon)} cy={latToY(selectedLat)}
              r={10} fill="none" stroke="#dc2626" strokeWidth="2"
            />
            <circle
              cx={lonToX(selectedLon)} cy={latToY(selectedLat)}
              r={4} fill="#dc2626"
            />
            <line
              x1={lonToX(selectedLon) - 14} y1={latToY(selectedLat)}
              x2={lonToX(selectedLon) + 14} y2={latToY(selectedLat)}
              stroke="#dc2626" strokeWidth="1.5"
            />
            <line
              x1={lonToX(selectedLon)} y1={latToY(selectedLat) - 14}
              x2={lonToX(selectedLon)} y2={latToY(selectedLat) + 14}
              stroke="#dc2626" strokeWidth="1.5"
            />
          </g>
        )}
      </svg>
      <div className="absolute bottom-1 right-1 text-xs text-gray-400 bg-white/70 px-1 rounded">
        🟡 = drawn polygon &nbsp;🔵 = test farms &nbsp;🔴 = selected
      </div>
    </div>
  );
};

export const FarmSelector: FC<FarmSelectorProps> = ({
  onFarmSelected,
  initialFarm,
}) => {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"preset" | "manual">("preset");
  const [selectedFarmId, setSelectedFarmId] = useState<string>("");
  const [lat, setLat] = useState<number>(initialFarm?.lat ?? 10.787);
  const [lon, setLon] = useState<number>(initialFarm?.lon ?? 79.1378);
  const [district, setDistrict] = useState<string>(initialFarm?.district ?? "Thanjavur");
  const [mainCrop, setMainCrop] = useState<string>(initialFarm?.main_crop ?? "Rice");
  const [areaAcres, setAreaAcres] = useState<number>(initialFarm?.area_acres ?? 5.0);
  const [farmName, setFarmName] = useState<string>(initialFarm?.farm_name ?? "");
  const [error, setError] = useState<string>("");

  const handleMapClick = useCallback((clickLat: number, clickLon: number) => {
    setLat(clickLat);
    setLon(clickLon);
  }, []);

  const handlePresetSelect = (farm: FarmLocation) => {
    setSelectedFarmId(farm.farm_id);
    setLat(farm.lat);
    setLon(farm.lon);
    setDistrict(farm.district);
    setMainCrop(farm.main_crop);
    setAreaAcres(farm.area_acres);
    setFarmName(farm.farm_name);
    onFarmSelected(farm);
  };

  const handleSubmit = () => {
    setError("");

    if (mode === "preset") {
      if (!selectedFarmId) { setError("Please select a test farm."); return; }
      const farm = TEST_FARMS.find((f) => f.farm_id === selectedFarmId);
      if (!farm) return;
      onFarmSelected(farm);
      return;
    }

    if (!lat || !lon) { setError("Please provide a valid location (latitude & longitude)."); return; }
    if (lat < 8 || lat > 13.5 || lon < 76 || lon > 80.5) { setError("Location must be within Tamil Nadu bounds."); return; }
    if (areaAcres <= 0) { setError("Farm area must be greater than 0 acres."); return; }

    onFarmSelected({
      farm_id: crypto.randomUUID(),
      farm_name: farmName || `${district} Farm`,
      lat, lon, district,
      main_crop: mainCrop,
      area_acres: areaAcres,
    });
  };

  return (
    <div className="space-y-5">
      {/* Mode tabs */}
      <div className="flex gap-2 flex-wrap">
        {(["preset", "manual"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-xl transition-all ${
              mode === m
                ? "bg-farm-green text-white shadow-md shadow-farm-green/20"
                : "bg-white border border-gray-200 text-gray-600 hover:border-farm-green/40 hover:text-farm-green"
            }`}
          >
            {m === "preset" ? "🗂 Test Farms" : "📍 Enter Location"}
          </button>
        ))}
        {/* Draw Boundary → navigate to dedicated sketch page */}
        <button
          onClick={() => navigate("/sketch")}
          className="flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-xl transition-all bg-white border border-gray-200 text-gray-600 hover:border-farm-green/40 hover:text-farm-green"
        >
          ✏️ Draw Boundary
        </button>
      </div>

      {/* Preset mode */}
      {mode === "preset" && (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">
            Select a pre-loaded test farm to get started instantly.
          </p>
          {TEST_FARMS.map((farm) => (
            <div
              key={farm.farm_id}
              onClick={() => handlePresetSelect(farm)}
              className={`p-4 rounded-2xl border cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5 ${
                selectedFarmId === farm.farm_id
                  ? "border-farm-green bg-farm-green/5 shadow-sm"
                  : "border-gray-100 hover:border-farm-green/30 bg-white"
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-gray-900">{farm.farm_name}</h4>
                  <p className="text-sm text-gray-500 mt-0.5">
                    {farm.district} · {farm.main_crop} · {farm.area_acres} acres
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {farm.lat.toFixed(4)}°N, {farm.lon.toFixed(4)}°E
                  </p>
                </div>
                <span className="text-farm-green text-lg ml-2">→</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Manual / Enter Location mode */}
      {mode === "manual" && (
        <div className="space-y-4">
          <p className="text-sm text-gray-500">
            Click the map or enter coordinates manually to set your farm location.
          </p>
          <MapGrid
            selectedLat={lat}
            selectedLon={lon}
            polygonPoints={[]}
            onPointClick={handleMapClick}
          />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Latitude (°N)</label>
              <input type="number" step="0.0001" min="8" max="13.5" value={lat}
                onChange={(e) => setLat(parseFloat(e.target.value))}
                className="w-full px-4 py-2.5 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Longitude (°E)</label>
              <input type="number" step="0.0001" min="76" max="80.5" value={lon}
                onChange={(e) => setLon(parseFloat(e.target.value))}
                className="w-full px-4 py-2.5 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">District</label>
              <select value={district} onChange={(e) => setDistrict(e.target.value)}
                className="w-full px-4 py-2.5 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all">
                {TN_DISTRICTS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Main Crop</label>
              <select value={mainCrop} onChange={(e) => setMainCrop(e.target.value)}
                className="w-full px-4 py-2.5 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all">
                {CROPS.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Farm Area (acres)</label>
              <input type="number" step="0.1" min="0.1" max="1000" value={areaAcres}
                onChange={(e) => setAreaAcres(parseFloat(e.target.value))}
                className="w-full px-4 py-2.5 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Farm Name (optional)</label>
              <input type="text" value={farmName} onChange={(e) => setFarmName(e.target.value)}
                placeholder={`${district} Farm`}
                className="w-full px-4 py-2.5 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all" />
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-3.5 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">{error}</div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        className="w-full py-4 bg-farm-green text-white rounded-xl font-semibold shadow-lg shadow-farm-green/20 hover:bg-green-800 transition-all flex items-center justify-center gap-2"
      >
        ⚡ {mode === "preset" ? "Analyse Selected Farm" : "Analyse This Farm"}
      </button>

      <p className="text-xs text-gray-400 text-center">
        Location data is used only to fetch weather, soil, and market insights for your farm.
      </p>
    </div>
  );
};

export default FarmSelector;
