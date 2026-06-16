(() => {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const browseBtn = document.getElementById('browse-btn');
  const clearBtn = document.getElementById('clear-btn');
  const previewRow = document.getElementById('preview-row');
  const fileName = document.getElementById('file-name');
  const analyzeBtn = document.getElementById('analyze-btn');
  const confidence = document.getElementById('confidence');
  const confValue = document.getElementById('conf-value');
  const results = document.getElementById('results');
  const emptyState = document.getElementById('empty-state');
  const detCount = document.getElementById('det-count');
  const imgOriginal = document.getElementById('img-original');
  const imgMarked = document.getElementById('img-marked');
  const downloadBtn = document.getElementById('download-btn');
  const detBody = document.getElementById('det-body');
  const tableWrap = document.getElementById('table-wrap');
  const toast = document.getElementById('toast');
  const loading = document.getElementById('loading');
  const loadingTitle = document.getElementById('loading-title');
  const loadingSub = document.getElementById('loading-sub');
  const statusPill = document.getElementById('model-status');
  const statusText = document.getElementById('status-text');
  const errorPanel = document.getElementById('error-panel');
  const errorMessage = document.getElementById('error-message');
  const errorClose = document.getElementById('error-close');

  let selectedFile = null;
  let selectedSample = null;
  let modelReady = false;
  let previewUrl = null;

  function showToast(msg, isError = false) {
    toast.textContent = msg;
    toast.classList.toggle('error', isError);
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 4500);
  }

  function showOpgError(msg) {
    errorMessage.textContent = msg;
    errorPanel.classList.remove('hidden');
    errorPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    results.classList.add('hidden');
  }

  function hideOpgError() {
    errorPanel.classList.add('hidden');
  }

  errorClose.addEventListener('click', hideOpgError);

  function updateAnalyzeButton() {
    analyzeBtn.disabled = !modelReady || (!selectedFile && !selectedSample);
  }

  function setFile(file) {
    if (!file) return;
    hideOpgError();
    selectedSample = null;
    document.querySelectorAll('.sample-card').forEach(c => c.classList.remove('selected'));
    const ok = /\.(jpe?g|png|pdf)$/i.test(file.name);
    if (!ok) {
      showToast('Please upload JPG, PNG, or PDF', true);
      return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    previewRow.classList.remove('hidden');

    const wrap = document.querySelector('.thumb-wrap');
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = null;

    if (/\.pdf$/i.test(file.name)) {
      wrap.innerHTML = '<span class="pdf-thumb">PDF</span>';
    } else {
      wrap.innerHTML = '<img id="thumb-preview" alt="" />';
      previewUrl = URL.createObjectURL(file);
      document.getElementById('thumb-preview').src = previewUrl;
    }
    updateAnalyzeButton();
  }

  function clearFile() {
    selectedFile = null;
    selectedSample = null;
    fileInput.value = '';
    previewRow.classList.add('hidden');
    hideOpgError();
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = null;
    document.querySelectorAll('.sample-card').forEach(c => c.classList.remove('selected'));
    updateAnalyzeButton();
  }

  function selectSample(item, autoRun = false) {
    hideOpgError();
    selectedFile = null;
    fileInput.value = '';
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = null;
    selectedSample = item.name;

    fileName.textContent = `Sample: ${item.label}`;
    previewRow.classList.remove('hidden');
    const wrap = document.querySelector('.thumb-wrap');
    wrap.innerHTML = '<img id="thumb-preview" alt="" />';
    document.getElementById('thumb-preview').src = item.url + '?t=' + Date.now();

    document.querySelectorAll('.sample-card').forEach(c => {
      c.classList.toggle('selected', c.dataset.name === item.name);
    });
    updateAnalyzeButton();
    if (autoRun && modelReady) runAnalysis();
  }

  async function loadSamples() {
    const grid = document.getElementById('sample-grid');
    const empty = document.getElementById('sample-empty');
    try {
      const res = await fetch('/api/samples');
      const data = await res.json();
      if (!data.samples?.length) {
        grid.innerHTML = '';
        empty.classList.remove('hidden');
        return;
      }
      empty.classList.add('hidden');
      grid.innerHTML = data.samples.map(s => `
        <article class="sample-card" data-name="${esc(s.name)}">
          <img class="sample-thumb" src="${esc(s.url)}" alt="${esc(s.label)}" loading="lazy" />
          <div class="sample-meta">
            <span>${esc(s.label)}</span>
            <button type="button" class="btn-sample" data-name="${esc(s.name)}">Try this sample</button>
          </div>
        </article>`).join('');

      grid.querySelectorAll('.btn-sample').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const sample = data.samples.find(x => x.name === btn.dataset.name);
          if (sample) selectSample(sample, true);
        });
      });
    } catch {
      empty.classList.remove('hidden');
      empty.textContent = 'Could not load sample library.';
    }
  }

  async function runAnalysis() {
    if ((!selectedFile && !selectedSample) || !modelReady) return;

    const fd = new FormData();
    if (selectedSample) {
      fd.append('sample', selectedSample);
    } else {
      fd.append('file', selectedFile);
    }
    fd.append('confidence', (confidence.value / 100).toFixed(2));

    hideOpgError();
    loading.classList.remove('hidden');
    setLoadingStep('validate');
    analyzeBtn.disabled = true;

    const stepTimer = setTimeout(() => setLoadingStep('infer'), 800);
    const stepTimer2 = setTimeout(() => setLoadingStep('render'), 2200);

    try {
      const res = await fetch('/api/analyze', { method: 'POST', body: fd });
      const data = await res.json();

      if (!res.ok) {
        if (res.status === 422 || data.code === 'not_opg') {
          showOpgError(data.error || 'This file does not appear to be an OPG scan.');
          return;
        }
        throw new Error(data.error || 'Analysis failed');
      }

      emptyState.classList.add('hidden');
      results.classList.remove('hidden');
      results.scrollIntoView({ behavior: 'smooth', block: 'start' });

      const cache = `?t=${Date.now()}`;
      imgOriginal.src = data.original_url + cache;
      imgMarked.src = data.marked_url + cache;
      downloadBtn.href = data.download_url;
      downloadBtn.download = data.filename;
      detCount.textContent = data.count;

      if (data.detections?.length) {
        tableWrap.classList.remove('hidden');
        detBody.innerHTML = data.detections.map((d, i) => `
          <tr>
            <td>${i + 1}</td>
            <td>${esc(d.label)}</td>
            <td>${(d.confidence * 100).toFixed(1)}%</td>
            <td>(${d.x1},${d.y1}) → (${d.x2},${d.y2})</td>
            <td>${d.width}×${d.height}</td>
          </tr>`).join('');
      } else {
        tableWrap.classList.add('hidden');
        showToast('No faulty regions detected at this sensitivity');
      }
    } catch (err) {
      showToast(err.message, true);
    } finally {
      clearTimeout(stepTimer);
      clearTimeout(stepTimer2);
      loading.classList.add('hidden');
      updateAnalyzeButton();
    }
  }

  browseBtn.addEventListener('click', (e) => { e.stopPropagation(); fileInput.click(); });
  dropzone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', () => setFile(fileInput.files[0]));
  clearBtn.addEventListener('click', clearFile);

  ['dragenter', 'dragover'].forEach(ev => {
    dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
  });
  ['dragleave', 'drop'].forEach(ev => {
    dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.remove('dragover'); });
  });
  dropzone.addEventListener('drop', (e) => {
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  });

  confidence.addEventListener('input', () => {
    confValue.textContent = `${confidence.value}%`;
  });

  function setLoadingStep(step) {
    const steps = document.querySelectorAll('.load-step');
    const order = ['validate', 'infer', 'render'];
    const idx = order.indexOf(step);
    steps.forEach((el, i) => {
      el.classList.toggle('active', i === idx);
      el.classList.toggle('done', i < idx);
    });
    const titles = {
      validate: ['Validating OPG…', 'Checking panoramic X-ray format'],
      infer: ['Running detection…', 'YOLOv8 scanning for faulty regions'],
      render: ['Rendering results…', 'Drawing bounding boxes'],
    };
    if (titles[step]) {
      loadingTitle.textContent = titles[step][0];
      loadingSub.textContent = titles[step][1];
    }
  }

  function applyStatus(data) {
    statusPill.classList.remove('ok', 'bad');

    if (data.loaded) {
      modelReady = true;
      statusPill.classList.add('ok');
      statusText.textContent = 'Model ready';
    } else if (data.loading) {
      modelReady = false;
      statusText.textContent = 'Loading model…';
    } else if (data.error?.includes('not found') || !data.available) {
      modelReady = false;
      statusPill.classList.add('bad');
      statusText.textContent = 'Model missing';
    } else if (data.error) {
      modelReady = false;
      statusPill.classList.add('bad');
      statusText.textContent = 'Model error';
    } else if (data.available) {
      modelReady = false;
      statusText.textContent = 'Starting model…';
    } else {
      modelReady = false;
      statusText.textContent = 'Checking…';
    }

    updateAnalyzeButton();
  }

  let statusPolls = 0;
  const MAX_POLLS = 45; // ~90s — covers Render free-tier cold starts

  async function checkStatus() {
    try {
      const res = await fetch('/api/status', { signal: AbortSignal.timeout(30000) });
      const data = await res.json();
      applyStatus(data);
      return data.loaded;
    } catch {
      statusPill.classList.add('bad');
      if (statusPolls < 8) {
        statusText.textContent = 'Waking server…';
      } else {
        statusText.textContent = 'Server unreachable';
      }
      modelReady = false;
      updateAnalyzeButton();
      return false;
    }
  }

  async function pollStatus() {
    statusPolls += 1;
    const ready = await checkStatus();
    const done = ['Model ready', 'Model missing', 'Model error'];
    if (!ready && !done.includes(statusText.textContent) && statusPolls < MAX_POLLS) {
      setTimeout(pollStatus, 2000);
    }
  }

  analyzeBtn.addEventListener('click', () => runAnalysis());

  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
  }

  loadSamples();
  pollStatus();
})();
