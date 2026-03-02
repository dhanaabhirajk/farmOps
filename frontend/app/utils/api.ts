export async function fetchFarmSnapshot(farmId: string) {
  const response = await fetch(`${process.env.API_URL || 'http://localhost:8000'}/api/v1/farm/snapshot?farm_id=${farmId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch farm snapshot');
  }
  return response.json();
}

export async function fetchWeather(lat: number, lon: number) {
  // In a real app, this might go through a backend proxy to keep keys secret
  // or use the backend's weather service via an API endpoint.
  // For now, we'll assume the snapshot endpoint includes weather.
  return null; 
}
