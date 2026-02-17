<template>
  <div>
    <SiteHeader />

    <!-- ── PAGE HEADER ────────────────────────────────────────── -->
    <section class="relative overflow-hidden pt-24 pb-16 px-5 sm:px-8">
      <div
        class="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[500px] rounded-full"
        style="background: radial-gradient(ellipse at center, rgba(255,30,230,0.08) 0%, transparent 65%);"
      />
      <div class="relative max-w-5xl mx-auto">
        <div class="inline-flex items-center gap-2 mb-6">
          <span class="w-1.5 h-1.5 rounded-full bg-ln-pink animate-pulse" />
          <span class="font-mono text-xs uppercase tracking-widest text-ln-muted">Step-by-step</span>
        </div>
        <h1 class="font-display font-bold text-ln-text leading-[1.1] tracking-tight mb-4"
            style="font-size: clamp(2rem, 6vw, 3.5rem);">
          How It Works
        </h1>
        <p class="font-display text-ln-muted text-lg sm:text-xl leading-relaxed max-w-xl">
          From unboxing to accepting payments in minutes.
        </p>
      </div>
    </section>

    <!-- ── STEP 1 — PLUG IN ───────────────────────────────────── -->
    <section class="px-5 sm:px-8 py-20 border-t border-ln-border">
      <div class="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-center">
        <div>
          <span class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-ln-pink/10 font-mono text-ln-pink text-sm font-bold mb-4">1</span>
          <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-4">
            Plug in
          </h2>
          <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed">
            Plug LNbitsBox into power and your router (or Wi-Fi). That's all the hardware setup there is.
          </p>
        </div>
        <img src="~/assets/img/how-it-works-plugin.jpg" alt="" title=""
          class="rounded-2xl border-2 border-ln-border bg-ln-card/60 flex flex-col items-center justify-center gap-3 overflow-hidden"
           />
      </div>
    </section>

    <!-- ── STEP 2 — OPEN SETUP ────────────────────────────────── -->
    <section class="px-5 sm:px-8 py-20 border-t border-ln-border">
      <div class="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-center">
        <div class="md:order-2">
          <span class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-ln-pink/10 font-mono text-ln-pink text-sm font-bold mb-4">2</span>
          <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-4">
            Open setup page
          </h2>
          <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed">
            Open the setup page in your browser. Create your wallet and finish setup.
          </p>
        </div>
        <div class="md:order-1">
          <img src="~/assets/img/how-it-works-configure.jpg" alt="" title=""
          class="rounded-2xl border-2 border-ln-border bg-ln-card/60 flex flex-col items-center justify-center gap-3 overflow-hidden"
           />
        </div>
      </div>
    </section>

    <!-- ── STEP 3 — START USING ───────────────────────────────── -->
    <section class="px-5 sm:px-8 py-20 border-t border-ln-border">
      <div class="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-center">
        <div>
          <span class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-ln-pink/10 font-mono text-ln-pink text-sm font-bold mb-4">3</span>
          <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-4">
            Start using LNbits
          </h2>
          <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed">
            LNbits opens automatically after setup. Create wallets, apps, or payment screens.
          </p>
        </div>
        <img src="~/assets/img/how-it-works-use.jpg" alt="" title=""
          class="rounded-2xl border-2 border-ln-border bg-ln-card/60 flex flex-col items-center justify-center gap-3 overflow-hidden"
           />
      </div>
    </section>

    <!-- STEP 4 - MANAGE YOUR SERVER USING THE ADMIN PANEL -->
     <section class="px-5 sm:px-8 py-20 border-t border-ln-border">
      <div class="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-center">
        <div class="md:order-2">
          <span class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-ln-pink/10 font-mono text-ln-pink text-sm font-bold mb-4">4</span>
          <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-4">
            Manage your server using the admin panel
          </h2>
          <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed">
            Access the admin panel to manage and monitor your LNbitsBox.
          </p>
        </div>
        <div class="md:order-1">
          <img src="~/assets/img/how-it-works-monitor.jpg" alt="" title=""
          class="rounded-2xl border-2 border-ln-border bg-ln-card/60 flex flex-col items-center justify-center gap-3 overflow-hidden"
           />
        </div>
      </div>
    </section>

    <!-- ── SPARK EXPLANATION ──────────────────────────────────── -->
    <section class="px-5 sm:px-8 py-24 border-t border-ln-border">
      <div class="max-w-3xl mx-auto text-center">
        <div class="w-12 h-12 rounded-xl bg-ln-pink/10 flex items-center justify-center mx-auto mb-6">
          <svg class="w-6 h-6 text-ln-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
          </svg>
        </div>
        <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-6">
          Lightning funding with Spark
        </h2>
        <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed mb-4">
          Spark is the Lightning funding system used by LNbitsBox. It lets LNbits interact
          with the Lightning network while you keep control of your wallet.
        </p>
        <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed">
          Spark gives you a fully self-custodial Bitcoin experience with the ability to
          exit to Bitcoin at any time without relying on a third party.
        </p>
      </div>
    </section>

    <!-- ── CTA ────────────────────────────────────────────────── -->
    <section class="relative px-5 sm:px-8 py-28 border-t border-ln-border overflow-hidden">
      <div
        class="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full"
        style="background: radial-gradient(ellipse at center, rgba(255,30,230,0.06) 0%, transparent 65%);"
      />
      <div class="relative max-w-5xl mx-auto text-center">
        <h2 class="font-display font-bold text-ln-text text-3xl sm:text-4xl tracking-tight mb-4">
          Plug in. Set up. <span class="text-ln-pink">Use Bitcoin.</span>
        </h2>
        <p class="font-display text-ln-muted text-lg mb-10">
          Ready in minutes, no experience required.
        </p>
        <a
          href="https://shop.lnbits.com/LNbitsbox"
          target="_blank" rel="noopener"
          class="inline-flex items-center gap-2.5 bg-ln-pink hover:bg-ln-pink-dim text-white font-mono text-sm uppercase tracking-wider px-8 py-4 rounded-xl transition-colors duration-150 glow-pink"
        >
          Buy LNbitsBox
        </a>
      </div>
    </section>

    <SiteFooter />
  </div>
</template>
