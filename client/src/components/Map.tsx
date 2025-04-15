import React, { useState, useEffect } from "react";
import {
  GoogleMap,
  Marker,
  InfoWindow,
  useJsApiLoader,
} from "@react-google-maps/api";
import axios from "axios";
import { config } from "../config/index";
export interface RentalScoreLocation {
  lat: number;
  long: number;
  name: string;
  qolScore: number;
  walkScore: number;
  transitScore: number;
  bikeScore: number;
  airQualityScore: number;
  busStopsNumber: number;
  metroStationNumber: number;
  openStreetNumber: number;
  reviewScore: number;
}

const containerStyle = {
  width: "100%",
  height: "600px",
};

const center = {
  lat: 38.9072, // Default to Washington, DC
  lng: -77.0369,
};

// Color mapping based on qolScore ranges
const getColorByQOL = (score: number) => {
  if (score >= 80) return "green";
  if (score >= 60) return "yellow";
  if (score >= 40) return "orange";
  return "red";
};

function filterRentalLocations(
  locations: RentalScoreLocation[],
  filters: {
    fQolScore: number;
    fCrimeNumber: number;
    fWalkScore: number;
    fBusStopsNumber: number;
  }
): RentalScoreLocation[] {
  return locations.filter((loc) => {
    if (filters.fQolScore !== undefined && loc.qolScore < filters.fQolScore)
      return false;
    if (
      filters.fCrimeNumber !== undefined &&
      loc.crimeNumber > filters.fCrimeNumber
    )
      return false;
    if (filters.fWalkScore !== undefined && loc.walkScore < filters.fWalkScore)
      return false;
    if (
      filters.fBusStopsNumber !== undefined &&
      loc.busStopsNumber > filters.fBusStopsNumber
    )
      return false;
    return true;
  });
}

function MapComponent() {
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: config.googleMapsApiKey,
  });

  const [locations, setLocations] = useState<RentalScoreLocation[]>([]);
  const [filteredLocations, setFilteredLocations] = useState<
    RentalScoreLocation[]
  >([]);
  const [selected, setSelected] = useState<RentalScoreLocation | null>(null);
  const [filters, setFilters] = useState({
    minQolScore: 0,
    maxCrimeNumber: 0,
    minWalkScore: 0,
    maxBusStopsNumber: 0,
  });

  useEffect(() => {
    fetchRentalQol(setLocations);
  }, []);

  useEffect(() => {
    setFilteredLocations(
      filterRentalLocations(locations, {
        fQolScore: filters.minQolScore,
        fCrimeNumber: filters.maxCrimeNumber,
        fWalkScore: filters.minWalkScore,
        fBusStopsNumber: filters.maxBusStopsNumber,
      })
    );
  }, [locations, filters]);

  if (!isLoaded) return <div>Loading Map...</div>;

  return (
    <div>
      <div className="filter-container">
        <h3>Filters</h3>
        <label>
          Min QOL Score:
          <input
            type="range"
            value={filters.minQolScore}
            onChange={(e) =>
              setFilters({
                ...filters,
                minQolScore: Number(e.target.value),
              })
            }
          />
          <span>{filters.minQolScore}</span>
        </label>
        <label>
          Max Crime Number:
          <input
            type="range"
            value={filters.maxCrimeNumber}
            onChange={(e) =>
              setFilters({
                ...filters,
                maxCrimeNumber: Number(e.target.value),
              })
            }
          />
          <span>{filters.maxCrimeNumber}</span>
        </label>
        <label>
          Min Walk Score:
          <input
            type="range"
            value={filters.minWalkScore}
            onChange={(e) =>
              setFilters({
                ...filters,
                minWalkScore: Number(e.target.value),
              })
            }
          />
          <span>{filters.minWalkScore}</span>
        </label>
        <label>
          Max Bus Stops Number:
          <input
            type="range"
            value={filters.maxBusStopsNumber}
            onChange={(e) =>
              setFilters({
                ...filters,
                maxBusStopsNumber: Number(e.target.value),
              })
            }
          />
          <span>{filters.maxBusStopsNumber}</span>
        </label>
      </div>

      <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={12}>
        {filteredLocations.map((loc, index) => (
          <Marker
            key={index}
            position={{ lat: loc.lat, lng: loc.long }}
            icon={{
              path: google.maps.SymbolPath.CIRCLE,
              scale: 10,
              fillColor: getColorByQOL(loc.qolScore),
              fillOpacity: 1,
              strokeWeight: 1,
            }}
            onClick={() => {
              setSelected(loc);
            }}
          />
        ))}

        {selected && (
          <InfoWindow
            position={{ lat: selected.lat, lng: selected.long }}
            onCloseClick={() => setSelected(null)}
          >
            <div style={{ fontSize: "14px", color: "black" }}>
              <strong>{selected.name}</strong>
              <ul style={{ padding: 0, listStyle: "none" }}>
                <li>QOL Score: {selected.qolScore}</li>
                <li>Walk Score: {selected.walkScore}</li>
                <li>Transit Score: {selected.transitScore}</li>
                <li>Bike Score: {selected.bikeScore}</li>
                <li>Air Quality: {selected.airQualityScore}</li>
                <li>Bus Stops: {selected.busStopsNumber}</li>
                <li>Metro Stations: {selected.metroStationNumber}</li>
                <li>Parks Nearby: {selected.openStreetNumber}</li>
                <li>Review Score: {selected.reviewScore}</li>
              </ul>
            </div>
          </InfoWindow>
        )}
      </GoogleMap>
    </div>
  );
}

