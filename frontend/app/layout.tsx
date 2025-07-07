'use client';

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { isAuthenticated } from "./services/auth";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Handle authentication routing
    const handleAuth = () => {
      const isAuth = isAuthenticated();
      
      // If user is on signin page and authenticated, redirect to dashboard
      if (pathname === '/signin' && isAuth) {
        router.push('/dashboard');
        return;
      }
      
      // If user is on dashboard and not authenticated, redirect to signin
      if (pathname.startsWith('/dashboard') && !isAuth) {
        router.push('/signin');
        return;
      }
      
      // If user is on root and authenticated, redirect to dashboard
      if (pathname === '/' && isAuth) {
        router.push('/dashboard');
        return;
      }
    };

    handleAuth();
  }, [pathname, router]);

  return (
    <html lang="en">
      <head>
        <title>AudienceAI - Create Viral Content with AI</title>
        <meta name="description" content="Transform your social media presence with AI that understands your brand and generates posts that actually engage your audience." />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
} 