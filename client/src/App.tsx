import Map from "./components/Map";
import RentalFilter from "./components/RentalFilter";
import { useState } from "react";
import { MapFilter } from "./components/Map";
import "./App.css";

function App() {
  const [filters, setFilters] = useState<MapFilter>({
    fQolScore: 0,
    fWalkScore: 0,
    fBusStopsNumber: 0,
    fPrice: 0,
    searchQuery: "",
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
