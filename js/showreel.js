/* ═══════════════════════════════════════════════════════════════
   showreel.js — Netflix-style custom video player for showreel
═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

    const video = document.getElementById('showreel-video');
    const playBtn = document.getElementById('sr-play');
    const playIcon = document.getElementById('sr-play-icon');
    const pauseIcon = document.getElementById('sr-pause-icon');
    const muteBtn = document.getElementById('sr-mute');
    const soundIcon = document.getElementById('sr-sound-icon');
    const muteIcon = document.getElementById('sr-mute-icon');
    const fsBtn = document.getElementById('sr-fullscreen');
    const progress = document.getElementById('sr-progress');
    const progressBar = document.getElementById('sr-progress-bar');
    const currentTime = document.getElementById('sr-current');
    const duration = document.getElementById('sr-duration');
    const playCenter = document.getElementById('sr-play-center');
    const wrap = document.querySelector('.showreel-player-wrap');

    if (!video) return;

    /* ─── Format Time ─────────────────────────────────────────── */
    function formatTime(s) {
        const m = Math.floor(s / 60);
        const sec = Math.floor(s % 60);
        return `${m}:${sec.toString().padStart(2, '0')}`;
    }

    /* ─── Play / Pause ────────────────────────────────────────── */
    function togglePlay() {
        if (video.paused) {
            video.play();
            playIcon.style.display = 'none';
            pauseIcon.style.display = '';
            playCenter.classList.add('hidden');
        } else {
            video.pause();
            playIcon.style.display = '';
            pauseIcon.style.display = 'none';
            playCenter.classList.remove('hidden');
        }
    }

    playBtn.addEventListener('click', togglePlay);
    playCenter.addEventListener('click', togglePlay);
    video.addEventListener('click', togglePlay);

    /* ─── Mute Toggle ─────────────────────────────────────────── */
    muteBtn.addEventListener('click', () => {
        video.muted = !video.muted;
        soundIcon.style.display = video.muted ? 'none' : '';
        muteIcon.style.display = video.muted ? '' : 'none';
    });

    /* ─── Fullscreen ─────────────────────────────────────────────*/
    fsBtn.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            wrap.requestFullscreen().catch(() => { });
        } else {
            document.exitFullscreen();
        }
    });

    /* ─── Progress Bar ────────────────────────────────────────── */
    video.addEventListener('timeupdate', () => {
        if (!video.duration) return;
        const pct = (video.currentTime / video.duration) * 100;
        progressBar.style.width = pct + '%';
        currentTime.textContent = formatTime(video.currentTime);
    });

    video.addEventListener('loadedmetadata', () => {
        duration.textContent = formatTime(video.duration);
    });

    // Click on progress to seek
    progress.addEventListener('click', e => {
        const rect = progress.getBoundingClientRect();
        const pct = (e.clientX - rect.left) / rect.width;
        video.currentTime = pct * (video.duration || 0);
    });

    // Drag seek
    let dragging = false;
    progress.addEventListener('mousedown', () => { dragging = true; });
    document.addEventListener('mousemove', e => {
        if (!dragging) return;
        const rect = progress.getBoundingClientRect();
        const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        progressBar.style.width = (pct * 100) + '%';
        video.currentTime = pct * (video.duration || 0);
    });
    document.addEventListener('mouseup', () => { dragging = false; });

    /* ─── Keyboard shortcuts ─────────────────────────────────── */
    document.addEventListener('keydown', e => {
        if (e.code === 'Space' && document.activeElement.tagName !== 'INPUT') {
            e.preventDefault();
            togglePlay();
        }
        if (e.code === 'ArrowRight') video.currentTime = Math.min(video.currentTime + 5, video.duration || 0);
        if (e.code === 'ArrowLeft') video.currentTime = Math.max(video.currentTime - 5, 0);
        if (e.code === 'KeyM') muteBtn.click();
        if (e.code === 'KeyF') fsBtn.click();
    });

    /* ─── Video Error Fallback ────────────────────────────────── */
    video.addEventListener('error', () => {
        wrap.style.background = 'linear-gradient(135deg, #0a0a14, #141424)';
        playCenter.style.display = 'none';
        const msg = document.createElement('div');
        msg.style.cssText = `
      position: absolute; inset: 0; display: flex; flex-direction: column;
      align-items: center; justify-content: center; gap: 16px;
      font-family: 'Space Mono', monospace; color: rgba(255,255,255,0.3);
      font-size: 0.7rem; letter-spacing: 0.2em;
    `;
        msg.innerHTML = `
      <div style="font-size:2rem;opacity:0.2">▶</div>
      <div>SHOWREEL COMING SOON</div>
      <div style="font-size:0.55rem;opacity:0.5">Convert ProRes MOV files to MP4 for playback</div>
    `;
        wrap.appendChild(msg);
    });

});
