import { useState, useEffect, useContext } from "react";
import Map from "./components/Map";
import RentalFilter from "./components/RentalFilter";
import { MapFilter, RentalScore } from "./type";
import { RentalScoreProvider, RentalScoreContext } from "./contexts/RentalScoreContext";
import { defaultFilters } from "./consts/defaultFilters";
import ComparisonPanel from "./components/ComparisonPanel";
import Chatbot from "./components/Chatbot";
import "./App.css";
import httpClient from "./services/httpClient";

const AppContent: React.FC = () => {
  const { updateQolScores } = useContext(RentalScoreContext);
  const [filters, setFilters] = useState<MapFilter>(defaultFilters);
  const [comparisonList, setComparisonList] = useState<RentalScore[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    httpClient.get<any>("/api/dynamicQol/defaultWeights").then((response) => {
      const data = response.data;
      const backendWeights = {
        Price: data.price ?? 0,
        AirQualityScore: data.airQualityScore ?? 0,
        WalkScore: data.walkScore ?? 0,
        NearestBusStopDistance: data.nearestBusStopDistance ?? 0,
        BusStopsNumber: data.busStopsNumber ?? 0,
        OpenStreetNumber: data.openStreetNumber ?? 0,
        NearestParkDistance: data.nearestParkDistance ?? 0,
      };

      const scaledWeights: [string, number][] = Object.entries(backendWeights).map(([key, value]) => [
        key,
        Math.round(value * 100)
      ]);

      const currentSum = scaledWeights.reduce((sum, [, value]) => sum + value, 0);
      const difference = 100 - currentSum;

      if (difference !== 0) {
        const maxIndex = scaledWeights.reduce((maxIdx, [, value], idx) =>
          value > scaledWeights[maxIdx][1] ? idx : maxIdx, 0);
        scaledWeights[maxIndex][1] += difference;
      }

      const finalWeights = Object.fromEntries(scaledWeights) as {
        Price: number;
        AirQualityScore: number;
        WalkScore: number;
        NearestBusStopDistance: number;
        BusStopsNumber: number;
        OpenStreetNumber: number;
        NearestParkDistance: number;
      };

      setFilters(prevFilters => ({
        ...prevFilters,
        weights: finalWeights
      }));
    })
    .catch(console.error);
  }, [updateQolScores]);

  const handleQolUpdate = (qolScores: RentalScore[]) => {
    try {
      updateQolScores(qolScores);
      console.log('Dynamic QoL scores updated:', qolScores);
    } catch (error) {
      console.error('Failed to update QoL scores in context:', error);
    }
  };

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
        <button onClick={() => setIsSidebarOpen(true)} className="p-2" title="Open filters">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
            <path fillRule="evenodd" d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5z"/>
          </svg>
        </button>
      </div>

      <div
        className={`fixed inset-y-0 left-0 z-30 w-80 bg-white shadow-lg transform ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        } transition-transform duration-300 ease-in-out md:relative md:h-full md:translate-x-0`}
      >
        <RentalFilter
          filters={filters}
          setFilters={setFilters}
          onClose={() => setIsSidebarOpen(false)}
          onQolUpdate={handleQolUpdate}
        />
      </div>

      <div className="flex-1 h-full relative p-0 m-0">
        <Map
          filters={filters}
          comparisonList={comparisonList}
          onToggleCompare={handleToggleCompare}
        />
      </div>
      <ComparisonPanel
        comparisonList={comparisonList}
        onRemove={(propertyId: number) => handleToggleCompare({ id: propertyId } as RentalScore)}
        onClear={handleClearCompare}
      />
      <Chatbot />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <RentalScoreProvider>
      <AppContent />
    </RentalScoreProvider>
  );
};

export default App;