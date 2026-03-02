// Global type augmentations for FarmOps frontend

interface Window {
  ENV: {
    SUPABASE_URL: string;
    SUPABASE_ANON_KEY: string;
    API_URL?: string;
    [key: string]: string | undefined;
  };
}
