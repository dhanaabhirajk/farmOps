/**
 * Alert component for notifications and messages.
 */

interface AlertProps {
  variant?: "info" | "success" | "warning" | "error";
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function Alert({
  variant = "info",
  title,
  children,
  className = "",
}: AlertProps) {
  const variantClasses = {
    info: "bg-blue-50 border-blue-200 text-blue-800",
    success: "bg-green-50 border-green-200 text-green-800",
    warning: "bg-yellow-50 border-yellow-200 text-yellow-800",
    error: "bg-red-50 border-red-200 text-red-800",
  };

  const iconClasses = {
    info: "text-blue-600",
    success: "text-green-600",
    warning: "text-yellow-600",
    error: "text-red-600",
  };

  return (
    <div
      className={`border-l-4 p-4 ${variantClasses[variant]} ${className}`}
      role="alert"
    >
      {title && (
        <h4 className={`font-bold mb-1 ${iconClasses[variant]}`}>{title}</h4>
      )}
      <div>{children}</div>
    </div>
  );
}
