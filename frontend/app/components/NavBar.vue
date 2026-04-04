<script setup lang="ts">
const { user, logout } = useAuth()
const route = useRoute()

const navItems = [
  { path: '/ledger', label: 'Ledger', icon: '&#9874;' },
  { path: '/inquiry', label: 'Inquiry', icon: '&#10067;' },
  { path: '/roadmap', label: 'Roadmap', icon: '&#9670;' },
]

const isActive = (path: string) => route.path === path

const userColor = computed(() =>
  user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose'
)
</script>

<template>
  <!-- Desktop/tablet top nav -->
  <nav class="hidden sm:block bg-white/90 backdrop-blur-sm border-b border-verse-slate/10 sticky top-0 z-40">
    <div class="max-w-4xl mx-auto px-4 flex items-center justify-between h-14">
      <NuxtLink to="/ledger" class="font-serif text-xl text-verse-text tracking-wide">Verse</NuxtLink>

      <div class="flex items-center gap-1">
        <NuxtLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="px-3 py-1.5 rounded-lg text-sm transition"
          :class="isActive(item.path) ? 'bg-verse-slate text-white' : 'text-verse-text hover:bg-verse-slate/10'"
        >
          {{ item.label }}
        </NuxtLink>
      </div>

      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <span class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-medium" :class="userColor">
            {{ user?.display_name?.[0] }}
          </span>
          <span class="text-sm text-verse-text">{{ user?.display_name }}</span>
        </div>
        <button @click="logout" class="text-xs text-verse-slate hover:text-verse-text transition">
          Logout
        </button>
      </div>
    </div>
  </nav>

  <!-- Mobile top bar (minimal) -->
  <div class="sm:hidden bg-white/90 backdrop-blur-sm border-b border-verse-slate/10 sticky top-0 z-40">
    <div class="px-4 flex items-center justify-between h-12">
      <span class="font-serif text-lg text-verse-text">Verse</span>
      <div class="flex items-center gap-2">
        <span class="w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] font-medium" :class="userColor">
          {{ user?.display_name?.[0] }}
        </span>
        <button @click="logout" class="text-xs text-verse-slate">Logout</button>
      </div>
    </div>
  </div>

  <!-- Mobile bottom nav -->
  <nav class="sm:hidden fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-t border-verse-slate/10 z-40 safe-area-bottom">
    <div class="flex items-center justify-around h-14 px-2">
      <NuxtLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex flex-col items-center gap-0.5 px-4 py-1 rounded-lg transition"
        :class="isActive(item.path) ? 'text-verse-slate' : 'text-verse-text/40'"
      >
        <span class="text-lg" v-html="item.icon" />
        <span class="text-[10px] font-medium">{{ item.label }}</span>
      </NuxtLink>
    </div>
  </nav>
</template>
