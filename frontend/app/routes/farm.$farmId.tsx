import { json, type LoaderFunctionArgs } from "@remix-run/node";
import { 
  Outlet, 
  useLoaderData, 
  useLocation, 
  useNavigate, 
  NavLink,
  Link,
  useSearchParams
} from "@remix-run/react";
import { useEffect, useRef, useState } from "react";
import { 
  TrendingUp, 
  Sprout, 
  Package, 
  Droplets, 
  IndianRupee, 
  Settings, 
  Leaf, 
  ChevronDown, 
  CheckCircle2, 
  Pencil, 
  PlusCircle, 
  MapPin 
} from "lucide-react";
import { cn } from "~/lib/utils";
import { useFarmStore } from "~/store/useFarmStore";

// This layout replaces the Dashboard component from the new UI
// It provides the Sidebar and Header, and renders child routes (tabs) via Outlet

export async function loader({ params, request }: LoaderFunctionArgs) {
  const farmId = params.farmId;
  if (!farmId) throw new Error("Farm ID is required");

  const url = new URL(request.url);
  const farmName = url.searchParams.get("farm_name") ?? null;
  const district  = url.searchParams.get("district")  ?? null;
  const mainCrop  = url.searchParams.get("main_crop") ?? null;
  const areaAcres = parseFloat(url.searchParams.get("area_acres") ?? "0") || null;
  const lat       = parseFloat(url.searchParams.get("lat") ?? "0") || null;
  const lon       = parseFloat(url.searchParams.get("lon") ?? "0") || null;

  return json({ farmId, farmName, district, mainCrop, areaAcres, lat, lon, error: null });
}

