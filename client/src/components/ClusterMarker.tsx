import React, { useEffect, useRef, useState } from "react";
import { Marker, useMap } from "@vis.gl/react-google-maps";
import {
  Marker as cMarker,
  MarkerClusterer,
  GridAlgorithm,
} from "@googlemaps/markerclusterer";

import { RentalScore } from "../type";
// import { CustomRenderer } from "./CustomRender";

type ClusterMarkerProps = {
  locations: RentalScore[]; // Array of rental locations
  setSelected: (loc: RentalScore) => void; // Function to handle marker selection
  setClusterMarkers: (markers: RentalScore[]) => void; // Function to handle markers in a cluster
};

export const ClusteredMarker: React.FC<ClusterMarkerProps> = ({
  locations,
  setSelected,
}) => {
  const map = useMap();

  const [markers, setMarkers] = useState<{ [key: string]: cMarker }>({});
  const clusterer = useRef<MarkerClusterer | null>(null);

  useEffect(() => {
    if (!map) return;
    if (!clusterer.current) {
      clusterer.current = new MarkerClusterer({
        map,
        algorithm: new GridAlgorithm({
          gridSize: 50,
        }),
      });
    }
  }, [map]);

  useEffect(() => {
    clusterer.current?.clearMarkers();
    clusterer.current?.addMarkers(Object.values(markers));
  }, [markers]);

  const setMarkerRef = (marker: cMarker | null, key: string) => {
    console.log("setMarkerRef called for key:", key, "marker:", marker);

    if (marker && markers[key]) return;
    if (!marker && !markers[key]) return;

    setMarkers((prev) => {
      if (marker) {
        return { ...prev, [key]: marker };
      } else {
        const newMarkers = { ...prev };
        delete newMarkers[key];
        return newMarkers;
      }
    });
  };
  return (
    <>
      {locations.map((location, index) => {
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
              color:
                location.qolScore >= 80
                  ? "#86efac" // Tailwind green-300
                  : location.qolScore >= 60
                  ? "#fde047" // Tailwind yellow-300
                  : location.qolScore >= 40
                  ? "#fdba74" // Tailwind orange-300
                  : "#fca5a5", // Tailwind red-300
              fontSize: "12px",
              fontWeight: "bold",
            }}
            ref={(marker) => setMarkerRef(marker, location.name)}
          ></Marker>
        );
      })}
    </>
  );
};
