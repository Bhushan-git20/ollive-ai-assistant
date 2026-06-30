import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getApiUrl(path: string): string {
  let baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";

  if (!baseUrl && typeof window !== "undefined") {
    if (window.location.port === "3000") {
      baseUrl = "http://localhost:8000";
    }
  }

  if (baseUrl) {
    const normalizedBase = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    return `${normalizedBase}${normalizedPath}`;
  }

  return path;
}

