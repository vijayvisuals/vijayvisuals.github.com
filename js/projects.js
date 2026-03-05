/* ═══════════════════════════════════════════════════════════════
   projects.js — Project grid modal, before/after slider, hover preview
═══════════════════════════════════════════════════════════════ */

/* ─── PROJECT DATA ─────────────────────────────────────────── */
const projectData = {
    furiosa: {
        title: 'Furiosa: A Mad Max Saga',
        studio: 'Warner Bros. / DNEG',
        year: '2024',
        role: 'Compositor',
        desc: `George Miller's epic prequel to Mad Max: Fury Road, produced by Warner Bros. at DNEG. As Compositor, the work involved integrating vast desert wastelands, post-apocalyptic vehicle sequences, and complex CG destruction effects with live-action plates. Atmospheric sand storms, dust simulations, and harsh Australian sunlight matching were central compositing challenges on this visually iconic film.`,
        shots: [
            'Wasteland environment extension and sky replacement',
            'CG vehicle destruction and particle FX integration',
            'Dust storm atmospheric compositing',
            'Colour management in ACES pipeline',
        ],
        software: ['Nuke', 'Blender', 'Python'],
        beforeLabel: 'RAW PLATE',
        afterLabel: 'FINAL COMP',
        bgBefore: 'linear-gradient(135deg, #2e1a00, #3a2200)',
        bgAfter: 'linear-gradient(135deg, #4a2800, #1a0e00)',
    },
    ghostbusters: {
        title: 'Ghostbusters: Frozen Empire',
        studio: 'Sony Pictures / DNEG',
        year: '2024',
        role: 'Compositor',
        desc: `Sony Pictures' continuation of the Ghostbusters franchise, with extensive supernatural and creature VFX delivered by DNEG. Compositing responsibilities included ghostly apparition integration, ice and freeze effects, slime and particle simulations, and the signature Ghostbusters proton beam renders — all required to appear both fantastical and grounded within New York locations.`,
        shots: [
            'Ghost creature integration and transparency effects',
            'Ice freeze environment simulation compositing',
            'Proton beam energy FX compositing',
            'New York location extension and augmentation',
        ],
        software: ['Nuke', 'Blender', 'Python'],
        beforeLabel: 'RAW PLATE',
        afterLabel: 'FINAL COMP',
        bgBefore: 'linear-gradient(135deg, #001a2e, #00253a)',
        bgAfter: 'linear-gradient(135deg, #00101a, #001525)',
    },
    kalki: {
        title: 'Kalki 2898-AD',
        studio: 'Vyjayanthi Films / DNEG',
        year: '2024',
        role: 'Compositor',
        desc: `Kalki 2898-AD is a landmark Indian sci-fi epic with one of the largest VFX budgets in Indian cinema history. DNEG handled a significant portion of the film's futuristic world-building, dystopian cityscapes, and ancient mythological environments. Compositing involved seamlessly blending massive CG environments with practical plates across a complex dual-timeline narrative.`,
        shots: [
            'Futuristic Kasi city environment compositing',
            'CG spacecraft and aerial battle integration',
            'Ancient mythological world matte painting composite',
            'Crowd augmentation for large-scale battle sequences',
        ],
        software: ['Nuke', 'Blender', 'Python', 'Comfy UI'],
        beforeLabel: 'RAW PLATE',
        afterLabel: 'FINAL COMP',
        bgBefore: 'linear-gradient(135deg, #1a0c00, #2e1600)',
        bgAfter: 'linear-gradient(135deg, #0a0a1a, #101020)',
    },
    skyforce: {
        title: 'Sky Force',
        studio: 'Jio Studios / DNEG',
        year: '2025',
        role: 'Compositor',
        desc: `Sky Force is an Indian Air Force war epic based on the 1965 India-Pakistan war — one of India's most ambitious aerial action films. DNEG's composite work included MiG aircraft integration in period-accurate atmospheric environments, dogfight sequence FX, missile trails, and large-scale aerial battlefield compositing, all requiring historically grounded visual realism.`,
        shots: [
            'MiG aircraft CG integration and atmosphere',
            'Dogfight aerial battle sequence compositing',
            'Missile and explosion FX integration',
            'Period sky and environment atmosphere',
        ],
        software: ['Nuke', 'Blender', 'Python'],
        beforeLabel: 'RAW PLATE',
        afterLabel: 'FINAL COMP',
        bgBefore: 'linear-gradient(135deg, #0a1020, #101828)',
        bgAfter: 'linear-gradient(135deg, #081018, #0d1828)',
    },
    ramayana: {
        title: 'Ramayana Part 1',
        studio: 'Nitesh Tiwari / DNEG',
        year: '2026',
        role: 'Compositor',
        desc: `Currently in post-production, Ramayana Part 1 is one of the most ambitious Indian mythological epics ever attempted. Directed by Nitesh Tiwari, the film requires building entire ancient worlds from scratch — divine celestial environments, mythological creatures, supernatural battles. DNEG's compositing work is at the frontier of Indian cinema's VFX ambition.`,
        shots: [
            'Ancient Lanka and Ayodhya world-building composite',
            'Divine celestial environment and light development',
            'Mythological creature CG integration',
            'Epic battle sequence multi-layer compositing',
        ],
        software: ['Nuke', 'Blender', 'Python', 'Comfy UI'],
        beforeLabel: 'RAW PLATE',
        afterLabel: 'FINAL COMP',
        bgBefore: 'linear-gradient(135deg, #200a00, #3a1200)',
        bgAfter: 'linear-gradient(135deg, #2a0a00, #4a1800)',
    },
    mortalkombat: {
        title: 'Mortal Kombat II',
        studio: 'New Line Cinema / DNEG',
        year: '2026',
        role: 'Compositor',
        desc: `The sequel to the 2021 reboot, Mortal Kombat II expands the supernatural fighting universe with even more spectacular otherworldly environments and character-specific elemental powers. DNEG composite work involved realm-hopping environments, character transformation FX, and the signature brutal energy-based combat effects.`,
        shots: [
            'Outworld environment integration',
            'Character elemental power FX compositing',
            'Realm transition visual effects',
            'Combat energy and impact FX integration',
        ],
        software: ['Nuke', 'Blender', 'Python'],
        beforeLabel: 'RAW PLATE',
        afterLabel: 'FINAL COMP',
        bgBefore: 'linear-gradient(135deg, #1a0000, #2e0808)',
        bgAfter: 'linear-gradient(135deg, #0a0000, #200000)',
    },
    dulo: {
        title: 'Dulo',
        studio: 'FABFX Studios · Freelance',
        year: '2023',
        role: 'Compositor',
        desc: `Dulo is a freelance project completed at FABFX Studios, where Vijay contributed as an independent Compositor. Working outside the DNEG pipeline, this engagement showcased versatility across a different studio environment — handling compositing tasks end-to-end with full ownership of shots from plate integration through to final delivery.`,
        shots: [
            'Shot compositing from plate to final delivery',
            'CG element integration and colour matching',
            'Lighting and atmosphere consistency across cuts',
            'Final render review and delivery',
        ],
        software: ['Nuke', 'After Effects', 'Python'],
        beforeLabel: 'RAW PLATE',
        afterLabel: 'FINAL COMP',
        bgBefore: 'linear-gradient(135deg, #001a1a, #002020)',
        bgAfter: 'linear-gradient(135deg, #001212, #002e2e)',
    },
};

