/**
 * /setup/location — Step 2 of farm creation.
 * User sets district, main crop and location (auto-detect or manual).
 * Receives: farm_id, farm_name, area_acres via search params (from /sketch).
 */

import type { MetaFunction } from "@remix-run/node";
import { useNavigate, useNavigation, useSearchParams, Link } from "@remix-run/react";
import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Leaf,
  ArrowLeft,
  LocateFixed,
  MapPin,
  ChevronRight,
  ChevronDown,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { useFarmStore } from "~/store/useFarmStore";

export const meta: MetaFunction = () => [
  { title: "Set Farm Location — FarmOps" },
];

const TN_DISTRICTS = [
  "Ariyalur","Chengalpattu","Chennai","Coimbatore","Cuddalore","Dharmapuri",
  "Dindigul","Erode","Kallakurichi","Kancheepuram","Kanyakumari","Karur",
  "Krishnagiri","Madurai","Mayiladuthurai","Nagapattinam","Namakkal",
  "Nilgiris","Perambalur","Pudukkottai","Ramanathapuram","Ranipet","Salem",
  "Sivaganga","Tenkasi","Thanjavur","The Nilgiris","Theni","Thoothukudi",
  "Tiruchirappalli","Tirunelveli","Tirupathur","Tiruppur","Tiruvallur",
  "Tiruvannamalai","Tiruvarur","Vellore","Villupuram","Virudhunagar",
];

const CROPS = [
  "Rice","Wheat","Cotton","Sugarcane","Maize","Groundnut","Sorghum",
  "Pearl Millet","Finger Millet","Pulses","Banana","Coconut","Turmeric",
  "Chilli","Tomato","Onion","Brinjal","Lady's Finger","Tapioca","Other",
];

// Rough reverse-geocode: snap coordinates to nearest TN district centroid
const DISTRICT_COORDS: Record<string, [number, number]> = {
  "Chennai": [13.0827, 80.2707],
  "Coimbatore": [11.0168, 76.9558],
  "Madurai": [9.9252, 78.1198],
  "Thanjavur": [10.7870, 79.1378],
  "Salem": [11.6643, 78.1460],
  "Tiruchirappalli": [10.7905, 78.7047],
  "Tirunelveli": [8.7139, 77.7567],
  "Vellore": [12.9165, 79.1325],
  "Erode": [11.3410, 77.7172],
  "Thoothukudi": [8.7642, 78.1348],
};

function nearestDistrict(lat: number, lon: number): string {
  let best = "Thanjavur";
  let bestDist = Infinity;
  for (const [d, [dlat, dlon]] of Object.entries(DISTRICT_COORDS)) {
    const dist = Math.hypot(lat - dlat, lon - dlon);
    if (dist < bestDist) { bestDist = dist; best = d; }
  }
  return best;
}

