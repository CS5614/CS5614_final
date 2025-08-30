
import httpClient from '../services/httpClient';

// Type for default weights response
export interface DefaultWeightsResponse {
  Price: number;
  AirQualityScore: number;
  WalkScore: number;
  Review: number;
}

/**
 * Fetch default weights for dynamic scoring from the server.
 * @returns Promise<DefaultWeightsResponse>
 */
export async function getDefaultWeights(): Promise<DefaultWeightsResponse> {
  try {
    const response = await httpClient.get<DefaultWeightsResponse>("/api/default-weights");
    if (response.data) {
      return response.data;
    } else {
      throw new Error("Default weights not found in server response.");
    }
  } catch (error) {
    console.error("Failed to fetch default weights:", error);
    throw new Error("Could not retrieve default weights.");
  }
}


let cachedApiKey: string | null = null;
interface AppConfigResponse { googleMapsApiKey: string; }

export async function getGoogleMapsApiKey(): Promise<string> {
  if (cachedApiKey) return cachedApiKey;
  try {
    const response = await httpClient.get<AppConfigResponse>('/api/config');
    if (response.data && response.data.googleMapsApiKey) {
      cachedApiKey = response.data.googleMapsApiKey;
      return cachedApiKey;
    } else {
      throw new Error('API key not found in server response.');
    }
  } catch (error) {
    console.error('Failed to fetch Google Maps API key:', error);
    throw new Error('Could not retrieve map configuration.');
  }
}