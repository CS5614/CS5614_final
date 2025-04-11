import { GoogleMap, useLoadScript, Marker } from "@react-google-maps/api";
import { config } from "../config";
const containerStyle = {
  width: "100%",
  height: "400px",
};

const center = {
  lat: 37.7749,
  lng: -122.4194,
};

const Map: React.FC = () => {
  console.log("Google Maps API Key:", config.googleMapsApiKey);
  const { isLoaded } = useLoadScript({
    googleMapsApiKey: config.googleMapsApiKey,
  });

  if (!isLoaded) return <div>Loading...</div>;

  return (
    <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={10}>
      <Marker position={center} />
    </GoogleMap>
  );
};

export default Map;
