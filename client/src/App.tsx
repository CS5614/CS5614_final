import Map from "./components/Map";
import RentalFilter from "./components/RentalFilter";
import { useState } from "react";
import "./App.css";
import { defaultFilters, MapFilter } from "./type";

function App() {
  const [filters, setFilters] = useState<MapFilter>(defaultFilters);

  return (
    <div className="flex h-screen w-screen bg-gray-100">
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
