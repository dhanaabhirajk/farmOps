import type { LinksFunction, MetaFunction } from "@remix-run/node";
import {
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useNavigation,
  useRouteError,
} from "@remix-run/react";
import tailwindStyles from "./styles/tailwind.css?url";

export const links: LinksFunction = () => [
  { rel: "stylesheet", href: tailwindStyles },
];

export const meta: MetaFunction = () => {
  return [
    { title: "FarmOps - Location-Based Insights for Tamil Nadu Farmers" },
    {
      name: "description",
      content: "AI-powered agricultural insights for Tamil Nadu farmers",
    },
    { name: "viewport", content: "width=device-width,initial-scale=1" },
  ];
};

export default function App() {
  const navigation = useNavigation();
  const isNavigating = navigation.state === "loading";

  return (
    <html lang="ta">
      <head>
        <meta charSet="utf-8" />
        <Meta />
        <Links />
      </head>
      <body className="min-h-screen bg-gray-50">
        {/* Global top progress bar */}
        {isNavigating && (
          <div className="fixed top-0 left-0 right-0 z-50 h-1 bg-green-100">
            <div className="h-1 bg-green-500 animate-pulse" style={{ width: "70%" }} />
          </div>
        )}
        <Outlet />
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export function ErrorBoundary() {
  const error = useRouteError();

  return (
    <html lang="ta">
      <head>
        <title>Error - FarmOps</title>
        <Meta />
        <Links />
      </head>
      <body className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
          <h1 className="text-2xl font-bold text-red-600 mb-4">
            Something went wrong
          </h1>
          <p className="text-gray-700 mb-4">
            {error instanceof Error ? error.message : "Unknown error occurred"}
          </p>
          <a
            href="/"
            className="inline-block bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Go Home
          </a>
        </div>
        <Scripts />
      </body>
    </html>
  );
}
