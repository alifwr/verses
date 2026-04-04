<script setup lang="ts">
interface Activity {
  type: string
  actor: string
  summary: string
  timestamp: string
}

interface Rule {
  id: number
  is_sealed: boolean
  is_agreed_by_me: boolean
}

interface Question {
  id: number
  my_answer: any
  partner_answer: any
}

interface Milestone {
  id: number
  is_confirmed: boolean
  is_completed: boolean
}

const { user } = useAuth()
const { api } = useApi()

const loading = ref(true)
const activities = ref<Activity[]>([])
const rules = ref<Rule[]>([])
const questions = ref<Question[]>([])
const milestones = ref<Milestone[]>([])

const ruleStats = computed(() => {
  const sealed = rules.value.filter(r => r.is_sealed).length
  const pending = rules.value.filter(r => !r.is_agreed_by_me && !r.is_sealed).length
  return { sealed, pending, total: rules.value.length }
})

const questionStats = computed(() => {
  const revealed = questions.value.filter(q => q.my_answer && q.partner_answer).length
  const awaiting = questions.value.filter(q => !q.my_answer).length
  return { revealed, awaiting, total: questions.value.length }
})

const milestoneStats = computed(() => {
  const completed = milestones.value.filter(m => m.is_completed).length
  const confirmed = milestones.value.filter(m => m.is_confirmed && !m.is_completed).length
  const total = milestones.value.length
  return { completed, confirmed, total }
})

