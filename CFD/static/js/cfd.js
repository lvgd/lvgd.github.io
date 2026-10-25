// CFD project page: BibTeX copy, figure zoom, back-to-top and the active section in the nav.
(function () {
  'use strict';

  const copyButton = document.querySelector('.copy-btn');
  const bibtex = document.getElementById('bibtex-text');
  if (copyButton && bibtex) {
    copyButton.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(bibtex.textContent.trim());
        copyButton.textContent = 'Copied';
      } catch (error) {
        copyButton.textContent = 'Copy failed';
      }
      window.setTimeout(() => { copyButton.textContent = 'Copy'; }, 1500);
    });
  }

  // Figures open in a larger view; images that are links (the poster preview) keep their link.
  if ('HTMLDialogElement' in window) {
    const images = [...document.querySelectorAll('.figure-block img')].filter((img) => !img.closest('a'));
    if (images.length) {
      const dialog = document.createElement('dialog');
      dialog.className = 'image-viewer';
      dialog.setAttribute('aria-label', 'Expanded figure');
      dialog.innerHTML = '<button class="image-viewer-close" type="button" aria-label="Close figure">×</button><img alt="">';
      document.body.appendChild(dialog);
      const expanded = dialog.querySelector('img');
      const open = (img) => {
        expanded.src = img.currentSrc || img.src;
        expanded.alt = img.alt;
        dialog.showModal();
      };
      images.forEach((img) => {
        img.classList.add('zoomable');
        img.tabIndex = 0;
        img.setAttribute('role', 'button');
        img.addEventListener('click', () => open(img));
        img.addEventListener('keydown', (event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            open(img);
          }
        });
      });
      dialog.querySelector('.image-viewer-close').addEventListener('click', () => dialog.close());
      dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
    }
  }

  const backToTop = document.createElement('button');
  backToTop.className = 'back-to-top';
  backToTop.type = 'button';
  backToTop.setAttribute('aria-label', 'Back to top');
  backToTop.textContent = '↑';
  document.body.appendChild(backToTop);
  const updateBackToTop = () => backToTop.classList.toggle('show', window.scrollY > 480);
  window.addEventListener('scroll', updateBackToTop, { passive: true });
  updateBackToTop();
  backToTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

  // Highlight the nav link of the section being read.
  const links = new Map([...document.querySelectorAll('.nav-links a')].map((a) => [a.hash.slice(1), a]));
  if ('IntersectionObserver' in window && links.size) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((a) => a.classList.remove('active'));
        const link = links.get(entry.target.id);
        if (link) link.classList.add('active');
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    document.querySelectorAll('section[id]').forEach((section) => observer.observe(section));
  }
})();
