<script setup lang="ts">
interface Answer {
  id: number
  user_id: number
  username: string
  text: string
  created_at: string
}

interface Question {
  id: number
  text: string
  asked_by: number
  asker_name: string
  my_answer: Answer | null
  partner_answer: Answer | null
  created_at: string
}

const props = defineProps<{ question: Question }>()
const emit = defineEmits<{ answer: [questionId: number, text: string] }>()

const { user } = useAuth()
const answerText = ref('')
const showAnswerForm = ref(false)

const partnerName = computed(() => user.value?.partner?.display_name ?? 'Partner')
const hasMyAnswer = computed(() => !!props.question.my_answer)
const hasPartnerAnswer = computed(() => !!props.question.partner_answer)
const bothAnswered = computed(() => hasMyAnswer.value && hasPartnerAnswer.value)

const askerColor = computed(() => {
  if (props.question.asked_by === user.value?.id) {
    return user.value?.username === 'alif' ? 'border-l-verse-slate' : 'border-l-verse-rose'
  }
  return user.value?.username === 'alif' ? 'border-l-verse-rose' : 'border-l-verse-slate'
})

const askerInitial = computed(() => props.question.asker_name[0])
const askerAvatarColor = computed(() => {
  if (props.question.asked_by === user.value?.id) {
    return user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose'
  }
  return user.value?.username === 'alif' ? 'bg-verse-rose' : 'bg-verse-slate'
})

function submitAnswer() {
  if (!answerText.value.trim()) return
  emit('answer', props.question.id, answerText.value)
  answerText.value = ''
  showAnswerForm.value = false
}
</script>

<template>
  <div
    class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 border-l-[3px] hover:shadow-md transition"
    :class="askerColor"
  >
    <div class="flex items-start justify-between mb-3 gap-2">
      <div class="min-w-0 flex-1">
        <h3 class="font-serif text-base sm:text-lg text-verse-text">{{ question.text }}</h3>
        <div class="flex items-center gap-1.5 mt-1.5">
          <span class="avatar-dot" :class="askerAvatarColor">{{ askerInitial }}</span>
          <span class="text-xs text-verse-text/40">{{ question.asker_name }}</span>
        </div>
      </div>
      <span
        v-if="bothAnswered"
        class="text-xs px-2 py-0.5 rounded-full bg-verse-gold text-white font-medium shrink-0"
      >
        Revealed
      </span>
    </div>

    <div class="space-y-3 mt-4">
      <div v-if="hasMyAnswer" class="rounded-lg p-3 bg-verse-slate/5 border-l-[3px] border-l-verse-slate">
        <p class="text-xs font-medium text-verse-slate mb-1">Your answer</p>
        <p class="text-sm text-verse-text">{{ question.my_answer!.text }}</p>
      </div>

      <div v-if="bothAnswered" class="rounded-lg p-3 bg-verse-rose/5 border-l-[3px] border-l-verse-rose">
        <p class="text-xs font-medium text-verse-rose mb-1">{{ partnerName }}'s answer</p>
        <p class="text-sm text-verse-text">{{ question.partner_answer!.text }}</p>
      </div>
      <MountainBackground v-else-if="!hasMyAnswer" />

      <div v-if="!hasMyAnswer">
        <button
          v-if="!showAnswerForm"
          @click="showAnswerForm = true"
          class="w-full py-2.5 text-sm rounded-lg border border-verse-slate/20 text-verse-slate hover:bg-verse-slate/5 transition animate-soft-pulse"
        >
          Write your answer
        </button>
        <form v-else @submit.prevent="submitAnswer" class="space-y-2">
          <textarea
            v-model="answerText"
            rows="3"
            placeholder="Share your thoughts..."
            class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm"
          />
          <div class="flex gap-2">
            <button type="submit" class="px-4 py-1.5 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
              Submit
            </button>
            <button type="button" @click="showAnswerForm = false" class="px-4 py-1.5 text-sm text-verse-text/50 hover:text-verse-text transition">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
