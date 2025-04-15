import { useState, useEffect, useContext } from "react";
import {
  GoogleMap,
  Marker,
  InfoWindow,
  useJsApiLoader,
} from "@react-google-maps/api";
import { RentalScoreContext } from "../contexts/RentalScoreContext";
import { config } from "../config/index";
import { RentalScore } from "../type";
import "../assets/css/Map.css";
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
  locations: RentalScore[],
  filters: MapFilter
): RentalScore[] {
  const filter = locations.filter((loc) => {
    if (loc.qolScore < filters.fQolScore) return false;
    if (loc.walkScore < filters.fWalkScore) return false;
    if (loc.busStopsNumber < filters.fBusStopsNumber) return false;

    // Fuzzy search by name
    if (
      filters.searchQuery &&
      !loc.name.toLowerCase().includes(filters.searchQuery.toLowerCase())
    ) {
      return false;
    }

    return true;
  });
  console.log("Filtered locations:", filter);
  return filter;
}
interface MapFilter {
  fQolScore: number;
  fWalkScore: number;
  fBusStopsNumber: number;
  searchQuery: string; // New property for fuzzy search
}
function MapComponent() {
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: config.googleMapsApiKey,
  });

  const rentalScores = useContext(RentalScoreContext);

  const [filteredLocations, setFilteredLocations] = useState<RentalScore[]>([]);
  const [selected, setSelected] = useState<RentalScore>({} as RentalScore);
  const [filters, setFilters] = useState<MapFilter>({
    fQolScore: 0,
    fWalkScore: 0,
    fBusStopsNumber: 0,
    searchQuery: "", // Initialize search query
  });

  useEffect(() => {
    console.log("Rental Scores:", rentalScores);
    console.log("Filters:", filters);

    const filtered = filterRentalLocations(rentalScores, {
      fQolScore: filters.fQolScore,
      fWalkScore: filters.fWalkScore,
      fBusStopsNumber: filters.fBusStopsNumber,
      searchQuery: filters.searchQuery,
    });

    console.log("Filtered Locations:", filtered);
    setFilteredLocations(filtered);
  }, [rentalScores, filters]);

  if (!isLoaded) return <div>Loading Map...</div>;

  return (
    <div>
      <div className="filter-container">
        <h3>Filters</h3>
        <label>
          Search by Name:
          <input
            type="text"
            value={filters.searchQuery}
            onChange={(e) =>
              setFilters({
                ...filters,
                searchQuery: e.target.value,
              })
            }
          />
        </label>
        <label>
          Min QOL Score:
          <input
            type="range"
            value={filters.fQolScore}
            onChange={(e) =>
              setFilters({
                ...filters,
                fQolScore: Number(e.target.value),
              })
            }
          />
          <span>{filters.fQolScore}</span>
        </label>
        <label>
          Min Walk Score:
          <input
            type="range"
            value={filters.fWalkScore}
            onChange={(e) =>
              setFilters({
                ...filters,
                fWalkScore: Number(e.target.value),
              })
            }
          />
          <span>{filters.fWalkScore}</span>
        </label>
        <label>
          Min Bus Stops Number:
          <input
            type="range"
            value={filters.fBusStopsNumber}
            onChange={(e) =>
              setFilters({
                ...filters,
                fBusStopsNumber: Number(e.target.value),
              })
            }
          />
          <span>{filters.fBusStopsNumber}</span>
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

        {selected.lat !== undefined && selected.long !== undefined && (
          <InfoWindow
            position={{ lat: selected.lat, lng: selected.long }}
            onCloseClick={() => setSelected({} as RentalScore)}
          >
            <div className="rentalDetails">
              <strong>{selected.name}</strong>
              <ul className="p-0 list-none">
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
