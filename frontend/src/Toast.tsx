import { useEffect } from "react";
export function Toast({ message, onClose }: { message: string; onClose: () => void }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3000);
    return () => clearTimeout(t);
  }, [onClose]);
  return <div data-testid="success-toast" className="fixed bottom-4 right-4 bg-green-600 text-white px-4 py-2 rounded">{message}</div>;
}
