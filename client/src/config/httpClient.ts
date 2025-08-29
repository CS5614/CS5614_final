import axios from 'axios';

// Determine base URL based on environment (Vite uses import.meta.env.MODE)
const baseURL = import.meta.env.VITE_API_BASE_URL || '';
console.log('API Base URL:', baseURL);
const httpClient = axios.create({
    baseURL,
    // You can add more default config here (headers, timeout, etc.)
});

export default httpClient;
