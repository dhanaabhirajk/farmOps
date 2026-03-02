import React from 'react';
import { useOutletContext } from '@remix-run/react';
import { Leaf, Sprout } from 'lucide-react';
import { cn } from '~/lib/utils'; // Use our Remix util

export default function PlanningRoute() {
  const { farmData } = useOutletContext<{ farmData: any }>();
  const recommendations = farmData?.recommendations || [];

  // TODO: Use real crops from farmData when available
  const activeCrops = farmData?.crops || []; 

  return (
    <div className="space-y-8">
      {/* Active Crops Section */}
      <div className="space-y-6">
        <h2 className="font-serif font-bold text-xl flex items-center gap-2">
            <Leaf className="w-5 h-5 text-farm-green" /> Crop Planning
        </h2>
        
        {activeCrops.length === 0 ? (
          <div className="p-8 bg-white rounded-3xl border border-gray-100 text-center">
            <Sprout className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No active crops planned yet.</p>
          </div>
        ) : (
          <div>{/* Active crops list would go here */}</div>
        )}
      </div>

      {/* Recommendations Section */}
      <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
        <h2 className="font-serif font-bold text-xl mb-2">New Planting Recommendations</h2>
        <p className="text-gray-500 text-sm mb-6">Based on your soil and season.</p>
        
        {recommendations.length === 0 ? (
          <p className="text-gray-500 italic">No recommendations available from backend yet.</p>
        ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {recommendations.map((rec: any, i: number) => (
            <div key={rec.id} className="border border-gray-200 rounded-2xl p-5 hover:shadow-md transition-shadow relative overflow-hidden group">
              {i === 0 && (
                <div className="absolute top-0 right-0 bg-farm-green text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl">
                  TOP PICK
                </div>
              )}
              
              <div className="flex justify-between items-start mb-4">
                <h3 className="font-bold text-lg text-gray-900">{rec.crop}</h3>
                <div className="text-right">
                  <span className={cn(
                    "text-xs font-bold px-2 py-1 rounded-full",
                    rec.riskScore < 0.3 ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
                  )}>
                    {rec.riskScore < 0.3 ? "Low Risk" : "Medium Risk"}
                  </span>
                </div>
              </div>
              
              <p className="text-sm text-gray-600 mb-4 min-h-[40px]">{rec.reason}</p>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-gray-50 p-3 rounded-xl">
                  <p className="text-xs text-gray-500">Est. Profit</p>
                  <p className="font-bold text-farm-green">{rec.metrics.profit}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-xl">
                  <p className="text-xs text-gray-500">Duration</p>
                  <p className="font-bold text-gray-900">{rec.metrics.duration}</p>
                </div>
              </div>
              
              <button 
                className="w-full py-2 border border-farm-green text-farm-green rounded-xl font-medium hover:bg-farm-green hover:text-white transition-colors"
                onClick={() => alert("Implementation coming soon: Select plan via API")}
              >
                Select Plan
              </button>
            </div>
          ))}
        </div>
        )}
      </div>
    </div>
  );
}