export default function FarmDashboardLayout() {
  const { farmId, farmName, district, mainCrop, areaAcres, lat, lon, error } = useLoaderData<typeof loader>();
  const location = useLocation();
  const navigate = useNavigate();
  
  const { 
    farms, 
    selectedFarmId, 
    selectFarm, 
    addFarm 
  } = useFarmStore();
  
  const [isFarmMenuOpen, setIsFarmMenuOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const initialized = useRef(false);

  // Add this farm to the store once, using URL params for the real name
  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    const existing = useFarmStore.getState().farms.find(f => f.id === farmId);
    if (!existing) {
      addFarm({
        id: farmId || 'unknown',
        name: farmName || (district ? `${district} Farm` : 'My Farm'),
        location: {
          lat: lat ?? 0,
          lng: lon ?? 0,
          city: district ?? 'Unknown',
        },
        totalAcres: areaAcres ?? 0,
        crops: [],
        inventory: [],
      });
    }
    selectFarm(farmId || '');
  }, [farmId]); // only run when farmId changes

  const selectedFarm = farms.find(f => f.id === (selectedFarmId || farmId));
  const activeSegment = location.pathname.split("/").pop();
  const [searchParams] = useSearchParams();

  // Build a query string that preserves farm identity params across tab switches.
  // Strips use_cache=false so navigating tabs never forces an LLM re-run.
  const farmParams = (() => {
    const p = new URLSearchParams(searchParams);
    p.delete("use_cache");
    const qs = p.toString();
    return qs ? `?${qs}` : "";
  })();

  return (
    <div className="min-h-screen bg-cream pb-20 md:pb-0 md:pl-20">
      {/* Mobile Nav */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 p-2 flex justify-around md:hidden z-50">
        <NavButton to="snapshot" farmParams={farmParams} icon={TrendingUp} label="Snapshot" active={activeSegment === 'snapshot'} />
        <NavButton to="planning" farmParams={farmParams} icon={Sprout} label="Crops" active={activeSegment === 'planning'} />
        <NavButton to="inventory" farmParams={farmParams} icon={Package} label="Stock" active={activeSegment === 'inventory'} />
        <NavButton to="schemes" farmParams={farmParams} icon={IndianRupee} label="Schemes" active={activeSegment === 'schemes'} />
        <NavButton to="settings" farmParams={farmParams} icon={Settings} label="Settings" active={false} onClick={() => setIsSettingsOpen(true)} />
      </div>

      {/* Desktop Nav */}
      <div className="hidden md:flex fixed top-0 bottom-0 left-0 w-20 bg-white border-r border-gray-100 flex-col items-center py-8 z-50">
        <Link to="/" className="w-10 h-10 bg-farm-green rounded-xl flex items-center justify-center text-white mb-8">
          <Leaf className="w-6 h-6" />
        </Link>
        <div className="flex flex-col gap-4 w-full">
          <NavButton to="snapshot" farmParams={farmParams} icon={TrendingUp} label="Snapshot" active={activeSegment === 'snapshot'} desktop />
          <NavButton to="planning" farmParams={farmParams} icon={Sprout} label="Crops" active={activeSegment === 'planning'} desktop />
          <NavButton to="inventory" farmParams={farmParams} icon={Package} label="Stock" active={activeSegment === 'inventory'} desktop />
          <NavButton to="schemes" farmParams={farmParams} icon={IndianRupee} label="Schemes" active={activeSegment === 'schemes'} desktop />
          <div className="mt-auto">
            <button 
              onClick={() => setIsSettingsOpen(true)}
              className="flex flex-col items-center justify-center gap-1 p-2 rounded-xl transition-all text-gray-400 hover:text-gray-600 w-16 h-16"
            >
              <Settings className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>

      <main className="p-6 max-w-7xl mx-auto">
        <header className="flex justify-between items-center mb-8">
          <div>
            <div className="relative">
              <button 
                onClick={() => setIsFarmMenuOpen(!isFarmMenuOpen)}
                className="flex items-center gap-2 text-2xl font-serif font-bold text-gray-900 hover:text-farm-green transition-colors"
              >
                {selectedFarm?.name || farmName || 'My Farm'}
                <ChevronDown className="w-5 h-5 text-gray-400" />
              </button>
              
              {isFarmMenuOpen && (
                <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden z-50">
                  <div className="p-2">
                    <p className="text-xs font-bold text-gray-400 uppercase px-3 py-2">Switch Farm</p>
                    {farms.map(farm => (
                      <button
                        key={farm.id}
                        onClick={() => {
                          selectFarm(farm.id);
                          setIsFarmMenuOpen(false);
                          // Keep the same tab but switch farm, preserving search params
                          navigate(`/farm/${farm.id}/${activeSegment ?? 'snapshot'}${farmParams}`);
                        }}
                        className={cn(
                          "w-full text-left px-3 py-2 rounded-xl text-sm font-medium transition-colors flex items-center justify-between",
                          selectedFarmId === farm.id ? "bg-farm-green/10 text-farm-green" : "hover:bg-gray-50 text-gray-700"
                        )}
                      >
                        {farm.name}
                        {selectedFarmId === farm.id && <CheckCircle2 className="w-4 h-4" />}
                      </button>
                    ))}
                    <div className="h-px bg-gray-100 my-2" />
                    <button
                      onClick={() => { setIsFarmMenuOpen(false); navigate(`/sketch?farm_id=${farmId}`); }}
                      className="w-full text-left px-3 py-2 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2"
                    >
                      <Pencil className="w-4 h-4" />
                      Redraw Layout
                    </button>
                    <button
                      onClick={() => { setIsFarmMenuOpen(false); navigate('/'); }}
                      className="w-full text-left px-3 py-2 rounded-xl text-sm font-medium text-farm-green hover:bg-farm-green/5 transition-colors flex items-center gap-2"
                    >
                      <PlusCircle className="w-4 h-4" />
                      Add New Farm
                    </button>
                  </div>
                </div>
              )}
            </div>
            <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
              <MapPin className="w-3 h-3" /> {selectedFarm?.location?.city || district || 'Unknown Location'}
            </p>
          </div>
          <button 
            onClick={() => setIsSettingsOpen(true)}
            className="w-10 h-10 rounded-full bg-gray-200 overflow-hidden border-2 border-white shadow-sm hover:ring-2 hover:ring-farm-green transition-all"
          >
            <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedFarm?.id || 'farmer'}`} alt="Profile" />
          </button>
        </header>

        <Outlet context={{ farmId, farmName, district, mainCrop, areaAcres, lat, lon }} />
      </main>

      {/* Settings Modal would go here */}
    </div>
  );
}

function NavButton({ to, farmParams = "", icon: Icon, label, active, desktop, onClick }: any) {
  if (onClick) {
     return (
        <button
          onClick={onClick}
          className={cn(
            "flex flex-col items-center justify-center gap-1 p-2 rounded-xl transition-all",
            active ? "text-farm-green bg-farm-green/5" : "text-gray-400 hover:text-gray-600",
            desktop && "w-16 h-16"
          )}
        >
          <Icon className={cn("w-6 h-6", active && "fill-current")} />
          {!desktop && <span className="text-[10px] font-medium">{label}</span>}
        </button>
     );
  }
  return (
    <NavLink
      to={`${to}${farmParams}`}
      className={({ isActive }) => cn(
        "flex flex-col items-center justify-center gap-1 p-2 rounded-xl transition-all",
        isActive ? "text-farm-green bg-farm-green/5" : "text-gray-400 hover:text-gray-600",
        desktop && "w-16 h-16"
      )}
    >
      <Icon className={cn("w-6 h-6", active && "fill-current")} />
      {!desktop && <span className="text-[10px] font-medium">{label}</span>}
    </NavLink>
  );
}
