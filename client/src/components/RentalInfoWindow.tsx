import { useState, useEffect } from "react";
import { InfoWindow } from "@vis.gl/react-google-maps";
import { RentalScore } from "../type";

// Interfaces for API responses
interface BusStopsResponse {
  nearby_bus_stops: string;
}

interface ParksResponse {
  nearby_parks: string;
}

interface RentalInfoWindowProps {
  selected: RentalScore;
  locationsAtPoint: RentalScore[];
  currentLocationIndex: number;
  onClose: () => void;
  onNextProperty: () => void;
  onPrevProperty: () => void;
}

const RentalInfoWindow: React.FC<RentalInfoWindowProps> = ({
  selected,
  locationsAtPoint,
  currentLocationIndex,
  onClose,
  onNextProperty,
  onPrevProperty,
}) => {
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

  // Fetch data when selected property changes
  useEffect(() => {
    if (selected && selected.id) {
      fetchNearbyBusStops(selected.id);
      fetchNearbyParks(selected.id);
    }
  }, [selected]);

  if (!selected || selected.lat === undefined || selected.long === undefined) {
    return null;
  }

  return (
    <InfoWindow
      position={{ lat: selected.lat, lng: selected.long }}
      onCloseClick={onClose}
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
              onClick={onPrevProperty}
              className="bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
            >
              ←
            </button>
            <span className="text-sm font-medium">
              {currentLocationIndex + 1} of {locationsAtPoint.length} properties
            </span>
            <button
              onClick={onNextProperty}
              className="bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
            >
              →
            </button>
          </div>
        )}

        {/* Property Details Grid */}
        <div className="grid grid-cols-2 gap-y-3 text-sm">
          {/* Basic details */}
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
              <div className="text-xs text-gray-500">Loading bus stops...</div>
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
              <div className="text-xs text-gray-500">Loading parks...</div>
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
          <div>{selected.reviewScore === 0 ? "NA" : selected.reviewScore}</div>
        </div>
      </div>
    </InfoWindow>
  );
};

export default RentalInfoWindow;
