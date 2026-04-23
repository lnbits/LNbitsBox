(function () {
    const maskedSeed = '••••• ••••• ••••• ••••• ••••• ••••• ••••• ••••• ••••• ••••• ••••• •••••';

    function bindSeedToggle(valueId, buttonId) {
        const seedValue = document.getElementById(valueId);
        const toggleBtn = document.getElementById(buttonId);
        if (!seedValue || !toggleBtn) return;

        toggleBtn.addEventListener('click', function () {
            const seedPhrase = seedValue.dataset.seedPhrase || '';
            if (!seedPhrase) return;

            const isMasked = seedValue.dataset.masked === 'true';
            seedValue.textContent = isMasked ? seedPhrase : maskedSeed;
            seedValue.dataset.masked = isMasked ? 'false' : 'true';
            toggleBtn.textContent = isMasked ? 'Hide Seed Phrase' : 'Show Seed Phrase';
        });
    }

    bindSeedToggle('spark-seed-value', 'spark-seed-toggle-btn');
    bindSeedToggle('phoenixd-seed-value', 'phoenixd-seed-toggle-btn');
})();
