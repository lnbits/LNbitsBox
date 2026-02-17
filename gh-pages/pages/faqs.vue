<script setup>
const faqs = [
  {
    q: 'What is LNbitsBox?',
    a: 'LNbitsBox is a small, ready-to-use device that runs LNbits with a self-custodial Lightning wallet powered by Spark. You plug it in, open the setup page in your browser, create your wallet, and you\'re ready to send and accept Bitcoin payments.',
  },
  // do i have to to be on the same network to use lnbits and lnbits extensions?
  {
    q: 'Do I need to be on the same network to use LNbits and LNbits extensions?',
    a: 'No. LNbitsBox runs on your local network, but you can access it from anywhere using the optional LNbits Tunnel. This secure remote access solution lets you use LNbits without needing to be on the same network.'
  },
  {
    q: 'What\'s in the box?',
    a: 'You receive the LNbitsBox device, a power supply, a pre-flashed microSD card, and a quick start guide. Everything you need is included — just plug in and follow the setup.',
  },
  {
    q: 'Do I need any technical knowledge?',
    a: 'No. LNbitsBox is designed for people with no technical background. The setup takes a few minutes and is done entirely through your web browser — no command line, no configuration files, no software to install on your computer.',
  },
  {
    q: 'Do I control my own funds?',
    a: 'Yes. LNbitsBox uses Spark, a self-custodial Bitcoin layer 2. Your wallet keys stay on your device and you can exit to on-chain Bitcoin at any time. No third party ever controls your funds.',
  },
  {
    q: 'What is Spark?',
    a: 'Spark is the Bitcoin layer 2 built into LNbits. It connects your LNbits to the Bitcoin network while keeping you in full control of your wallet. You don\'t need to manage channels or understand how Lightning works — Spark handles that for you.',
  },
  {
    q: 'Is it suitable for a shop or business?',
    a: 'Yes. LNbits includes a point-of-sale and inventory management system that works on mobile devices. You can set prices in your local currency, accept Bitcoin payments via QR code or NFC, and export transaction records as CSV for bookkeeping.',
  },
  {
    q: 'Does it need an internet connection?',
    a: 'Yes. LNbits needs an internet connection to send and receive Lightning payments. Connect it to your router with an ethernet cable or configure Wi-Fi during setup.',
  },
  {
    q: 'Do you ship worldwide?',
    a: 'Yes. LNbitsBox ships worldwide from the LNbits shop.',
  },
  {
    q: 'Where can I get help?',
    a: 'Community support is available on Telegram and GitHub. The LNbits community is active and welcoming to newcomers.',
  },
]

const openIndex = ref(null)

function toggle(i) {
  openIndex.value = openIndex.value === i ? null : i
}
</script>

<template>
  <div>
    <SiteHeader />

    <!-- ── PAGE HEADER ────────────────────────────────────────── -->
    <section class="relative overflow-hidden pt-24 pb-16 px-5 sm:px-8">
      <div
        class="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[500px] rounded-full"
        style="background: radial-gradient(ellipse at center, rgba(255,30,230,0.08) 0%, transparent 65%);"
      />
      <div class="relative max-w-3xl mx-auto">
        <h1 class="font-display font-bold text-ln-text leading-[1.1] tracking-tight mb-4"
            style="font-size: clamp(2rem, 6vw, 3.5rem);">
          Frequently Asked Questions
        </h1>
        <p class="font-display text-ln-muted text-lg sm:text-xl leading-relaxed">
          Everything you need to know about LNbitsBox.
        </p>
      </div>
    </section>

    <!-- ── FAQ LIST ───────────────────────────────────────────── -->
    <section class="px-5 sm:px-8 pb-24">
      <div class="max-w-3xl mx-auto space-y-3">

        <div
          v-for="(faq, i) in faqs"
          :key="i"
          class="border border-ln-border rounded-xl overflow-hidden transition-colors duration-200"
          :class="openIndex === i ? 'border-ln-pink/30 bg-ln-card' : 'bg-ln-card/50 hover:border-ln-pink/20'"
        >
          <button
            class="w-full flex items-center justify-between gap-4 px-6 py-5 text-left"
            @click="toggle(i)"
          >
            <span class="font-display font-semibold text-ln-text text-base">{{ faq.q }}</span>
            <span
              class="text-ln-muted text-xl flex-shrink-0 transition-transform duration-200"
              :class="openIndex === i ? 'rotate-45' : ''"
            >+</span>
          </button>
          <div
            v-show="openIndex === i"
            class="px-6 pb-5"
          >
            <p class="font-display text-ln-muted text-sm leading-relaxed">{{ faq.a }}</p>
          </div>
        </div>

      </div>
    </section>

    <!-- ── CTA ────────────────────────────────────────────────── -->
    <section class="relative px-5 sm:px-8 py-28 border-t border-ln-border overflow-hidden">
      <div
        class="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full"
        style="background: radial-gradient(ellipse at center, rgba(255,30,230,0.06) 0%, transparent 65%);"
      />
      <div class="relative max-w-5xl mx-auto text-center">
        <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-4">
          Ready to get started?
        </h2>
        <div class="flex flex-wrap justify-center gap-4">
          <a
            href="https://shop.lnbits.com/LNbitsbox"
            target="_blank" rel="noopener"
            class="inline-flex items-center gap-2.5 bg-ln-pink hover:bg-ln-pink-dim text-white font-mono text-sm uppercase tracking-wider px-8 py-4 rounded-xl transition-colors duration-150 glow-pink"
          >
            Buy LNbitsBox
          </a>
          <a
            href="https://t.me/lnbits"
            target="_blank" rel="noopener"
            class="inline-flex items-center gap-2.5 border border-ln-border hover:border-ln-pink/30 text-ln-muted hover:text-ln-text font-mono text-sm uppercase tracking-wider px-8 py-4 rounded-xl transition-colors duration-150"
          >
            Ask on Telegram
          </a>
        </div>
      </div>
    </section>

    <SiteFooter />
  </div>
</template>
