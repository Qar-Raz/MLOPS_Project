'use client';

import Aurora from '@/components/Aurora';
import GradientText from '@/components/GradientText';

export default function Home() {
  return (
    // We keep bg-black here as a fallback color
    <main className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden">

      {/* The Aurora background component container */}
      <div className="absolute inset-0">
        <Aurora
          colorStops={["#1E4620", "#1A5D3B", "#2A9D8F"]}
          blend={0.1}
          amplitude={1.2}
          speed={0.7}
        />
      </div>

      {/* The main content container */}
      <div className="relative z-10 text-center text-white drop-shadow-lg">
        <h1 className="mb-6 tracking-tighter">
          <GradientText
            colors={["#40ffaa", "#4079ff", "#40ffaa", "#4079ff", "#40ffaa"]}
            animationSpeed={10}
            showBorder={false}
            className="text-5xl md:text-7xl font-bold custom-class"
          >
            Fluora Care
          </GradientText>
        </h1>
        <p className="text-lg text-gray-300 mb-10 max-w-2xl mx-auto">

        </p>

        {/* The button container */}
        <div className="flex justify-center items-center gap-4">
          <button className="bg-white text-black font-semibold py-3 px-8 rounded-full shadow-lg transform hover:scale-105 transition-transform duration-300 ease-in-out">
            Try It Out
          </button>
        </div>
      </div>
    </main>
  );
}
