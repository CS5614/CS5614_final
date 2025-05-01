import Map from "./components/Map";
import RentalFilter from "./components/RentalFilter";
import { useState } from "react";
import "./App.css";
import { MapFilter } from "./type";
import { RentalScoreProvider } from "./contexts/RentalScoreContext";
import { APIProvider } from "@vis.gl/react-google-maps";
import { config } from "./config";
import { defaultFilters } from "./consts/defaultFilters";

const App: React.FC = () => {
  const [filters, setFilters] = useState<MapFilter>(defaultFilters);

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="w-80 bg-white shadow-lg z-10 overflow-y-auto">
        <RentalFilter filters={filters} setFilters={setFilters} />
      </div>
      <div className="flex-1 h-full relative p-0 m-0">
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
