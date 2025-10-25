// src/middleware.ts
import { clerkMiddleware } from "@clerk/nextjs/server";

// This default export applies Clerk's authentication logic.
// By default, it protects all routes that are not part of Clerk's
// authentication flow or explicitly marked as public.
export default clerkMiddleware();

export const config = {
  matcher: [
    // Skip Next.js internals (like static files) and all assets, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run middleware on API routes
    '/(api|trpc)(.*)',
  ],
};