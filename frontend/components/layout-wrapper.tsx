"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/sidebar";
import { useAppDispatch, useAppSelector } from "@/store";
import { fetchUsers } from "@/store/slices/users-slice";
import { fetchInvitations } from "@/store/slices/invitations-slice";
import { fetchPractice } from "@/store/slices/practice-slice";
import { websocketClient } from "@/lib/websocket";
import { handleWebSocketEvent } from "@/store/websocket-handler";
export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const dispatch = useAppDispatch();
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);

  const publicRoutes = [
    "/login",
    "/accept-invitation",
    "/forgot-password",
    "/reset-password",
  ];
  const isPublicRoute = publicRoutes.some((route) =>
    pathname?.startsWith(route)
  );
  const isHomePage = pathname === "/";

  const showSidebar = !isPublicRoute && !isHomePage && isAuthenticated;

  useEffect(() => {
    if (isAuthenticated && user) {
      dispatch(fetchUsers());
      dispatch(fetchPractice());
      dispatch(fetchInvitations());
    }
  }, [isAuthenticated, user, dispatch]);

  useEffect(() => {
    if (isAuthenticated) {
      const token = localStorage.getItem("access_token");
      if (token) {
        websocketClient.onMessage((event) => {
          handleWebSocketEvent(
            event as { type: string; data: unknown },
            dispatch
          );
        });
        websocketClient.connect(token);
      }
    }

    return () => {
      websocketClient.disconnect();
    };
  }, [isAuthenticated, dispatch]);

  if (!showSidebar) {
    return <>{children}</>;
  }

  return (
    <SidebarProvider defaultOpen={false}>
      <div className="flex h-screen w-full bg-white">
        <AppSidebar />
        <main
          className="flex-1 overflow-auto"
          style={{ backgroundColor: "#FBF9F7" }}
        >
          {children}
        </main>
      </div>
    </SidebarProvider>
  );
}
