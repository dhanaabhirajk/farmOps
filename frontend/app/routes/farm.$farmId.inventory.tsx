import React, { useState } from 'react';
import { Package, Plus, Search, MapPin, Edit2, Trash2 } from 'lucide-react';
import { useOutletContext } from '@remix-run/react';
import { cn } from '~/lib/utils'; // Use our Remix util

export default function InventoryRoute() {
  const { farmData } = useOutletContext<{ farmData: any }>();
  // In a real app, inventory would be a separate API call or part of farmData
  const [inventory, setInventory] = useState<any[]>([]); // Start empty or hydrate from props
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [isAdding, setIsAdding] = useState(false);

  const filteredInventory = inventory.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          item.location?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = filterCategory === 'all' || item.category === filterCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="font-serif font-bold text-xl flex items-center gap-2">
            <Package className="w-5 h-5 text-farm-green" /> Farm Inventory
          </h2>
          <p className="text-sm text-gray-500">Manage seeds, fertilizers, and equipment.</p>
        </div>
        <button 
          onClick={() => setIsAdding(true)}
          className="flex items-center gap-2 px-4 py-2 bg-farm-green text-white rounded-xl font-medium hover:bg-farm-green/90 transition-colors"
        >
          <Plus className="w-4 h-4" /> Add Item
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 bg-white p-4 rounded-2xl shadow-sm border border-gray-100">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input 
            type="text" 
            placeholder="Search inventory..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-farm-green/20"
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0">
          {['all', 'seed', 'fertilizer', 'harvest', 'equipment'].map(cat => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm font-medium capitalize whitespace-nowrap transition-colors",
                filterCategory === cat 
                  ? "bg-farm-green text-white" 
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              )}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Inventory List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredInventory.map(item => (
          <div key={item.id} className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow group relative">
             {/* Item details */}
             <h4 className="font-bold">{item.name}</h4>
          </div>
        ))}
        
        {filteredInventory.length === 0 && (
          <div className="col-span-full py-12 text-center text-gray-400 bg-gray-50 rounded-3xl border border-dashed border-gray-200">
            <Package className="w-12 h-12 mx-auto mb-3 opacity-20" />
            <p>No items found in inventory.</p>
          </div>
        )}
      </div>
    </div>
  );
}
