<script setup lang="ts">
interface TalkNote {
  id: number
  user_id: number
  username: string
  text: string
  created_at: string
}

interface Talk {
  id: number
  title: string
  description: string | null
  proposed_by: number
  proposer_name: string
  status: string
  queued_for: string | null
  notes: TalkNote[]
  note_count: number
  created_at: string
}

const { user } = useAuth()
const { api } = useApi()
const route = useRoute()
const loading = ref(true)
const talks = ref<Talk[]>([])
const filter = ref<'all' | 'queued' | 'follow_up' | 'discussed'>('all')
const showNewForm = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const newQueuedFor = ref('')
const expandedId = ref<number | null>(null)
const noteTexts = ref<Record<number, string>>({})

async function loadTalks() {
  try {
    talks.value = await api<Talk[]>('/talks')
  } finally {
    loading.value = false
  }
}

const filteredTalks = computed(() => {
  if (filter.value === 'all') return talks.value
  return talks.value.filter(t => t.status === filter.value)
})

const stats = computed(() => ({
  total: talks.value.length,
  queued: talks.value.filter(t => t.status === 'queued').length,
  followUp: talks.value.filter(t => t.status === 'follow_up').length,
  discussed: talks.value.filter(t => t.status === 'discussed').length,
}))

function statusBadge(status: string): { text: string; style: string } {
  switch (status) {
    case 'queued': return { text: 'Queued', style: 'bg-verse-slate text-white' }
    case 'discussed': return { text: 'Discussed', style: 'bg-verse-gold text-white' }
    case 'follow_up': return { text: 'Follow-up', style: 'bg-verse-rose text-white' }
    default: return { text: status, style: 'bg-verse-slate/20' }
  }
}

function proposerInitial(talk: Talk): string {
  return talk.proposer_name[0]
}

