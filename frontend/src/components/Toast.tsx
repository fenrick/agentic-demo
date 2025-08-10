import React, { useEffect } from "react";

interface Props {
  /** Message to display inside the toast. */
  message: string;
  /** Callback fired when the toast is dismissed. */
  onClose: () => void;
  /** How long the toast stays visible in milliseconds. */
  duration?: number;
}

/**
 * Simple toast notification that auto-dismisses after a delay.
 */
const Toast: React.FC<Props> = ({ message, onClose, duration = 3000 }) => {
  useEffect(() => {
    const id = window.setTimeout(onClose, duration);
    return () => window.clearTimeout(id);
  }, [duration, onClose]);

  return (
    <div
      data-testid="toast"
      className="fixed right-4 bottom-4 rounded bg-gray-800 px-4 py-2 text-white shadow"
      role="status"
    >
      {message}
    </div>
  );
};

export default Toast;
