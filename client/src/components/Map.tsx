import { useState, useEffect, useContext } from "react";
import {
  GoogleMap,
  Marker,
  InfoWindow,
  useJsApiLoader,
} from "@react-google-maps/api";
import { RentalScoreContext } from "../contexts/RentalScoreContext";
import { config } from "../config/index";
import { MapFilter, RentalScore } from "../type";

const containerStyle = {
  width: "100%",
  height: "100vh",
};

const center = {
  lat: 38.9072,
  lng: -77.0369,
};

const getColorByQOL = (score: number) => {
  if (score >= 80) return "green";
  if (score >= 60) return "yellow";
  if (score >= 40) return "orange";
  return "red";
};

const Map: React.FC<{ filters: MapFilter }> = ({ filters }) => {
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: config.googleMapsApiKey,
  });

  const rentalScores = useContext(RentalScoreContext);
  const [filteredLocations, setFilteredLocations] = useState<RentalScore[]>([]);
  const [selected, setSelected] = useState<RentalScore>({} as RentalScore);

  // Add a legend for QOL color indicators
  const qolLegend = [
    { color: "green", range: "80+" },
    { color: "yellow", range: "60-79" },
    { color: "orange", range: "40-59" },
    { color: "red", range: "Below 40" },
  ];

  useEffect(() => {
    const filtered = filterRentalLocations(rentalScores, filters);
    setFilteredLocations(filtered);
  }, [rentalScores, filters]);

  const filterRentalLocations = (
    locations: RentalScore[],
    filters: MapFilter
  ): RentalScore[] => {
    return locations.filter((loc) => {
      if (loc.qolScore < filters.QolScore) return false;
      if (loc.walkScore < filters.WalkScore) return false;
      if (loc.busStopsNumber < filters.BusStopsNumber) return false;
      if (loc.price < filters.Price) return false;
      if (loc.airQualityScore < filters.AirQualityScore) return false;
      if (loc.openStreetNumber < filters.ParkNumber) return false;
      if (loc.reviewScore < filters.Review) return false;
      if (loc.bathroom < filters.Bathroom) return false;
      if (loc.bedroom < filters.Bedroom) return false;
      if (
        filters.SearchQuery &&
        !loc.name.toLowerCase().includes(filters.SearchQuery.toLowerCase())
      )
        return false;
      return true;
    });
  };

  if (!isLoaded) return <div className="text-center p-6">Loading Map...</div>;

  return (
    <div className="relative">
      {/* QOL Legend */}
      <div className="absolute top-4 left-4 bg-white p-4 rounded shadow-md z-10">
        <h3 className="text-lg font-semibold mb-2 text-gray-900">QOL Legend</h3>
        <ul>
          {qolLegend.map((item, index) => (
            <li key={index} className="flex items-center mb-1 text-gray-700">
              <span
                className={`inline-block w-4 h-4 mr-2 rounded ${
                  item.color === "green"
                    ? "bg-green-300"
                    : item.color === "yellow"
                    ? "bg-yellow-300"
                    : item.color === "orange"
                    ? "bg-orange-300"
                    : "bg-red-300"
                }`}
              ></span>
              <span>{item.range}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Google Map */}
      <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={12}>
        {filteredLocations.map((loc, index) => (
          <Marker
            key={index}
            position={{ lat: loc.lat, lng: loc.long }}
            icon={{
              path: google.maps.SymbolPath.CIRCLE,
              scale: 15, // Adjust scale to keep the oval size appropriate
              fillColor:
                loc.qolScore >= 80
                  ? "#86efac" // Tailwind green-300
                  : loc.qolScore >= 60
                  ? "#fde047" // Tailwind yellow-300
                  : loc.qolScore >= 40
                  ? "#fdba74" // Tailwind orange-300
                  : "#fca5a5", // Tailwind red-300
              fillOpacity: 1,
              strokeWeight: 1,
            }}
            onClick={() => setSelected(loc)}
            label={{
              text: loc.price.toString(),
              color: "black",
              fontSize: "12px",
              fontWeight: "bold",
              className: "text-center", // Ensures text is centered
            }}
          />
        ))}

        {selected.lat !== undefined && selected.long !== undefined && (
          <InfoWindow
            position={{ lat: selected.lat, lng: selected.long }}
            onCloseClick={() => setSelected({} as RentalScore)}
          >
            <div className="w-72 p-4 text-base text-gray-800 font-sans">
              <h2 className="text-lg font-semibold mb-2">{selected.name}</h2>
              <p className="text-gray-600 mb-3 font-medium">
                ${selected.price}/mo
              </p>
              <div className="grid grid-cols-2 gap-y-2 text-sm text-gray-700">
                <span className="font-medium">QOL:</span>{" "}
                <span>{selected.qolScore}</span>
                <span className="font-medium">Walk:</span>{" "}
                <span>{selected.walkScore}</span>
                <span className="font-medium">Bathroom:</span>{" "}
                <span>{selected.bathroom}</span>
                <span className="font-medium">Bedroom:</span>{" "}
                <span>{selected.bedroom}</span>
                <span className="font-medium">Air Quality:</span>{" "}
                <span>{selected.airQualityScore}</span>
                <span className="font-medium">Bus Stops:</span>{" "}
                <span>{selected.busStopsNumber}</span>
                <span className="font-medium">Parks:</span>{" "}
                <span>{selected.openStreetNumber}</span>
                <span className="font-medium">Reviews:</span>{" "}
                <span>{selected.reviewScore}</span>
              </div>
            </div>
          </InfoWindow>
        )}
      </GoogleMap>
    </div>
  );
};

export default Map;
