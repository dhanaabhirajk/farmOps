import type { MetaFunction } from "@remix-run/node";
import { useNavigate } from "@remix-run/react";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Leaf,
  PlusCircle,
  ChevronRight,
  TrendingUp,
  Sprout,
  Droplets,
  IndianRupee,
  MapPin,
  Trash2,
} from "lucide-react";
import { useFarmStore } from "~/store/useFarmStore";

export const meta: MetaFunction = () => [
  { title: "FarmOps — AI Insights for Tamil Nadu Farmers" },
  { name: "description", content: "AI-powered crop insights for Tamil Nadu farmers." },
];

export default function Home() {
  const navigate = useNavigate();
  const [farms, setFarms] = useState<ReturnType<typeof useFarmStore.getState>["farms"]>([]);

  // SSR-safe hydration — only read localStorage on client
  useEffect(() => {
    setFarms(useFarmStore.getState().farms);
    return useFarmStore.subscribe((s) => setFarms([...s.farms]));
  }, []);

  const removeFarm = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    useFarmStore.getState().removeFarm?.(id);
  };

  const openFarm = (f: (typeof farms)[0]) =>
    navigate(
      `/farm/${f.id}/snapshot?farm_name=${encodeURIComponent(f.name)}&area_acres=${f.totalAcres ?? 0}&district=${encodeURIComponent(f.location?.city ?? "Unknown")}&lat=${f.location?.lat ?? 0}&lon=${f.location?.lng ?? 0}`
    );

  return (
    <div className="min-h-screen bg-cream font-sans text-gray-900 flex flex-col">
      {/* ── Navbar */}
      <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-100 sticky top-0 z-20">
        <div className="max-w-2xl mx-auto px-5 sm:px-8 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-farm-green rounded-lg flex items-center justify-center">
              <Leaf className="w-4 h-4 text-white" />
            </div>
            <span className="font-serif text-xl font-bold text-farm-green">FarmOps</span>
          </div>
          <span className="text-xs text-gray-400 hidden sm:block tracking-wide uppercase">
            Mistral AI · Tamil Nadu
          </span>
        </div>
      </nav>

      <div className="flex-1 max-w-2xl mx-auto w-full px-5 sm:px-8 pt-12 pb-16">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="mb-10"
        >
          <h1 className="font-serif text-4xl sm:text-5xl font-bold text-gray-900 leading-tight mb-3">
            Farm insights,<br />
            <span className="text-farm-green">rooted in data.</span>
          </h1>
          <p className="text-gray-500 leading-relaxed max-w-md">
            Get live soil analysis, mandi prices, satellite NDVI and AI recommendations —
            specific to your land.
          </p>
        </motion.div>

        {/* ── My Farms list */}
        {farms.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="mb-8"
          >
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
              My Farms
            </p>
            <div className="space-y-2.5">
              {farms.map((f, i) => (
                <motion.button
                  key={f.id}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06 }}
                  onClick={() => openFarm(f)}
                  className="w-full flex items-center justify-between bg-white rounded-2xl border border-gray-100 px-5 py-4 shadow-sm hover:shadow-md hover:border-farm-green/30 hover:-translate-y-0.5 transition-all group text-left"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-farm-green/10 rounded-xl flex items-center justify-center shrink-0">
                      <Sprout className="w-5 h-5 text-farm-green" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900 group-hover:text-farm-green transition-colors">
                        {f.name}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
                        {f.location?.city && (
                          <><MapPin className="w-3 h-3" />{f.location.city} · </>
                        )}
                        {f.totalAcres ? `${f.totalAcres} acres` : "Area not set"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      role="button"
                      tabIndex={0}
                      onClick={(e) => { e.stopPropagation(); useFarmStore.getState().removeFarm?.(f.id); }}
                      onKeyDown={(e) => { if (e.key === 'Enter') { e.stopPropagation(); useFarmStore.getState().removeFarm?.(f.id); } }}
                      className="p-1.5 rounded-lg text-gray-300 hover:text-red-400 hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100 cursor-pointer"
                      title="Remove farm"
                    >
                      <Trash2 className="w-4 h-4" />
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-farm-green transition-colors" />
                  </div>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}

        {/* ── Create New Farm CTA */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <button
            onClick={() => navigate("/sketch")}
            className="w-full flex items-center justify-between bg-farm-green text-white rounded-2xl px-6 py-5 shadow-lg shadow-farm-green/20 hover:bg-green-800 active:scale-[0.98] transition-all group"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-white/15 rounded-xl flex items-center justify-center">
                <PlusCircle className="w-5 h-5" />
              </div>
              <div className="text-left">
                <p className="font-semibold text-base">Create New Farm</p>
                <p className="text-white/70 text-xs mt-0.5">Draw boundary → set location → analyse</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-white/60 group-hover:translate-x-1 transition-transform" />
          </button>
        </motion.div>

        {/* ── Feature pills */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-3"
        >
          {[
            { icon: TrendingUp, label: "NDVI Snapshot" },
            { icon: Sprout,     label: "Crop Recs" },
            { icon: Droplets,   label: "Irrigation" },
            { icon: IndianRupee, label: "Mandi Prices" },
          ].map(({ icon: Icon, label }) => (
            <div
              key={label}
              className="bg-white rounded-2xl border border-gray-100 p-4 flex flex-col items-center gap-2 text-center shadow-sm"
            >
              <div className="w-9 h-9 bg-farm-green/10 rounded-xl flex items-center justify-center">
                <Icon className="w-5 h-5 text-farm-green" />
              </div>
              <p className="text-xs font-semibold text-gray-700">{label}</p>
            </div>
          ))}
        </motion.div>
      </div>

      {/* ── Footer */}
      <footer className="border-t border-gray-100 py-6">
        <div className="max-w-2xl mx-auto px-5 sm:px-8 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-farm-green rounded-md flex items-center justify-center">
              <Leaf className="w-2.5 h-2.5 text-white" />
            </div>
            <span className="font-serif font-bold text-farm-green text-sm">FarmOps</span>
          </div>
          <p className="text-xs text-gray-400">Remix · FastAPI · Mistral AI</p>
        </div>
      </footer>
    </div>
  );
}
