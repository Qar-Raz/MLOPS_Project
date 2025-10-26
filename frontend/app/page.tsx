// File: app/page.tsx

'use client';

import Aurora from '@/components/Aurora';
import GradientText from '@/components/GradientText';
import Link from 'next/link';
import Header from '@/components/Header'; // Import the reusable Header component

export default function Home() {
  const buttonClass = "bg-transparent border-2 border-green-400 text-green-400 font-semibold py-3 px-10 rounded-full shadow-lg transform hover:scale-105 transition-all duration-300 ease-in-out hover:shadow-xl min-w-[180px] flex justify-center items-center";

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-start overflow-hidden bg-black pt-40">

      {/* Use your new, clean Header component right here */}
      <Header />

      {/* --- The rest of your page content remains unchanged --- */}

      <div className="absolute inset-0">
        <Aurora
          colorStops={["#1E4620", "#1A5D3B", "#2A9D8F"]}
          blend={0.1}
          amplitude={1.2}
          speed={0.7}
        />
      </div>

      <div className="relative z-10 px-4 text-center text-white drop-shadow-lg">
        <h1 className="mb-6 tracking-tighter">
          <GradientText
            colors={["#40ffaa", "#4079ff", "#40ffaa", "#4079ff", "#40ffaa"]}
            animationSpeed={10}
            showBorder={false}
            className="text-5xl font-bold md:text-7xl"
          >
            Fluora Care
          </GradientText>
        </h1>
        <p className="mx-auto mb-12 max-w-3xl text-xl font-semibold text-gray-200 md:text-2xl">
          Harnessing advanced AI to redefine botanical wellness and help your plants thrive like never before.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link href="/learn-more" className={buttonClass}>
            Learn More
          </Link>
          <Link href="/try-it-out" className={buttonClass}>
            Try It Out
          </Link>
        </div>
      </div>
    </main>
  );
}
