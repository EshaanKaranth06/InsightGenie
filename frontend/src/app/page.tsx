// src/app/page.tsx
import Link from 'next/link';
import { SignedIn, SignedOut } from '@clerk/nextjs';

export default function HomePage() {
  return (
    <div className="text-center mt-20">
      <h1 className="text-4xl font-bold mb-4">Welcome to InsightGenie 🧞</h1>
      <p className="text-lg text-gray-600 mb-8">
        Get AI-powered insights from customer feedback across the web.
      </p>
      <div>
        <SignedOut>
          <Link href="/sign-in">
            <button className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded mr-4">
              Sign In to Get Started
            </button>
          </Link>
          <Link href="/sign-up">
            <button className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded">
              Sign Up
            </button>
          </Link>
        </SignedOut>
        <SignedIn>
          <Link href="/dashboard">
            <button className="bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded">
              Go to Dashboard
            </button>
          </Link>
        </SignedIn>
      </div>
    </div>
  );
}