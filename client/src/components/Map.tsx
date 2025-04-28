import { useState, useEffect, useContext } from "react";
import {
  Map as GoogleMap,
  InfoWindow,
  Marker,
} from "@vis.gl/react-google-maps";

import { RentalScoreContext } from "../contexts/RentalScoreContext";

import { MapFilter, RentalScore } from "../type";
// import { ClusteredMarker } from "./ClusterMarker";

const center = {
  lat: 38.9072,
  lng: -77.0369,
};

const Map: React.FC<{ filters: MapFilter }> = ({ filters }) => {
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
    console.log("Filtered length:", filtered.length);
    setFilteredLocations(filtered);
  }, [rentalScores, filters]);

  const filterRentalLocations = (
    locations: RentalScore[],
    filters: MapFilter
  ): RentalScore[] => {
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
        filters.SearchQuery &&
        !loc.name.toLowerCase().includes(filters.SearchQuery.toLowerCase())
      )
        return false;
      return true;
    });
  };

  // if (!isLoaded) return <div className="text-center p-6">Loading Map...</div>;

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
      <GoogleMap
        defaultCenter={center}
        defaultZoom={10}
        mapId="cde3df1b3d78f48c"
        className="h-screen w-full"
        disableDefaultUI
        gestureHandling={"greedy"}
        zoomControl={true}
      >
        {/* <ClusteredMarker
          locations={filteredLocations}
          setSelected={setSelected}
          setClusterMarkers={setClusterMarkers}
        /> */}
        {filteredLocations.map((location, index) => {
          return (
            <Marker
              key={index}
              position={{ lat: location.lat, lng: location.long }}
              icon={{
                path: google.maps.SymbolPath.CIRCLE,
                scale: 15, // Adjust scale to keep the oval size appropriate
                fillColor:
                  location.qolScore >= 80
                    ? "#86efac" // Tailwind green-300
                    : location.qolScore >= 60
                    ? "#fde047" // Tailwind yellow-300
                    : location.qolScore >= 40
                    ? "#fdba74" // Tailwind orange-300
                    : "#fca5a5", // Tailwind red-300
                fillOpacity: 1,
                strokeWeight: 1,
              }}
              onClick={() => setSelected(location)}
              label={{
                text: location.price.toString(),
                color: "black",
                fontSize: "12px",
                fontWeight: "bold",
              }}
              // ref={(marker) => setMarkerRef(marker, location.name)}
            ></Marker>
          );
        })}

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