function relativeTime(ts: string): string {
  const now = new Date()
  const then = new Date(ts)
  const diff = Math.floor((now.getTime() - then.getTime()) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`
  return then.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function activityIcon(type: string): string {
  const icons: Record<string, string> = {
    rule_created: 'bg-verse-slate',
    rule_signed: 'bg-verse-slate',
    rule_sealed: 'bg-verse-gold',
    question_asked: 'bg-verse-slate',
    answer_submitted: 'bg-verse-rose',
    answers_revealed: 'bg-verse-gold',
    milestone_proposed: 'bg-verse-slate',
    milestone_approved: 'bg-verse-slate',
    milestone_confirmed: 'bg-verse-gold',
    milestone_completed: 'bg-green-500',
  }
  return icons[type] || 'bg-verse-slate/30'
}

async function loadAll() {
  loading.value = true
  try {
    const [a, r, q, m] = await Promise.all([
      api<Activity[]>('/activity'),
      api<Rule[]>('/rules'),
      api<Question[]>('/questions'),
      api<Milestone[]>('/milestones'),
    ])
    activities.value = a.slice(0, 10)
    rules.value = r
    questions.value = q
    milestones.value = m
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>

<template>
  <div>
    <!-- Loading skeleton -->
    <div v-if="loading" class="animate-pulse">
      <div class="h-8 bg-verse-slate/10 rounded w-48 mb-2" />
      <div class="h-4 bg-verse-slate/10 rounded w-32 mb-6" />
      <div class="grid grid-cols-3 gap-3 mb-6">
        <div v-for="i in 3" :key="i" class="bg-white rounded-xl border border-verse-slate/10 p-4">
          <div class="h-3 bg-verse-slate/10 rounded w-16 mb-2" />
          <div class="h-8 bg-verse-slate/10 rounded w-10 mb-2" />
          <div class="h-4 bg-verse-slate/10 rounded w-24" />
        </div>
      </div>
      <div class="flex gap-2 mb-8">
        <div v-for="i in 3" :key="i" class="flex-1 h-10 bg-verse-slate/10 rounded-lg" />
      </div>
      <div class="h-6 bg-verse-slate/10 rounded w-36 mb-4" />
      <div class="bg-white rounded-xl border border-verse-slate/10 divide-y divide-verse-slate/5">
        <div v-for="i in 4" :key="i" class="flex items-center gap-3 px-4 py-3">
          <div class="w-2 h-2 rounded-full bg-verse-slate/10" />
          <div class="flex-1 h-4 bg-verse-slate/10 rounded" />
          <div class="w-12 h-3 bg-verse-slate/10 rounded" />
        </div>
      </div>
    </div>

    <!-- Welcome header -->
    <template v-else>
    <!-- Welcome header -->
    <div class="mb-6">
      <h1 class="text-2xl font-serif text-verse-text">
        Welcome back, {{ user?.display_name }}
      </h1>
      <div class="header-gradient-line w-16" />
      <p class="text-sm text-verse-text/50 mt-2 flex items-center gap-2">
        <span
          class="w-2 h-2 rounded-full inline-block"
          :class="user?.partner?.is_online ? 'bg-green-400' : 'bg-verse-slate/30'"
        />
        {{ user?.partner?.display_name }} is {{ user?.partner?.is_online ? 'online' : 'offline' }}
      </p>
    </div>

    <!-- Quick stats -->
    <div class="grid grid-cols-3 gap-3 mb-6">
      <NuxtLink to="/rules" class="bg-white rounded-xl border border-verse-slate/10 p-4 hover:shadow-md transition">
        <p class="text-xs text-verse-text/50 mb-1">Rules</p>
        <p class="text-2xl font-serif text-verse-text">{{ ruleStats.total }}</p>
        <div class="flex gap-2 mt-2 flex-wrap">
          <span class="stats-pill bg-verse-gold/10 text-verse-gold">{{ ruleStats.sealed }} sealed</span>
          <span v-if="ruleStats.pending" class="stats-pill bg-verse-slate/10 text-verse-slate">{{ ruleStats.pending }} pending</span>
        </div>
      </NuxtLink>

      <NuxtLink to="/inquiry" class="bg-white rounded-xl border border-verse-slate/10 p-4 hover:shadow-md transition">
        <p class="text-xs text-verse-text/50 mb-1">Questions</p>
        <p class="text-2xl font-serif text-verse-text">{{ questionStats.total }}</p>
        <div class="flex gap-2 mt-2 flex-wrap">
          <span class="stats-pill bg-verse-gold/10 text-verse-gold">{{ questionStats.revealed }} revealed</span>
          <span v-if="questionStats.awaiting" class="stats-pill bg-verse-rose/10 text-verse-rose">{{ questionStats.awaiting }} awaiting</span>
        </div>
      </NuxtLink>

      <NuxtLink to="/roadmap" class="bg-white rounded-xl border border-verse-slate/10 p-4 hover:shadow-md transition">
        <p class="text-xs text-verse-text/50 mb-1">Milestones</p>
        <p class="text-2xl font-serif text-verse-text">{{ milestoneStats.total }}</p>
        <div class="flex gap-2 mt-2 flex-wrap">
          <span class="stats-pill bg-green-500/10 text-green-600">{{ milestoneStats.completed }} done</span>
          <span v-if="milestoneStats.confirmed" class="stats-pill bg-verse-gold/10 text-verse-gold">{{ milestoneStats.confirmed }} confirmed</span>
        </div>
      </NuxtLink>
    </div>

    <!-- Quick actions -->
    <div class="flex flex-col sm:flex-row gap-2 mb-8">
      <NuxtLink to="/rules?new=1" class="flex-1 py-2.5 text-center text-sm rounded-lg border border-verse-slate/20 text-verse-slate hover:bg-verse-slate/5 transition">
        + Propose a Rule
      </NuxtLink>
      <NuxtLink to="/inquiry?new=1" class="flex-1 py-2.5 text-center text-sm rounded-lg border border-verse-slate/20 text-verse-slate hover:bg-verse-slate/5 transition">
        + Ask a Question
      </NuxtLink>
      <NuxtLink to="/roadmap?new=1" class="flex-1 py-2.5 text-center text-sm rounded-lg border border-verse-slate/20 text-verse-slate hover:bg-verse-slate/5 transition">
        + Add Milestone
      </NuxtLink>
    </div>

    <!-- Activity feed -->
    <div>
      <h2 class="text-lg font-serif text-verse-text mb-1">Recent Activity</h2>
      <div class="header-gradient-line w-10 mb-4" />

      <div v-if="activities.length" class="bg-white rounded-xl border border-verse-slate/10 divide-y divide-verse-slate/5">
        <div v-for="(a, i) in activities" :key="i" class="flex items-start gap-3 px-4 py-3">
          <span class="w-2 h-2 rounded-full mt-1.5 shrink-0" :class="activityIcon(a.type)" />
          <div class="flex-1 min-w-0">
            <p class="text-sm text-verse-text">
              <span class="font-medium">{{ a.actor }}</span>
              — {{ a.summary }}
            </p>
          </div>
          <span class="text-xs text-verse-text/30 shrink-0">{{ relativeTime(a.timestamp) }}</span>
        </div>
      </div>

      <div v-else class="bg-white rounded-xl border border-verse-slate/10 p-8 text-center">
        <p class="text-verse-text/40">No activity yet. Start your journey together.</p>
      </div>
    </div>

    <!-- Geometric divider -->
    <div class="flex justify-center mt-8 gap-2">
      <span class="w-1 h-1 rounded-full bg-verse-slate/15" />
      <span class="w-1.5 h-1.5 rounded-full bg-verse-slate/20" />
      <span class="w-1 h-1 rounded-full bg-verse-slate/15" />
    </div>
    </template>
  </div>
</template>
