/* ==========================================================================
   Snip — Main JavaScript
   Handles form submission, copy, theme toggle, and UI interactions.
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initShortenForm();
    initExpiryToggle();
    initShortenAnother();
    initCopyButtons();
    initDeleteButtons();
    loadRecentLinks();
});


/* --------------------------------------------------------------------------
   Theme Toggle
   -------------------------------------------------------------------------- */

function initThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    // Load saved theme
    const saved = localStorage.getItem('snip-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);

    toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('snip-theme', next);
    });
}


/* --------------------------------------------------------------------------
   URL Shortener Form
   -------------------------------------------------------------------------- */

function initShortenForm() {
    const form = document.getElementById('shorten-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const btn = document.getElementById('shorten-btn');
        const btnText = btn.querySelector('.btn-text');
        const btnLoader = btn.querySelector('.btn-loader');
        const errorEl = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');

        // Get form values
        const url = document.getElementById('url-input').value.trim();
        const customCode = document.getElementById('custom-code-input').value.trim();
        const expiry = document.getElementById('expiry-select').value;
        const customExpiry = document.getElementById('custom-expiry-input')?.value || '';

        if (!url) {
            showError(errorEl, errorText, 'Please enter a URL to shorten.');
            return;
        }

        // Show loading state
        btnText.hidden = true;
        btnLoader.hidden = false;
        btn.disabled = true;
        hideError(errorEl);

        try {
            const response = await fetch('/shorten', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: url,
                    custom_code: customCode,
                    expiry: expiry,
                    custom_expiry: customExpiry,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                showError(errorEl, errorText, data.error || 'Something went wrong.');
                return;
            }

            // Show result
            showResult(data);
            saveToRecent(data);
            form.reset();

        } catch (err) {
            showError(errorEl, errorText, 'Network error. Please try again.');
        } finally {
            btnText.hidden = false;
            btnLoader.hidden = true;
            btn.disabled = false;
        }
    });
}


/* --------------------------------------------------------------------------
   Expiry Toggle — show/hide custom date picker
   -------------------------------------------------------------------------- */

function initExpiryToggle() {
    const select = document.getElementById('expiry-select');
    const customGroup = document.getElementById('custom-date-group');
    if (!select || !customGroup) return;

    select.addEventListener('change', () => {
        if (select.value === 'custom') {
            customGroup.hidden = false;
            // Set min date to now
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            const minDate = now.toISOString().slice(0, 16);
            document.getElementById('custom-expiry-input').min = minDate;
        } else {
            customGroup.hidden = true;
        }
    });
}


/* --------------------------------------------------------------------------
   Result Display
   -------------------------------------------------------------------------- */

function showResult(data) {
    const card = document.getElementById('result-card');
    const shortenCard = document.getElementById('shorten-card');

    document.getElementById('result-url').value = data.short_url;
    document.getElementById('result-original').textContent = '→ ' + data.original_url;
    document.getElementById('result-expiry').textContent =
        data.expires_at !== 'Never' ? 'Expires: ' + data.expires_at : '';

    shortenCard.style.display = 'none';
    card.hidden = false;
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
}


/* --------------------------------------------------------------------------
   Shorten Another
   -------------------------------------------------------------------------- */

function initShortenAnother() {
    const btn = document.getElementById('shorten-another-btn');
    if (!btn) return;

    btn.addEventListener('click', () => {
        const resultCard = document.getElementById('result-card');
        const shortenCard = document.getElementById('shorten-card');

        resultCard.hidden = true;
        shortenCard.style.display = '';
        document.getElementById('url-input').focus();
    });
}


/* --------------------------------------------------------------------------
   Copy to Clipboard
   -------------------------------------------------------------------------- */

function initCopyButtons() {
    // Main copy button on result card
    const copyBtn = document.getElementById('copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const url = document.getElementById('result-url').value;
            copyToClipboard(url, copyBtn);
        });
    }
}

