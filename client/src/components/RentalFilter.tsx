import React from "react";
import { MapFilter } from "./Map";

interface Props {
  filters: MapFilter;
  setFilters: React.Dispatch<React.SetStateAction<MapFilter>>;
}

const RentalFilter: React.FC<Props> = ({ filters, setFilters }) => {
  return (
    <div className="bg-white/70 backdrop-blur-md rounded-2xl shadow-lg p-6 space-y-4">
      <h3 className="text-xl font-semibold text-gray-800">Filters</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Search</label>
          <input
            className="w-full px-3 py-2 border rounded-md"
            type="text"
            value={filters.searchQuery}
            onChange={(e) =>
              setFilters({ ...filters, searchQuery: e.target.value })
            }
            placeholder="Enter address or name"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">
            Min QOL Score: {filters.fQolScore}
          </label>
          <input
            title="Adjust the minimum quality of life score"
            className="w-full"
            type="range"
            min="0"
            max="100"
            value={filters.fQolScore}
            onChange={(e) =>
              setFilters({ ...filters, fQolScore: Number(e.target.value) })
            }
          />
        </div>
        <div>
          <label className="block text-sm font-medium">
            Min Walk Score: {filters.fWalkScore}
          </label>
          <input
            title="Adjust the minimum walk score"
            className="w-full"
            type="range"
            min="0"
            max="100"
            value={filters.fWalkScore}
            onChange={(e) =>
              setFilters({ ...filters, fWalkScore: Number(e.target.value) })
            }
          />
        </div>
        <div>
          <label className="block text-sm font-medium">
            Min Bus Stops: {filters.fBusStopsNumber}
          </label>
          <input
            title="Adjust the minimum number of bus stops"
            className="w-full"
            type="range"
            min="0"
            max="20"
            value={filters.fBusStopsNumber}
            onChange={(e) =>
              setFilters({
                ...filters,
                fBusStopsNumber: Number(e.target.value),
              })
            }
          />
        </div>
      </div>
    </div>
  );
};

export default RentalFilter;
