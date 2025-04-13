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
  crimeNumber: number;
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

function MapComponent() {
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: config.googleMapsApiKey,
  });

  const [locations, setLocations] = useState<RentalScoreLocation[]>([]);
  const [selected, setSelected] = useState<RentalScoreLocation | null>(null);

  useEffect(() => {
    fetchRentalQol(setLocations);
  }, []);

  if (!isLoaded) return <div>Loading Map...</div>;

  return (
    <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={12}>
      {locations.map((loc, index) => (
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
              <li>Crime Reports: {selected.crimeNumber}</li>
              <li>Bus Stops: {selected.busStopsNumber}</li>
              <li>Metro Stations: {selected.metroStationNumber}</li>
              <li>Parks Nearby: {selected.openStreetNumber}</li>
              <li>Review Score: {selected.reviewScore}</li>
            </ul>
          </div>
        </InfoWindow>
      )}
    </GoogleMap>
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
  const mockRentalScore: RentalScoreLocation = {
    lat: 38.929782,
    long: -76.990611,
    name: "3207 12th St NE, Unit 101, Washington, DC 20017",
    qolScore: 72,
    walkScore: 85,
    transitScore: 78,
    bikeScore: 67,
    airQualityScore: 90,
    crimeNumber: 12,
    busStopsNumber: 5,
    metroStationNumber: 2,
    openStreetNumber: 3,
    reviewScore: 4.3,
  };
  setLocations([mockRentalScore]);
}
