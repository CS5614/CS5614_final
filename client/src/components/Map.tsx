import { useState, useEffect, useContext } from "react";
import {
  AdvancedMarker,
  AdvancedMarkerAnchorPoint,
  Map as GoogleMap,
  InfoWindow,
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
    { color: "green", range: "80+", icon: "🏡" },
    { color: "yellow", range: "60-79", icon: "🏠" },
    { color: "orange", range: "40-59", icon: "🛖" },
    { color: "red", range: "Below 40", icon: "🏚️" },
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
            // <Marker
            //   key={index}
            //   position={{ lat: location.lat, lng: location.long }}
            //   icon={{
            //     path: google.maps.SymbolPath.CIRCLE,
            //     scale: 15, // Adjust scale to keep the oval size appropriate
            //     fillColor:
            //       location.qolScore >= 80
            //         ? "#86efac" // Tailwind green-300
            //         : location.qolScore >= 60
            //         ? "#fde047" // Tailwind yellow-300
            //         : location.qolScore >= 40
            //         ? "#fdba74" // Tailwind orange-300
            //         : "#fca5a5", // Tailwind red-300
            //     fillOpacity: 1,
            //     strokeWeight: 1,
            //   }}
            //   onClick={() => setSelected(location)}
            //   label={{
            //     text: location.price.toString(),
            //     color: "black",
            //     fontSize: "12px",
            //     fontWeight: "bold",
            //   }}
            // />
            <AdvancedMarker
              key={index}
              position={{ lat: location.lat, lng: location.long }}
              onClick={() => setSelected(location)}
              anchorPoint={AdvancedMarkerAnchorPoint.TOP_LEFT}
            >
              <div
                className={`absolute -top-2 -left-2 text-xs font-bold text-gray-800 rounded-full p-1 ${
                  location.qolScore >= 80
                    ? "bg-green-300"
                    : location.qolScore >= 60
                    ? "bg-yellow-300"
                    : location.qolScore >= 40
                    ? "bg-orange-300"
                    : "bg-red-300"
                }`}
              >
                ${location.price}
              </div>
              <span className="text-[2rem] w-full text-center">
                {location.qolScore >= 80
                  ? "🏡"
                  : location.qolScore >= 60
                  ? "🏠"
                  : location.qolScore >= 40
                  ? "🛖"
                  : "🏚️"}
              </span>
              {/* <Pin
                background={
                  location.qolScore >= 80
                    ? "#86efac"
                    : location.qolScore >= 60
                    ? "#fde047"
                    : location.qolScore >= 40
                    ? "#fdba74"
                    : "#fca5a5"
                }
              /> */}
            </AdvancedMarker>
          );
        })}

        {selected.lat !== undefined && selected.long !== undefined && (
          <InfoWindow
            position={{ lat: selected.lat, lng: selected.long }}
            onCloseClick={() => setSelected({} as RentalScore)}
          >
            <div className="w-80 p-4 bg-white rounded-lg shadow-lg text-gray-800 font-sans">
              {/* Title and Price */}
              <h2 className="text-xl font-bold mb-2 text-gray-900">
                {selected.name}
              </h2>
              <p className="text-lg text-blue-600 font-semibold mb-4">
                ${selected.price}/mo
              </p>

              {/* Details Grid */}
              <div className="grid grid-cols-2 gap-y-3 text-sm">
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

                <div className="font-medium flex items-center">
                  <span className="mr-2">🚌</span> Bus Stops:
                </div>
                <div>{selected.busStopsNumber}</div>

                <div className="font-medium flex items-center">
                  <span className="mr-2">🌳</span> Parks:
                </div>
                <div>{selected.openStreetNumber}</div>

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
