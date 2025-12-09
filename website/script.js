function switchTab(os) {
    const wins = document.getElementById('cmd-win');
    const unix = document.getElementById('cmd-unix');
    const tabBtns = document.querySelectorAll('.tab-btn');

    if (os === 'win') {
        wins.classList.remove('hidden');
        unix.classList.add('hidden');
        tabBtns[0].classList.add('active');
        tabBtns[1].classList.remove('active');
    } else {
        unix.classList.remove('hidden');
        wins.classList.add('hidden');
        tabBtns[1].classList.add('active');
        tabBtns[0].classList.remove('active');
    }
}

function copyCmd(elementId) {
    const text = document.getElementById(elementId).innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert("Command copied to clipboard!");
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}