export default MapComponent;
//todo fetch real data from backend
function fetchRentalQol(
  setLocations: React.Dispatch<React.SetStateAction<RentalScoreLocation[]>>
) {
  // axios
  //   .get<{ data: RentalScoreLocation[]; }>("/api/rentalScore")
  //   .then((response) => {
  //     setLocations(response.data.data);
  //   });
  const mockRentalScores: RentalScoreLocation[] = [
    {
      lat: 38.929782,
      long: -76.990611,
      name: "3207 12th St NE, Unit 101, Washington, DC 20017",
      qolScore: 72,
      walkScore: 85,
      transitScore: 78,
      bikeScore: 67,
      airQualityScore: 90,
      busStopsNumber: 5,
      metroStationNumber: 2,
      openStreetNumber: 3,
      reviewScore: 4.3,
    },
    {
      lat: 38.934567,
      long: -76.995432,
      name: "1234 15th St NW, Unit 202, Washington, DC 20005",
      qolScore: 65,
      walkScore: 80,
      transitScore: 75,
      bikeScore: 70,
      airQualityScore: 85,
      busStopsNumber: 3,
      metroStationNumber: 1,
      openStreetNumber: 2,
      reviewScore: 4.0,
    },
    {
      lat: 38.941234,
      long: -77.005678,
      name: "5678 18th St NW, Unit 303, Washington, DC 20009",
      qolScore: 80,
      walkScore: 90,
      transitScore: 85,
      bikeScore: 75,
      airQualityScore: 95,
      busStopsNumber: 4,
      metroStationNumber: 2,
      openStreetNumber: 5,
      reviewScore: 4.5,
    },
    {
      lat: 38.94789,
      long: -77.012345,
      name: "9101 20th St NW, Unit 404, Washington, DC 20011",
      qolScore: 55,
      walkScore: 70,
      transitScore: 65,
      bikeScore: 60,
      airQualityScore: 80,
      busStopsNumber: 2,
      metroStationNumber: 1,
      openStreetNumber: 1,
      reviewScore: 3.8,
    },
    {
      lat: 38.951234,
      long: -77.020123,
      name: "1123 22nd St NW, Unit 505, Washington, DC 20015",
      qolScore: 78,
      walkScore: 88,
      transitScore: 82,
      bikeScore: 72,
      airQualityScore: 92,
      busStopsNumber: 6,
      metroStationNumber: 3,
      openStreetNumber: 4,
      reviewScore: 4.6,
    },
    {
      lat: 38.95789,
      long: -77.028456,
      name: "1314 25th St NW, Unit 606, Washington, DC 20016",
      qolScore: 62,
      walkScore: 75,
      transitScore: 70,
      bikeScore: 65,
      airQualityScore: 88,
      busStopsNumber: 3,
      metroStationNumber: 2,
      openStreetNumber: 2,
      reviewScore: 4.1,
    },
    {
      lat: 38.963456,
      long: -77.035678,
      name: "1516 Adams Morgan St NW, Unit A, Washington, DC",
      qolScore: 90,
      walkScore: 95,
      transitScore: 90,
      bikeScore: 85,
      airQualityScore: 98,
      busStopsNumber: 7,
      metroStationNumber: 4,
      openStreetNumber: 6,
      reviewScore: 4.9,
    },
  ];
  setLocations(mockRentalScores);
}
