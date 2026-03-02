import React from 'react';
import { 
  CloudSun, 
  Droplets, 
  TrendingUp, 
  Sprout, 
  AlertTriangle,
  Info,
  CheckCircle2,
  ArrowUpRight,
  Leaf
} from 'lucide-react';
import { format } from 'date-fns';
import { Area, AreaChart, ResponsiveContainer, Tooltip } from 'recharts';
import { cn } from '~/lib/utils'; // Assuming I'll create this util next

// Ported from new_sample_ui/src/components/Dashboard.tsx - SnapshotTab
// Modified to accept data as props instead of using mock data directly

interface SnapshotViewProps {
  farmData: any; // We can type this better based on the backend response later
}

export function SnapshotView({ farmData }: SnapshotViewProps) {
  const data = farmData;
  if (!data) return <div>Loading snapshot...</div>;

  return (
    <div className="space-y-6">
      {/* Top Action Card */}
      {data.topAction && (
        <div className="bg-gradient-to-r from-orange-50 to-orange-100 border border-orange-200 rounded-3xl p-6 flex flex-col md:flex-row gap-6 items-start md:items-center shadow-sm">
          <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center text-white shrink-0 shadow-md">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-bold text-orange-900 text-lg">{data.topAction.title}</h3>
              <span className="px-2 py-0.5 bg-orange-200 text-orange-800 text-[10px] font-bold uppercase rounded-full">
                Priority Action
              </span>
            </div>
            <p className="text-orange-800 mb-2">{data.topAction.reason}</p>
            <div className="flex items-center gap-4 text-xs text-orange-700/70">
              <span className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Confidence: {(data.topAction.confidence * 100).toFixed(0)}%</span>
              <span className="flex items-center gap-1"><Info className="w-3 h-3" /> Source: {data.topAction.source}</span>
            </div>
          </div>
          <button className="px-6 py-3 bg-orange-600 text-white rounded-xl font-semibold shadow-lg shadow-orange-600/20 hover:bg-orange-700 transition-all whitespace-nowrap">
            View Details
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Weather & Soil */}
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 space-y-6">
          {data.weather && (
            <div>
              <h3 className="font-serif font-bold text-gray-900 mb-4 flex items-center gap-2">
                <CloudSun className="w-5 h-5 text-green-600" /> Weather (7-Day)
              </h3>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <span className="text-4xl font-bold text-gray-900">{data.weather.current?.temp}°C</span>
                  <p className="text-sm text-gray-500">{data.weather.current?.condition}</p>
                </div>
                <div className="text-right text-sm text-gray-500">
                  <p>Hum: {data.weather.current?.humidity}%</p>
                  <p>Wind: {data.weather.current?.windSpeed} km/h</p>
                </div>
              </div>
              <div className="flex justify-between gap-2 overflow-x-auto pb-2">
                {data.weather.forecast?.slice(0, 5).map((day: any, i: number) => (
                  <div key={i} className="flex flex-col items-center min-w-[50px]">
                    <span className="text-xs text-gray-400 mb-1">{format(new Date(day.date), 'EEE')}</span>
                    {day.rainProb > 50 ? <Droplets className="w-6 h-6 text-blue-500 mb-1" /> : <CloudSun className="w-6 h-6 text-yellow-500 mb-1" />}
                    <span className="text-xs font-medium">{day.tempHigh}°</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {data.soil && (
            <div className="pt-6 border-t border-gray-100">
              <h3 className="font-serif font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Leaf className="w-5 h-5 text-green-600" /> Soil Profile
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Type</span>
                  <span className="font-medium text-gray-900">{data.soil.type}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Moisture</span>
                  <span className="font-medium text-gray-900">{(data.soil.moisture * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Nitrogen</span>
                  <span className="font-medium text-green-600">{data.soil.nitrogen}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* NDVI & Map */}
        {data.ndvi && (
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col">
            <h3 className="font-serif font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Sprout className="w-5 h-5 text-green-600" /> Crop Health (NDVI)
            </h3>
            <div className="h-40 w-full mb-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.ndvi.history.map((val: number, i: number) => ({ day: i, val }))}>
                  <defs>
                    <linearGradient id="colorNdvi" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2D5A27" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#2D5A27" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Tooltip />
                  <Area type="monotone" dataKey="val" stroke="#2D5A27" fillOpacity={1} fill="url(#colorNdvi)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-between items-center mb-6">
              <span className="text-sm text-gray-500">Current Score</span>
              <span className="text-2xl font-bold text-green-700">{data.ndvi.current}</span>
            </div>
            
            <div className="flex-1 rounded-xl overflow-hidden relative bg-gray-100 min-h-[150px]">
              {data.sketchUrl ? (
                 <img 
                  src={data.sketchUrl} 
                  alt="Farm Map" 
                  className="w-full h-full object-cover absolute inset-0"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <Sprout className="w-8 h-8 opacity-20" />
                </div>
              )}
              <div className="absolute bottom-2 left-2 bg-white/90 backdrop-blur px-2 py-1 rounded text-xs font-medium">
                {data.area?.acres} Acres
              </div>
            </div>
          </div>
        )}

        {/* Market Prices */}
        {data.market && (
          <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-serif font-bold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" /> Market Prices
            </h3>
            <p className="text-xs text-gray-500 mb-4">Nearest: {data.market.nearestMandi} ({data.market.distanceKm}km)</p>
            
            <div className="space-y-4">
              {data.market.commodities.map((item: any, i: number) => (
                <div key={i} className="p-4 bg-gray-50 rounded-2xl flex justify-between items-center">
                  <div>
                    <p className="font-medium text-gray-900">{item.name}</p>
                    <p className="text-xs text-gray-500">per {item.unit}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900">₹{item.price}</p>
                    <p className={cn("text-xs flex items-center justify-end gap-1", item.trend === 'up' ? "text-green-600" : "text-gray-500")}>
                      {item.trend === 'up' ? <ArrowUpRight className="w-3 h-3" /> : null}
                      {item.trend === 'up' ? 'Rising' : 'Stable'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-6 p-4 bg-blue-50 rounded-2xl">
              <h4 className="font-bold text-blue-900 text-sm mb-1">Price Prediction</h4>
              <p className="text-xs text-blue-800">Paddy prices expected to rise by 5-8% in next 15 days due to procurement demand.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
