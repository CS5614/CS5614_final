import { useState } from "react";
import Map from "./components/Map";
import RentalFilter from "./components/RentalFilter";
import { MapFilter, RentalScore } from "./type";
import { RentalScoreProvider } from "./contexts/RentalScoreContext";
import { defaultFilters } from "./consts/defaultFilters";
import ComparisonPanel from "./components/ComparisonPanel";
import "./App.css";

const App: React.FC = () => {
  const [filters, setFilters] = useState<MapFilter>(defaultFilters);
  const [comparisonList, setComparisonList] = useState<RentalScore[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const handleToggleCompare = (property: RentalScore) => {
    setComparisonList((prevList) => {
      const isAlreadyInList = prevList.some((item) => item.id === property.id);
      if (isAlreadyInList) {
        return prevList.filter((item) => item.id !== property.id);
      } else if (prevList.length < 3) {
        return [...prevList, property];
      }
      return prevList;
    });
  };

  const handleClearCompare = () => {
    setComparisonList([]);
  };

  return (
    <div className="h-screen w-screen flex flex-col md:flex-row overflow-hidden">
      <div className="md:hidden w-full bg-white shadow-md z-20 flex justify-between items-center p-2">
        <h1 className="text-lg font-bold text-gray-800">QoLScope</h1>
        <button onClick={() => setIsSidebarOpen(true)} className="p-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
            <path fillRule="evenodd" d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5z"/>
          </svg>
        </button>
      </div>

      {/* --- FIXED: Set to full height; scrolling is now handled inside RentalFilter --- */}
      <div
        className={`fixed inset-y-0 left-0 z-30 w-80 bg-white shadow-lg transform ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        } transition-transform duration-300 ease-in-out md:relative md:h-full md:translate-x-0`}
      >
        <RentalFilter
          filters={filters}
          setFilters={setFilters}
          onClose={() => setIsSidebarOpen(false)}
        />
      </div>
      
      <div className="flex-1 h-full relative p-0 m-0">
        <RentalScoreProvider>
          <Map
            filters={filters}
            comparisonList={comparisonList}
            onToggleCompare={handleToggleCompare}
          />
        </RentalScoreProvider>
      </div>
      <ComparisonPanel
        comparisonList={comparisonList}
        onRemove={(propertyId: number) => handleToggleCompare({ id: propertyId } as RentalScore)}
        onClear={handleClearCompare}
      />
    </div>
  );
};

export default App;