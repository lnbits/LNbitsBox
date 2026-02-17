<template>
  <footer class="border-t border-ln-border px-5 sm:px-8 py-8">
    <div class="max-w-5xl mx-auto flex flex-wrap items-center justify-between gap-4">

      <p class="font-mono text-xs uppercase tracking-widest text-ln-muted">
        LNbitsBox &middot; By
        <a href="https://lnbits.com" target="_blank" rel="noopener"
           class="text-ln-pink hover:text-ln-pink-dim transition-colors">LNbits</a>
      </p>

      <div class="flex flex-wrap items-center gap-x-6 gap-y-2">
        <NuxtLink
          to="/faqs"
          class="font-mono text-xs uppercase tracking-wider text-ln-muted hover:text-ln-text transition-colors"
        >
          FAQs
        </NuxtLink>
        <a
          href="https://github.com/lnbits/LNbitsBox"
          target="_blank" rel="noopener"
          class="font-mono text-xs uppercase tracking-wider text-ln-muted hover:text-ln-text transition-colors"
        >
          GitHub
        </a>
        <a
          href="https://t.me/lnbits"
          target="_blank" rel="noopener"
          class="font-mono text-xs uppercase tracking-wider text-ln-muted hover:text-ln-text transition-colors"
        >
          Telegram
        </a>
        <a
          href="https://lnbits.com"
          target="_blank" rel="noopener"
          class="font-mono text-xs uppercase tracking-wider text-ln-muted hover:text-ln-text transition-colors"
        >
          LNbits
        </a>
      </div>

    </div>
  </footer>
</template>
