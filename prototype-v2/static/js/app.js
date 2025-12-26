let candidates = [];
let currentIndex = 0;

let isHolding = false;
let countdownTimer = null;
let countdownValue = 5;

document.addEventListener('DOMContentLoaded', () => {
    const page = document.body.dataset.page;

    // Only initialize candidates on vote page
    if (page === 'vote') {
        candidates = Array.from(document.querySelectorAll('.candidate-box'));
        if (candidates.length > 0) {
            setActiveCandidate(0);
        }
    }
});

/* -------------------------------
   GLOBAL KEYDOWN HANDLER
-------------------------------- */
document.addEventListener('keydown', (e) => {
    const page = document.body.dataset.page;

    /* ===== ARROW KEYS (vote only) ===== */
    if (page === 'vote' && candidates.length > 0) {
        switch (e.key) {
            case 'ArrowRight':
            case 'ArrowDown':
                e.preventDefault();
                setActiveCandidate((currentIndex + 1) % candidates.length);
                return;

            case 'ArrowLeft':
            case 'ArrowUp':
                e.preventDefault();
                setActiveCandidate(
                    (currentIndex - 1 + candidates.length) % candidates.length
                );
                return;
        }
    }

    /* ===============================
       ENTER KEY (BUTTON EMULATION)
    ================================ */
if (e.key === 'Enter') {
        e.preventDefault();

        // Voting page logic: note dataset page is 'vote'
        if (page === 'vote') {
            if (!isHolding) startHoldConfirm(); // start countdown when holding
            return;
        }

        // For other pages (landing & thankyou):
        const primaryButton = document.querySelector('.btn-3d');
        if (primaryButton) {
            primaryButton.click();
        }
    }

});

/* -------------------------------
   GLOBAL KEYUP HANDLER
-------------------------------- */
document.addEventListener('keyup', (e) => {
    const page = document.body.dataset.page;

    if (e.key === 'Enter' && page === 'vote') {
        cancelHoldConfirm(); // reset countdown when released
    }
});

/* -------------------------------
   CANDIDATE SELECTION
-------------------------------- */
function setActiveCandidate(index) {
    candidates.forEach(c => c.classList.remove('selected'));
    currentIndex = index;
    candidates[currentIndex].classList.add('selected');
}

/* -------------------------------
   HOLD-TO-CONFIRM LOGIC
-------------------------------- */
function startHoldConfirm() {
    isHolding = true;
    countdownValue = 5;

    const countdownEl = document.getElementById('countdown');
    const numberEl = document.getElementById('countdown-number');

    countdownEl.style.display = 'block';
    numberEl.textContent = countdownValue;

    countdownTimer = setInterval(() => {
        countdownValue--;
        numberEl.textContent = countdownValue;

        if (countdownValue === 0) {
            confirmVote();
        }
    }, 1000);
}

function cancelHoldConfirm() {
    if (!isHolding) return;

    clearInterval(countdownTimer);
    isHolding = false;

    const countdownEl = document.getElementById('countdown');
    countdownEl.style.display = 'none';
}

/* -------------------------------
   VOTE CONFIRMED
-------------------------------- */
function confirmVote() {
    clearInterval(countdownTimer);
    isHolding = false;

    // Optional: store selection locally
    sessionStorage.setItem('selectedCandidate', currentIndex);

    window.location.href = '/thankyou';
}
