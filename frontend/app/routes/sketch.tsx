/**
 * /sketch — Canvas-based farm boundary sketching page.
 * After saving, navigates to the farm snapshot page.
 */

import type { MetaFunction } from "@remix-run/node";
import { useNavigate, useSearchParams } from "@remix-run/react";
import { useRef, useState, useEffect, useCallback } from "react";
import { Eraser, Check, Pencil, Leaf, ArrowLeft } from "lucide-react";
import { Link } from "@remix-run/react";
import { useFarmStore } from "~/store/useFarmStore";

export const meta: MetaFunction = () => [
  { title: "Sketch Your Farm — FarmOps" },
];

const GRID_SIZE = 40;

function drawGrid(ctx: CanvasRenderingContext2D, w: number, h: number) {
  ctx.fillStyle = "#f5f5f0";
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "#e5e5e5";
  ctx.lineWidth = 1;
  for (let x = 0; x <= w; x += GRID_SIZE) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }
  for (let y = 0; y <= h; y += GRID_SIZE) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }
}

export default function SketchPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const editFarmId = searchParams.get("farm_id"); // present when redrawing an existing farm

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasDrawn, setHasDrawn] = useState(false);
  const [acres, setAcres] = useState("");
  const [farmName, setFarmName] = useState("");
  const { addFarm, updateFarm } = useFarmStore();

  // Init canvas — restore existing sketch when redrawing
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    canvas.width = container.clientWidth;
    canvas.height = 400;
    const ctx = canvas.getContext("2d")!;
    drawGrid(ctx, canvas.width, canvas.height);

    if (editFarmId) {
      const existing = useFarmStore.getState().farms.find((f) => f.id === editFarmId);
      if (existing) {
        if (existing.name)       setFarmName(existing.name);
        if (existing.totalAcres) setAcres(String(existing.totalAcres));
        if (existing.sketchDataUrl) {
          const img = new Image();
          img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            setHasDrawn(true);
          };
          img.src = existing.sketchDataUrl;
        }
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getPos = (e: React.MouseEvent | React.TouchEvent, canvas: HTMLCanvasElement) => {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    if ("touches" in e) {
      return {
        x: (e.touches[0].clientX - rect.left) * scaleX,
        y: (e.touches[0].clientY - rect.top) * scaleY,
      };
    }
    return {
      x: ((e as React.MouseEvent).clientX - rect.left) * scaleX,
      y: ((e as React.MouseEvent).clientY - rect.top) * scaleY,
    };
  };

  const startDrawing = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    const { x, y } = getPos(e, canvas);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.strokeStyle = "#2D5A27";
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    setIsDrawing(true);
    setHasDrawn(true);
  }, []);

  const draw = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    const { x, y } = getPos(e, canvas);
    ctx.lineTo(x, y);
    ctx.stroke();
  }, [isDrawing]);

  const stopDrawing = useCallback(() => setIsDrawing(false), []);

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    drawGrid(ctx, canvas.width, canvas.height);
    setHasDrawn(false);
  };

  const handleSave = () => {
    if (!acres) return;
    const canvas = canvasRef.current;
    const dataUrl = canvas?.toDataURL("image/png");
    const name = farmName.trim() || `My Farm ${new Date().toLocaleDateString("en-IN")}`;

    if (editFarmId) {
      // Redraw mode — update the existing farm record
      updateFarm(editFarmId, {
        name,
        totalAcres: parseFloat(acres),
        sketchDataUrl: dataUrl,
      });
      navigate(`/setup/location?farm_id=${editFarmId}&farm_name=${encodeURIComponent(name)}&area_acres=${acres}`);
    } else {
      // New farm — use a real UUID so the backend accepts it
      const newId = crypto.randomUUID();
      addFarm({
        id: newId,
        name,
        totalAcres: parseFloat(acres),
        crops: [],
        inventory: [],
        sketchDataUrl: dataUrl,
      });
      navigate(`/setup/location?farm_id=${newId}&farm_name=${encodeURIComponent(name)}&area_acres=${acres}`);
    }
  };

  return (
    <div className="min-h-screen bg-cream font-sans">
      {/* Navbar */}
      <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-100 sticky top-0 z-20">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-3.5 flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 text-gray-400 hover:text-farm-green transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back</span>
          </Link>
          <div className="flex items-center gap-2 ml-2">
            <div className="w-7 h-7 bg-farm-green rounded-lg flex items-center justify-center">
              <Leaf className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-serif font-bold text-farm-green">FarmOps</span>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-5 sm:px-8 pt-10 pb-16">
        <div className="text-center mb-8">
          <h1 className="font-serif text-4xl font-bold text-farm-green mb-2">Sketch Your Farm</h1>
          <p className="text-gray-500">Draw the approximate boundaries of your land.</p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl p-6">
          {/* Canvas area */}
          <div
            ref={containerRef}
            className="relative rounded-2xl overflow-hidden border-2 border-dashed border-gray-200 cursor-crosshair touch-none select-none"
          >
            <canvas
              ref={canvasRef}
              onMouseDown={startDrawing}
              onMouseMove={draw}
              onMouseUp={stopDrawing}
              onMouseLeave={stopDrawing}
              onTouchStart={startDrawing}
              onTouchMove={draw}
              onTouchEnd={stopDrawing}
              className="w-full block"
              style={{ height: 400 }}
            />

            {/* Clear button */}
            <button
              onClick={clearCanvas}
              className="absolute top-3 right-3 p-2 bg-white rounded-xl shadow-sm border border-gray-100 hover:bg-red-50 hover:border-red-200 text-red-400 transition-all"
              title="Clear canvas"
            >
              <Eraser className="w-5 h-5" />
            </button>

            {/* Draw hint */}
            {!hasDrawn && (
              <div className="absolute bottom-3 left-3 bg-white/80 backdrop-blur px-3 py-1.5 rounded-full text-xs font-medium text-gray-500 pointer-events-none flex items-center gap-1.5">
                <Pencil className="w-3 h-3" /> Draw boundaries
              </div>
            )}
          </div>

          {/* Farm name + acres + save */}
          <div className="mt-6 flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1 w-full space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Farm Name
                </label>
                <input
                  type="text"
                  value={farmName}
                  onChange={(e) => setFarmName(e.target.value)}
                  placeholder={`My Farm ${new Date().toLocaleDateString("en-IN")}`}
                  className="w-full px-4 py-3 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Total Area (Acres)
                </label>
                <input
                  type="number"
                  value={acres}
                  onChange={(e) => setAcres(e.target.value)}
                  placeholder="e.g. 5.5"
                  min="0.1"
                  step="0.1"
                  className="w-full px-4 py-3 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:ring-2 focus:ring-farm-green/20 outline-none text-sm transition-all"
                />
              </div>
            </div>

            <button
              onClick={handleSave}
              disabled={!acres}
              className="w-full sm:w-auto px-8 py-3.5 bg-farm-green text-white rounded-xl font-semibold shadow-lg shadow-farm-green/20 hover:bg-green-800 transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Check className="w-4 h-4" /> Save &amp; Continue
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
