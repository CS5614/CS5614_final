import React from "react";
import { MapFilter } from "../type";
import { defaultFilters } from "../consts/defaultFilters";

interface Props {
  filters: MapFilter;
  setFilters: React.Dispatch<React.SetStateAction<MapFilter>>;
}

const RentalFilter: React.FC<Props> = ({ filters, setFilters }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
      <h3 className="text-lg font-bold text-gray-800 text-center">Filters</h3>
      <div className="space-y-4">
        <div className="text-center">
          <label className="block text-sm font-medium text-gray-600 mb-1">
            Enter address or building name
          </label>
          <input
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
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
              <input
                type="checkbox"
                name="state"
                value="DC"
                checked={filters.State.includes("DC")}
                onChange={() =>
                  setFilters({
                    ...filters,
                    State: filters.State.includes("DC")
                      ? filters.State.filter((state) => state !== "DC")
                      : [...filters.State, "DC"],
                  })
                }
              />
              DC
            </label>
            <label>
              <input
                type="checkbox"
                name="state"
                value="VA"
                checked={filters.State.includes("VA")}
                onChange={() =>
                  setFilters({
                    ...filters,
                    State: filters.State.includes("VA")
                      ? filters.State.filter((state) => state !== "VA")
                      : [...filters.State, "VA"],
                  })
                }
              />
              VA
            </label>
            <label>
              <input
                type="checkbox"
                name="state"
                value="MD"
                checked={filters.State.includes("MD")}
                onChange={() =>
                  setFilters({
                    ...filters,
                    State: filters.State.includes("MD")
                      ? filters.State.filter((state) => state !== "MD")
                      : [...filters.State, "MD"],
                  })
                }
              />
              MD
            </label>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 text-center mb-1">
            Qol Score
          </label>
          <input
            title="Qol Score"
            className="w-full accent-blue-500"
            type="range"
            min="0"
            max="100"
            value={filters.QolScore}
            onChange={(e) =>
              setFilters({ ...filters, QolScore: Number(e.target.value) })
            }
          />
          <div className="text-sm text-gray-500 text-center">
            {filters.QolScore}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 text-center mb-1">
            Max Price
          </label>
          <input
            title="Max Price"
            className="w-full accent-blue-500"
            type="range"
            min="0"
            max="12000"
            value={filters.Price}
            onChange={(e) =>
              setFilters({ ...filters, Price: Number(e.target.value) })
            }
          />
          <div className="flex justify-between text-sm text-gray-500">
            <span>$0</span>
            <span>${filters.Price}</span>
            <span>$12,000</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 text-center mb-1">
            Bedroom
          </label>
          <input
            title="Bedroom"
            className="w-full accent-blue-500"
            type="range"
            min="1"
            max="5"
            value={filters.Bedroom}
            onChange={(e) =>
              setFilters({ ...filters, Bedroom: Number(e.target.value) })
            }
          />
          <div className="text-sm text-gray-500 text-center">
            {filters.Bedroom}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 text-center mb-1">
            Bathroom
          </label>
          <input
            title="Bathroom"
            className="w-full accent-blue-500"
            type="range"
            min="1"
            max="5"
            value={filters.Bathroom}
            onChange={(e) =>
              setFilters({ ...filters, Bathroom: Number(e.target.value) })
            }
          />
          <div className="text-sm text-gray-500 text-center">
            {filters.Bathroom}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 text-center mb-1">
            Air Quality Index
          </label>
          <input
            title="Air Quality Index"
            className="w-full accent-blue-500"
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
          <div className="text-sm text-gray-500 text-center">
            {filters.AirQualityScore}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 text-center mb-1">
            Walk Score
          </label>
          <input
            title="Walk Score"
            className="w-full accent-blue-500"
            type="range"
            min="1"
            max="20"
            value={filters.WalkScore}
            onChange={(e) =>
              setFilters({ ...filters, WalkScore: Number(e.target.value) })
            }
          />
          <div className="text-sm text-gray-500 text-center">
            {filters.WalkScore}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 text-center mb-1">
            Google Review
          </label>
          <input
            title="Google Review"
            className="w-full accent-blue-500"
            type="range"
            min="0"
            max="5"
            value={filters.Review}
            onChange={(e) =>
              setFilters({ ...filters, Review: Number(e.target.value) })
            }
          />
          <div className="text-sm text-gray-500 text-center">
            {filters.Review}
          </div>
        </div>

        <div className="text-center">
          <button
            onClick={() => setFilters(defaultFilters)}
            className="bg-black text-white px-6 py-2 rounded-md hover:bg-gray-800 transition-colors"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
};

export default RentalFilter;