async function copyToClipboard(text, button) {
    try {
        await navigator.clipboard.writeText(text);

        // Visual feedback
        button.classList.add('copied');
        const textEl = button.querySelector('.copy-text') || button;
        const originalText = textEl.textContent;

        if (button.querySelector('.copy-text')) {
            button.querySelector('.copy-icon').textContent = '✓';
            button.querySelector('.copy-text').textContent = 'Copied!';
        } else {
            textEl.textContent = '✓';
        }

        setTimeout(() => {
            button.classList.remove('copied');
            if (button.querySelector('.copy-text')) {
                button.querySelector('.copy-icon').textContent = '⧉';
                button.querySelector('.copy-text').textContent = originalText;
            } else {
                textEl.textContent = '⧉';
            }
        }, 2000);

    } catch (err) {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }
}


/* --------------------------------------------------------------------------
   Recent Links (localStorage)
   -------------------------------------------------------------------------- */

function saveToRecent(data) {
    const recent = JSON.parse(localStorage.getItem('snip-recent') || '[]');
    recent.unshift({
        short_url: data.short_url,
        short_code: data.short_code,
        original_url: data.original_url,
        expires_at: data.expires_at,
        created_at: new Date().toISOString(),
    });
    // Keep only last 10
    localStorage.setItem('snip-recent', JSON.stringify(recent.slice(0, 10)));
    loadRecentLinks();
}

function loadRecentLinks() {
    const container = document.getElementById('recent-list');
    if (!container) return;

    const recent = JSON.parse(localStorage.getItem('snip-recent') || '[]');

    if (recent.length === 0) {
        container.innerHTML = '<p class="text-center py-8 text-brand-text-tertiary text-sm" id="empty-state">No links shortened yet. Try one above!</p>';
        return;
    }

    container.innerHTML = recent.map((item, i) => `
        <div class="flex items-center justify-between p-3 bg-brand-bg-card border border-brand-border-subtle rounded-[12px] transition-all duration-150 animate-fade-in-up hover:bg-brand-bg-card-hover hover:border-brand-border-default max-sm:flex-col max-sm:items-start max-sm:gap-2" style="animation-delay: ${i * 0.04}s; animation-fill-mode: both;">
            <div class="flex flex-col gap-0.5 min-w-0 flex-1">
                <a href="${item.short_url}" class="font-mono text-[0.88rem] font-medium text-brand-accent hover:underline" target="_blank">${item.short_url}</a>
                <span class="text-[0.78rem] text-brand-text-tertiary overflow-hidden text-ellipsis whitespace-nowrap">${item.original_url}</span>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0 ml-4 max-sm:ml-0 max-sm:w-full max-sm:justify-between">
                <span class="text-[0.78rem] text-brand-text-tertiary whitespace-nowrap">${item.expires_at !== 'Never' ? item.expires_at : '∞'}</span>
                <button class="inline-flex items-center justify-center w-8 h-8 bg-brand-accent-soft text-brand-accent border-none rounded-sm text-[0.85rem] cursor-pointer transition-all duration-150 hover:bg-brand-accent hover:text-white btn-copy-sm" onclick="copyToClipboard('${item.short_url}', this)" title="Copy">⧉</button>
            </div>
        </div>
    `).join('');
}


/* --------------------------------------------------------------------------
   Delete URL (Dashboard)
   -------------------------------------------------------------------------- */

function initDeleteButtons() {
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.dataset.id;
            if (!confirm('Delete this shortened URL? This cannot be undone.')) return;

            try {
                const res = await fetch(`/api/urls/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    const row = document.getElementById(`url-row-${id}`);
                    if (row) {
                        row.style.transition = 'opacity 0.3s, transform 0.3s';
                        row.style.opacity = '0';
                        row.style.transform = 'translateX(20px)';
                        setTimeout(() => row.remove(), 300);
                    }
                }
            } catch (err) {
                alert('Failed to delete. Please try again.');
            }
        });
    });
}


/* --------------------------------------------------------------------------
   Helpers
   -------------------------------------------------------------------------- */

function showError(el, textEl, message) {
    textEl.textContent = message;
    el.hidden = false;
}

function hideError(el) {
    if (el) el.hidden = true;
}
