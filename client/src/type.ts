export interface RentalScore {
    id: number;
    lat: number;
    long: number;
    name: string;
    qolScore: number;
    walkScore: number;
    airQualityScore: number;
    busStopsNumber: number;
    nearestBusStopDistance: number;
    openStreetNumber: number;
    nearestParkDistance: number;
    reviewScore: number;
    price: number;
    bedroom: number;
    bathroom: number;
    state: string;
    address: string;
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
    State: string[];
}