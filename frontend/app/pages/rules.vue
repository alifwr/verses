<script setup lang="ts">
interface Rule {
  id: number
  title: string
  description: string
  proposed_by: number
  proposer_name: string
  is_sealed: boolean
  is_agreed_by_me: boolean
  is_agreed_by_partner: boolean
  created_at: string
}

const { user } = useAuth()
const { api } = useApi()
const route = useRoute()
const loading = ref(true)
const rules = ref<Rule[]>([])
const filter = ref<'all' | 'pending' | 'sealed'>('all')
const showNewForm = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const expandedId = ref<number | null>(null)

async function loadRules() {
  try {
    rules.value = await api<Rule[]>('/rules')
  } finally {
    loading.value = false
  }
}

const filteredRules = computed(() => {
  switch (filter.value) {
    case 'pending':
      return rules.value.filter(r => !r.is_agreed_by_me && !r.is_sealed)
    case 'sealed':
      return rules.value.filter(r => r.is_sealed)
    default:
      return rules.value
  }
})

const stats = computed(() => ({
  total: rules.value.length,
  sealed: rules.value.filter(r => r.is_sealed).length,
  pending: rules.value.filter(r => !r.is_agreed_by_me && !r.is_sealed).length,
}))

function actionLabel(rule: Rule): { text: string; style: string } {
  if (rule.is_sealed) return { text: 'Sealed', style: 'bg-verse-gold text-white' }
  if (rule.is_agreed_by_me && !rule.is_agreed_by_partner) return { text: 'Awaiting partner', style: 'text-verse-text/40' }
  if (!rule.is_agreed_by_me) return { text: 'Sign', style: 'bg-verse-slate text-white cursor-pointer hover:bg-verse-slate/90' }
  return { text: '-', style: 'text-verse-text/20' }
}

function proposerInitial(rule: Rule): string {
  return rule.proposer_name[0]
}

function proposerColor(rule: Rule): string {
  return rule.proposed_by === user.value?.id
    ? (user.value?.display_name === 'Alif' ? 'bg-verse-slate' : 'bg-verse-rose')
    : (user.value?.display_name === 'Alif' ? 'bg-verse-rose' : 'bg-verse-slate')
}

async function createRule() {
  await api('/rules', {
    method: 'POST',
    body: { title: newTitle.value, description: newDesc.value },
  })
  newTitle.value = ''
  newDesc.value = ''
  showNewForm.value = false
  await loadRules()
}

async function signRule(rule: Rule) {
  if (rule.is_agreed_by_me || rule.is_sealed) return
  await api(`/rules/${rule.id}/sign`, { method: 'POST' })
  await loadRules()
}

async function deleteRule(ruleId: number) {
  await api(`/rules/${ruleId}`, { method: 'DELETE' })
  await loadRules()
}

onMounted(() => {
  loadRules()
  if (route.query.new === '1') showNewForm.value = true
})
</script>

