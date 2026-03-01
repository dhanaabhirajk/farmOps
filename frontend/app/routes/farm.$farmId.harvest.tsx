/**
 * Harvest Timing Route (stub)
 * Optimal harvest window and sell-vs-store decision — coming soon.
 */

import type { LoaderFunctionArgs, MetaFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { Link, useLoaderData, useSearchParams } from "@remix-run/react";

export const meta: MetaFunction = () => [
  { title: "Harvest Timing - FarmOps" },
];

export async function loader({ params, request }: LoaderFunctionArgs) {
  const farmId = params.farmId ?? "";
  const url = new URL(request.url);
  const farmName = url.searchParams.get("farm_name") ?? "Your Farm";
  return json({ farmId, farmName });
}

export default function FarmHarvest() {
  const { farmId, farmName } = useLoaderData<typeof loader>();
  const [searchParams] = useSearchParams();

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-50">
      {/* Nav */}
      <nav className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-green-600 hover:text-green-700 text-sm">← Home</Link>
            <span className="text-gray-300">/</span>
            <Link
              to={`/farm/${farmId}/snapshot?${searchParams.toString()}`}
              className="text-green-600 hover:text-green-700 text-sm"
            >
              ← Snapshot
            </Link>
            <span className="text-gray-300">/</span>
            <span className="text-gray-800 font-semibold text-sm">{farmName} — Harvest</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to={`/farm/${farmId}/snapshot?${searchParams.toString()}`} className="text-sm text-blue-600 hover:text-blue-700">📸 Snapshot</Link>
            <Link to={`/farm/${farmId}/recommendations?${searchParams.toString()}`} className="text-sm text-blue-600 hover:text-blue-700">🌱 Crop Recs</Link>
            <Link to={`/farm/${farmId}/irrigation?${searchParams.toString()}`} className="text-sm text-blue-600 hover:text-blue-700">💧 Irrigation</Link>
          </div>
        </div>
      </nav>

      {/* Coming soon */}
      <main className="max-w-2xl mx-auto px-4 py-24 text-center">
        <div className="text-6xl mb-6">🚜</div>
        <h1 className="text-3xl font-bold text-gray-900 mb-3">Harvest Timing</h1>
        <p className="text-gray-600 mb-2">
          Optimal harvest window and sell-vs-store decision based on crop maturity,
          weather windows, and mandi price forecasts.
        </p>
        <p className="text-sm text-amber-600 font-medium mb-8">Coming soon in the next sprint.</p>
        <div className="flex justify-center gap-3">
          <Link
            to={`/farm/${farmId}/snapshot?${searchParams.toString()}`}
            className="px-5 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
          >
            ← Back to Snapshot
          </Link>
          <Link
            to="/"
            className="px-5 py-2.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200"
          >
            Home
          </Link>
        </div>
      </main>
    </div>
  );
}
