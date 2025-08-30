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
    Bedroom: number;
    Bathroom: number;
    SearchQuery: string;
    State: string[];
    weights: {
        Price: number;
        AirQualityScore: number;
        WalkScore: number;
        NearestBusStopDistance: number;
        BusStopsNumber: number;
        OpenStreetNumber: number;
        NearestParkDistance: number;
    };
    useDynamicWeight: boolean;
}