import { MapFilter } from "../type";

export const defaultFilters: MapFilter = {
  QolScore: 50,
  WalkScore: 0,
  Price: 3000,
  AirQualityScore: 0,
  BusStopsNumber: 0,
  Bedroom: 2,
  Bathroom: 2,
  SearchQuery: "",
  State: ["DC"],
  weights: {
    Price: 0,
    AirQualityScore: 0,
    WalkScore: 0,
    NearestBusStopDistance: 0,
    BusStopsNumber: 0,
    OpenStreetNumber: 0,
    NearestParkDistance: 0,
  },
  useDynamicWeight: false,
};
