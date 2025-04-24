import React from "react";
import { defaultFilters, MapFilter } from "../type";

interface Props {
  filters: MapFilter;
  setFilters: React.Dispatch<React.SetStateAction<MapFilter>>;
}

const RentalFilter: React.FC<Props> = ({ filters, setFilters }) => {
  // Define default filter values (adjust as needed)
  const handleReset = () => {
    setFilters(defaultFilters);
  };
  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
      <h3 className="text-lg font-bold text-gray-800">Filters</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-600">
            Enter address or building name
          </label>
          <input
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            type="text"
            value={filters.SearchQuery}
            onChange={(e) =>
              setFilters({ ...filters, SearchQuery: e.target.value })
            }
            placeholder="Search"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-600">
            Price Range
          </label>
          <input
            title="Price Range"
            className="w-full"
            type="range"
            min="0"
            max="4000"
            value={filters.Price}
            onChange={(e) =>
              setFilters({ ...filters, Price: Number(e.target.value) })
            }
          />
          <div className="flex justify-between text-sm text-gray-500">
            <span>$0</span>
            <span>${filters.Price}</span>
            <span>$4,000</span>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-600">
            Air Quality Index
          </label>
          <input
            title="Air Quality Index"
            className="w-full"
            type="range"
            min="0"
            max="100"
            value={filters.AirQualityScore}
            onChange={(e) =>
              setFilters({
                ...filters,
                AirQualityScore: Number(e.target.value),
              })
            }
          />
          <div className="text-sm text-gray-500">{filters.AirQualityScore}</div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-600">
            Walk Score
          </label>
          <input
            title="Walk Score"
            className="w-full"
            type="range"
            min="0"
            max="100"
            value={filters.WalkScore}
            onChange={(e) =>
              setFilters({ ...filters, WalkScore: Number(e.target.value) })
            }
          />
          <div className="text-sm text-gray-500">{filters.WalkScore}</div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-600">
            Bedroom
          </label>
          <input
            title="Bedroom"
            className="w-full"
            type="range"
            min="0"
            max="100"
            value={filters.Bedroom}
            onChange={(e) =>
              setFilters({ ...filters, Bedroom: Number(e.target.value) })
            }
          />
          <div className="text-sm text-gray-500">{filters.Bedroom}</div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-600">
            Bathroom
          </label>
          <input
            title="Bathroom"
            className="w-full"
            type="range"
            min="0"
            max="100"
            value={filters.Bathroom}
            onChange={(e) =>
              setFilters({ ...filters, Bathroom: Number(e.target.value) })
            }
          />
          <div className="text-sm text-gray-500">{filters.Bathroom}</div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-600">
            Google Review
          </label>
          <input
            title="Google Review"
            className="w-full"
            type="range"
            min="0"
            max="5"
            value={filters.Review}
            onChange={(e) =>
              setFilters({ ...filters, Review: Number(e.target.value) })
            }
          />
          <div className="text-sm text-gray-500">{filters.Review}</div>
        </div>
      </div>
      <button
        className="mt-4 px-4 py-2 bg-red-500 hover:bg-red-300 rounded text-black-700 font-semibold"
        onClick={handleReset}
        type="button"
      >
        Reset Filters
      </button>
    </div>
  );
};

export default RentalFilter;
