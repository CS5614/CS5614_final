import Map from "./components/Map";
import RentalFilter from "./components/RentalFilter";
import { useState } from "react";
import "./App.css";
import { MapFilter } from "./type";

function App() {
  const [filters, setFilters] = useState<MapFilter>({
    QolScore: 0,
    WalkScore: 0,
    Price: 0,
    AirQualityScore: 0,
    BusStopsNumber: 0,
    ParkNumber: 0,
    Review: 0,
    Bedroom: 0,
    Bathroom: 0,
    SearchQuery: "",
  });

  return (
    <div className="h-screen w-screen bg-gray-100 flex">
      <div className="w-80 bg-white shadow-lg">
        <RentalFilter filters={filters} setFilters={setFilters} />
      </div>
      <div className="flex-1">
        <Map filters={filters} />
      </div>
    </div>
  );
}

export default App;
