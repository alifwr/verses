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
const milestones = ref<Milestone[]>([])
const showNewForm = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const newDate = ref('')

async function loadMilestones() {
  milestones.value = await api<Milestone[]>('/milestones')
}

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

onMounted(loadMilestones)
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-3">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Marriage Roadmap</h1>
        <p class="text-sm text-verse-text/50 mt-1">Your journey together, one milestone at a time</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition w-full sm:w-auto"
      >
        {{ showNewForm ? 'Cancel' : '+ Propose Milestone' }}
      </button>
    </div>

    <form v-if="showNewForm" @submit.prevent="createMilestone" class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 mb-6">
      <input
        v-model="newTitle"
        placeholder="Milestone title"
        required
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm"
      />
      <textarea
        v-model="newDesc"
        placeholder="Describe this milestone..."
        required
        rows="3"
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm"
      />
      <input
        v-model="newDate"
        type="date"
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm"
      />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
        Propose
      </button>
    </form>

    <div>
      <MilestoneCard
        v-for="m in milestones"
        :key="m.id"
        :milestone="m"
        @approve="approveMilestone"
        @complete="completeMilestone"
        @delete="deleteMilestone"
      />
      <p v-if="milestones.length === 0" class="text-center text-verse-text/40 py-8">
        No milestones yet. Propose your first step forward.
      </p>
    </div>
  </div>
</template>
