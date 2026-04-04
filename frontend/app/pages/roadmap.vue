<script setup lang="ts">
interface Milestone {
  id: number
  title: string
  description: string
  target_date: string | null
  proposed_by: number
  proposer_name: string
  is_confirmed: boolean
  is_completed: boolean
  is_approved_by_me: boolean
  is_approved_by_partner: boolean
  created_at: string
}

const { api } = useApi()
const route = useRoute()
const loading = ref(true)
const milestones = ref<Milestone[]>([])
const showNewForm = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const newDate = ref('')

async function loadMilestones() {
  try {
    milestones.value = await api<Milestone[]>('/milestones')
  } finally {
    loading.value = false
  }
}

const stats = computed(() => {
  const completed = milestones.value.filter(m => m.is_completed).length
  const confirmed = milestones.value.filter(m => m.is_confirmed && !m.is_completed).length
  const proposed = milestones.value.filter(m => !m.is_confirmed).length
  const total = milestones.value.length
  const progress = total > 0 ? Math.round((completed / total) * 100) : 0
  return { completed, confirmed, proposed, total, progress }
})

async function createMilestone() {
  await api('/milestones', {
    method: 'POST',
    body: {
      title: newTitle.value,
      description: newDesc.value,
      target_date: newDate.value || null,
    },
  })
  newTitle.value = ''
  newDesc.value = ''
  newDate.value = ''
  showNewForm.value = false
  await loadMilestones()
}

async function approveMilestone(id: number) {
  await api(`/milestones/${id}/approve`, { method: 'POST' })
  await loadMilestones()
}

async function completeMilestone(id: number) {
  await api(`/milestones/${id}`, { method: 'PATCH', body: { is_completed: true } })
  await loadMilestones()
}

async function deleteMilestone(id: number) {
  await api(`/milestones/${id}`, { method: 'DELETE' })
  await loadMilestones()
}

onMounted(() => {
  loadMilestones()
  if (route.query.new === '1') showNewForm.value = true
})
</script>

<template>
  <div>
    <!-- Loading skeleton -->
    <div v-if="loading" class="animate-pulse">
      <div class="flex justify-between mb-4">
        <div>
          <div class="h-8 bg-verse-slate/10 rounded w-44 mb-2" />
          <div class="h-4 bg-verse-slate/10 rounded w-56" />
        </div>
        <div class="h-10 bg-verse-slate/10 rounded w-36" />
      </div>
      <div class="flex gap-2 mb-2">
        <div v-for="i in 4" :key="i" class="h-6 bg-verse-slate/10 rounded-full w-24" />
      </div>
      <div class="h-1.5 bg-verse-slate/10 rounded-full mb-4" />
      <div class="space-y-4">
        <div v-for="i in 3" :key="i" class="flex gap-3">
          <div class="w-3 h-3 rounded-full bg-verse-slate/10 mt-1 shrink-0" />
          <div class="flex-1 bg-white rounded-xl border border-verse-slate/10 p-4">
            <div class="h-5 bg-verse-slate/10 rounded w-1/2 mb-2" />
            <div class="h-4 bg-verse-slate/10 rounded w-3/4" />
          </div>
        </div>
      </div>
    </div>

    <template v-else>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-2 gap-3">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Marriage Roadmap</h1>
        <div class="header-gradient-line w-14" />
        <p class="text-sm text-verse-text/50 mt-2">Your journey together, one milestone at a time</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition w-full sm:w-auto"
      >
        {{ showNewForm ? 'Cancel' : '+ Propose Milestone' }}
      </button>
    </div>

    <div class="mb-4">
      <div class="flex gap-2 mb-2 flex-wrap">
        <span class="stats-pill bg-verse-slate/10 text-verse-text/60">{{ stats.total }} total</span>
        <span class="stats-pill bg-green-500/10 text-green-600">{{ stats.completed }} completed</span>
        <span class="stats-pill bg-verse-gold/10 text-verse-gold">{{ stats.confirmed }} confirmed</span>
        <span v-if="stats.proposed" class="stats-pill bg-verse-slate/10 text-verse-slate">{{ stats.proposed }} proposed</span>
      </div>
      <div v-if="stats.total > 0" class="h-1.5 bg-verse-slate/10 rounded-full overflow-hidden">
        <div
          class="h-full bg-gradient-to-r from-verse-gold to-green-500 rounded-full transition-all duration-500"
          :style="{ width: stats.progress + '%' }"
        />
      </div>
      <p v-if="stats.total > 0" class="text-xs text-verse-text/40 mt-1">{{ stats.completed }} of {{ stats.total }} milestones completed</p>
    </div>

    <form v-if="showNewForm" @submit.prevent="createMilestone" class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 mb-6">
      <input v-model="newTitle" placeholder="Milestone title" required class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm" />
      <textarea v-model="newDesc" placeholder="Describe this milestone..." required rows="3" class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm" />
      <input v-model="newDate" type="date" class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm" />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">Propose</button>
    </form>

    <div>
      <MilestoneCard
        v-for="(m, i) in milestones"
        :key="m.id"
        :milestone="m"
        :is-last="i === milestones.length - 1"
        @approve="approveMilestone"
        @complete="completeMilestone"
        @delete="deleteMilestone"
      />
      <p v-if="milestones.length === 0" class="text-center text-verse-text/40 py-8">
        No milestones yet. Propose your first step forward.
      </p>
    </div>
    </template>
  </div>
</template>
