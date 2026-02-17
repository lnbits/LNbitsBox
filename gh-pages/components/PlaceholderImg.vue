<script setup>
defineProps({
  label: { type: String, required: true },
  aspect: { type: String, default: '16/9' },
})
</script>

<template>
  <div
    class="rounded-2xl border-2 border-dashed border-ln-border bg-ln-card/60 flex flex-col items-center justify-center gap-3 overflow-hidden"
    :style="{ aspectRatio: aspect }"
    :title="label"
  >
    <svg class="w-10 h-10 text-ln-muted/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
    </svg>
    <span class="font-mono text-xs text-ln-muted/50 uppercase tracking-wider text-center px-4">{{ label }}</span>
  </div>
</template>
