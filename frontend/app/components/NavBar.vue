<script setup lang="ts">
const { user, logout } = useAuth()
const route = useRoute()

const navItems = [
  { path: '/', label: 'Home', icon: '&#9679;' },
  { path: '/rules', label: 'Rules', icon: '&#9874;' },
  { path: '/talks', label: 'Talks', icon: '&#9993;' },
  { path: '/inquiry', label: 'Inquiry', icon: '&#10067;' },
  { path: '/roadmap', label: 'Roadmap', icon: '&#9670;' },
]

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const userColor = computed(() =>
  user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose'
)

const partnerOnline = computed(() => user.value?.partner?.is_online ?? false)
</script>

<template>
  <!-- Desktop/tablet top nav -->
  <nav class="hidden sm:block bg-white/90 backdrop-blur-sm border-b border-verse-slate/10 sticky top-0 z-40">
    <div class="max-w-4xl mx-auto px-4 flex items-center justify-between h-14">
      <NuxtLink to="/" class="font-serif text-xl text-verse-text tracking-wide">Verse</NuxtLink>

      <div class="flex items-center gap-1">
        <NuxtLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="px-3 py-1.5 rounded-lg text-sm transition relative"
          :class="isActive(item.path) ? 'bg-verse-slate text-white' : 'text-verse-text hover:bg-verse-slate/10'"
        >
          {{ item.label }}
          <span v-if="isActive(item.path)" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 bg-verse-gold rounded-full" />
        </NuxtLink>
      </div>

      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <div class="relative">
            <span class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-medium" :class="userColor">
              {{ user?.display_name?.[0] }}
            </span>
            <span
              class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white"
              :class="partnerOnline ? 'bg-green-400' : 'bg-verse-slate/30'"
              :title="partnerOnline ? 'Partner online' : 'Partner offline'"
            />
          </div>
          <span class="text-sm text-verse-text">{{ user?.display_name }}</span>
        </div>
        <button @click="logout" class="text-xs text-verse-slate hover:text-verse-text transition">
          Logout
        </button>
      </div>
    </div>
  </nav>

  <!-- Mobile top bar -->
  <div class="sm:hidden bg-white/90 backdrop-blur-sm border-b border-verse-slate/10 sticky top-0 z-40">
    <div class="px-4 flex items-center justify-between h-12">
      <span class="font-serif text-lg text-verse-text">Verse</span>
      <div class="flex items-center gap-2">
        <div class="relative">
          <span class="w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] font-medium" :class="userColor">
            {{ user?.display_name?.[0] }}
          </span>
          <span
            class="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border border-white"
            :class="partnerOnline ? 'bg-green-400' : 'bg-verse-slate/30'"
          />
        </div>
        <button @click="logout" class="text-xs text-verse-slate">Logout</button>
      </div>
    </div>
  </div>

  <!-- Mobile bottom nav -->
  <nav class="sm:hidden fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-t border-verse-slate/10 z-40">
    <div class="flex items-center justify-around h-14 px-2">
      <NuxtLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition relative"
        :class="isActive(item.path) ? 'text-verse-slate' : 'text-verse-text/40'"
      >
        <span class="text-lg" v-html="item.icon" />
        <span class="text-[10px] font-medium">{{ item.label }}</span>
        <span v-if="isActive(item.path)" class="absolute -bottom-1 w-4 h-0.5 bg-verse-gold rounded-full" />
      </NuxtLink>
    </div>
  </nav>
</template>
