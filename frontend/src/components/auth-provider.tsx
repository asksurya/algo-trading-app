"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/stores/auth-store";
import { useRouter, usePathname } from "next/navigation";

/**
 * AuthProvider component that:
 * 1. Initializes auth state on app load
 * 2. Validates stored tokens
 * 3. Handles route protection
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isInitialized, setIsInitialized] = useState(false);
  const { checkAuth, isAuthenticated, token } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Initialize auth on mount
    const initAuth = async () => {
      if (token) {
        // Validate token and fetch user data
        try {
          await checkAuth();
        } catch (error) {
          console.error("Auth check failed:", error);
        }
      }
      setIsInitialized(true);
    };

    initAuth();
  }, []);

  useEffect(() => {
    // Only run route protection after initialization
    if (!isInitialized) return;

    const isAuthRoute = pathname?.startsWith("/login") || pathname?.startsWith("/register");
    const isDashboardRoute = pathname?.startsWith("/dashboard");

    // Redirect to dashboard if authenticated user tries to access auth pages
    if (isAuthenticated && isAuthRoute) {
      router.push("/dashboard");
    }

    // Redirect to login if unauthenticated user tries to access protected routes
    if (!isAuthenticated && isDashboardRoute) {
      router.push("/login");
    }
  }, [isInitialized, isAuthenticated, pathname, router]);

  // Only show loading for protected routes while initializing
  const isDashboardRoute = pathname?.startsWith("/dashboard");

  if (!isInitialized && isDashboardRoute) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  return <>{children}</>;
}
