import { MapFilter } from "../type";

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
  State: ["DC"],
  weights: {
    Price: 25,
    AirQualityScore: 25,
    WalkScore: 25,
    Review: 25,
  },
  useDynamicWeight: false,
};
