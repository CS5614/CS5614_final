import Map from "./components/Map";
import RentalFilter from "./components/RentalFilter";
import { useState } from "react";
import "./App.css";
import { MapFilter } from "./type";
import { RentalScoreProvider } from "./contexts/RentalScoreContext";
import { APIProvider } from "@vis.gl/react-google-maps";
import { config } from "./config";

export const defaultFilters: MapFilter = {
  QolScore: 50,
  WalkScore: 0,
  Price: 3000,
  AirQualityScore: 0,
  BusStopsNumber: 0,
  ParkNumber: 0,
  Review: 0,
  Bedroom: 2,
  Bathroom: 2,
  SearchQuery: "",
  State: ["VA"],
};
const App: React.FC = () => {
  const [filters, setFilters] = useState<MapFilter>(defaultFilters);

  return (
    <div className="h-screen w-screen bg-gray-100 flex">
      <div className="w-80 bg-white shadow-lg">
        <RentalFilter filters={filters} setFilters={setFilters} />
      </div>
      <div className="flex-1">
        <RentalScoreProvider>
          <APIProvider apiKey={config.googleMapsApiKey}>
            <Map filters={filters} />
          </APIProvider>
        </RentalScoreProvider>
      </div>
    </div>
  );
};

export default App;
