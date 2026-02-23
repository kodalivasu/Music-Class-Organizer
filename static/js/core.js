// Tab switching and lightbox — used by the main nav and event photos
function showTab(id, btn) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    btn.classList.add('active');
    window.scrollTo(0, 0);
}

function openLightbox(src) {
    document.getElementById('lightbox-img').src = src;
    document.getElementById('lightbox').classList.add('active');
}

// When any audio or video starts playing, pause all others (single-at-a-time playback)
document.addEventListener('play', function (e) {
    var el = e.target;
    if (el.tagName !== 'AUDIO' && el.tagName !== 'VIDEO') return;
    document.querySelectorAll('audio, video').forEach(function (other) {
        if (other !== el && !other.paused) other.pause();
    });
}, true);