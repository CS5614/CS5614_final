export interface RentalScore {
    lat: number;
    long: number;
    name: string;
    qolScore: number;
    walkScore: number;
    transitScore: number;
    bikeScore: number;
    airQualityScore: number;
    busStopsNumber: number;
    metroStationNumber: number;
    openStreetNumber: number;
    reviewScore: number;
    price: number;
}

export interface MapFilter {
    QolScore: number;
    WalkScore: number;
    BusStopsNumber: number;
    Price: number;
    AirQualityScore: number;
    ParkNumber: number;
    Review: number;
    SearchQuery: string;
}