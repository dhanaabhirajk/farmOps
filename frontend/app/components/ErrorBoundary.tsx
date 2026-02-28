/**
 * Error boundary component for graceful error handling.
 */

import { Component, ErrorInfo, ReactNode } from "react";
import { Alert } from "./ui/Alert";
import { Button } from "./ui/Button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full">
            <Alert variant="error" title="Something went wrong">
              <p className="mb-4">
                {this.state.error?.message || "An unexpected error occurred"}
              </p>
              <div className="flex gap-2">
                <Button onClick={this.handleReset} size="sm">
                  Try Again
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => (window.location.href = "/")}
                >
                  Go Home
                </Button>
              </div>
            </Alert>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
