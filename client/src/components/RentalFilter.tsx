import React from "react";
import { MapFilter } from "../type";
import { defaultFilters } from "../consts/defaultFilters";

interface Props {
  filters: MapFilter;
  setFilters: React.Dispatch<React.SetStateAction<MapFilter>>;
  onClose?: () => void;
}

const RentalFilter: React.FC<Props> = ({ filters, setFilters, onClose }) => {
  // Helper to sum weights
  const totalWeight = Object.values(filters.weights || {}).reduce((a, b) => a + b, 0);
  const weightKeys = [
    "Price",
    "AirQualityScore",
    "WalkScore",
    "Review",
    "GreenSpace",
    "PublicTransportation"
  ] as const;
  type WeightKey = typeof weightKeys[number];
  const handleWeightChange = (key: WeightKey, value: number) => {
    setFilters({
      ...filters,
      weights: {
        ...filters.weights,
        [key]: value,
      },
    });
  };
  return (
    // --- FIXED: Use flexbox to structure the panel ---
    <div className="bg-white h-full flex flex-col">
      {/* 1. Static Header */}
      <div className="flex-shrink-0 p-6 pb-4 border-b">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-bold text-gray-800 text-center w-full">Filters</h3>
          {onClose && (
            <button onClick={onClose} className="-mr-4 md:hidden" title="Close filter panel">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* 2. Scrollable Content Area with original spacing restored */}
      <div className="flex-grow overflow-y-auto p-6 space-y-6">
        {/* Toggle for Dynamic Weights */}
        <div className="mb-4 flex items-center justify-center gap-2">
          <label htmlFor="toggle-dynamic-weight" className="text-sm font-medium text-gray-700">Use Dynamic Weights</label>
          <input
            id="toggle-dynamic-weight"
            type="checkbox"
            checked={filters.useDynamicWeight}
            onChange={e => setFilters({ ...filters, useDynamicWeight: e.target.checked })}
            className="accent-blue-500 h-4 w-4"
          />
        </div>
        {/* Dynamic Weights Section (conditionally rendered) */}
        {filters.useDynamicWeight && (
          <div className="mb-6 border rounded-lg p-4 bg-gray-50">
            <div className="text-center font-semibold text-gray-700 mb-2">Dynamic Score Weights</div>
            <div className="grid grid-cols-2 gap-4">
              {weightKeys.map((key) => (
                <div key={key} className="flex flex-col items-center">
                  <label className="text-sm text-gray-600 mb-1">
                    {key === "GreenSpace" ? "Green Space"
                      : key === "PublicTransportation" ? "Public Transportation"
                      : key === "AirQualityScore" ? "Air Quality"
                      : key === "WalkScore" ? "Walk Score"
                      : key === "Review" ? "Google Review"
                      : key === "Price" ? "Price"
                      : key}
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={filters.weights?.[key as WeightKey] ?? 0}
                    onChange={e => {
                      let val = Number(e.target.value);
                      if (val < 0) val = 0;
                      if (val > 100) val = 100;
                      handleWeightChange(key as WeightKey, val);
                    }}
                    className="w-20 px-2 py-1 border border-gray-300 rounded text-center text-gray-900"
                    title={`Set weight for ${key}`}
                    placeholder="0"
                  />
                  <span className="text-xs text-gray-500">%</span>
                </div>
              ))}
            </div>
            <div className="mt-2 text-center text-sm">
              Total: <span className={totalWeight === 100 ? "text-green-600" : "text-red-600 font-bold"}>{totalWeight}%</span>
              {totalWeight !== 100 && (
                <span className="ml-2 text-red-500">(Total must be 100%)</span>
              )}
            </div>
          </div>
        )}
        <div className="space-y-4">
          <div className="text-center">
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Enter address or building name
            </label>
            <input
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
              type="text"
              value={filters.SearchQuery}
              onChange={(e) =>
                setFilters({ ...filters, SearchQuery: e.target.value })
              }
              placeholder="Search"
            />
          </div>
          <div className="text-gray-600">
            <label className="block text-sm font-medium text-center mb-2">
              State
            </label>
            <div className="flex space-x-4 justify-center">
              <label>
                <input type="checkbox" name="state" value="DC" checked={filters.State.includes("DC")} onChange={() => setFilters({ ...filters, State: filters.State.includes("DC") ? filters.State.filter((s) => s !== "DC") : [...filters.State, "DC"]})}/> DC
              </label>
              <label>
                <input type="checkbox" name="state" value="VA" checked={filters.State.includes("VA")} onChange={() => setFilters({ ...filters, State: filters.State.includes("VA") ? filters.State.filter((s) => s !== "VA") : [...filters.State, "VA"]})}/> VA
              </label>
              <label>
                <input type="checkbox" name="state" value="MD" checked={filters.State.includes("MD")} onChange={() => setFilters({ ...filters, State: filters.State.includes("MD") ? filters.State.filter((s) => s !== "MD") : [...filters.State, "MD"]})}/> MD
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 text-center mb-1">Qol Score</label>
            <input title="Qol Score" className="w-full accent-blue-500" type="range" min="0" max="100" value={filters.QolScore} onChange={(e) => setFilters({ ...filters, QolScore: Number(e.target.value) })}/>
            <div className="text-sm text-gray-500 text-center">{filters.QolScore}</div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 text-center mb-1">Max Price</label>
            <input title="Max Price" className="w-full accent-blue-500" type="range" min="0" max="12000" value={filters.Price} onChange={(e) => setFilters({ ...filters, Price: Number(e.target.value) })}/>
            <div className="flex justify-between text-sm text-gray-500">
              <span>$0</span><span>${filters.Price}</span><span>$12,000</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 text-center mb-1">Bedroom</label>
            <input title="Bedroom" className="w-full accent-blue-500" type="range" min="1" max="5" value={filters.Bedroom} onChange={(e) => setFilters({ ...filters, Bedroom: Number(e.target.value) })}/>
            <div className="text-sm text-gray-500 text-center">{filters.Bedroom}</div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 text-center mb-1">Bathroom</label>
            <input title="Bathroom" className="w-full accent-blue-500" type="range" min="1" max="5" value={filters.Bathroom} onChange={(e) => setFilters({ ...filters, Bathroom: Number(e.target.value) })}/>
            <div className="text-sm text-gray-500 text-center">{filters.Bathroom}</div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 text-center mb-1">Air Quality Index</label>
            <input title="Air Quality Index" className="w-full accent-blue-500" type="range" min="0" max="100" value={filters.AirQualityScore} onChange={(e) => setFilters({ ...filters, AirQualityScore: Number(e.target.value) })}/>
            <div className="text-sm text-gray-500 text-center">{filters.AirQualityScore}</div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 text-center mb-1">Walk Score</label>
            <input title="Walk Score" className="w-full accent-blue-500" type="range" min="1" max="20" value={filters.WalkScore} onChange={(e) => setFilters({ ...filters, WalkScore: Number(e.target.value) })}/>
            <div className="text-sm text-gray-500 text-center">{filters.WalkScore}</div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 text-center mb-1">Google Review</label>
            <input title="Google Review" className="w-full accent-blue-500" type="range" min="0" max="5" value={filters.Review} onChange={(e) => setFilters({ ...filters, Review: Number(e.target.value) })}/>
            <div className="text-sm text-gray-500 text-center">{filters.Review}</div>
          </div>
        </div>
      </div>

      {/* 3. Static Footer */}
      <div className="flex-shrink-0 p-6 pt-4 border-t">
        <button
          onClick={() => setFilters(defaultFilters)}
          className="w-full bg-black text-white px-6 py-2 rounded-md hover:bg-gray-800 transition-colors"
        >
          Reset
        </button>
      </div>
    </div>
  );
};

export default RentalFilter;