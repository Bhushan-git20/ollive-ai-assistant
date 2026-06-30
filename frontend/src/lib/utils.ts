import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getApiUrl(path: string): string {
  if (typeof window !== "undefined") {
    if (window.location.port === "3000") {
      return `http://localhost:8000${path}`;
    }
  }
  return path;
}