function proposerColor(talk: Talk): string {
  return talk.proposed_by === user.value?.id
    ? (user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose')
    : (user.value?.username === 'alif' ? 'bg-verse-rose' : 'bg-verse-slate')
}

function noteAuthorColor(note: TalkNote): string {
  return note.user_id === user.value?.id
    ? (user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose')
    : (user.value?.username === 'alif' ? 'bg-verse-rose' : 'bg-verse-slate')
}

function formatQueuedFor(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

async function createTalk() {
  await api('/talks', {
    method: 'POST',
    body: {
      title: newTitle.value,
      description: newDesc.value || null,
      queued_for: newQueuedFor.value || null,
    },
  })
  newTitle.value = ''
  newDesc.value = ''
  newQueuedFor.value = ''
  showNewForm.value = false
  await loadTalks()
}

async function updateStatus(talkId: number, status: string) {
  await api(`/talks/${talkId}`, {
    method: 'PATCH',
    body: { status },
  })
  await loadTalks()
}

async function deleteTalk(talkId: number) {
  await api(`/talks/${talkId}`, { method: 'DELETE' })
  await loadTalks()
}

async function addNote(talkId: number) {
  const text = noteTexts.value[talkId]?.trim()
  if (!text) return
  await api(`/talks/${talkId}/notes`, {
    method: 'POST',
    body: { text },
  })
  noteTexts.value[talkId] = ''
  await loadTalks()
}

async function deleteNote(talkId: number, noteId: number) {
  await api(`/talks/${talkId}/notes/${noteId}`, { method: 'DELETE' })
  await loadTalks()
}

onMounted(() => {
  loadTalks()
  if (route.query.new === '1') showNewForm.value = true
})
</script>

<template>
  <div>
    <!-- Loading skeleton -->
    <div v-if="loading" class="animate-pulse">
      <div class="flex justify-between mb-4">
        <div>
          <div class="h-8 bg-verse-slate/10 rounded w-40 mb-2" />
          <div class="h-4 bg-verse-slate/10 rounded w-56" />
        </div>
        <div class="h-10 bg-verse-slate/10 rounded w-28" />
      </div>
      <div class="flex gap-2 mb-4">
        <div v-for="i in 3" :key="i" class="h-6 bg-verse-slate/10 rounded-full w-20" />
      </div>
      <div class="space-y-3">
        <div v-for="i in 3" :key="i" class="bg-white rounded-xl border border-verse-slate/10 p-4">
          <div class="h-5 bg-verse-slate/10 rounded w-1/2 mb-2" />
          <div class="h-4 bg-verse-slate/10 rounded w-1/3" />
        </div>
      </div>
    </div>

    <template v-else>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-2 gap-3">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Queued Talks</h1>
        <div class="header-gradient-line w-14" />
        <p class="text-sm text-verse-text/50 mt-2">Save important topics for your weekend QT</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition w-full sm:w-auto"
      >
        {{ showNewForm ? 'Cancel' : '+ Queue Talk' }}
      </button>
    </div>

    <div class="flex gap-2 mb-4 flex-wrap">
      <span class="stats-pill bg-verse-slate/10 text-verse-text/60">{{ stats.total }} total</span>
      <span class="stats-pill bg-verse-slate/10 text-verse-slate">{{ stats.queued }} queued</span>
      <span v-if="stats.followUp" class="stats-pill bg-verse-rose/10 text-verse-rose">{{ stats.followUp }} follow-up</span>
    </div>

    <form v-if="showNewForm" @submit.prevent="createTalk" class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 mb-6">
      <input v-model="newTitle" placeholder="What do you need to discuss?" required class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm" />
      <textarea v-model="newDesc" placeholder="Add context (optional)" rows="2" class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm" />
      <div class="mb-3">
        <label class="block text-xs text-verse-text/50 mb-1">Discuss by (optional)</label>
        <input v-model="newQueuedFor" type="datetime-local" class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm text-verse-text/70" />
      </div>
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">Queue Talk</button>
    </form>

    <div class="flex gap-1 mb-4 bg-white rounded-lg p-1 border border-verse-slate/10 w-full sm:w-fit overflow-x-auto">
      <button
        v-for="f in (['all', 'queued', 'follow_up', 'discussed'] as const)"
        :key="f"
        @click="filter = f"
        class="flex-1 sm:flex-none px-3 py-1 text-sm rounded-md transition whitespace-nowrap"
        :class="filter === f ? 'bg-verse-slate text-white' : 'text-verse-text/60 hover:bg-verse-slate/5'"
      >
        {{ f === 'follow_up' ? 'Follow-up' : f.charAt(0).toUpperCase() + f.slice(1) }}
        <span class="ml-1 opacity-70">({{ f === 'all' ? stats.total : f === 'queued' ? stats.queued : f === 'follow_up' ? stats.followUp : stats.discussed }})</span>
      </button>
    </div>

    <div class="space-y-2">
      <div
        v-for="talk in filteredTalks"
        :key="talk.id"
        class="rounded-xl border p-4 transition bg-white border-verse-slate/10"
        :class="talk.status === 'discussed' ? 'opacity-60' : ''"
      >
        <div class="flex items-center justify-between gap-2 cursor-pointer" @click="expandedId = expandedId === talk.id ? null : talk.id">
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <span class="avatar-dot shrink-0" :class="proposerColor(talk)">{{ proposerInitial(talk) }}</span>
            <span class="text-sm font-medium text-verse-text truncate">{{ talk.title }}</span>
            <span v-if="talk.queued_for" class="text-[10px] text-verse-slate/50 shrink-0 hidden sm:inline">📅 {{ formatQueuedFor(talk.queued_for) }}</span>
            <span v-if="talk.note_count" class="text-xs text-verse-text/30">{{ talk.note_count }} notes</span>
          </div>
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium shrink-0"
            :class="statusBadge(talk.status).style"
          >
            {{ statusBadge(talk.status).text }}
          </span>
        </div>

        <div v-if="expandedId === talk.id" class="mt-3 pt-3 border-t border-verse-slate/5">
          <p v-if="talk.queued_for" class="text-xs text-verse-text/40 mb-2 sm:hidden">📅 Discuss by: {{ formatQueuedFor(talk.queued_for) }}</p>
          <p v-if="talk.description" class="text-xs text-verse-text/60 mb-3">{{ talk.description }}</p>

          <!-- Notes -->
          <div v-if="talk.notes.length" class="space-y-2 mb-3">
            <div v-for="note in talk.notes" :key="note.id" class="flex items-start gap-2">
              <span class="avatar-dot text-[7px] mt-0.5 shrink-0" :class="noteAuthorColor(note)">{{ note.username[0] }}</span>
              <div class="flex-1 min-w-0">
                <p class="text-xs text-verse-text">{{ note.text }}</p>
                <p class="text-[10px] text-verse-text/30">{{ note.username }}</p>
              </div>
              <button
                v-if="note.user_id === user?.id"
                @click.stop="deleteNote(talk.id, note.id)"
                class="text-verse-text/20 hover:text-red-400 transition text-xs shrink-0"
              >&times;</button>
            </div>
          </div>

          <!-- Add note -->
          <form @submit.prevent="addNote(talk.id)" class="flex gap-2 mb-3">
            <input
              v-model="noteTexts[talk.id]"
              placeholder="Add a note..."
              class="flex-1 px-2.5 py-1.5 rounded-lg border border-verse-slate/15 text-xs focus:outline-none focus:ring-1 focus:ring-verse-slate/30"
              @click.stop
            />
            <button type="submit" class="px-3 py-1.5 bg-verse-slate/10 text-verse-slate text-xs rounded-lg hover:bg-verse-slate/20 transition" @click.stop>Add</button>
          </form>

          <!-- Actions -->
          <div class="flex flex-wrap gap-2">
            <button
              v-if="talk.status !== 'discussed'"
              @click.stop="updateStatus(talk.id, 'discussed')"
              class="text-xs px-3 py-1 rounded-full bg-verse-gold/10 text-verse-gold hover:bg-verse-gold/20 transition"
            >Mark Discussed</button>
            <button
              v-if="talk.status !== 'follow_up'"
              @click.stop="updateStatus(talk.id, 'follow_up')"
              class="text-xs px-3 py-1 rounded-full bg-verse-rose/10 text-verse-rose hover:bg-verse-rose/20 transition"
            >Needs Follow-up</button>
            <button
              v-if="talk.status !== 'queued'"
              @click.stop="updateStatus(talk.id, 'queued')"
              class="text-xs px-3 py-1 rounded-full bg-verse-slate/10 text-verse-slate hover:bg-verse-slate/20 transition"
            >Re-queue</button>
            <button
              v-if="talk.proposed_by === user?.id && talk.status === 'queued'"
              @click.stop="deleteTalk(talk.id)"
              class="text-xs text-red-400 ml-auto"
            >Delete</button>
          </div>
        </div>
      </div>

      <p v-if="filteredTalks.length === 0" class="text-center text-verse-text/40 py-8">
        No talks match this filter.
      </p>
    </div>
    </template>
  </div>
</template>
