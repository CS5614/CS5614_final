import { useState, useEffect, useContext, useMemo } from "react";
import {
  APIProvider,
  AdvancedMarker,
  AdvancedMarkerAnchorPoint,
  Map as GoogleMap,
} from "@vis.gl/react-google-maps";

import { RentalScoreContext } from "../contexts/RentalScoreContext";
import { MapFilter, RentalScore } from "../type";
import RentalInfoWindow from "./RentalInfoWindow";

// Change the apikey from fetching from backend to constant variable in frontend
// api access restriction is set on GCP
const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
const center = { lat: 38.891014, lng: -77.026703 };

// Interface for the props being passed INTO this component
interface MapProps {
  filters: MapFilter;
  comparisonList: RentalScore[];
  onToggleCompare: (property: RentalScore) => void;
}

// FIXED: The props are now correctly destructured here
const Map: React.FC<MapProps> = ({ filters, comparisonList, onToggleCompare }) => {
  const { rentalScores } = useContext(RentalScoreContext);
  const [filteredLocations, setFilteredLocations] = useState<RentalScore[]>([]);
  const [selected, setSelected] = useState<RentalScore | null>(null);
  const [locationsAtPoint, setLocationsAtPoint] = useState<RentalScore[]>([]);
  const [currentLocationIndex, setCurrentLocationIndex] = useState(0);


  const filterRentalLocations = (
    locations: RentalScore[],
    currentFilters: MapFilter
  ) => {
    if (!locations || !locations.length) return [];
    return locations.filter((loc) => {
      if (!currentFilters.State?.includes(loc.state)) return false;
      if (loc.qolScore < (currentFilters.QolScore ?? 0)) return false;
      if (loc.walkScore < (currentFilters.WalkScore ?? 0)) return false;
      if (loc.busStopsNumber < (currentFilters.BusStopsNumber ?? 0)) return false;
      if (loc.price > (currentFilters.Price ?? Infinity)) return false;
      if (loc.airQualityScore < (currentFilters.AirQualityScore ?? 0)) return false;
      if (loc.bathroom < (currentFilters.Bathroom ?? 0)) return false;
      if (loc.bedroom < (currentFilters.Bedroom ?? 0)) return false;
      if (currentFilters.SearchQuery) {
        const q = currentFilters.SearchQuery.toLowerCase();
        const addr = loc.address?.toLowerCase().includes(q);
        const name = loc.name?.toLowerCase().includes(q);
        if (!addr && !name) return false;
      }
      return true;
    });
  };

  useEffect(() => {
    setFilteredLocations(filterRentalLocations(rentalScores, filters));
  }, [rentalScores, filters]);

  const groupedLocations = useMemo(() => {
    const groups: Record<string, RentalScore[]> = {};
    filteredLocations.forEach((loc) => {
      if (typeof loc.lat !== "number" || typeof loc.long !== "number") return;
      const key = `${loc.lat.toFixed(6)},${loc.long.toFixed(6)}`;
      groups[key] = groups[key] || [];
      groups[key].push(loc);
    });
    return groups;
  }, [filteredLocations]);

  const handleMarkerClick = (_key: string, locs: RentalScore[]) => {
    setLocationsAtPoint(locs);
    setCurrentLocationIndex(0);
    setSelected(locs[0]);
  };
  const nextProperty = () => {
    if (locationsAtPoint.length <= 1) return;
    const next = (currentLocationIndex + 1) % locationsAtPoint.length;
    setCurrentLocationIndex(next);
    setSelected(locationsAtPoint[next]);
  };
  const prevProperty = () => {
    if (locationsAtPoint.length <= 1) return;
    const prev = (currentLocationIndex - 1 + locationsAtPoint.length) % locationsAtPoint.length;
    setCurrentLocationIndex(prev);
    setSelected(locationsAtPoint[prev]);
  };
  const handleInfoWindowClose = () => {
    setSelected(null);
    setLocationsAtPoint([]);
  };

  const qolLegend = [
    { color: "green", range: "80+", icon: "🏡" },
    { color: "yellow", range: "60-79", icon: "🏠" },
    { color: "orange", range: "40-59", icon: "🛖" },
    { color: "red", range: "Below 40", icon: "🏚️" },
  ];


  // Check if api key exists
  if (!apiKey) {
    return (
      <div className="flex justify-center items-center h-screen">
        Error: missing Google Maps API key.
      </div>
    );
  }

  return (
    <APIProvider apiKey={apiKey}>
      <div className="relative h-screen w-full">
        <div className="absolute top-4 left-4 bg-white p-4 rounded shadow-md z-10">
          <h3 className="text-lg font-semibold mb-2 text-gray-900">QoL Legend</h3>
          <ul>
            {qolLegend.map((item, i) => (
              <li key={i} className="flex items-center mb-1 text-gray-700">
                <span className="mr-2">{item.icon}</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  item.color === "green"
                    ? "bg-green-200 text-green-800"
                    : item.color === "yellow"
                    ? "bg-yellow-200 text-yellow-800"
                    : item.color === "orange"
                    ? "bg-orange-200 text-orange-800"
                    : "bg-red-200 text-red-800"
                }`}>
                  {item.range}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <GoogleMap
          defaultCenter={center}
          defaultZoom={12}
          mapId="cde3df1b3d78f48c"
          className="h-full w-full"
          disableDefaultUI
          gestureHandling="greedy"
          zoomControl
        >
          {Object.entries(groupedLocations).map(([key, mapLocations]) => {
            const [lat, lng] = key.split(",").map(Number);
            if (isNaN(lat) || isNaN(lng)) return null;
            const representative = mapLocations[0];
            const count = mapLocations.length;
            return (
              <AdvancedMarker
                key={key}
                position={{ lat, lng }}
                onClick={() => handleMarkerClick(key, mapLocations)}
                anchorPoint={AdvancedMarkerAnchorPoint.TOP_CENTER}
              >
                <div className="relative flex flex-col items-center -mt-3 overflow-visible">
                  <div className={`inline-flex items-center text-xs font-bold text-gray-800 rounded-full py-1 px-2 whitespace-nowrap ${
                      representative.qolScore >= 80
                        ? "bg-green-300"
                        : representative.qolScore >= 60
                        ? "bg-yellow-300"
                        : representative.qolScore >= 40
                        ? "bg-orange-300"
                        : "bg-red-300"
                    }`}
                  >
                    ${representative.price}
                    {count > 1 && (
                      <span className="ml-1 bg-blue-500 text-white rounded-full px-2 py-0.5 whitespace-nowrap">
                        +{count - 1}
                      </span>
                    )}
                  </div>
                  <span className="text-[2rem] mt-1">
                    {representative.qolScore >= 80
                      ? "🏡"
                      : representative.qolScore >= 60
                      ? "🏠"
                      : representative.qolScore >= 40
                      ? "🛖"
                      : "🏚️"}
                  </span>
                </div>
              </AdvancedMarker>
            );
          })}

          {selected && (
            <RentalInfoWindow
              selected={selected}
              locationsAtPoint={locationsAtPoint}
              currentLocationIndex={currentLocationIndex}
              onClose={handleInfoWindowClose}
              onNextProperty={nextProperty}
              onPrevProperty={prevProperty}
              onToggleCompare={onToggleCompare} // This is now in scope
              isCompared={comparisonList.some((item: RentalScore) => item.id === selected.id)} // This is now in scope and typed
            />
          )}
        </GoogleMap>
      </div>
    </APIProvider>
  );
};

export default Map;
