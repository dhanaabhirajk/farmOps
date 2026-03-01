/// <reference types="vite/client" />

declare module "*.css" {
  const content: string;
  export default content;
}

declare module "*.css?url" {
  const content: string;
  export default content;
}

// Declare Vite URL import pattern
declare module "*?url" {
  const url: string;
  export default url;
}

// Extend Window to include ENV injected by root loader
declare global {
  interface Window {
    ENV: {
      SUPABASE_URL: string;
      SUPABASE_ANON_KEY: string;
      API_URL?: string;
      [key: string]: string | undefined;
    };
  }
}

export {};

