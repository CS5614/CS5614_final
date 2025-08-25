import axios from 'axios'; // Or use fetch

let cachedApiKey: string | null = null;
interface AppConfigResponse { googleMapsApiKey: string; }

export async function getGoogleMapsApiKey(): Promise<string> {
  if (cachedApiKey) return cachedApiKey;
  try {
    // Use relative path assuming same domain deployment
    const response = await axios.get<AppConfigResponse>('/api/config');
    if (response.data && response.data.googleMapsApiKey) {
      cachedApiKey = response.data.googleMapsApiKey;
      return cachedApiKey;
    } else {
      throw new Error('API key not found in server response.');
    }
  } catch (error) {
    console.error('Failed to fetch Google Maps API key:', error);
    // Throw a more specific error for the UI to handle
    throw new Error('Could not retrieve map configuration.');
  }
}