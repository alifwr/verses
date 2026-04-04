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

const props = defineProps<{ milestone: Milestone; isLast?: boolean }>()
const emit = defineEmits<{
  approve: [milestoneId: number]
  complete: [milestoneId: number]
  delete: [milestoneId: number]
}>()

const { user } = useAuth()
const isMyProposal = computed(() => props.milestone.proposed_by === user.value?.id)

const statusLabel = computed(() => {
  if (props.milestone.is_completed) return 'Completed'
  if (props.milestone.is_confirmed) return 'Confirmed'
  return 'Proposed'
})

const statusColor = computed(() => {
  if (props.milestone.is_completed) return 'bg-green-500'
  if (props.milestone.is_confirmed) return 'bg-verse-gold'
  return 'bg-verse-slate/30'
})

const lineGradient = computed(() => {
  if (props.milestone.is_completed) return 'from-green-500/30 to-verse-gold/20'
  if (props.milestone.is_confirmed) return 'from-verse-gold/30 to-verse-slate/10'
  return 'from-verse-slate/15 to-verse-slate/5'
})

const proposerColor = computed(() => {
  if (props.milestone.proposed_by === user.value?.id) {
    return user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose'
  }
  return user.value?.username === 'alif' ? 'bg-verse-rose' : 'bg-verse-slate'
})

const cardBorderColor = computed(() => {
  if (props.milestone.proposed_by === user.value?.id) {
    return user.value?.username === 'alif' ? 'border-l-verse-slate' : 'border-l-verse-rose'
  }
  return user.value?.username === 'alif' ? 'border-l-verse-rose' : 'border-l-verse-slate'
})

function formatDate(d: string | null) {
  if (!d) return null
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<template>
  <div class="flex gap-3 sm:gap-4">
    <div class="flex flex-col items-center shrink-0">
      <div
        class="w-4 h-4 rounded-full mt-1 flex items-center justify-center text-white text-[8px]"
        :class="statusColor"
      >
        <span v-if="milestone.is_completed">&#10003;</span>
      </div>
      <div
        v-if="!isLast"
        class="w-0.5 flex-1 mt-1 bg-gradient-to-b"
        :class="lineGradient"
      />
    </div>

    <div
      class="flex-1 rounded-xl border p-4 sm:p-5 mb-4 transition min-w-0 border-l-[3px] hover:shadow-md"
      :class="[
        milestone.is_confirmed ? 'bg-verse-gold-light/50 border-verse-gold/20' : 'bg-white border-verse-slate/10',
        cardBorderColor
      ]"
    >
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1 flex-wrap">
            <h3 class="font-serif text-base sm:text-lg text-verse-text">{{ milestone.title }}</h3>
            <span class="text-xs px-2 py-0.5 rounded-full text-white font-medium shrink-0" :class="statusColor">
              {{ statusLabel }}
            </span>
          </div>
          <p class="text-sm text-verse-text/70">{{ milestone.description }}</p>
          <p v-if="milestone.target_date" class="text-xs text-verse-text/40 mt-2">
            Target: {{ formatDate(milestone.target_date) }}
          </p>
        </div>

        <button
          v-if="isMyProposal && !milestone.is_confirmed"
          @click="emit('delete', milestone.id)"
          class="text-verse-text/30 hover:text-red-400 transition text-lg shrink-0"
          title="Delete milestone"
        >
          &times;
        </button>
      </div>

      <div class="mt-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div class="flex items-center gap-3 text-xs text-verse-text/50 flex-wrap">
          <span class="flex items-center gap-1.5">
            <span class="avatar-dot" :class="proposerColor">{{ milestone.proposer_name[0] }}</span>
            {{ milestone.proposer_name }}
          </span>
          <span class="flex items-center gap-1">
            <span v-if="milestone.is_approved_by_me" class="text-green-500 text-sm">&#10003;</span>
            <span v-else class="w-3.5 h-3.5 rounded-full border border-verse-slate/20 inline-block" />
            Me
          </span>
          <span class="flex items-center gap-1">
            <span v-if="milestone.is_approved_by_partner" class="text-green-500 text-sm">&#10003;</span>
            <span v-else class="w-3.5 h-3.5 rounded-full border border-verse-slate/20 inline-block" />
            Partner
          </span>
        </div>

        <div class="flex gap-2 w-full sm:w-auto">
          <button
            v-if="!milestone.is_approved_by_me && !milestone.is_completed"
            @click="emit('approve', milestone.id)"
            class="flex-1 sm:flex-none px-3 py-1.5 text-sm rounded-lg bg-verse-slate text-white hover:bg-verse-slate/90 transition"
          >
            Approve
          </button>
          <button
            v-if="milestone.is_confirmed && !milestone.is_completed"
            @click="emit('complete', milestone.id)"
            class="flex-1 sm:flex-none px-3 py-1.5 text-sm rounded-lg bg-green-500 text-white hover:bg-green-600 transition"
          >
            Complete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
