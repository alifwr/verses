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

const props = defineProps<{ rule: Rule }>()
const emit = defineEmits<{
  sign: [ruleId: number]
  delete: [ruleId: number]
}>()

const { user } = useAuth()
const isMyProposal = computed(() => props.rule.proposed_by === user.value?.id)
</script>

<template>
  <div
    class="rounded-xl border p-4 sm:p-5 transition"
    :class="rule.is_sealed
      ? 'bg-verse-gold-light border-verse-gold/30'
      : 'bg-white border-verse-slate/10'"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1 flex-wrap">
          <h3 class="font-serif text-base sm:text-lg text-verse-text">{{ rule.title }}</h3>
          <span v-if="rule.is_sealed" class="text-xs px-2 py-0.5 rounded-full bg-verse-gold text-white font-medium shrink-0">
            Sealed
          </span>
        </div>
        <p class="text-sm text-verse-text/70">{{ rule.description }}</p>
      </div>

      <button
        v-if="isMyProposal && !rule.is_sealed"
        @click="emit('delete', rule.id)"
        class="text-verse-text/30 hover:text-red-400 transition text-lg shrink-0"
        title="Delete rule"
      >
        &times;
      </button>
    </div>

    <div class="mt-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
      <div class="flex items-center gap-3 text-xs text-verse-text/50 flex-wrap">
        <span>Proposed by {{ rule.proposer_name }}</span>
        <span class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full" :class="rule.is_agreed_by_me ? 'bg-green-400' : 'bg-verse-slate/20'" />
          Me
        </span>
        <span class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full" :class="rule.is_agreed_by_partner ? 'bg-green-400' : 'bg-verse-slate/20'" />
          Partner
        </span>
      </div>

      <button
        v-if="!rule.is_agreed_by_me && !rule.is_sealed"
        @click="emit('sign', rule.id)"
        class="px-4 py-1.5 text-sm rounded-lg bg-verse-slate text-white hover:bg-verse-slate/90 transition w-full sm:w-auto"
      >
        Sign
      </button>
    </div>
  </div>
</template>
