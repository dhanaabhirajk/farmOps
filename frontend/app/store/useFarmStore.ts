import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { FarmState, Crop, FarmLocation, UserSettings, Farm, InventoryItem } from '~/types';

interface FarmStore extends FarmState {
  setSettings: (settings: Partial<UserSettings>) => void;
  
  // Farm Management
  setFarms: (farms: Farm[]) => void; // New: Initialize from backend
  addFarm: (farm: Farm) => void;
  removeFarm: (id: string) => void;
  selectFarm: (id: string) => void;
  updateFarm: (id: string, updates: Partial<Farm>) => void;
  
  // Current Farm Actions (helpers)
  setSketch: (dataUrl: string, acres: number) => void;
  setEnhancedSketch: (url: string) => void;
  setLocation: (location: FarmLocation) => void;
  
  // Crop Management
  addCrop: (crop: Crop) => void;
  updateCrop: (id: string, updates: Partial<Crop>) => void;
  removeCrop: (id: string) => void;

  // Inventory Management
  addInventoryItem: (item: InventoryItem) => void;
  updateInventoryItem: (id: string, updates: Partial<InventoryItem>) => void;
  removeInventoryItem: (id: string) => void;
}

export const useFarmStore = create<FarmStore>()(
  persist(
    (set, get) => ({
  farms: [],
  selectedFarmId: null,
  settings: {
    language: 'en',
    currency: 'INR',
    unit: 'metric',
  },
  
  setSettings: (settings) => set((state) => ({ settings: { ...state.settings, ...settings } })),
  
  setFarms: (farms) => set({ farms, selectedFarmId: farms.length > 0 ? farms[0].id : null }),

  addFarm: (farm) => set((state) => ({ 
    farms: [...state.farms, farm],
    selectedFarmId: farm.id 
  })),
  
  removeFarm: (id) => set((state) => ({
    farms: state.farms.filter((f) => f.id !== id),
    selectedFarmId: state.selectedFarmId === id ? null : state.selectedFarmId,
  })),

  selectFarm: (id) => set({ selectedFarmId: id }),
  
  updateFarm: (id, updates) => set((state) => ({
    farms: state.farms.map((f) => (f.id === id ? { ...f, ...updates } : f))
  })),

  // Helper to update the currently selected farm
  setSketch: (dataUrl, acres) => {
    const { selectedFarmId, updateFarm } = get();
    if (selectedFarmId) {
      updateFarm(selectedFarmId, { sketchDataUrl: dataUrl, totalAcres: acres });
    }
  },

  setEnhancedSketch: (url) => {
    const { selectedFarmId, updateFarm } = get();
    if (selectedFarmId) {
      updateFarm(selectedFarmId, { enhancedSketchUrl: url });
    }
  },

  setLocation: (location) => {
    const { selectedFarmId, updateFarm } = get();
    if (selectedFarmId) {
      updateFarm(selectedFarmId, { location });
    }
  },

  addCrop: (crop) => set((state) => {
    const farm = state.farms.find(f => f.id === state.selectedFarmId);
    if (!farm) return state;
    return {
      farms: state.farms.map(f => 
        f.id === state.selectedFarmId 
          ? { ...f, crops: [...f.crops, crop] }
          : f
      )
    };
  }),

  updateCrop: (cropId, updates) => set((state) => {
    return {
      farms: state.farms.map(f => 
        f.id === state.selectedFarmId 
          ? { 
              ...f, 
              crops: f.crops.map(c => c.id === cropId ? { ...c, ...updates } : c)
            }
          : f
      )
    };
  }),

  removeCrop: (cropId) => set((state) => {
    return {
      farms: state.farms.map(f => 
        f.id === state.selectedFarmId 
          ? { ...f, crops: f.crops.filter(c => c.id !== cropId) }
          : f
      )
    };
  }),

  addInventoryItem: (item) => set((state) => {
    return {
      farms: state.farms.map(f => 
        f.id === state.selectedFarmId 
          ? { ...f, inventory: [...(f.inventory || []), item] }
          : f
      )
    };
  }),

  updateInventoryItem: (itemId, updates) => set((state) => {
    return {
      farms: state.farms.map(f => 
        f.id === state.selectedFarmId 
          ? { 
              ...f, 
              inventory: (f.inventory || []).map(i => i.id === itemId ? { ...i, ...updates } : i)
            }
          : f
      )
    };
  }),

  removeInventoryItem: (itemId) => set((state) => {
    return {
      farms: state.farms.map(f => 
        f.id === state.selectedFarmId 
          ? { ...f, inventory: (f.inventory || []).filter(i => i.id !== itemId) }
          : f
      )
    };
  }),
}),
  { name: 'farmops-store' }
  )
);
