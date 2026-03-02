import React from 'react';

const SCHEMES: any[] = []; // Empty until backend provides

export default function SchemesRoute() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-serif font-bold text-lg mb-6">Eligible Government Schemes</h3>
        {SCHEMES.length === 0 ? (
          <p className="text-gray-500">No schemes data available from backend.</p>
        ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {SCHEMES.map((scheme) => (
            <div key={scheme.id} className="border border-gray-200 rounded-2xl p-6 hover:border-farm-green transition-colors">
              <div className="flex justify-between items-start mb-4">
                <h4 className="font-bold text-gray-900 text-lg">{scheme.name}</h4>
                <span className="bg-green-100 text-green-800 text-xs font-bold px-2 py-1 rounded">
                  {scheme.status}
                </span>
              </div>
              <p className="text-farm-green font-medium mb-2">{scheme.benefit}</p>
              <p className="text-sm text-gray-500 mb-6">{scheme.eligibility}</p>
              <a 
                href={scheme.link} 
                target="_blank" 
                rel="noreferrer"
                className="block w-full text-center py-2 bg-gray-50 hover:bg-gray-100 text-gray-900 rounded-xl text-sm font-medium transition-colors"
              >
                View Application
              </a>
            </div>
          ))}
        </div>
        )}
      </div>
    </div>
  );
}
