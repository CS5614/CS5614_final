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
    Price: 20,
    AirQualityScore: 20,
    WalkScore: 20,
    Review: 20,
    GreenSpace: 10,
    PublicTransportation: 10,
  },
  useDynamicWeight: false,
};
