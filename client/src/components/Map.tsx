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
      if (loc.metroStationNumber < filters.BusStopsNumber) return false;
      if (loc.openStreetNumber < filters.ParkNumber) return false;
      if (loc.reviewScore < filters.Review) return false;
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
      {/* Google Map */}
      <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={12}>
        {filteredLocations.map((loc, index) => (
          <Marker
            key={index}
            position={{ lat: loc.lat, lng: loc.long }}
            icon={{
              path: google.maps.SymbolPath.CIRCLE,
              scale: 15, // Adjust scale to keep the oval size appropriate
              fillColor: getColorByQOL(loc.qolScore),
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
            <div className="text-sm space-y-1 text-gray-700">
              <strong className="block text-base">{selected.name}</strong>
              <ul className="list-none p-0">
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
};

export default Map;