<template>
  <div>
    <!-- Loading skeleton -->
    <div v-if="loading" class="animate-pulse">
      <div class="flex justify-between mb-4">
        <div>
          <div class="h-8 bg-verse-slate/10 rounded w-32 mb-2" />
          <div class="h-4 bg-verse-slate/10 rounded w-48" />
        </div>
        <div class="h-10 bg-verse-slate/10 rounded w-28" />
      </div>
      <div class="flex gap-2 mb-4">
        <div v-for="i in 3" :key="i" class="h-6 bg-verse-slate/10 rounded-full w-20" />
      </div>
      <div class="bg-white rounded-xl border border-verse-slate/10 overflow-hidden">
        <div class="px-4 py-2.5 bg-verse-slate/[0.04] border-b border-verse-slate/5">
          <div class="h-3 bg-verse-slate/10 rounded w-full" />
        </div>
        <div v-for="i in 4" :key="i" class="flex items-center gap-3 px-4 py-3 border-b border-verse-slate/5 last:border-b-0">
          <div class="w-2.5 h-2.5 rounded-full bg-verse-slate/10" />
          <div class="flex-1 h-4 bg-verse-slate/10 rounded" />
          <div class="w-16 h-4 bg-verse-slate/10 rounded" />
          <div class="w-20 h-6 bg-verse-slate/10 rounded-full" />
        </div>
      </div>
    </div>

    <template v-else>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-2 gap-3">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Rules</h1>
        <div class="header-gradient-line w-12" />
        <p class="text-sm text-verse-text/50 mt-2">Seal and sign your shared agreements</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition w-full sm:w-auto"
      >
        {{ showNewForm ? 'Cancel' : '+ New Rule' }}
      </button>
    </div>

    <div class="flex gap-2 mb-4 flex-wrap">
      <span class="stats-pill bg-verse-slate/10 text-verse-text/60">{{ stats.total }} total</span>
      <span class="stats-pill bg-verse-gold/10 text-verse-gold">{{ stats.sealed }} sealed</span>
      <span v-if="stats.pending" class="stats-pill bg-verse-rose/10 text-verse-rose">{{ stats.pending }} pending</span>
    </div>

    <form v-if="showNewForm" @submit.prevent="createRule" class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 mb-6">
      <input v-model="newTitle" placeholder="Rule title" required class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm" />
      <textarea v-model="newDesc" placeholder="Describe the rule..." required rows="3" class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm" />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">Propose Rule</button>
    </form>

    <div class="flex gap-1 mb-4 bg-white rounded-lg p-1 border border-verse-slate/10 w-full sm:w-fit overflow-x-auto">
      <button
        v-for="f in (['all', 'pending', 'sealed'] as const)"
        :key="f"
        @click="filter = f"
        class="flex-1 sm:flex-none px-3 py-1 text-sm rounded-md transition whitespace-nowrap"
        :class="filter === f ? 'bg-verse-slate text-white' : 'text-verse-text/60 hover:bg-verse-slate/5'"
      >
        {{ f === 'pending' ? 'Pending' : f.charAt(0).toUpperCase() + f.slice(1) }}
        <span class="ml-1 opacity-70">({{ f === 'all' ? stats.total : f === 'pending' ? stats.pending : stats.sealed }})</span>
      </button>
    </div>

    <div class="hidden sm:block bg-white rounded-xl border border-verse-slate/10 overflow-hidden">
      <div class="grid grid-cols-[2rem_1fr_6rem_2.5rem_2.5rem_8rem] gap-3 px-4 py-2.5 bg-verse-slate/[0.04] text-xs text-verse-text/50 font-medium uppercase tracking-wide border-b border-verse-slate/5">
        <div></div>
        <div>Rule</div>
        <div>By</div>
        <div class="text-center">Me</div>
        <div class="text-center">Partner</div>
        <div class="text-right">Action</div>
      </div>
      <div
        v-for="rule in filteredRules"
        :key="rule.id"
        class="grid grid-cols-[2rem_1fr_6rem_2.5rem_2.5rem_8rem] gap-3 px-4 py-3 items-center border-b border-verse-slate/5 last:border-b-0 transition hover:bg-verse-slate/[0.02]"
        :class="rule.is_sealed ? 'bg-verse-gold-light/50' : ''"
      >
        <div class="flex justify-center">
          <span class="w-2.5 h-2.5 rounded-full" :class="rule.is_sealed ? 'bg-verse-gold' : rule.is_agreed_by_me ? 'bg-green-400' : 'bg-verse-slate/20'" />
        </div>
        <div class="min-w-0">
          <p class="text-sm font-medium text-verse-text truncate">{{ rule.title }}</p>
          <p class="text-xs text-verse-text/40 truncate">{{ rule.description }}</p>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="avatar-dot" :class="proposerColor(rule)">{{ proposerInitial(rule) }}</span>
          <span class="text-xs text-verse-text/50 truncate">{{ rule.proposer_name }}</span>
        </div>
        <div class="text-center">
          <span v-if="rule.is_agreed_by_me" class="text-green-500 text-sm">&#10003;</span>
          <span v-else class="w-3.5 h-3.5 rounded-full border border-verse-slate/20 inline-block" />
        </div>
        <div class="text-center">
          <span v-if="rule.is_agreed_by_partner" class="text-green-500 text-sm">&#10003;</span>
          <span v-else class="w-3.5 h-3.5 rounded-full border border-verse-slate/20 inline-block" />
        </div>
        <div class="flex items-center justify-end gap-2">
          <span
            class="text-xs px-3 py-1 rounded-full font-medium"
            :class="actionLabel(rule).style"
            @click="actionLabel(rule).text === 'Sign' && signRule(rule)"
          >
            {{ actionLabel(rule).text }}
          </span>
          <button
            v-if="rule.proposed_by === user?.id && !rule.is_sealed"
            @click="deleteRule(rule.id)"
            class="text-verse-text/20 hover:text-red-400 transition text-sm"
            title="Delete"
          >
            &times;
          </button>
        </div>
      </div>
      <div v-if="filteredRules.length === 0" class="px-4 py-8 text-center text-verse-text/40">
        No rules match this filter.
      </div>
    </div>

    <div class="sm:hidden space-y-2">
      <div
        v-for="rule in filteredRules"
        :key="rule.id"
        class="rounded-xl border p-3 transition"
        :class="rule.is_sealed ? 'bg-verse-gold-light/50 border-verse-gold/20' : 'bg-white border-verse-slate/10'"
        @click="expandedId = expandedId === rule.id ? null : rule.id"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <span class="w-2 h-2 rounded-full shrink-0" :class="rule.is_sealed ? 'bg-verse-gold' : rule.is_agreed_by_me ? 'bg-green-400' : 'bg-verse-slate/20'" />
            <span class="text-sm font-medium text-verse-text truncate">{{ rule.title }}</span>
          </div>
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium shrink-0"
            :class="actionLabel(rule).style"
            @click.stop="actionLabel(rule).text === 'Sign' && signRule(rule)"
          >
            {{ actionLabel(rule).text }}
          </span>
        </div>
        <div v-if="expandedId === rule.id" class="mt-3 pt-3 border-t border-verse-slate/5">
          <p class="text-xs text-verse-text/60 mb-2">{{ rule.description }}</p>
          <div class="flex items-center gap-3 text-xs text-verse-text/40">
            <span class="flex items-center gap-1">
              <span class="avatar-dot text-[7px]" :class="proposerColor(rule)">{{ proposerInitial(rule) }}</span>
              {{ rule.proposer_name }}
            </span>
            <span class="flex items-center gap-1">
              <span v-if="rule.is_agreed_by_me" class="text-green-500">&#10003;</span>
              <span v-else class="w-3 h-3 rounded-full border border-verse-slate/20 inline-block" />
              Me
            </span>
            <span class="flex items-center gap-1">
              <span v-if="rule.is_agreed_by_partner" class="text-green-500">&#10003;</span>
              <span v-else class="w-3 h-3 rounded-full border border-verse-slate/20 inline-block" />
              Partner
            </span>
          </div>
          <button
            v-if="rule.proposed_by === user?.id && !rule.is_sealed"
            @click.stop="deleteRule(rule.id)"
            class="text-xs text-red-400 mt-2"
          >
            Delete rule
          </button>
        </div>
      </div>
      <p v-if="filteredRules.length === 0" class="text-center text-verse-text/40 py-8">
        No rules match this filter.
      </p>
    </div>

    </template>
  </div>
</template>
