// Ported from new_sample_ui/src/types.ts

export interface Crop {
  id: string;
  name: string;
  type: 'existing' | 'new';
  plantedDate?: Date;
  acres: number;
  status: 'growing' | 'harvested' | 'planned';
  imageUrl?: string;
  predictedHarvestDate?: Date;
  predictedPrice?: number;
  expenses: number;
  // New fields for intercropping and rotation
  interCrops?: string[]; // Names of crops growing alongside
  rotationSuggestion?: string; // Suggested next crop
  rotationReason?: string;
}

export interface InventoryItem {
  id: string;
  name: string;
  category: 'seed' | 'fertilizer' | 'harvest' | 'equipment';
  quantity: number;
  unit: string;
  location?: string;
  expiryDate?: Date;
  notes?: string;
}

export interface FarmLocation {
  lat: number;
  lng: number;
  address?: string;
  city?: string;
  country?: string;
}

export interface Farm {
  id: string;
  name: string;
  location?: FarmLocation;
  totalAcres: number;
  sketchDataUrl?: string; // Ported: For drawing capability
  enhancedSketchUrl?: string; // Ported: For AI enhanced map
  crops: Crop[];
  inventory?: InventoryItem[];
}

export interface UserSettings {
  language: string;
  currency: string;
  unit: 'metric' | 'imperial';
}

export interface FarmState {
  farms: Farm[];
  selectedFarmId: string | null;
  settings: UserSettings;
}
