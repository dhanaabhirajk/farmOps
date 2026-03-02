import { json, type LoaderFunctionArgs } from "@remix-run/node";
import { 
  Outlet, 
  useLoaderData, 
  useLocation, 
  useNavigate, 
  NavLink,
  Link
} from "@remix-run/react";
import { useEffect, useState } from "react";
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
import { fetchFarmSnapshot } from "~/utils/api";

// This layout replaces the Dashboard component from the new UI
// It provides the Sidebar and Header, and renders child routes (tabs) via Outlet

export async function loader({ params }: LoaderFunctionArgs) {
  const farmId = params.farmId;
  if (!farmId) throw new Error("Farm ID is required");

  // Fetch real data from the API
  // In a real implementation, we would probably fetch the list of farms here too
  // for the switcher. For now, we'll mock the list but fetch the current farm details.
  
  try {
    const snapshot = await fetchFarmSnapshot(farmId);
    return json({ 
      farmData: snapshot.data, 
      farmId,
      error: null 
    });
  } catch (error) {
    console.error("Failed to fetch farm data", error);
    // Return mock fallback or error state if API fails (for development robustness)
    return json({ 
      farmData: null, 
      farmId,
      error: "Failed to load farm data" 
    });
  }
}

export default function FarmDashboardLayout() {
  const { farmData, farmId, error } = useLoaderData<typeof loader>();
  const location = useLocation();
  const navigate = useNavigate();
  
  const { 
    farms, 
    selectedFarmId, 
    selectFarm, 
    setFarms, 
    addFarm 
  } = useFarmStore();
  
  const [isFarmMenuOpen, setIsFarmMenuOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Initialize store with loaded data
  useEffect(() => {
    if (farmData) {
      // If we have data, ensure it's in the store
      // Logic to merge or set farm data in Zustand
      // For now, we'll just ensure the farm exists in the list
      const existing = farms.find(f => f.id === farmId);
      if (!existing) {
        addFarm({
            id: farmId || 'unknown',
            name: farmData.name || 'My Farm',
            location: {
                lat: farmData.centroid?.coordinates[1],
                lng: farmData.centroid?.coordinates[0],
                city: farmData.district
            },
            totalAcres: farmData.area_acres || 0,
            crops: [], // Would need to fetch these too
            inventory: []
        });
      }
      selectFarm(farmId || '');
    }
  }, [farmData, farmId, addFarm, selectFarm, farms]);

  const selectedFarm = farms.find(f => f.id === (selectedFarmId || farmId));
  const activeSegment = location.pathname.split("/").pop(); // 'snapshot', 'planning', etc.

  return (
    <div className="min-h-screen bg-cream pb-20 md:pb-0 md:pl-20">
      {/* Mobile Nav */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 p-2 flex justify-around md:hidden z-50">
        <NavButton to="snapshot" icon={TrendingUp} label="Snapshot" active={activeSegment === 'snapshot'} />
        <NavButton to="planning" icon={Sprout} label="Crops" active={activeSegment === 'planning'} />
        <NavButton to="inventory" icon={Package} label="Stock" active={activeSegment === 'inventory'} />
        <NavButton to="irrigation" icon={Droplets} label="Water" active={activeSegment === 'irrigation'} />
        <NavButton to="schemes" icon={IndianRupee} label="Schemes" active={activeSegment === 'schemes'} />
        <NavButton to="settings" icon={Settings} label="Settings" active={false} onClick={() => setIsSettingsOpen(true)} />
      </div>

      {/* Desktop Nav */}
      <div className="hidden md:flex fixed top-0 bottom-0 left-0 w-20 bg-white border-r border-gray-100 flex-col items-center py-8 z-50">
        <Link to="/" className="w-10 h-10 bg-farm-green rounded-xl flex items-center justify-center text-white mb-8">
          <Leaf className="w-6 h-6" />
        </Link>
        <div className="flex flex-col gap-4 w-full">
          <NavButton to="snapshot" icon={TrendingUp} label="Snapshot" active={activeSegment === 'snapshot'} desktop />
          <NavButton to="planning" icon={Sprout} label="Crops" active={activeSegment === 'planning'} desktop />
          <NavButton to="inventory" icon={Package} label="Stock" active={activeSegment === 'inventory'} desktop />
          <NavButton to="irrigation" icon={Droplets} label="Water" active={activeSegment === 'irrigation'} desktop />
          <NavButton to="schemes" icon={IndianRupee} label="Schemes" active={activeSegment === 'schemes'} desktop />
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
                {selectedFarm?.name || farmData?.name || 'My Farm'}
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
                          navigate(`/farm/${farm.id}/snapshot`);
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
                      className="w-full text-left px-3 py-2 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2"
                    >
                      <Pencil className="w-4 h-4" />
                      Redraw Layout
                    </button>
                    <button
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
              <MapPin className="w-3 h-3" /> {selectedFarm?.location?.city || farmData?.district || 'Unknown Location'}
            </p>
          </div>
          <button 
            onClick={() => setIsSettingsOpen(true)}
            className="w-10 h-10 rounded-full bg-gray-200 overflow-hidden border-2 border-white shadow-sm hover:ring-2 hover:ring-farm-green transition-all"
          >
            <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedFarm?.id || 'farmer'}`} alt="Profile" />
          </button>
        </header>

        {error ? (
           <div className="bg-red-50 p-4 rounded-xl text-red-500">
             Error: {error}. Is the backend running?
           </div>
        ) : (
           <Outlet context={{ farmData }} />
        )}
      </main>

      {/* Settings Modal would go here */}
    </div>
  );
}

function NavButton({ to, icon: Icon, label, active, desktop, onClick }: any) {
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
      to={to}
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
