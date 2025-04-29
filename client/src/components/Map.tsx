import { useState, useEffect, useContext, useMemo } from "react";
import {
  AdvancedMarker,
  AdvancedMarkerAnchorPoint,
  Map as GoogleMap,
  InfoWindow,
} from "@vis.gl/react-google-maps";

import { RentalScoreContext } from "../contexts/RentalScoreContext";
import { MapFilter, RentalScore } from "../type";

// Interfaces for API responses
interface BusStopsResponse {
  nearby_bus_stops: string;
}

interface ParksResponse {
  nearby_parks: string;
}

const center = {
  lat: 38.9072,
  lng: -77.0369,
};

const Map: React.FC<{ filters: MapFilter }> = ({ filters }) => {
  const rentalScores = useContext(RentalScoreContext);
  const [filteredLocations, setFilteredLocations] = useState<RentalScore[]>([]);
  const [selected, setSelected] = useState<RentalScore>({} as RentalScore);
  const [, setSelectedLocation] = useState<{
    lat: number;
    lng: number;
  } | null>(null);
  const [locationsAtPoint, setLocationsAtPoint] = useState<RentalScore[]>([]);
  const [currentLocationIndex, setCurrentLocationIndex] = useState(0);

  // State for nearby amenities
  const [nearbyBusStops, setNearbyBusStops] = useState<string[]>([]);
  const [nearbyParks, setNearbyParks] = useState<string[]>([]);
  const [isLoadingBusStops, setIsLoadingBusStops] = useState(false);
  const [isLoadingParks, setIsLoadingParks] = useState(false);

  // Fetch nearby bus stops
  const fetchNearbyBusStops = async (listingId: number) => {
    try {
      setIsLoadingBusStops(true);
      const response = await fetch(
        `http://0.0.0.0:8000/api/busStopsInOneMiles/${listingId}`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch bus stops");
      }
      const data: BusStopsResponse = await response.json();

      // Split the comma-separated string into an array
      const busStops = data.nearby_bus_stops
        ? data.nearby_bus_stops.split(", ").filter((stop) => stop.trim())
        : [];

      setNearbyBusStops(busStops);
    } catch (error) {
      console.error("Error fetching bus stops:", error);
      setNearbyBusStops([]);
    } finally {
      setIsLoadingBusStops(false);
    }
  };

  // Fetch nearby parks
  const fetchNearbyParks = async (listingId: number) => {
    try {
      setIsLoadingParks(true);
      const response = await fetch(
        `http://0.0.0.0:8000/api/parksInOneMiles/${listingId}`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch parks");
      }
      const data: ParksResponse = await response.json();

      // Split the comma-separated string into an array
      const parks = data.nearby_parks
        ? data.nearby_parks.split(", ").filter((park) => park.trim())
        : [];

      setNearbyParks(parks);
    } catch (error) {
      console.error("Error fetching parks:", error);
      setNearbyParks([]);
    } finally {
      setIsLoadingParks(false);
    }
  };

  // Enhanced marker click handler to fetch details
  const handleMarkerClick = (key: string, locations: RentalScore[]) => {
    const [lat, lng] = key.split(",").map(Number);
    setSelectedLocation({ lat, lng });
    setLocationsAtPoint(locations);
    setCurrentLocationIndex(0);

    const selectedLocation = locations[0];
    setSelected(selectedLocation);

    // Reset previous data
    setNearbyBusStops([]);
    setNearbyParks([]);

    // Fetch new data for the selected location
    if (selectedLocation) {
      fetchNearbyBusStops(selectedLocation.id);
      fetchNearbyParks(selectedLocation.id);
    }
  };

  // Enhanced property navigation to fetch new data
  const nextProperty = () => {
    if (locationsAtPoint.length <= 1) return;
    const nextIndex = (currentLocationIndex + 1) % locationsAtPoint.length;
    setCurrentLocationIndex(nextIndex);

    const nextLocation = locationsAtPoint[nextIndex];
    setSelected(nextLocation);

    // Fetch data for the new selection
    if (nextLocation.id) {
      fetchNearbyBusStops(nextLocation.id);
      fetchNearbyParks(nextLocation.id);
    }
  };

  const prevProperty = () => {
    if (locationsAtPoint.length <= 1) return;
    const prevIndex =
      (currentLocationIndex - 1 + locationsAtPoint.length) %
      locationsAtPoint.length;
    setCurrentLocationIndex(prevIndex);

    const prevLocation = locationsAtPoint[prevIndex];
    setSelected(prevLocation);

    // Fetch data for the new selection
    if (prevLocation.id) {
      fetchNearbyBusStops(prevLocation.id);
      fetchNearbyParks(prevLocation.id);
    }
  };

  // Filter rentals based on filters - existing code...
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

  // Group locations by coordinates - existing code...
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
      {/* QOL Legend - existing code... */}
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

      {/* Google Map - existing code... */}
      <GoogleMap
        defaultCenter={center}
        defaultZoom={12}
        mapId="cde3df1b3d78f48c"
        className="h-screen w-full"
        disableDefaultUI
        gestureHandling={"greedy"}
        zoomControl={true}
      >
        {/* Markers - existing code... */}
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

        {/* Info Window with enhanced details */}
        {selected.lat !== undefined && selected.long !== undefined && (
          <InfoWindow
            position={{ lat: selected.lat, lng: selected.long }}
            onCloseClick={() => {
              setSelected({} as RentalScore);
              setLocationsAtPoint([]);
              setSelectedLocation(null);
              setNearbyBusStops([]);
              setNearbyParks([]);
            }}
          >
            <div className="w-80 p-4 bg-white rounded-lg shadow-lg text-gray-800 font-sans">
              {/* Title and Price */}
              <h2 className="text-xl font-bold mb-2 text-gray-900">
                {selected.name}
              </h2>
              <p className="text-lg text-blue-600 font-semibold mb-4">
                ${selected.price}/mo
              </p>
              {selected.address !== selected.name && (
                <p className="text-base text-gray-600">{selected.address}</p>
              )}

              {/* Multi-property navigation */}
              {locationsAtPoint.length > 1 && (
                <div className="flex justify-between items-center mb-3 bg-gray-100 p-2 rounded">
                  <button
                    onClick={prevProperty}
                    className="bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
                  >
                    ←
                  </button>
                  <span className="text-sm font-medium">
                    {currentLocationIndex + 1} of {locationsAtPoint.length}{" "}
                    properties
                  </span>
                  <button
                    onClick={nextProperty}
                    className="bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
                  >
                    →
                  </button>
                </div>
              )}

              {/* Property Details Grid */}
              <div className="grid grid-cols-2 gap-y-3 text-sm">
                {/* Basic details - existing code... */}
                <div className="font-medium flex items-center">
                  <span className="mr-2">🌟</span> QOL:
                </div>
                <div>{selected.qolScore}</div>

                <div className="font-medium flex items-center">
                  <span className="mr-2">📍</span> State:
                </div>
                <div>{selected.state}</div>

                <div className="font-medium flex items-center">
                  <span className="mr-2">🛏️</span> Bedroom:
                </div>
                <div>{selected.bedroom}</div>

                <div className="font-medium flex items-center">
                  <span className="mr-2">🛁</span> Bathroom:
                </div>
                <div>{selected.bathroom}</div>

                <div className="font-medium flex items-center">
                  <span className="mr-2">🚶</span> Walkability:
                </div>
                <div>{selected.walkScore}</div>

                <div className="font-medium flex items-center">
                  <span className="mr-2">🌬️</span> Air Quality:
                </div>
                <div>{selected.airQualityScore}</div>

                {/* Streamlined Bus Stops Section */}
                <div className="font-medium flex items-center">
                  <span className="mr-2">🚌</span> Bus Stops:
                </div>
                <div className="flex flex-col">
                  {isLoadingBusStops ? (
                    <div className="text-xs text-gray-500">
                      Loading bus stops...
                    </div>
                  ) : (
                    <details className="text-xs">
                      <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                        {selected.busStopsNumber} nearby stops
                      </summary>
                      <div className="max-h-32 overflow-y-auto mt-1 pl-2 pr-1">
                        <p className="mb-1 text-gray-700">
                          <span className="font-medium">Nearest:</span>{" "}
                          {selected.nearestBusStopDistance.toFixed(2)} miles
                        </p>
                        <ul className="list-disc pl-4">
                          {nearbyBusStops.slice(0, 10).map((stop, idx) => (
                            <li key={idx} className="mb-1">
                              {stop}
                            </li>
                          ))}
                          {nearbyBusStops.length > 10 && (
                            <li className="text-gray-500">
                              +{nearbyBusStops.length - 10} more stops
                            </li>
                          )}
                        </ul>
                      </div>
                    </details>
                  )}
                </div>

                {/* Streamlined Parks Section */}
                <div className="font-medium flex items-center">
                  <span className="mr-2">🌳</span> Parks:
                </div>
                <div className="flex flex-col">
                  {isLoadingParks ? (
                    <div className="text-xs text-gray-500">
                      Loading parks...
                    </div>
                  ) : (
                    <details className="text-xs">
                      <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                        {selected.openStreetNumber} nearby parks
                      </summary>
                      <div className="mt-1 pl-2">
                        <p className="mb-1 text-gray-700">
                          <span className="font-medium">Nearest:</span>{" "}
                          {selected.nearestParkDistance.toFixed(2)} miles
                        </p>
                        <ul className="list-disc pl-4">
                          {nearbyParks.map((park, idx) => (
                            <li key={idx} className="mb-1">
                              {park}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </details>
                  )}
                </div>

                <div className="font-medium flex items-center">
                  <span className="mr-2">⭐</span> Reviews:
                </div>
                <div>
                  {selected.reviewScore === 0 ? "NA" : selected.reviewScore}
                </div>
              </div>
            </div>
          </InfoWindow>
        )}
      </GoogleMap>
    </div>
  );
};

export default Map;
