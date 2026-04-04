<template>
  <div class="min-h-screen bg-verse-bg relative">
    <!-- Topographic background texture -->
    <div class="fixed inset-0 pointer-events-none z-0">
      <svg class="w-full h-full opacity-[0.03]">
        <pattern id="topo-bg" width="120" height="120" patternUnits="userSpaceOnUse">
          <circle cx="60" cy="60" r="50" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
          <circle cx="60" cy="60" r="35" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
          <circle cx="60" cy="60" r="20" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
        </pattern>
        <rect width="100%" height="100%" fill="url(#topo-bg)"/>
      </svg>
    </div>

    <NavBar />
    <main class="relative z-10 max-w-4xl mx-auto px-4 py-6 pb-20 sm:pb-6">
      <slot />
    </main>
  </div>
</template>
