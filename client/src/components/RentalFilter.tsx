
import React, { useEffect, useState } from "react";
import { MapFilter, RentalScore } from "../type";
import { defaultFilters } from "../consts/defaultFilters";
import httpClient from "../services/httpClient";

type DefaultWeightsResponse = {
  price: number;
  airQualityScore: number;
  walkScore: number;
  nearestBusStopDistance: number;
  busStopsNumber: number;
  openStreetNumber: number;
  nearestParkDistance: number;
};

type Props = {
  filters: MapFilter;
  setFilters: React.Dispatch<React.SetStateAction<MapFilter>>;
  onClose?: () => void;
  onQolUpdate?: (qolScores: RentalScore[]) => void; // callback to update qol scores in parent
};


// Backend feature keys

// If featureDisplayNames is needed elsewhere, uncomment and use:
// const featureDisplayNames: Record<WeightKey, string> = { ... };

const RentalFilter: React.FC<Props> = ({ filters, setFilters, onClose, onQolUpdate }) => {
  // Backend feature keys
  const weightKeys = [
    "Price",
    "AirQualityScore",
    "WalkScore",
    "NearestBusStopDistance",
    "BusStopsNumber",
    "OpenStreetNumber",
    "NearestParkDistance"
  ] as const;
  type WeightKey = typeof weightKeys[number];

  // State to track if weights have been modified but not applied
  const [hasUnappliedChanges, setHasUnappliedChanges] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  // State for negative/positive direction for prices
  const [priceDirection, setPriceDirection] = useState<'positive' | 'negative'>('negative');

  // Helper to sum weights
  const totalWeight = Object.values(filters.weights || {}).reduce((a: number, b: number) => a + b, 0);

  // Fetch default weights on mount if not set
  useEffect(() => {
    if (filters.useDynamicWeight && (!filters.weights || Object.keys(filters.weights).length === 0)) {
      httpClient.get<DefaultWeightsResponse>("/api/dynamicQol/defaultWeights")
        .then((response) => {
          const data = response.data;
          // Convert backend weights (0-1) to frontend weights (0-100) while preserving proportions
          const backendWeights = {
            Price: data.price ?? 0,
            AirQualityScore: data.airQualityScore ?? 0,
            WalkScore: data.walkScore ?? 0,
            NearestBusStopDistance: data.nearestBusStopDistance ?? 0,
            BusStopsNumber: data.busStopsNumber ?? 0,
            OpenStreetNumber: data.openStreetNumber ?? 0,
            NearestParkDistance: data.nearestParkDistance ?? 0,
          };

          // Scale to 100 and round, then adjust to ensure sum equals 100
          const scaledWeights: [string, number][] = Object.entries(backendWeights).map(([key, value]) => [
            key,
            Math.round(value * 100)
          ]);

          const currentSum = scaledWeights.reduce((sum, [, value]) => sum + value, 0);
          const difference = 100 - currentSum;

          // Adjust the largest weight by the difference to make sum exactly 100
          if (difference !== 0) {
            const maxIndex = scaledWeights.reduce((maxIdx, [, value], idx) =>
              value > scaledWeights[maxIdx][1] ? idx : maxIdx, 0);
            scaledWeights[maxIndex][1] += difference;
          }

          const finalWeights = Object.fromEntries(scaledWeights) as {
            Price: number;
            AirQualityScore: number;
            WalkScore: number;
            NearestBusStopDistance: number;
            BusStopsNumber: number;
            OpenStreetNumber: number;
            NearestParkDistance: number;
          };

          setFilters((f: MapFilter) => ({ ...f, weights: finalWeights }));
          // Auto-apply default weights when first enabling dynamic weights
          setHasUnappliedChanges(true);
        })
        .catch(console.error);
    }
    // eslint-disable-next-line
  }, [filters.useDynamicWeight]);

  // Reset unapplied changes when dynamic weight toggle changes
  useEffect(() => {
    setHasUnappliedChanges(false);
  }, [filters.useDynamicWeight]);

  // Call dynamic QoL API when Apply button is clicked
  const applyWeights = async () => {
    if (filters.useDynamicWeight && filters.weights && totalWeight === 100) {
      setIsApplying(true);
      try {
        const payload: { [key: string]: any } = {};

        for (const key of Object.keys(filters.weights || {})) {
          const weightValue = filters.weights[key as WeightKey];

          if (weightValue > 0) { // 只處理權重大於 0 的特徵
            const backendKey = key.charAt(0).toLowerCase() + key.slice(1);

            if (key === 'Price') {
              // 對於 Price，組裝成包含 weight 和 direction 的物件
              payload['price'] = {
                weight: weightValue,
                direction: priceDirection
              };
            } else {
              // 對於其他特徵，直接傳遞權重數字
              payload[backendKey] = weightValue;
            }
          }
        }

        if (Object.keys(payload).length === 0) {
          console.warn("No weights greater than 0 were provided.");
          setIsApplying(false);
          return;
        }

        const response = await httpClient.post<RentalScore[]>("/api/dynamicQol", payload);
        if (onQolUpdate) onQolUpdate(response.data);
        setHasUnappliedChanges(false);
      } catch (error) {
        console.error("Failed to apply dynamic weights:", error);
      } finally {
        setIsApplying(false);
      }
    }
  };

  const handleWeightChange = (key: WeightKey, value: number) => {
    setFilters({
      ...filters,
      weights: {
        ...filters.weights,
        [key]: value,
      },
    });
    setHasUnappliedChanges(true);
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
            <div className="text-center font-semibold text-gray-700 mb-2">Dynamic Weights</div>
            <div className="grid grid-cols-2 gap-3">
              {weightKeys.map((key) => (
                <div
                  key={key}
                  className="flex flex-col items-stretch p-2 rounded bg-white shadow-sm border border-gray-200"
                >
                  <div className="flex items-start gap-1 mb-1">
                    <span className="text-[10px] font-medium text-gray-600 leading-tight flex-1">
                      {key === "AirQualityScore" ? "Air Quality"
                        : key === "WalkScore" ? "Walk Score"
                        : key === "NearestBusStopDistance" ? "Nearest Bus Stop"
                        : key === "BusStopsNumber" ? "Nearby Bus Stops"
                        : key === "OpenStreetNumber" ? "Nearby Parks"
                        : key === "NearestParkDistance" ? "Nearest Park"
                        : key === "Price" ? "Price"
                        : key}
                    </span>
                    <span className="text-[11px] tabular-nums font-semibold text-gray-700 w-8 text-right">
                      {filters.weights?.[key as WeightKey] ?? 0}%
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <input
                      type="range"
                      min={0}
                      max={100}
                      step={1}
                      value={filters.weights?.[key as WeightKey] ?? 0}
                      onChange={e => {
                        let val = Number(e.target.value);
                        if (val < 0) val = 0;
                        if (val > 100) val = 100;
                        handleWeightChange(key as WeightKey, val);
                      }}
                      className="w-full accent-blue-500 h-2 bg-gray-200 rounded-lg cursor-pointer"
                      title={`Set weight for ${key}`}
                      aria-label={`Weight slider for ${key}`}
                    />
                  </div>
                    {key === 'Price' && (
                    <div className="mt-1.5 flex items-center justify-around gap-1 text-[10px] text-gray-500">
                      <label className="cursor-pointer flex items-center gap-1">
                        <input
                          type="radio"
                          name="price-direction"
                          value="negative"
                          checked={priceDirection === 'negative'}
                          onChange={() => { setPriceDirection('negative'); setHasUnappliedChanges(true); }}
                          className="accent-blue-500 h-2.5 w-2.5"
                        />
                        <span>Lower Better</span>
                      </label>
                      <label className="cursor-pointer flex items-center gap-1">
                        <input
                          type="radio"
                          name="price-direction"
                          value="positive"
                          checked={priceDirection === 'positive'}
                          onChange={() => { setPriceDirection('positive'); setHasUnappliedChanges(true); }}
                          className="accent-blue-500 h-2.5 w-2.5"
                        />
                        <span>Higher Better</span>
                      </label>
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-2 text-center text-sm">
              Total: <span className={totalWeight === 100 ? "text-green-600" : "text-red-600 font-bold"}>{totalWeight}%</span>
              {totalWeight !== 100 && (
                <span className="ml-2 text-red-500">(Total must be 100%)</span>
              )}
            </div>
            <div className="mt-4 text-center">
              <button
                onClick={applyWeights}
                disabled={totalWeight !== 100 || isApplying || !hasUnappliedChanges}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  totalWeight === 100 && hasUnappliedChanges && !isApplying
                    ? "bg-blue-500 text-white hover:bg-blue-600"
                    : "bg-gray-300 text-gray-500 cursor-not-allowed"
                }`}
              >
                {isApplying ? "Applying..." : "Apply Weights"}
              </button>
              {hasUnappliedChanges && totalWeight === 100 && (
                <p className="text-xs text-orange-600 mt-1">Changes not applied yet</p>
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
                <input type="checkbox" name="state" value="DC" checked={filters.State.includes("DC")} onChange={() => setFilters({ ...filters, State: filters.State.includes("DC") ? filters.State.filter((s: string) => s !== "DC") : [...filters.State, "DC"]})}/> DC
              </label>
              <label>
                <input type="checkbox" name="state" value="VA" checked={filters.State.includes("VA")} onChange={() => setFilters({ ...filters, State: filters.State.includes("VA") ? filters.State.filter((s: string) => s !== "VA") : [...filters.State, "VA"]})}/> VA
              </label>
              <label>
                <input type="checkbox" name="state" value="MD" checked={filters.State.includes("MD")} onChange={() => setFilters({ ...filters, State: filters.State.includes("MD") ? filters.State.filter((s: string) => s !== "MD") : [...filters.State, "MD"]})}/> MD
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