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

const { api } = useApi()
const rules = ref<Rule[]>([])
const filter = ref<'all' | 'pending' | 'sealed'>('all')
const showNewForm = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const showOverrideModal = ref(false)
const pendingAction = ref<(() => Promise<void>) | null>(null)

async function loadRules() {
  rules.value = await api<Rule[]>('/rules')
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

async function createRule(emergencyOverride = false) {
  try {
    await api('/rules', {
      method: 'POST',
      body: { title: newTitle.value, description: newDesc.value, emergency_override: emergencyOverride },
    })
    newTitle.value = ''
    newDesc.value = ''
    showNewForm.value = false
    await loadRules()
  } catch (error: any) {
    if (error?.status === 403 || error?.statusCode === 403) {
      pendingAction.value = () => createRule(true)
      showOverrideModal.value = true
      return
    }
    throw error
  }
}

async function signRule(ruleId: number) {
  await api(`/rules/${ruleId}/sign`, { method: 'POST' })
  await loadRules()
}

async function deleteRule(ruleId: number) {
  await api(`/rules/${ruleId}`, { method: 'DELETE' })
  await loadRules()
}

async function handleOverrideConfirm() {
  showOverrideModal.value = false
  if (pendingAction.value) {
    await pendingAction.value()
    pendingAction.value = null
  }
}

onMounted(loadRules)
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-3">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Distancing Ledger</h1>
        <p class="text-sm text-verse-text/50 mt-1">Seal and sign your shared agreements</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition w-full sm:w-auto"
      >
        {{ showNewForm ? 'Cancel' : '+ New Rule' }}
      </button>
    </div>

    <!-- New rule form -->
    <form v-if="showNewForm" @submit.prevent="() => createRule()" class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 mb-6">
      <input
        v-model="newTitle"
        placeholder="Rule title"
        required
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm"
      />
      <textarea
        v-model="newDesc"
        placeholder="Describe the rule..."
        required
        rows="3"
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm"
      />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
        Propose Rule
      </button>
    </form>

    <!-- Filter tabs -->
    <div class="flex gap-1 mb-4 bg-white rounded-lg p-1 border border-verse-slate/10 w-full sm:w-fit overflow-x-auto">
      <button
        v-for="f in (['all', 'pending', 'sealed'] as const)"
        :key="f"
        @click="filter = f"
        class="flex-1 sm:flex-none px-3 py-1 text-sm rounded-md transition whitespace-nowrap"
        :class="filter === f ? 'bg-verse-slate text-white' : 'text-verse-text/60 hover:bg-verse-slate/5'"
      >
        {{ f === 'pending' ? 'Pending My Signature' : f.charAt(0).toUpperCase() + f.slice(1) }}
      </button>
    </div>

    <!-- Rules list -->
    <div class="space-y-3">
      <RuleCard
        v-for="rule in filteredRules"
        :key="rule.id"
        :rule="rule"
        @sign="signRule"
        @delete="deleteRule"
      />
      <p v-if="filteredRules.length === 0" class="text-center text-verse-text/40 py-8">
        No rules yet. Propose one to get started.
      </p>
    </div>

    <EmergencyOverrideModal
      v-if="showOverrideModal"
      @confirm="handleOverrideConfirm"
      @cancel="showOverrideModal = false; pendingAction = null"
    />
  </div>
</template>
