<script setup>
const sections = [
  { id: 'introduction', label: 'Introduction' },
  { id: 'unboxing-and-plugging-in', label: 'Unboxing and Plugging In' },
  { id: 'accessing-the-configurator', label: 'Initial Set-up' },
  { id: 'after-configuration', label: 'Managing Your LNbitsBox' },
]
</script>

<template>
  <div>
    <SiteHeader />

    <section class="relative overflow-hidden pt-24 pb-16 px-5 sm:px-8">
      <div
        class="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[500px] rounded-full"
        style="background: radial-gradient(ellipse at center, rgba(255,30,230,0.08) 0%, transparent 65%);"
      />
      <div class="relative max-w-5xl mx-auto">
        <div class="inline-flex items-center gap-2 mb-6">
          <span class="w-1.5 h-1.5 rounded-full bg-ln-pink animate-pulse" />
          <span class="font-mono text-xs uppercase tracking-widest text-ln-muted">User Guide</span>
        </div>
        <h1
          class="font-display font-bold text-ln-text leading-[1.1] tracking-tight mb-4"
          style="font-size: clamp(2rem, 6vw, 3.5rem);"
        >
          LNbitsBox User Guide
        </h1>
      </div>
    </section>

    <section class="px-5 sm:px-8 pb-24 border-t border-ln-border">
      <div class="max-w-5xl mx-auto grid lg:grid-cols-[240px_minmax(0,1fr)] gap-10 pt-10">
        <aside class="lg:sticky lg:top-24 lg:self-start">
          <div class="border border-ln-border rounded-2xl bg-ln-card/70 p-5 backdrop-blur-sm">
            <p class="font-mono text-xs uppercase tracking-[0.25em] text-ln-muted mb-4">
              On this page
            </p>
            <nav class="flex flex-col gap-2">
              <a
                v-for="section in sections"
                :key="section.id"
                :href="`#${section.id}`"
                class="rounded-xl px-3 py-2 font-display text-sm text-ln-muted hover:text-ln-text hover:bg-white/5 transition-colors duration-150"
              >
                {{ section.label }}
              </a>
            </nav>
          </div>
        </aside>

        <div class="space-y-6">
          <section
            id="introduction"
            class="scroll-mt-24 border border-ln-border rounded-3xl bg-ln-card/60 p-6 sm:p-8"
          >
            <p class="font-mono text-xs uppercase tracking-[0.25em] text-ln-pink mb-3">
              Introduction
            </p>
            <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-4">
              What this guide covers
            </h2>
            <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed mb-4">
              LNbitsBox simple to get up and running. You can go from unopened box
              to working setup in a few minutes using only a browser on the same network.
            </p>
            <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed">
              This guide walks through the first setup, and shows where to how your LNbitsBox once up and running.
            </p>
          </section>

          <section
            id="unboxing-and-plugging-in"
            class="scroll-mt-24 border border-ln-border rounded-3xl bg-ln-card/60 p-6 sm:p-8"
          >
            <p class="font-mono text-xs uppercase tracking-[0.25em] text-ln-pink mb-3">
              Unboxing and Plugging In
            </p>
            <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-6">
              Connect the hardware
            </h2>

            <div class="rounded-2xl border border-ln-border bg-black/10 p-5 mb-4">
              <h3 class="font-display font-semibold text-ln-text text-lg mb-2">Network</h3>
              <p class="font-display text-ln-muted text-sm leading-relaxed mb-3">
                You can connect your LNbitsBox to the internet using either Wi-Fi or ethernet.
              </p>
              <ul class="list-disc list-inside font-display text-ln-muted text-sm leading-relaxed mb-3">
                <li>Ethernet cable - Connect to your router for a stable and fast network connection.</li>
                <li>Wi-Fi - Remove the SD card from your LNbitsBox and connect to your computer. Copy the file wifi.txt.example to wifi.txt and add your WiFi details.</li>
              </ul>
            </div>
            <div class="rounded-2xl border border-ln-pink/20 bg-ln-pink/5 p-5 mb-4">
                <p class="font-display text-ln-text text-sm leading-relaxed">
                  Tip: Ethernet is usually the fastest way to reach the configurator for the first time.
                  Wi-Fi works too, but only after the network details have been added to the SD card.
                </p>
              </div>
            <div class="rounded-2xl border border-ln-border bg-black/10 p-5 mb-4">
              <h3 class="font-display font-semibold text-ln-text text-lg mb-2">HDMI (optional)</h3>
              <p class="font-display text-ln-muted text-sm leading-relaxed">
                You do not need a monitor to use LNbitsBox, but connecting one can help. During boot,
                it can show device status and local network details.
              </p>
            </div>

            <div class="space-y-4">
              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-2">Power cable</h3>
                <p class="font-display text-ln-muted text-sm leading-relaxed">
                  Connect the included power supply to LNbitsBox and power it on. The device will begin
                  booting immediately.
                </p>
              </div>
            </div>
          </section>

          <section
            id="accessing-the-configurator"
            class="scroll-mt-24 border border-ln-border rounded-3xl bg-ln-card/60 p-6 sm:p-8"
          >
            <p class="font-mono text-xs uppercase tracking-[0.25em] text-ln-pink mb-3">
              Initial Set-up
            </p>
            <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-6">
              Open the setup page in your browser
            </h2>

            <div class="space-y-5">
              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-2">Start with `lnbits.local`</h3>
                <p class="font-display text-ln-muted text-sm leading-relaxed mb-2">
                  On a phone or computer connected to the same network as your LNbitsBox, open a web browser and go to
                  `http://lnbits.local`.
                </p>
                <p class="font-display text-ln-muted text-sm leading-relaxed">
                  You will see the SSL installation page, which is the first step of the configuration process.
                  Follow the prompts to set up the SSL certificate on your device.
                  This ensures secure communication between your device and the browser.
                </p>
              </div>

              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-2">
                  If `lnbits.local` does not load
                </h3>
                <p class="font-display text-ln-muted text-sm leading-relaxed mb-3">
                  Use a network scanner such as Angry IP Scanner to find the device on your local network.
                  Once you have the IP address, open that address in your browser instead.
                </p>
                <p class="font-display text-ln-muted text-sm leading-relaxed">
                  If you connected a monitor, the device may also show its network address during boot.
                </p>
              </div>

              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-3">Configuration steps</h3>
                <ol class="space-y-3">
                  <li class="flex gap-3">
                    <span class="w-6 h-6 flex-shrink-0 rounded-lg bg-ln-pink/10 text-ln-pink font-mono text-xs flex items-center justify-center">1</span>
                    <p class="font-display text-ln-muted text-sm leading-relaxed">
                      Open the configurator and follow the prompts to create your wallet.
                    </p>
                  </li>
                  <li class="flex gap-3">
                    <span class="w-6 h-6 flex-shrink-0 rounded-lg bg-ln-pink/10 text-ln-pink font-mono text-xs flex items-center justify-center">2</span>
                    <p class="font-display text-ln-muted text-sm leading-relaxed">
                      Write down and securely store the seed phrase shown during setup. This backup is
                      critical for recovering access if you lose access to your LNbitsBox.
                    </p>
                  </li>
                  <li class="flex gap-3">
                    <span class="w-6 h-6 flex-shrink-0 rounded-lg bg-ln-pink/10 text-ln-pink font-mono text-xs flex items-center justify-center">3</span>
                    <p class="font-display text-ln-muted text-sm leading-relaxed">
                      Choose a strong password and save it somewhere safe. This password protects
                      administrative access to your LNbitsBox.
                    </p>
                  </li>
                </ol>
              </div>

              <div class="grid sm:grid-cols-2 gap-4">
                <div class="rounded-2xl border border-ln-pink/20 bg-ln-pink/5 p-5">
                  <h3 class="font-display font-semibold text-ln-text text-base mb-2">
                    Back up the seed phrase
                  </h3>
                  <p class="font-display text-ln-muted text-sm leading-relaxed">
                    Treat the seed phrase as the most important part of the setup. If you lose the device,
                    this is what protects your ability to recover your funds.
                  </p>
                </div>
                <div class="rounded-2xl border border-ln-pink/20 bg-ln-pink/5 p-5">
                  <h3 class="font-display font-semibold text-ln-text text-base mb-2">
                    Why the SSH password matters
                  </h3>
                  <p class="font-display text-ln-muted text-sm leading-relaxed">
                    The SSH password is for secure device access and management. Use a strong password and
                    keep it saved somewhere you control.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section
            id="after-configuration"
            class="scroll-mt-24 border border-ln-border rounded-3xl bg-ln-card/60 p-6 sm:p-8"
          >
            <p class="font-mono text-xs uppercase tracking-[0.25em] text-ln-pink mb-3">
              Managing Your LNbitsBox
            </p>
            <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-6">
              The Admin Panel and Remote Access
            </h2>

            <div class="space-y-4">
              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-2">
                  Open the admin panel at <a href="http://lnbits.local/box" target="_blank" class="text-ln-pink hover:underline">lnbits.local/box</a>
                </h3>
                <p class="font-display text-ln-muted text-sm leading-relaxed">
                  After setup is complete, you can access the admin panel by visiting <a href="http://lnbits.local/box"  target="_blank" class="text-ln-pink hover:underline">lnbits.local/box</a> on your
                  LNbitsBox address. This is where you can manage updates and settings, make backups, monitor device status, and perform other administrative tasks.
                </p>
              </div>

              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-2">
                  Use the password from setup
                </h3>
                <p class="font-display text-ln-muted text-sm leading-relaxed">
                  Log in to the admin panel using the SSH password you created during configuration.
                </p>
              </div>

              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-2">
                  Remote access options
                </h3>
                <p class="font-display text-ln-muted text-sm leading-relaxed mb-3">
                  LNbitsBox supports remote access in two ways: through a paid tunnel service, or through
                  Tor. Both are managed from the box after your initial setup is complete.
                </p>
                <p class="font-display text-ln-muted text-sm leading-relaxed">
                  The paid tunnel is designed for straightforward remote access from a normal browser.
                  Tor provides an alternative route for users who prefer that access method.
                </p>
              </div>

              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-2">
                  Running updates
                </h3>
                <p class="font-display text-ln-muted text-sm leading-relaxed mb-2">
                  Software updates are handled from the admin panel. When an update is available you will see a notification on the dashboard.
                </p>
                <p class="font-display text-ln-muted text-sm leading-relaxed">
                  We recommend applying updates when they become available to ensure you have the latest features and security improvements.
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </section>

    <SiteFooter />
  </div>
</template>
