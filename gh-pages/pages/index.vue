<template>
  <div>
    <SiteHeader />

    <!-- ── HERO ───────────────────────────────────────────────── -->
    <section class="relative overflow-hidden pt-24 pb-28 px-5 sm:px-8">

      <!-- Pink radial glow -->
      <div
        class="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[500px] rounded-full"
        style="background: radial-gradient(ellipse at center, rgba(255,30,230,0.10) 0%, transparent 65%);"
      />

      <div class="relative max-w-5xl mx-auto">

        <!-- Badge -->
        <div class="inline-flex items-center gap-2 mb-8">
          <span class="w-1.5 h-1.5 rounded-full bg-ln-pink animate-pulse" />
          <span class="font-mono text-xs uppercase tracking-widest text-ln-muted">
            Plug-and-play &middot; Self-custodial
          </span>
        </div>

        <!-- Headline -->
        <h1 class="font-display font-bold text-ln-text leading-[1.1] tracking-tight mb-6"
            style="font-size: clamp(2.4rem, 7vw, 4.5rem);">
          LNbits.<br>
          <span class="text-ln-pink">Running where you are.</span>
        </h1>

        <!-- Sub -->
        <p class="font-display text-ln-muted text-lg sm:text-xl leading-relaxed max-w-xl mb-10">
          LNbitsBox lets you run LNbits with a
          self-custodial Lightning wallet. Simply.
          <br>Plug it in, complete a quick setup,
          and start sending or accepting payments.
        </p>

        <!-- CTAs -->
        <div class="flex flex-wrap items-center gap-4 mb-16">
          <a
            href="https://shop.lnbits.com/LNbitsbox"
            target="_blank" rel="noopener"
            class="inline-flex items-center gap-2.5 bg-ln-pink hover:bg-ln-pink-dim text-white font-mono text-sm uppercase tracking-wider px-6 py-3 rounded-xl transition-colors duration-150 glow-pink"
          >
            Buy LNbitsBox
          </a>
          <NuxtLink
            to="/how-it-works"
            class="inline-flex items-center gap-2.5 border border-ln-border hover:border-ln-pink/30 text-ln-muted hover:text-ln-text font-mono text-sm uppercase tracking-wider px-6 py-3 rounded-xl transition-colors duration-150"
          >
            How It Works
          </NuxtLink>
        </div>

        <!-- Hero image -->
        <div class="rounded-2xl overflow-hidden border border-ln-border max-w-3xl">
          <img
            src="~/assets/img/lnbits-box-on-desk.jpg"
            alt="LNbitsBox device on a desk"
            title="LNbitsBox — clean product photo in a friendly home setting"
            class="w-full h-auto"
          />
        </div>

      </div>
    </section>

    <!-- ── KEY BENEFITS ───────────────────────────────────────── -->
    <section class="px-5 sm:px-8 py-24">
      <div class="max-w-5xl mx-auto">

        <h2 class="font-display font-bold text-ln-text text-3xl sm:text-4xl tracking-tight mb-4 text-center">
          Why LNbitsBox?
        </h2>
        <p class="font-display text-ln-muted text-base text-center mb-14 max-w-lg mx-auto">
          Everything you need for self-custodial Lightning payments, in one small box.
        </p>

        <div class="grid sm:grid-cols-3 gap-6">

          <!-- Simple -->
          <div class="bg-ln-card border border-ln-border rounded-2xl p-8 hover:border-ln-pink/20 transition-colors duration-200">
            <div class="w-12 h-12 rounded-xl bg-ln-pink/10 flex items-center justify-center mb-5">
              <svg class="w-6 h-6 text-ln-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
              </svg>
            </div>
            <h3 class="font-display font-semibold text-ln-text text-lg mb-3">Simple</h3>
            <p class="font-display text-ln-muted text-sm leading-relaxed">
              Plug in, connect to your network, and follow the setup page in your browser. Ready in minutes.
            </p>
          </div>

          <!-- Self-custodial -->
          <div class="bg-ln-card border border-ln-border rounded-2xl p-8 hover:border-ln-pink/20 transition-colors duration-200">
            <div class="w-12 h-12 rounded-xl bg-ln-pink/10 flex items-center justify-center mb-5">
              <svg class="w-6 h-6 text-ln-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
              </svg>
            </div>
            <h3 class="font-display font-semibold text-ln-text text-lg mb-3">Self-custodial</h3>
            <p class="font-display text-ln-muted text-sm leading-relaxed">
              Your wallet, your keys, your funds. No third party ever touches your money.
            </p>
          </div>

          <!-- Private -->
          <div class="bg-ln-card border border-ln-border rounded-2xl p-8 hover:border-ln-pink/20 transition-colors duration-200">
            <div class="w-12 h-12 rounded-xl bg-ln-pink/10 flex items-center justify-center mb-5">
              <svg class="w-6 h-6 text-ln-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
              </svg>
            </div>
            <h3 class="font-display font-semibold text-ln-text text-lg mb-3">Private</h3>
            <p class="font-display text-ln-muted text-sm leading-relaxed">
              Everything runs on your own network, in your own space. Access it remotely when you need to.
            </p>
          </div>

        </div>
      </div>
    </section>

    <!-- ── WHAT IT IS ─────────────────────────────────────────── -->
    <section class="px-5 sm:px-8 py-24 border-t border-ln-border">
      <div class="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-center">

        <div>
          <h2 class="font-display font-bold text-ln-text text-3xl sm:text-4xl tracking-tight mb-6">
            What it is
          </h2>
          <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed mb-4">
            A small device that runs LNbits with a built-in Lightning wallet
            powered by Spark. You own it, you control it, and everything stays
            with you.
          </p>
        </div>

        
         <img
          src="~/assets/img/lnbits-box-with-pos.jpg"
          alt="LNbitsBox device next to a tablet showing a checkout screen"
          title="LNbitsBox — device next to a tablet showing a checkout screen"
          class="w-full h-auto rounded-2xl border border-ln-border"
        />

      </div>
    </section>

    <!-- ── WHO IT'S FOR ───────────────────────────────────────── -->
    <section class="px-5 sm:px-8 py-24 border-t border-ln-border">
      <div class="max-w-5xl mx-auto">

        <h2 class="font-display font-bold text-ln-text text-3xl sm:text-4xl tracking-tight mb-14 text-center">
          Who it's for
        </h2>

        <div class="grid md:grid-cols-2 gap-6 mb-10">

          <!-- At home -->
          <div class="bg-ln-card border border-ln-border rounded-2xl p-8 hover:border-ln-pink/20 transition-colors duration-200">
            <div class="w-10 h-10 rounded-lg bg-ln-pink/10 flex items-center justify-center mb-5">
              <svg class="w-5 h-5 text-ln-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
              </svg>
            </div>
            <h3 class="font-display font-semibold text-ln-text text-xl mb-5">At home</h3>
            <ul class="space-y-3">
              <li class="flex items-start gap-3">
                <span class="text-ln-pink mt-0.5">→</span>
                <span class="font-display text-ln-muted text-sm leading-relaxed">Your own Bitcoin wallet, running on your network</span>
              </li>
              <li class="flex items-start gap-3">
                <span class="text-ln-pink mt-0.5">→</span>
                <span class="font-display text-ln-muted text-sm leading-relaxed">Send and receive Bitcoin privately</span>
              </li>
              <li class="flex items-start gap-3">
                <span class="text-ln-pink mt-0.5">→</span>
                <span class="font-display text-ln-muted text-sm leading-relaxed">Explore LNbits apps and extensions</span>
              </li>
            </ul>
          </div>

          <!-- In business -->
          <div class="bg-ln-card border border-ln-border rounded-2xl p-8 hover:border-ln-pink/20 transition-colors duration-200">
            <div class="w-10 h-10 rounded-lg bg-ln-pink/10 flex items-center justify-center mb-5">
              <svg class="w-5 h-5 text-ln-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 21v-7.5a.75.75 0 0 1 .75-.75h3a.75.75 0 0 1 .75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349M3.75 21V9.349m0 0a3.001 3.001 0 0 0 3.75-.615A2.993 2.993 0 0 0 9.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 0 0 2.25 1.016c.896 0 1.7-.393 2.25-1.015a3.001 3.001 0 0 0 3.75.614m-16.5 0a3.004 3.004 0 0 1-.621-4.72l1.189-1.19A1.5 1.5 0 0 1 5.378 3h13.243a1.5 1.5 0 0 1 1.06.44l1.19 1.189a3 3 0 0 1-.621 4.72M6.75 18h3.75a.75.75 0 0 0 .75-.75V13.5a.75.75 0 0 0-.75-.75H6.75a.75.75 0 0 0-.75.75v3.75c0 .414.336.75.75.75Z" />
              </svg>
            </div>
            <h3 class="font-display font-semibold text-ln-text text-xl mb-5">In business</h3>
            <ul class="space-y-3">
              <li class="flex items-start gap-3">
                <span class="text-ln-pink mt-0.5">→</span>
                <span class="font-display text-ln-muted text-sm leading-relaxed">Accept Bitcoin payments with LNbits</span>
              </li>
              <li class="flex items-start gap-3">
                <span class="text-ln-pink mt-0.5">→</span>
                <span class="font-display text-ln-muted text-sm leading-relaxed">Set prices in your currency, receive in Bitcoin</span>
              </li>
              <li class="flex items-start gap-3">
                <span class="text-ln-pink mt-0.5">→</span>
                <span class="font-display text-ln-muted text-sm leading-relaxed">Your funds go straight to your wallet</span>
              </li>
              <li class="flex items-start gap-3">
                <span class="text-ln-pink mt-0.5">→</span>
                <span class="font-display text-ln-muted text-sm leading-relaxed">No Lightning knowledge needed — it just works</span>
              </li>
            </ul>
          </div>

        </div>

      </div>
    </section>

    <!-- ── WHAT'S IN THE BOX ──────────────────────────────────── -->
    <section class="px-5 sm:px-8 py-24 border-t border-ln-border">
      <div class="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-center">

        <img src="~/assets/img/in-the-box.jpg" alt="" title=""
          class="rounded-2xl border-2 border-ln-border bg-ln-card/60 flex flex-col items-center justify-center gap-3 overflow-hidden"
           />

        <div>
          <h2 class="font-display font-bold text-ln-text text-3xl sm:text-4xl tracking-tight mb-8">
            What's in the box
          </h2>
          <ul class="space-y-5">
            <li class="flex items-start gap-4">
              <span class="w-7 h-7 rounded-lg bg-ln-pink/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg class="w-4 h-4 text-ln-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
              </span>
              <span class="font-display text-ln-text text-base">LNbitsBox</span>
            </li>
            <li class="flex items-start gap-4">
              <span class="w-7 h-7 rounded-lg bg-ln-pink/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg class="w-4 h-4 text-ln-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
              </span>
              <span class="font-display text-ln-text text-base">Power supply</span>
            </li>
            <li class="flex items-start gap-4">
              <span class="w-7 h-7 rounded-lg bg-ln-pink/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg class="w-4 h-4 text-ln-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
              </span>
              <span class="font-display text-ln-text text-base">Pre-flashed microSD card</span>
            </li>
          </ul>
        </div>

      </div>
    </section>

    <!-- ── PRICE / CTA ────────────────────────────────────────── -->
    <section class="relative px-5 sm:px-8 py-28 border-t border-ln-border overflow-hidden">
      <div
        class="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full"
        style="background: radial-gradient(ellipse at center, rgba(255,30,230,0.06) 0%, transparent 65%);"
      />
      <div class="relative max-w-5xl mx-auto text-center">

        <h2 class="font-display font-bold text-ln-text text-3xl sm:text-4xl tracking-tight mb-4">
          Plug in. <span class="text-ln-pink">Use Bitcoin.</span>
        </h2>

        <p class="font-mono text-xs uppercase tracking-widest text-ln-muted/60 mb-10">
          Ships worldwide
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
