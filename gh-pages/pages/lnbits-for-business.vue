<template>
  <div>
    <SiteHeader />

    <!-- ── HERO ───────────────────────────────────────────────── -->
    <section class="relative overflow-hidden pt-24 pb-28 px-5 sm:px-8">
      <div
        class="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[500px] rounded-full"
        style="background: radial-gradient(ellipse at center, rgba(255,30,230,0.10) 0%, transparent 65%);"
      />
      <div class="relative max-w-5xl mx-auto">

        <div class="inline-flex items-center gap-2 mb-8">
          <span class="w-1.5 h-1.5 rounded-full bg-ln-pink animate-pulse" />
          <span class="font-mono text-xs uppercase tracking-widest text-ln-muted">
            For business
          </span>
        </div>

        <h1 class="font-display font-bold text-ln-text leading-[1.1] tracking-tight mb-6"
            style="font-size: clamp(2.2rem, 6vw, 4rem);">
          Simple payments for your shop,<br>
          <span class="text-ln-pink">under your control.</span>
        </h1>

        <p class="font-display text-ln-muted text-lg sm:text-xl leading-relaxed max-w-xl mb-10">
          LNbitsBox lets your business accept Bitcoin payments without relying
          on third parties or managing lightning channels. It just works.
        </p>

        <div class="flex flex-wrap items-center gap-4">
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

      </div>
    </section>

    <!-- ── HERO IMAGE ─────────────────────────────────────────── -->
    <section class="px-5 sm:px-8 pb-20">
      <div class="max-w-4xl mx-auto">
        <PlaceholderImg label="Neutral retail setting with Android POS and LNbitsBox" aspect="16/9" />
      </div>
    </section>

    <!-- ── ACCEPT PAYMENTS ────────────────────────────────────── -->
    <section class="px-5 sm:px-8 py-24 border-t border-ln-border">
      <div class="max-w-5xl mx-auto">

        <h2 class="font-display font-bold text-ln-text text-3xl sm:text-4xl tracking-tight mb-14 text-center">
          Accept payments
        </h2>

        <div class="grid md:grid-cols-2 gap-8">

          <!-- Android POS -->
          <div class="bg-ln-card border border-ln-border rounded-2xl overflow-hidden hover:border-ln-pink/20 transition-colors duration-200">
            <div class="p-5 pb-0">
              <PlaceholderImg label="LNbits POS on Android" aspect="3/2" />
            </div>
            <div class="p-7">
              <h3 class="font-display font-semibold text-ln-text text-xl mb-4">Android POS</h3>
              <p class="font-display text-ln-muted text-sm leading-relaxed mb-4">
                Use an Android phone or tablet at your checkout.
              </p>
              <ul class="space-y-2">
                <li class="flex items-start gap-2.5">
                  <span class="text-ln-pink mt-0.5">→</span>
                  <span class="font-display text-ln-muted text-sm">QR payments for Bitcoin</span>
                </li>
                <li class="flex items-start gap-2.5">
                  <span class="text-ln-pink mt-0.5">→</span>
                  <span class="font-display text-ln-muted text-sm">Tap-to-pay for fiat payments</span>
                </li>
                <li class="flex items-start gap-2.5">
                  <span class="text-ln-pink mt-0.5">→</span>
                  <span class="font-display text-ln-muted text-sm">Fast confirmation</span>
                </li>
                <li class="flex items-start gap-2.5">
                  <span class="text-ln-pink mt-0.5">→</span>
                  <span class="font-display text-ln-muted text-sm">Clear checkout screen</span>
                </li>
              </ul>
            </div>
          </div>

          <!-- Fiat display -->
          <div class="bg-ln-card border border-ln-border rounded-2xl overflow-hidden hover:border-ln-pink/20 transition-colors duration-200">
            <div class="p-5 pb-0">
              <PlaceholderImg label="Fiat checkout screen" aspect="3/2" />
            </div>
            <div class="p-7">
              <h3 class="font-display font-semibold text-ln-text text-xl mb-4">Fiat display</h3>
              <p class="font-display text-ln-muted text-sm leading-relaxed mb-4">
                Set prices in local currency. Customers pay in Bitcoin.
              </p>
              <ul class="space-y-2">
                <li class="flex items-start gap-2.5">
                  <span class="text-ln-pink mt-0.5">→</span>
                  <span class="font-display text-ln-muted text-sm">Shows local price</span>
                </li>
                <li class="flex items-start gap-2.5">
                  <span class="text-ln-pink mt-0.5">→</span>
                  <span class="font-display text-ln-muted text-sm">Converts automatically</span>
                </li>
                <li class="flex items-start gap-2.5">
                  <span class="text-ln-pink mt-0.5">→</span>
                  <span class="font-display text-ln-muted text-sm">Simple for staff</span>
                </li>
              </ul>
            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- ── RUNS IN YOUR SHOP ──────────────────────────────────── -->
    <section class="px-5 sm:px-8 py-24 border-t border-ln-border">
      <div class="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-center">
        <div>
          <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-4">
            Runs in your shop
          </h2>
          <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed mb-2">
            LNbitsBox runs on a small device in your space. Your payment system stays under your control.
          </p>
          <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed">
            No external account required for Bitcoin payments.
          </p>
        </div>
        <PlaceholderImg label="Device under counter near router" aspect="3/2" />
      </div>
    </section>

    <!-- ── TRANSACTIONS & EXPORTS ─────────────────────────────── -->
    <section class="px-5 sm:px-8 py-24 border-t border-ln-border">
      <div class="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-center">
        <div class="md:order-2">
          <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-4">
            Transactions &amp; exports
          </h2>
          <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed mb-5">
            LNbits includes tools for business records.
          </p>
          <ul class="space-y-3">
            <li class="flex items-start gap-3">
              <span class="text-ln-pink mt-0.5">→</span>
              <span class="font-display text-ln-muted text-sm">View transactions</span>
            </li>
            <li class="flex items-start gap-3">
              <span class="text-ln-pink mt-0.5">→</span>
              <span class="font-display text-ln-muted text-sm">Export CSV</span>
            </li>
            <li class="flex items-start gap-3">
              <span class="text-ln-pink mt-0.5">→</span>
              <span class="font-display text-ln-muted text-sm">Track activity</span>
            </li>
            <li class="flex items-start gap-3">
              <span class="text-ln-pink mt-0.5">→</span>
              <span class="font-display text-ln-muted text-sm">Use for bookkeeping</span>
            </li>
          </ul>
        </div>
        <div class="md:order-1">
          <PlaceholderImg label="LNbits transactions screen" aspect="3/2" />
        </div>
      </div>
    </section>

    <!-- ── COMPARISON TABLE ───────────────────────────────────── -->
    <section class="px-5 sm:px-8 py-24 border-t border-ln-border">
      <div class="max-w-3xl mx-auto">

        <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-10 text-center">
          How it compares
        </h2>

        <div class="overflow-x-auto rounded-2xl border border-ln-border">
          <table class="w-full text-left">
            <thead>
              <tr class="bg-ln-card border-b border-ln-border">
                <th class="font-display font-semibold text-ln-muted text-xs uppercase tracking-wider px-6 py-4">Feature</th>
                <th class="font-display font-semibold text-ln-pink text-xs uppercase tracking-wider px-6 py-4">LNbitsBox</th>
                <th class="font-display font-semibold text-ln-muted text-xs uppercase tracking-wider px-6 py-4">Typical hosted processor</th>
              </tr>
            </thead>
            <tbody class="font-display text-sm">
              <tr class="border-b border-ln-border/50">
                <td class="text-ln-muted px-6 py-3.5">Custody of funds</td>
                <td class="text-ln-text px-6 py-3.5">You control wallet</td>
                <td class="text-ln-muted px-6 py-3.5">Held by provider</td>
              </tr>
              <tr class="border-b border-ln-border/50">
                <td class="text-ln-muted px-6 py-3.5">Account required</td>
                <td class="text-ln-text px-6 py-3.5">No</td>
                <td class="text-ln-muted px-6 py-3.5">Yes</td>
              </tr>
              <tr class="border-b border-ln-border/50">
                <td class="text-ln-muted px-6 py-3.5">Runs locally</td>
                <td class="text-ln-text px-6 py-3.5">Yes</td>
                <td class="text-ln-muted px-6 py-3.5">No</td>
              </tr>
              <tr class="border-b border-ln-border/50">
                <td class="text-ln-muted px-6 py-3.5">Subscription</td>
                <td class="text-ln-text px-6 py-3.5">No</td>
                <td class="text-ln-muted px-6 py-3.5">Often yes</td>
              </tr>
              <tr class="border-b border-ln-border/50">
                <td class="text-ln-muted px-6 py-3.5">Transaction export</td>
                <td class="text-ln-text px-6 py-3.5">Yes</td>
                <td class="text-ln-muted px-6 py-3.5">Yes</td>
              </tr>
              <tr>
                <td class="text-ln-muted px-6 py-3.5">Setup time</td>
                <td class="text-ln-text px-6 py-3.5">Minutes</td>
                <td class="text-ln-muted px-6 py-3.5">Account setup needed</td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>
    </section>

    <!-- ── SPARK ──────────────────────────────────────────────── -->
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
          LNbitsBox uses Spark to interact with the Lightning network while you keep control
          of your wallet. Designed for simple self-custodial use.
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
        <h2 class="font-display font-bold text-ln-text text-3xl sm:text-4xl tracking-tight mb-10">
          Run your own <span class="text-ln-pink">Lightning payments</span>
        </h2>
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
