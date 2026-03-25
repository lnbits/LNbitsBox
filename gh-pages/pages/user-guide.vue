<script setup>
const sections = [
  { id: 'introduction', label: 'Introduction' },
  { id: 'unboxing-and-plugging-in', label: 'Unboxing and Plugging In' },
  { id: 'accessing-the-configurator', label: 'Initial Set-up' },
  { id: 'after-configuration', label: 'Managing Your LNbitsBox' },
  { id: 'recovery-tool', label: 'Recovery Tool' },
  { id: 'troubleshooting', label: 'Troubleshooting' },
]

const troubleshootingItems = [
  {
    title: 'I can’t reach `lnbits.local`',
    solution: [
      'Make sure your phone or computer is on the same local network as your LNbitsBox.',
      'Try `http://lnbits.local` first, then try the LNbitsBox\'s local IP address if that does not load.',
      'If needed, use a network scanner such as Angry IP Scanner, or connect a monitor to your LNbitsBox to check its IP during boot.',
    ],
  },
  {
    title: 'The LNbitsBox powers on, but never appears on my network',
    solution: [
      'Check that the Ethernet cable is connected properly, or confirm that your `wifi.txt` file was created correctly on the SD card before first boot.',
      'If using Wi-Fi, double-check the network name and password.',
      'Ethernet is the best first test because it removes Wi-Fi setup as a possible issue.',
    ],
  },
  {
    title: 'The configurator page does not open',
    solution: [
      'Give the device a few minutes to fully boot on first startup.',
      'If `lnbits.local` still does not work, try the local IP address instead.',
      'A reboot can also help if the LNbitsBox did not finish startup cleanly.',
    ],
  },
  {
    title: 'The browser shows certificate or security warnings',
    solution: [
      'LNbitsBox uses its own local certificate for secure access on your home network.',
      'Follow the certificate installation steps shown on the first setup page, then reload the site.',
      'If the warning continues, return to the certificate page and install the certificate again on that device.',
    ],
  },
  {
    title: 'I finished setup, but now the configurator is gone',
    solution: [
      'That is expected.',
      'After setup is complete, LNbitsBox switches from the configurator to the normal LNbits interface.',
      'Use `lnbits.local` for LNbits and `lnbits.local/box` for the admin panel.',
    ],
  },
  {
    title: 'I can’t log in to the admin panel',
    solution: [
      'Use the SSH password you created during setup.',
      'Make sure you are opening `lnbits.local/box` and not the main LNbits page.',
      'If you no longer know the password, recovery may require restoring from backup or reflashing the SD card.',
    ],
  },
  {
    title: 'My SD card seems corrupted or the system will not boot',
    solution: [
      'Power off your LNbitsBox and remove the SD card.',
      'Reflash it using Raspberry Pi Imager with the latest LNbitsBox release from `https://github.com/lnbits/LNbitsBox/releases/latest`.',
      'If you have Recovery Tool backups or your Spark seed phrase, keep those safe before starting.',
    ],
  },
  {
    title: 'How to reflash the SD card',
    solution: [
      'Download the latest LNbitsBox release from `https://github.com/lnbits/LNbitsBox/releases/latest`.',
      'Open Raspberry Pi Imager, choose `Use custom`, select the downloaded LNbitsBox image, choose your SD card, and write the image.',
      'When flashing is complete, safely eject the card, insert it into your LNbitsBox, and power the device back on.',
    ],
  },
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
                  Tor. Both are managed from the LNbitsBox after your initial setup is complete.
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

          <section
            id="recovery-tool"
            class="scroll-mt-24 border border-ln-border rounded-3xl bg-ln-card/60 p-6 sm:p-8"
          >
            <p class="font-mono text-xs uppercase tracking-[0.25em] text-ln-pink mb-3">
              Recovery Tool
            </p>
            <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-6">
              Back up and restore your LNbitsBox safely
            </h2>
            <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed mb-6">
              The Recovery Tool is your main safety net for your LNbitsBox. It helps you create encrypted recovery backups,
              checks that a backup is usable before restoring it, and keeps regular backups running so you are better
              prepared if your SD card fails or you need to move to a new LNbitsBox.
            </p>

            <div class="space-y-4">
              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-2">
                  Open the Recovery Tool from the admin panel
                </h3>
                <p class="font-display text-ln-muted text-sm leading-relaxed">
                  Visit <a href="http://lnbits.local/box" target="_blank" class="text-ln-pink hover:underline">lnbits.local/box</a>, sign in with your admin password, and open the
                  Maintenance page. The Recovery Tool lets you create encrypted backups, validate a restore before applying it, and configure automatic backups.
                </p>
              </div>

              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-3">
                  Create an encrypted backup
                </h3>
                <ol class="space-y-3">
                  <li class="flex gap-3">
                    <span class="w-6 h-6 flex-shrink-0 rounded-lg bg-ln-pink/10 text-ln-pink font-mono text-xs flex items-center justify-center">1</span>
                    <p class="font-display text-ln-muted text-sm leading-relaxed">
                      Choose <strong>Full backup</strong> for the most complete snapshot. This includes LNbits data, Spark wallet files, tunnel state, and device configuration.
                    </p>
                  </li>
                  <li class="flex gap-3">
                    <span class="w-6 h-6 flex-shrink-0 rounded-lg bg-ln-pink/10 text-ln-pink font-mono text-xs flex items-center justify-center">2</span>
                    <p class="font-display text-ln-muted text-sm leading-relaxed">
                      Enter a backup password. Every recovery archive is password protected, so store that password somewhere safe and separate from the LNbitsBox.
                    </p>
                  </li>
                  <li class="flex gap-3">
                    <span class="w-6 h-6 flex-shrink-0 rounded-lg bg-ln-pink/10 text-ln-pink font-mono text-xs flex items-center justify-center">3</span>
                    <p class="font-display text-ln-muted text-sm leading-relaxed">
                      Use <strong>Download Backup</strong> to save the archive to your computer, or <strong>Save on This LNbitsBox</strong> to keep a copy in the local recovery folder for later download.
                    </p>
                  </li>
                </ol>
              </div>

              <div class="grid sm:grid-cols-2 gap-4">
                <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                  <h3 class="font-display font-semibold text-ln-text text-lg mb-2">
                    Full vs Quick backups
                  </h3>
                  <p class="font-display text-ln-muted text-sm leading-relaxed">
                    Full backups are the best default for most people. Quick backups are smaller, but they skip some broader device state and are better suited to lighter routine snapshots.
                  </p>
                </div>
                <div class="rounded-2xl border border-ln-pink/20 bg-ln-pink/5 p-5">
                  <h3 class="font-display font-semibold text-ln-text text-lg mb-2">
                    Keep your Spark seed phrase too
                  </h3>
                  <p class="font-display text-ln-muted text-sm leading-relaxed">
                    Recovery archives help restore your LNbitsBox, but your Spark seed phrase is still the most important secret for recovering wallet access and funds.
                  </p>
                </div>
              </div>

              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-3">
                  Restore carefully
                </h3>
                <p class="font-display text-ln-muted text-sm leading-relaxed mb-3">
                  The restore flow checks the uploaded backup before making changes. You can restore from a backup file on your computer or from one already saved on the LNbitsBox.
                </p>
                <p class="font-display text-ln-muted text-sm leading-relaxed">
                  After validation, choose only the components you want to restore. This gives you a chance to confirm the archive and avoid overwriting parts of the system unnecessarily.
                </p>
              </div>

              <div class="rounded-2xl border border-ln-border bg-black/10 p-5">
                <h3 class="font-display font-semibold text-ln-text text-lg mb-2">
                  Automatic backups
                </h3>
                <p class="font-display text-ln-muted text-sm leading-relaxed mb-2">
                  If your LNbitsBox stays powered on, you can enable scheduled encrypted backups from the same Recovery Tool page.
                </p>
                <p class="font-display text-ln-muted text-sm leading-relaxed">
                  Pick how often the backup should run, choose full or quick mode, and set the stored backup password. We still recommend occasionally downloading a copy off the LNbitsBox as part of your backup routine.
                </p>
              </div>
            </div>
          </section>

          <section
            id="troubleshooting"
            class="scroll-mt-24 border border-ln-border rounded-3xl bg-ln-card/60 p-6 sm:p-8"
          >
            <p class="font-mono text-xs uppercase tracking-[0.25em] text-ln-pink mb-3">
              Troubleshooting
            </p>
            <h2 class="font-display font-bold text-ln-text text-2xl sm:text-3xl tracking-tight mb-6">
              Common issues and what to try
            </h2>
            <p class="font-display text-ln-muted text-base sm:text-lg leading-relaxed mb-6">
              If something is not working as expected, these are the most common issues and the fastest steps to try first.
            </p>

            <div class="space-y-4">
              <div
                v-for="item in troubleshootingItems"
                :key="item.title"
                class="rounded-2xl border border-ln-border bg-black/10 p-5"
              >
                <h3 class="font-display font-semibold text-ln-text text-lg mb-3">
                  {{ item.title }}
                </h3>
                <ul class="list-disc list-inside space-y-2">
                  <li
                    v-for="step in item.solution"
                    :key="step"
                    class="font-display text-ln-muted text-sm leading-relaxed"
                  >
                    {{ step }}
                  </li>
                </ul>
              </div>
            </div>
          </section>
        </div>
      </div>
    </section>

    <SiteFooter />
  </div>
</template>
