import { useState, useEffect, useContext, useMemo } from "react";
import {
  AdvancedMarker,
  AdvancedMarkerAnchorPoint,
  Map as GoogleMap,
} from "@vis.gl/react-google-maps";

import { RentalScoreContext } from "../contexts/RentalScoreContext";
import { MapFilter, RentalScore } from "../type";
import RentalInfoWindow from "./RentalInfoWindow";

const center = {
  lat: 38.9072,
  lng: -77.0369,
};

const Map: React.FC<{ filters: MapFilter }> = ({ filters }) => {
  const rentalScores = useContext(RentalScoreContext);
  const [filteredLocations, setFilteredLocations] = useState<RentalScore[]>([]);
  const [selected, setSelected] = useState<RentalScore>({} as RentalScore);
  const [selectedLocation, setSelectedLocation] = useState<{
    lat: number;
    lng: number;
  } | null>(null);
  const [locationsAtPoint, setLocationsAtPoint] = useState<RentalScore[]>([]);
  const [currentLocationIndex, setCurrentLocationIndex] = useState(0);

  // Enhanced marker click handler
  const handleMarkerClick = (key: string, locations: RentalScore[]) => {
    const [lat, lng] = key.split(",").map(Number);
    setSelectedLocation({ lat, lng });
    setLocationsAtPoint(locations);
    setCurrentLocationIndex(0);
    setSelected(locations[0]);
  };

  // Property navigation handlers
  const nextProperty = () => {
    if (locationsAtPoint.length <= 1) return;
    const nextIndex = (currentLocationIndex + 1) % locationsAtPoint.length;
    setCurrentLocationIndex(nextIndex);
    setSelected(locationsAtPoint[nextIndex]);
  };

  const prevProperty = () => {
    if (locationsAtPoint.length <= 1) return;
    const prevIndex =
      (currentLocationIndex - 1 + locationsAtPoint.length) %
      locationsAtPoint.length;
    setCurrentLocationIndex(prevIndex);
    setSelected(locationsAtPoint[prevIndex]);
  };

  // Handle closing the info window
  const handleInfoWindowClose = () => {
    setSelected({} as RentalScore);
    setLocationsAtPoint([]);
    setSelectedLocation(null);
  };

  // Filter rentals based on filters
  useEffect(() => {
    const filtered = filterRentalLocations(rentalScores, filters);
    console.log("Filtered length:", filtered.length);
    setFilteredLocations(filtered);
  }, [rentalScores, filters]);

  const filterRentalLocations = (
    locations: RentalScore[],
    filters: MapFilter
  ): RentalScore[] => {
    // Existing filter implementation...
    return locations.filter((loc) => {
      if (!filters.State.includes(loc.state)) return false;
      if (loc.qolScore < filters.QolScore) return false;
      if (loc.walkScore < filters.WalkScore) return false;
      if (loc.busStopsNumber < filters.BusStopsNumber) return false;
      if (loc.price > filters.Price) return false;
      if (loc.airQualityScore < filters.AirQualityScore) return false;
      if (loc.openStreetNumber < filters.ParkNumber) return false;
      if (loc.reviewScore < filters.Review) return false;
      if (loc.bathroom < filters.Bathroom) return false;
      if (loc.bedroom < filters.Bedroom) return false;
      if (
        (filters.SearchQuery &&
          !loc.address
            .toLowerCase()
            .includes(filters.SearchQuery.toLowerCase())) ||
        !loc.name.toLowerCase().includes(filters.SearchQuery.toLowerCase())
      )
        return false;
      return true;
    });
  };

  // Group locations by coordinates
  const groupedLocations = useMemo(() => {
    const groups: Record<string, RentalScore[]> = {};

    filteredLocations.forEach((location) => {
      const key = `${location.lat.toFixed(6)},${location.long.toFixed(6)}`;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(location);
    });

    return groups;
  }, [filteredLocations]);

  // Add a legend for QOL color indicators
  const qolLegend = [
    { color: "green", range: "80+", icon: "🏡" },
    { color: "yellow", range: "60-79", icon: "🏠" },
    { color: "orange", range: "40-59", icon: "🛖" },
    { color: "red", range: "Below 40", icon: "🏚️" },
  ];

  return (
    <div className="relative">
      {/* QOL Legend */}
      <div className="absolute top-4 left-4 bg-white p-4 rounded shadow-md z-10">
        <h3 className="text-lg font-semibold mb-2 text-gray-900">QOL Legend</h3>
        <ul>
          {qolLegend.map((item, index) => (
            <li key={index} className="flex items-center mb-1 text-gray-700">
              <span>{item.icon}</span>
              <span
                className={`${
                  item.color === "green"
                    ? "bg-green-300"
                    : item.color === "yellow"
                    ? "bg-yellow-300"
                    : item.color === "orange"
                    ? "bg-orange-300"
                    : "bg-red-300"
                }`}
              >
                {item.range}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* Google Map */}
      <GoogleMap
        defaultCenter={center}
        defaultZoom={12}
        mapId="cde3df1b3d78f48c"
        className="h-screen w-full"
        disableDefaultUI
        gestureHandling={"greedy"}
        zoomControl={true}
      >
        {/* Markers */}
        {Object.entries(groupedLocations).map(([key, locations]) => {
          const [lat, lng] = key.split(",").map(Number);
          const representative = locations[0];
          const count = locations.length;

          return (
            <AdvancedMarker
              key={key}
              position={{ lat, lng }}
              onClick={() => handleMarkerClick(key, locations)}
              anchorPoint={AdvancedMarkerAnchorPoint.TOP_LEFT}
            >
              <div
                className={`absolute -top-2 -left-2 text-xs font-bold text-gray-800 rounded-full p-1 ${
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
                  <span className="ml-1 bg-blue-500 text-white rounded-full px-1.5 py-0.5">
                    +{count - 1}
                  </span>
                )}
              </div>
              <span className="text-[2rem] w-full text-center">
                {representative.qolScore >= 80
                  ? "🏡"
                  : representative.qolScore >= 60
                  ? "🏠"
                  : representative.qolScore >= 40
                  ? "🛖"
                  : "🏚️"}
              </span>
            </AdvancedMarker>
          );
        })}

        {/* Info Window Component */}
        {selected.lat !== undefined && selected.long !== undefined && (
          <RentalInfoWindow
            selected={selected}
            locationsAtPoint={locationsAtPoint}
            currentLocationIndex={currentLocationIndex}
            onClose={handleInfoWindowClose}
            onNextProperty={nextProperty}
            onPrevProperty={prevProperty}
          />
        )}
      </GoogleMap>
    </div>
  );
};

export default Map;
