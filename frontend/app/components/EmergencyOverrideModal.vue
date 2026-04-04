<script setup lang="ts">
const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full">
      <h3 class="font-serif text-lg text-verse-text mb-2">Adab Curfew Active</h3>
      <p class="text-sm text-verse-text/70 mb-4">
        It's currently within the quiet hours (10 PM - 4 AM). This action requires an emergency override.
      </p>
      <p class="text-sm text-verse-text/70 mb-6">
        Do you wish to proceed?
      </p>
      <div class="flex gap-3">
        <button
          @click="emit('cancel')"
          class="flex-1 py-2 rounded-lg border border-verse-slate/20 text-verse-text text-sm hover:bg-verse-slate/5 transition"
        >
          Respect the Curfew
        </button>
        <button
          @click="emit('confirm')"
          class="flex-1 py-2 rounded-lg bg-verse-gold text-white text-sm hover:bg-verse-gold/90 transition"
        >
          Override
        </button>
      </div>
    </div>
  </div>
</template>
