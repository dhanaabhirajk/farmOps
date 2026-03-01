import type { MetaFunction } from "@remix-run/node";
import { Link } from "@remix-run/react";
import { Button } from "~/components/ui/Button";

export const meta: MetaFunction = () => {
  return [
    { title: "FarmOps - Agricultural Insights for Tamil Nadu Farmers" },
    {
      name: "description",
      content: "AI-powered crop recommendations, farm snapshots, and irrigation scheduling",
    },
  ];
};

export default function Home() {
  const testFarms = [
    {
      id: "00000000-0000-0000-0000-000000000001",
      name: "Thanjavur Farm (Rice Belt)",
      district: "Thanjavur",
      description: "Sample rice cultivation farm",
    },
    {
      id: "00000000-0000-0000-0000-000000000002",
      name: "Coimbatore Farm (Dry Land)",
      district: "Coimbatore",
      description: "Sample cotton and maize farm",
    },
    {
      id: "00000000-0000-0000-0000-000000000003",
      name: "Madurai Farm (Sugarcane)",
      district: "Madurai",
      description: "Sample sugarcane cultivation farm",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-green-600">🌾 FarmOps</h1>
            <p className="text-gray-600 text-sm">Location-Based Insights Engine</p>
          </div>
        </div>
      </nav>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid md:grid-cols-2 gap-8 items-center">
          <div>
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              AI-Powered Agricultural Insights
            </h2>
            <p className="text-xl text-gray-700 mb-6">
              Get instant farm snapshots, crop recommendations, and irrigation schedules
              powered by AI and real-time data.
            </p>

            <div className="space-y-4 mb-8">
              <div className="flex items-start gap-3">
                <span className="text-2xl">📸</span>
                <div>
                  <h3 className="font-semibold text-gray-900">Farm Snapshot</h3>
                  <p className="text-gray-600">
                    Instant analysis of soil, weather, NDVI trends, and market prices
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <span className="text-2xl">🌱</span>
                <div>
                  <h3 className="font-semibold text-gray-900">Crop Recommendations</h3>
                  <p className="text-gray-600">
                    AI-ranked crop suggestions with yield, profit, and risk analysis
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <span className="text-2xl">💧</span>
                <div>
                  <h3 className="font-semibold text-gray-900">Irrigation Scheduling</h3>
                  <p className="text-gray-600">
                    Smart irrigation calendar that respects soil moisture and weather
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="aspect-square bg-gradient-to-br from-green-100 to-blue-100 rounded-lg flex items-center justify-center">
              <p className="text-6xl">🚜</p>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white py-12 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">Select a Farm to Get Started</h2>

          <div className="grid md:grid-cols-3 gap-6">
            {testFarms.map((farm) => (
              <div
                key={farm.id}
                className="bg-gray-50 border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
              >
                <div className="mb-4">
                  <p className="text-sm text-gray-500 uppercase tracking-wide">{farm.district}</p>
                  <h3 className="text-xl font-semibold text-gray-900 mt-1">{farm.name}</h3>
                </div>

                <p className="text-gray-600 mb-6">{farm.description}</p>

                <div className="space-y-2">
                  <Link to={`/farm/${farm.id}/recommendations`} className="block">
                    <Button className="w-full bg-blue-600 hover:bg-blue-700">
                      Get Crop Recommendations
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-8">
          <h3 className="text-xl font-semibold text-blue-900 mb-4">📋 About FarmOps</h3>
          <p className="text-blue-800 mb-4">
            FarmOps is an AI-powered platform designed specifically for Tamil Nadu farmers.
            It provides location-based insights to help farmers make data-driven decisions about:
          </p>
          <ul className="text-blue-800 space-y-2 list-disc list-inside">
            <li>What crops to plant based on soil, climate, and market conditions</li>
            <li>When to plant within optimal planting windows</li>
            <li>How to manage irrigation efficiently</li>
            <li>Current market prices for various commodities</li>
            <li>Risk assessment and mitigation strategies</li>
          </ul>
        </div>
      </section>

      <footer className="bg-gray-900 text-white py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-400">
            FarmOps v0.1.0 • Location-Based Insights Engine for Tamil Nadu Farmers
          </p>
        </div>
      </footer>
    </div>
  );
}
