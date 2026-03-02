/**
 * Irrigation Scheduling Route
 *
 * Generates a 14-day smart irrigation calendar based on soil moisture,
 * weather forecast (skips when rain probability >70%), and crop growth stage.
 */

import type { ActionFunctionArgs, LoaderFunctionArgs, MetaFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { Form, Link, useActionData, useLoaderData, useNavigation, useSearchParams } from "@remix-run/react";
import { IrrigationScheduleCard } from "~/components/irrigation/IrrigationScheduleCard";
import type { IrrigationScheduleData } from "~/components/irrigation/IrrigationScheduleCard";

export const meta: MetaFunction = () => [
  { title: "Irrigation Scheduling - FarmOps" },
  { name: "description", content: "14-day smart irrigation calendar for your farm" },
];

const CROPS = ["Rice", "Wheat", "Sugarcane", "Cotton", "Maize", "Tomato", "Groundnut", "Default"];
const STAGES = [
  { value: "initial", label: "Initial (0-30%)" },
  { value: "mid", label: "Mid Season (30-70%)" },
  { value: "late", label: "Late Season (70-100%)" },
];
const METHODS = [
  { value: "flood", label: "Flood Irrigation" },
  { value: "furrow", label: "Furrow / Channel" },
  { value: "sprinkler", label: "Sprinkler" },
  { value: "drip", label: "Drip (Micro-irrigation)" },
];
const SOIL_TYPES = ["Clay", "Clay-Loam", "Loam", "Sandy-Loam", "Sandy", "Alluvial", "Black", "Red"];

interface LoaderData {
  farmId: string;
  farmName: string;
}

interface ActionData {
  success?: boolean;
  data?: IrrigationScheduleData;
  error?: string;
}

export async function loader({ params, request }: LoaderFunctionArgs) {
  const farmId = params.farmId ?? "";
  const url = new URL(request.url);
  const farmName = url.searchParams.get("farm_name") ?? "Your Farm";
  return json<LoaderData>({ farmId, farmName });
}

export async function action({ request, params }: ActionFunctionArgs) {
  const farmId = params.farmId ?? "";
  const formData = await request.formData();

  const payload = {
    farm_id: farmId === "" ? "00000000-0000-0000-0000-000000000001" : farmId,
    crop_name: formData.get("crop_name") as string || "Default",
    crop_stage: formData.get("crop_stage") as string || "mid",
    soil_type: formData.get("soil_type") as string || "Loam",
    area_acres: parseFloat(formData.get("area_acres") as string || "1"),
    irrigation_method: formData.get("irrigation_method") as string || "flood",
    rainfall_7day_mm: parseFloat(formData.get("rainfall_7day_mm") as string || "0"),
    rainfall_30day_mm: parseFloat(formData.get("rainfall_30day_mm") as string || "0"),
    temperature_avg_c: parseFloat(formData.get("temperature_avg_c") as string || "28"),
  };

  try {
    const backendUrl = process.env.BACKEND_URL || "http://farmops-backend-dev:8000";
    const resp = await fetch(`${backendUrl}/api/v1/farm/irrigation`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) throw new Error(`Backend error: ${resp.status}`);
    const result = await resp.json() as { success: boolean; data: IrrigationScheduleData };
    return json<ActionData>({ success: true, data: result.data });
  } catch (err) {
    return json<ActionData>({
      success: false,
      error: err instanceof Error ? err.message : "Failed to generate schedule",
    });
  }
}

export default function FarmIrrigation() {
  const { farmId, farmName } = useLoaderData<typeof loader>();
  const actionData = useActionData<typeof action>();
  const navigation = useNavigation();
  const [searchParams] = useSearchParams();
  const isLoading = navigation.state === "submitting";

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50">
      {/* Nav */}
      <nav className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-green-600 hover:text-green-700 text-sm">← Home</Link>
            <span className="text-gray-300">/</span>
            <Link to={`/farm/${farmId}/snapshot?${searchParams.toString()}`} className="text-green-600 hover:text-green-700 text-sm">← Snapshot</Link>
            <span className="text-gray-300">/</span>
            <span className="text-gray-800 font-semibold text-sm">{farmName} — Irrigation</span>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <Link to={`/farm/${farmId}/snapshot?${searchParams.toString()}`} className="text-sm text-blue-600 hover:text-blue-700">📸 Snapshot</Link>
            <Link to={`/farm/${farmId}/recommendations?${searchParams.toString()}`} className="text-sm text-blue-600 hover:text-blue-700">🌱 Crops</Link>
            <Link to={`/farm/${farmId}/harvest?${searchParams.toString()}`} className="text-sm text-blue-600 hover:text-blue-700">🚜 Harvest</Link>
            <Link to={`/farm/${farmId}/subsidies?${searchParams.toString()}`} className="text-sm text-blue-600 hover:text-blue-700">🏛️ Subsidies</Link>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">💧 Irrigation Scheduling</h1>
          <p className="text-gray-600 text-sm mt-1">
            14-day smart calendar — skips irrigation when rain probability exceeds 70%
          </p>
        </div>

        {/* Input form */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6">
          <h2 className="font-semibold text-gray-800 mb-4">Farm Details</h2>
          <Form method="post" className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Crop</label>
                <select name="crop_name" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  {CROPS.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Growth Stage</label>
                <select name="crop_stage" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  {STAGES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Soil Type</label>
                <select name="soil_type" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  {SOIL_TYPES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Irrigation Method</label>
                <select name="irrigation_method" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  {METHODS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Area (acres)</label>
                <input type="number" name="area_acres" defaultValue="1" min="0.1" step="0.1" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Avg Temperature (°C)</label>
                <input type="number" name="temperature_avg_c" defaultValue="28" min="10" max="50" step="0.5" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rainfall last 7 days (mm)</label>
                <input type="number" name="rainfall_7day_mm" defaultValue="0" min="0" step="1" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rainfall last 30 days (mm)</label>
                <input type="number" name="rainfall_30day_mm" defaultValue="0" min="0" step="5" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-2.5 rounded-lg text-sm transition-colors"
            >
              {isLoading ? "Generating schedule…" : "Generate 14-Day Schedule 💧"}
            </button>
          </Form>
        </div>

        {/* Results */}
        {actionData?.error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 text-red-700 text-sm">
            ⚠️ {actionData.error}
          </div>
        )}
        {actionData?.success && actionData.data && (
          <IrrigationScheduleCard schedule={actionData.data} />
        )}
      </main>
    </div>
  );
}
