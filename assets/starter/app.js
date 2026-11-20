/* Original experience layer. Pannellum handles the actual spherical projection. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const stage = $('stage');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let config, viewer, active, ready = false, illuminated = false, rotation = false;
  let revealTimer, loadTimer, noticeTimer, readingFocus;
  const isExploring = () => stage.dataset.state === 'exploring';

  function state(value) {
    stage.dataset.state = value;
    const dark = value === 'dark' || value === 'booting';
    $('panorama').inert = value !== 'exploring';
    $('panorama').setAttribute('aria-hidden', String(value !== 'exploring'));
    $('intro').hidden = !dark;
    $('hud').hidden = dark;
    $('controls').hidden = dark;
    $('waiting').hidden = !['booting', 'switching'].includes(value);
    $('light').disabled = !ready || value !== 'dark';
    $('scenes').querySelectorAll('button').forEach(b => { b.disabled = value === 'switching' || value === 'revealing'; });
    for (const id of ['zoom-in', 'zoom-out', 'reset', 'rotate']) $(id).disabled = value !== 'exploring';
    $('dark').disabled = value === 'fallback' || value === 'switching';
  }

  function announce(message) {
    clearTimeout(noticeTimer);
    $('notice').textContent = message;
    $('notice').hidden = false;
    noticeTimer = setTimeout(() => { $('notice').hidden = true; }, 4500);
  }

  function stopRotation() {
    if (viewer) { viewer.stopAutoRotate(); viewer.stopMovement(); }
    rotation = false;
    $('rotate').setAttribute('aria-pressed', 'false');
  }

  function read(title, body) {
    stopRotation();
    readingFocus = document.activeElement;
    $('reading-title').textContent = title;
    $('reading-body').textContent = body;
    if (!$('reading').open) $('reading').showModal();
    $('close-reading').focus();
  }

  function sceneUI() {
    const scene = config.scenes[active];
    const number = Object.keys(config.scenes).indexOf(active) + 1;
    $('scene-index').textContent = `CHAMBER ${String(number).padStart(2, '0')}`;
    $('scene-title').textContent = scene.title;
    $('scene-subtitle').textContent = scene.subtitle || '';
    $('provenance').textContent = scene.provenance.statement;
    $('poster').src = scene.poster;
    $('poster').alt = scene.title + ' · 静态预览';
    $('scenes').querySelectorAll('button').forEach(b => b.setAttribute('aria-current', String(b.dataset.scene === active)));
    $('history').textContent = '展览导读 ↗';
  }

  function fallback(message) {
    clearTimeout(loadTimer);
    clearTimeout(revealTimer);
    ready = false;
    if (viewer) { viewer.destroy(); viewer = null; }
    $('panorama').hidden = true;
    $('poster').hidden = false;
    state('fallback');
    $('notice').replaceChildren();
    const text = document.createElement('p');
    text.textContent = message + ' 当前显示静态预览，场景目录和文字解读仍可使用。';
    const retry = document.createElement('button');
    retry.type = 'button'; retry.textContent = '重试加载全景';
    retry.addEventListener('click', () => location.reload());
    const dismiss = document.createElement('button');
    dismiss.type = 'button'; dismiss.textContent = '继续静态浏览';
    dismiss.addEventListener('click', () => { $('notice').hidden = true; $('history').focus(); });
    $('notice').append(text, retry, dismiss);
    $('notice').hidden = false;
    dismiss.focus();
  }

  function armTimeout() {
    clearTimeout(loadTimer);
    loadTimer = setTimeout(() => fallback('全景加载超时，请检查本地素材和浏览器支持。'), 20000);
  }

  function switchScene(id) {
    if (!config.scenes[id] || stage.dataset.state === 'switching' || stage.dataset.state === 'revealing') return;
    if (stage.dataset.state === 'fallback') {
      active = id; sceneUI(); $('notice').hidden = true; return;
    }
    if (!viewer || !isExploring() || id === active) return;
    stopRotation();
    ready = false;
    $('waiting-text').textContent = '正在前往 · ' + config.scenes[id].title;
    state('switching');
    armTimeout();
    viewer.loadScene(id);
  }

  function marker(container, spot) {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'marker ' + spot.kind;
    const ring = document.createElement('span');
    ring.className = 'ring'; ring.setAttribute('aria-hidden', 'true');
    ring.textContent = spot.kind === 'scene' ? '›' : '·';
    const caption = document.createElement('span');
    caption.className = 'caption'; caption.textContent = spot.label;
    button.append(ring, caption);
    button.addEventListener('click', event => {
      event.stopPropagation();
      if (!isExploring()) return;
      if (spot.kind === 'scene') switchScene(spot.target);
      else read(spot.title, spot.body);
    });
    container.appendChild(button);
  }

  function lightOn() {
    if (!ready || stage.dataset.state !== 'dark') return;
    illuminated = true;
    clearTimeout(revealTimer);
    state('revealing');
    revealTimer = setTimeout(() => { state('exploring'); stage.focus({preventScroll: true}); }, reduced.matches ? 90 : 1250);
  }

  function lightOff() {
    if (!viewer || !ready) return;
    clearTimeout(revealTimer);
    stopRotation();
    illuminated = false;
    state('dark');
    $('light').focus();
  }

  async function start() {
    if (location.protocol === 'file:') throw new Error('请通过本地 HTTP 服务打开本工程。');
    const response = await fetch('tour.json');
    if (!response.ok) throw new Error('无法读取 tour.json。');
    config = await response.json();
    if (!config.scenes || !config.scenes[config.firstScene]) throw new Error('场景配置不完整。');
    active = config.firstScene;
    document.title = config.title;
    $('intro-title').textContent = config.title;
    Object.entries(config.scenes).forEach(([id, scene], index) => {
      const button = document.createElement('button');
      button.type = 'button'; button.dataset.scene = id;
      button.dataset.number = String(index + 1).padStart(2, '0');
      button.textContent = scene.title;
      button.addEventListener('click', () => switchScene(id));
      $('scenes').appendChild(button);
    });
    sceneUI();
    if (!window.pannellum) { fallback('本地全景引擎未加载。'); return; }
    const scenes = {};
    Object.entries(config.scenes).forEach(([id, scene]) => {
      scenes[id] = {
        type: 'equirectangular', panorama: scene.panorama,
        yaw: scene.yaw, pitch: scene.pitch, hfov: scene.hfov,
        hotSpots: scene.hotSpots.map(spot => ({
          id: spot.id, yaw: spot.yaw, pitch: spot.pitch, type: 'info',
          cssClass: 'cave-hotspot', createTooltipFunc: marker, createTooltipArgs: spot
        }))
      };
    });
    viewer = pannellum.viewer('panorama', {
      default: {
        firstScene: active, autoLoad: true, showControls: false,
        showFullscreenCtrl: false, disableKeyboardCtrl: true,
        minHfov: 50, maxHfov: 110, friction: 0.18,
        autoRotate: 0, sceneFadeDuration: reduced.matches ? 0 : 450,
        escapeHTML: true, hotSpotDebug: false,
        backgroundColor: [0.05, 0.04, 0.03]
      }, scenes
    });
    viewer.on('load', () => {
      if (!viewer) return;
      clearTimeout(loadTimer);
      ready = true; active = viewer.getScene(); sceneUI();
      state(illuminated ? 'exploring' : 'dark');
      if (!illuminated) $('light').focus();
    });
    viewer.on('error', () => { if (viewer) fallback('全景无法加载。'); });
    viewer.on('mousedown', stopRotation);
    viewer.on('touchstart', stopRotation);
    armTimeout();
  }

  $('light').addEventListener('click', lightOn);
  $('dark').addEventListener('click', lightOff);
  $('history').addEventListener('click', () => {
    const scene = config.scenes[active];
    const notes = scene.hotSpots.filter(s => s.kind === 'info').map(s => s.title + '\n' + s.body).join('\n\n');
    read(scene.title, (config.introduction || '') + '\n\n' + notes);
  });
  $('about').addEventListener('click', () => read('关于这些画面', config ? config.scenes[active].provenance.statement + '\n\n' + config.introduction + '\n\n全景查看器：Pannellum 2.5.7，Matthew Petroff，MIT 许可。本地许可位于 vendor/PANNELLUM-LICENSE.txt。' : '正在读取场景配置。'));
  $('close-reading').addEventListener('click', () => $('reading').close());
  $('reading').addEventListener('close', () => { if (readingFocus && readingFocus.isConnected) readingFocus.focus(); });
  $('reset').addEventListener('click', () => {
    if (!viewer || !isExploring()) return;
    stopRotation(); const scene = config.scenes[active];
    viewer.lookAt(scene.pitch, scene.yaw, scene.hfov, reduced.matches ? false : 500);
  });
  for (const [id, delta] of [['zoom-in', -10], ['zoom-out', 10]]) {
    $(id).addEventListener('click', () => {
      if (!viewer || !isExploring()) return;
      viewer.setHfov(Math.max(50, Math.min(110, viewer.getHfov() + delta)), reduced.matches ? false : 200);
    });
  }
  $('rotate').addEventListener('click', () => {
    if (!viewer || !isExploring()) return;
    if (rotation) stopRotation();
    else { viewer.startAutoRotate(-2, viewer.getPitch()); rotation = true; $('rotate').setAttribute('aria-pressed', 'true'); }
  });
  $('fullscreen').hidden = !document.fullscreenEnabled;
  $('fullscreen').addEventListener('click', async () => {
    try { if (document.fullscreenElement) await document.exitFullscreen(); else await stage.requestFullscreen(); }
    catch (_) { announce('此浏览器未允许全屏，可继续使用当前视图。'); }
  });
  document.addEventListener('fullscreenchange', () => { if (viewer) viewer.resize(); });
  window.addEventListener('resize', () => { if (viewer) viewer.resize(); });
  stage.addEventListener('pointermove', event => {
    if (stage.dataset.state !== 'dark' || event.pointerType === 'touch') return;
    const rect = stage.getBoundingClientRect();
    stage.style.setProperty('--lamp-x', (event.clientX - rect.left) + 'px');
    stage.style.setProperty('--lamp-y', (event.clientY - rect.top) + 'px');
  });
  stage.addEventListener('keydown', event => {
    if (!viewer || !isExploring() || event.target.closest('button, a, input, select, textarea')) return;
    const keys = {ArrowLeft: [0, -8], ArrowRight: [0, 8], ArrowUp: [6, 0], ArrowDown: [-6, 0]};
    if (keys[event.key]) {
      event.preventDefault(); stopRotation();
      const [dp, dy] = keys[event.key];
      viewer.lookAt(Math.max(-85, Math.min(85, viewer.getPitch() + dp)), viewer.getYaw() + dy, undefined, false);
    }
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) stopRotation(); });
  window.addEventListener('pagehide', () => {
    clearTimeout(loadTimer); clearTimeout(revealTimer); clearTimeout(noticeTimer);
    if (viewer) { viewer.destroy(); viewer = null; }
  });
  start().catch(error => {
    if (config && active) { fallback(error.message); return; }
    $('waiting').hidden = true; $('light').disabled = true;
    $('notice').textContent = error.message + ' 使用 python3 -m http.server 启动后重试。';
    $('notice').hidden = false;
  });
})();
