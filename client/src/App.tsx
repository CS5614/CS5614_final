import Map from "./components/Map";
import "./App.css";

function App() {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold">Google Maps in React with Vite</h1>
      <div className="flex w-full max-w-6xl gap-6">
        <div className="w-80"></div>
        <div className="flex-1 rounded-xl overflow-hidden shadow-lg">
          <Map />
        </div>
      </div>
    </div>
  );
}

export default App;
