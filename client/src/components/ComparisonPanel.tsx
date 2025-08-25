import React, { useState } from 'react';
import { RentalScore } from '../type';

interface ComparisonPanelProps {
  comparisonList: RentalScore[];
  onRemove: (propertyId: number) => void;
  onClear: () => void;
}

const ComparisonPanel: React.FC<ComparisonPanelProps> = ({ comparisonList, onRemove, onClear }) => {
  const [isMinimized, setIsMinimized] = useState(false);

  if (comparisonList.length === 0) {
    return null;
  }

  const attributesToShow = [
    { label: 'Price', key: 'price', prefix: '$', suffix: '/mo' },
    { label: 'QoL Score', key: 'qolScore' },
    { label: 'Walk Score', key: 'walkScore' },
    { label: 'Air Quality', key: 'airQualityScore' },
    { label: 'Bedrooms', key: 'bedroom' },
    { label: 'Bathrooms', key: 'bathroom' },
  ];

  if (isMinimized) {
    return (
      // FIXED: Increased z-index to 50
      <div className="fixed bottom-0 left-0 right-0 bg-gray-800 text-white shadow-lg z-50">
        <div className="max-w-7xl mx-auto p-2 flex justify-between items-center">
          <h2 className="text-lg font-bold">Comparing {comparisonList.length} Properties</h2>
          <button
            onClick={() => setIsMinimized(false)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1 rounded text-sm font-semibold"
          >
            Expand
          </button>
        </div>
      </div>
    );
  }

  return (
    // FIXED: Increased z-index to 50
    <div className="fixed bottom-0 left-0 right-0 bg-gray-800 text-white p-4 shadow-lg z-50 animate-slide-up">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-4">
          <button
            onClick={() => setIsMinimized(true)}
            className="flex items-center group cursor-pointer"
            title="Minimize"
          >
            <h2 className="text-xl font-bold mr-2 group-hover:text-blue-400">Comparing {comparisonList.length} Properties</h2>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-chevron-down group-hover:text-blue-400 transition-colors" viewBox="0 0 16 16">
              <path fillRule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/>
            </svg>
          </button>
          <button onClick={onClear} className="bg-red-600 hover:bg-red-700 text-white px-4 py-1 rounded text-sm font-semibold">
            Clear All
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-gray-600">
                <th className="p-2 font-semibold text-sm text-gray-300 sticky left-0 bg-gray-800">Feature</th>
                {comparisonList.map((property) => (
                  <th key={property.id} className="p-2 font-semibold text-sm">
                    <div className="flex justify-between items-center">
                      <span className="truncate pr-2">{property.name}</span>
                      <button
                        onClick={() => onRemove(property.id)}
                        className="text-gray-400 hover:text-white font-bold text-xl flex-shrink-0"
                        title="Remove"
                      >
                        &times;
                      </button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {attributesToShow.map((attr) => (
                <tr key={attr.key} className="border-b border-gray-700 last:border-b-0">
                  <td className="p-2 font-semibold text-gray-300 sticky left-0 bg-gray-800">{attr.label}</td>
                  {comparisonList.map((property) => (
                    <td key={property.id} className="p-2">
                      {attr.prefix || ''}
                      {String(property[attr.key as keyof RentalScore])}
                      {attr.suffix || ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <style>{`
        @keyframes slide-up {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
        .animate-slide-up { animation: slide-up 0.3s ease-out; }
      `}</style>
    </div>
  );
};

export default ComparisonPanel;