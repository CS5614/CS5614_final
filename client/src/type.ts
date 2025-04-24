export interface RentalScore {
    lat: number;
    long: number;
    name: string;
    qolScore: number;
    walkScore: number;
    airQualityScore: number;
    busStopsNumber: number;
    openStreetNumber: number;
    reviewScore: number;
    price: number;
    bedroom: number;
    bathroom: number;
}

export interface MapFilter {
    QolScore: number;
    WalkScore: number;
    BusStopsNumber: number;
    Price: number;
    AirQualityScore: number;
    ParkNumber: number;
    Review: number;
    Bedroom: number;
    Bathroom: number;
    SearchQuery: string;
}

export const defaultFilters: MapFilter = {
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
};