export default function SetupLocation() {
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const farmId    = params.get("farm_id") ?? `farm-${Date.now()}`;
  const farmName  = params.get("farm_name") ?? "My Farm";
  const areaAcres = params.get("area_acres") ?? "0";

  const [district, setDistrict]     = useState("Thanjavur");
  const [mainCrop, setMainCrop]     = useState("Rice");
  const [lat, setLat]               = useState<number>(10.787);
  const [lon, setLon]               = useState<number>(79.1378);
  const [gpsStatus, setGpsStatus]   = useState<"idle" | "loading" | "done" | "error">("idle");
  const [gpsError, setGpsError]     = useState("");
  const [showCoords, setShowCoords] = useState(false); // hidden after GPS success

  const navigation = useNavigation();
  const isNavigating = navigation.state !== "idle";

  const { updateFarm } = useFarmStore();

  const detectLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setGpsError("Geolocation is not supported by your browser.");
      setGpsStatus("error");
      return;
    }
    setGpsStatus("loading");
    setGpsError("");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setLat(parseFloat(latitude.toFixed(4)));
        setLon(parseFloat(longitude.toFixed(4)));
        setDistrict(nearestDistrict(latitude, longitude));
        setGpsStatus("done");
      },
      (err) => {
        setGpsError(err.message || "Could not get location. Please enter manually.");
        setGpsStatus("error");
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  }, []);

  const handleContinue = () => {
    // Persist location into the store entry created in sketch step
    updateFarm(farmId, {
      location: { lat, lng: lon, city: district },
    });

    navigate(
      `/farm/${farmId}/snapshot?farm_name=${encodeURIComponent(farmName)}&area_acres=${areaAcres}&district=${encodeURIComponent(district)}&main_crop=${encodeURIComponent(mainCrop)}&lat=${lat}&lon=${lon}`
    );
  };

  return (
    <div className="min-h-screen bg-cream font-sans text-gray-900">
      {/* Navbar */}
      <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-100 sticky top-0 z-20">
        <div className="max-w-2xl mx-auto px-5 sm:px-8 py-3.5 flex items-center gap-4">
          <Link to="/sketch" className="flex items-center gap-1.5 text-gray-400 hover:text-farm-green transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back</span>
          </Link>
          <div className="flex items-center gap-2 ml-1">
            <div className="w-7 h-7 bg-farm-green rounded-lg flex items-center justify-center">
              <Leaf className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-serif font-bold text-farm-green">FarmOps</span>
          </div>
        </div>
      </nav>

      <div className="max-w-2xl mx-auto px-5 sm:px-8 pt-10 pb-20">
        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8">
          <div className="flex items-center gap-1.5">
            <div className="w-6 h-6 rounded-full bg-farm-green/20 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4 text-farm-green" />
            </div>
            <span className="text-sm text-farm-green font-medium">Draw</span>
          </div>
          <div className="flex-1 h-px bg-farm-green/30" />
          <div className="flex items-center gap-1.5">
            <div className="w-6 h-6 rounded-full bg-farm-green flex items-center justify-center">
              <span className="text-xs font-bold text-white">2</span>
            </div>
            <span className="text-sm text-farm-green font-semibold">Location</span>
          </div>
          <div className="flex-1 h-px bg-gray-200" />
          <div className="flex items-center gap-1.5">
            <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center">
              <span className="text-xs font-bold text-gray-400">3</span>
            </div>
            <span className="text-sm text-gray-400">Analyse</span>
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <h1 className="font-serif text-3xl font-bold text-gray-900 mb-1">Set Your Location</h1>
          <p className="text-gray-500 text-sm mb-8">
            For <span className="font-medium text-gray-700">{farmName}</span> · {areaAcres} acres
          </p>

          <div className="bg-white rounded-3xl shadow-xl border border-gray-100 p-7 space-y-6">

            {/* ── GPS Auto-detect ─────────────────────────── */}
            <div>
              <p className="text-sm font-semibold text-gray-700 mb-3">Detect automatically</p>
              <button
                onClick={detectLocation}
                disabled={gpsStatus === "loading"}
                className="w-full flex items-center justify-center gap-3 py-3.5 rounded-2xl border-2 border-dashed border-farm-green/40 text-farm-green hover:bg-farm-green/5 hover:border-farm-green transition-all disabled:opacity-60"
              >
                {gpsStatus === "loading" ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : gpsStatus === "done" ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : (
                  <LocateFixed className="w-5 h-5" />
                )}
                <span className="font-medium text-sm">
                  {gpsStatus === "loading" ? "Detecting…"
                    : gpsStatus === "done" ? "Location detected"
                    : "Use My GPS Location"}
                </span>
              </button>
              {gpsError && (
                <p className="text-xs text-red-500 mt-2 flex items-center gap-1">
                  <MapPin className="w-3 h-3" />{gpsError}
                </p>
              )}
            </div>

            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-gray-100" />
              <span className="text-xs text-gray-400 font-medium">or enter manually</span>
              <div className="flex-1 h-px bg-gray-100" />
            </div>

            {/* ── Manual fields ───────────────────────────── */}
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">District</label>
                <select
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all"
                >
                  {TN_DISTRICTS.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>

              <div className="col-span-2">
                <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Main Crop</label>
                <select
                  value={mainCrop}
                  onChange={(e) => setMainCrop(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all"
                >
                  {CROPS.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              {/* Coordinates — hidden by default, toggle to reveal */}
              <div className="col-span-2">
                <button
                  type="button"
                  onClick={() => setShowCoords((v) => !v)}
                  className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-farm-green transition-colors"
                >
                  <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showCoords ? "rotate-180" : ""}`} />
                  {showCoords ? "Hide coordinates" : "Show / edit coordinates"}
                </button>
              </div>

              {showCoords && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Latitude (°N)</label>
                    <input
                      type="number" step="0.0001" min="8" max="13.5" value={lat}
                      onChange={(e) => setLat(parseFloat(e.target.value))}
                      className="w-full px-4 py-3 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Longitude (°E)</label>
                    <input
                      type="number" step="0.0001" min="76" max="80.5" value={lon}
                      onChange={(e) => setLon(parseFloat(e.target.value))}
                      className="w-full px-4 py-3 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all"
                    />
                  </div>
                </>
              )}
            </div>

            {/* ── Continue button ─────────────────────────── */}
            <button
              onClick={handleContinue}
              disabled={isNavigating}
              className="w-full flex items-center justify-center gap-2 py-4 bg-farm-green text-white rounded-2xl font-semibold shadow-lg shadow-farm-green/20 hover:bg-green-800 active:scale-[0.98] transition-all disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isNavigating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Connecting to live data…
                </>
              ) : (
                <>
                  Analyse My Farm
                  <ChevronRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