/* ─── MODAL ───────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {

    const modal = document.getElementById('project-modal');
    const backdrop = document.getElementById('modal-backdrop');
    const closeBtn = document.getElementById('modal-close');
    const content = document.getElementById('modal-content');


    function openModal(projectKey) {
        const p = projectData[projectKey];
        if (!p) return;

        // Build modal content
        content.innerHTML = `
      <div class="modal-film-title">${p.title}</div>
      <div class="modal-chip">${p.studio} · ${p.year}</div>

      <p class="modal-desc">${p.desc}</p>

      <div class="modal-section-label">BEFORE / AFTER</div>
      <div class="ba-slider" id="ba-slider">
        <div class="ba-before" style="background:${p.bgBefore}" id="ba-before">PLATE</div>
        <div class="ba-after" style="background:${p.bgAfter}" id="ba-after">COMP</div>
        <div class="ba-handle" id="ba-handle"></div>
        <div class="ba-label-before">${p.beforeLabel}</div>
        <div class="ba-label-after">${p.afterLabel}</div>
      </div>

      <div class="modal-section-label" style="margin-bottom:12px;">SHOT BREAKDOWN</div>
      <ul style="margin-bottom:40px; padding-left:0; list-style:none;">
        ${p.shots.map(s => `
          <li style="display:flex;align-items:flex-start;gap:12px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:0.85rem;color:#888880;">
            <span style="color:#C8A96E;font-family:'Space Mono',monospace;font-size:0.6rem;margin-top:3px;">◆</span>
            <span>${s}</span>
          </li>
        `).join('')}
      </ul>

      <div class="modal-section-label" style="margin-bottom:16px;">SOFTWARE USED</div>
      <div class="modal-sw-tags">
        ${p.software.map(sw => `<span class="sw-tag">${sw}</span>`).join('')}
      </div>
    `;

        modal.classList.add('open');
        document.body.style.overflow = 'hidden';

        // Init before/after slider
        initBASlider();
    }

    function closeModal() {
        modal.classList.remove('open');
        document.body.style.overflow = '';
    }

    closeBtn.addEventListener('click', closeModal);
    backdrop.addEventListener('click', closeModal);
    document.addEventListener('keydown', e => {
        if (e.code === 'Escape') closeModal();
    });

    // Attach to project cards
    document.querySelectorAll('.project-card').forEach(card => {
        const viewBtn = card.querySelector('.project-view-btn');
        const projectKey = card.getAttribute('data-project');

        if (viewBtn) {
            viewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                openModal(projectKey);
            });
        }

        card.addEventListener('click', () => openModal(projectKey));
    });

    /* ─── BEFORE / AFTER SLIDER ──────────────────────────────── */
    function initBASlider() {
        const slider = document.getElementById('ba-slider');
        const handle = document.getElementById('ba-handle');
        const after = document.getElementById('ba-after');
        if (!slider || !handle || !after) return;

        let isDragging = false;
        let pct = 50;

        function setPosition(x) {
            const rect = slider.getBoundingClientRect();
            pct = Math.max(0, Math.min(100, ((x - rect.left) / rect.width) * 100));
            handle.style.left = pct + '%';
            after.style.clipPath = `inset(0 ${100 - pct}% 0 0)`;
        }

        handle.addEventListener('mousedown', e => { isDragging = true; e.preventDefault(); });
        slider.addEventListener('mousedown', e => {
            isDragging = true;
            setPosition(e.clientX);
        });
        document.addEventListener('mousemove', e => { if (isDragging) setPosition(e.clientX); });
        document.addEventListener('mouseup', () => { isDragging = false; });

        // Touch
        handle.addEventListener('touchstart', e => { isDragging = true; }, { passive: true });
        document.addEventListener('touchmove', e => {
            if (isDragging) setPosition(e.touches[0].clientX);
        }, { passive: true });
        document.addEventListener('touchend', () => { isDragging = false; });
    }

    /* ─── HOVER PREVIEW VIDEOS ───────────────────────────────── */
    // Map project keys to video file references
    const previewMap = {
        furiosa: 'assets/videos/hero_loop.mp4',
        ghostbusters: 'assets/videos/hero_loop.mp4',
        kalki: 'assets/videos/hero_loop.mp4',
        skyforce: 'assets/videos/hero_loop.mp4',
        ramayana: 'assets/videos/hero_loop.mp4',
        mortalkombat: 'assets/videos/hero_loop.mp4',
    };

    document.querySelectorAll('.project-card').forEach(card => {
        const key = card.getAttribute('data-project');
        const src = previewMap[key];
        const thumb = card.querySelector('.project-thumb');
        if (!src || !thumb) return;

        let previewEl = null;

        card.addEventListener('mouseenter', () => {
            if (!previewEl) {
                previewEl = document.createElement('video');
                previewEl.className = 'preview';
                previewEl.src = src;
                previewEl.muted = true;
                previewEl.loop = true;
                previewEl.playsInline = true;
                previewEl.preload = 'none';
                thumb.appendChild(previewEl);
            }
            previewEl.play().catch(() => { });
        });

        card.addEventListener('mouseleave', () => {
            if (previewEl) previewEl.pause();
        });
    });

});
