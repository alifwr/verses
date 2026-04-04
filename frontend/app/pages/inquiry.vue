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

const { api } = useApi()
const route = useRoute()
const questions = ref<Question[]>([])
const showNewForm = ref(false)
const newText = ref('')
const showOverrideModal = ref(false)
const pendingAction = ref<(() => Promise<void>) | null>(null)

async function loadQuestions() {
  questions.value = await api<Question[]>('/questions')
}

const stats = computed(() => ({
  total: questions.value.length,
  revealed: questions.value.filter(q => q.my_answer && q.partner_answer).length,
  awaiting: questions.value.filter(q => !q.my_answer).length,
}))

async function createQuestion(emergencyOverride = false) {
  try {
    await api('/questions', {
      method: 'POST',
      body: { text: newText.value, emergency_override: emergencyOverride },
    })
    newText.value = ''
    showNewForm.value = false
    await loadQuestions()
  } catch (error: any) {
    if (error?.status === 403 || error?.statusCode === 403) {
      pendingAction.value = () => createQuestion(true)
      showOverrideModal.value = true
      return
    }
    throw error
  }
}

async function answerQuestion(questionId: number, text: string, emergencyOverride = false) {
  try {
    await api(`/questions/${questionId}/answer`, {
      method: 'POST',
      body: { text, emergency_override: emergencyOverride },
    })
    await loadQuestions()
  } catch (error: any) {
    if (error?.status === 403 || error?.statusCode === 403) {
      pendingAction.value = () => answerQuestion(questionId, text, true)
      showOverrideModal.value = true
      return
    }
    throw error
  }
}

async function handleOverrideConfirm() {
  showOverrideModal.value = false
  if (pendingAction.value) {
    await pendingAction.value()
    pendingAction.value = null
  }
}

onMounted(() => {
  loadQuestions()
  if (route.query.new === '1') showNewForm.value = true
})
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-2 gap-3">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Inquiry Hub</h1>
        <div class="header-gradient-line w-10" />
        <p class="text-sm text-verse-text/50 mt-2">Ask, reflect, then reveal together</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition w-full sm:w-auto"
      >
        {{ showNewForm ? 'Cancel' : '+ New Question' }}
      </button>
    </div>

    <div class="flex gap-2 mb-4 flex-wrap">
      <span class="stats-pill bg-verse-slate/10 text-verse-text/60">{{ stats.total }} total</span>
      <span class="stats-pill bg-verse-gold/10 text-verse-gold">{{ stats.revealed }} revealed</span>
      <span v-if="stats.awaiting" class="stats-pill bg-verse-rose/10 text-verse-rose">{{ stats.awaiting }} awaiting</span>
    </div>

    <form v-if="showNewForm" @submit.prevent="() => createQuestion()" class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 mb-6">
      <textarea
        v-model="newText"
        placeholder="What would you like to explore together?"
        required
        rows="3"
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm"
      />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
        Ask Question
      </button>
    </form>

    <div class="space-y-4">
      <QuestionCard
        v-for="q in questions"
        :key="q.id"
        :question="q"
        @answer="answerQuestion"
      />
      <p v-if="questions.length === 0" class="text-center text-verse-text/40 py-8">
        No questions yet. Start exploring together.
      </p>
    </div>

    <EmergencyOverrideModal
      v-if="showOverrideModal"
      @confirm="handleOverrideConfirm"
      @cancel="showOverrideModal = false; pendingAction = null"
    />
  </div>
</template>
