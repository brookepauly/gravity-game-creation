(async () => {

  // Which sheet to pull vocab from
  const SHEET_NAME = "Vocab_Repo"; // change to "Active_Study" to switch sheets
  const SHEET_URLS = {
    Active_Study: "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBYNEU5xj3BnWzR8fJQe8qHkAnxsBeptyJgbPFBP4LdDOdaZCkWCrTi0kDTAav42ksbAlp7HvwAVKc/pub?gid=923942808&single=true&output=csv",
    Vocab_Repo:   "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBYNEU5xj3BnWzR8fJQe8qHkAnxsBeptyJgbPFBP4LdDOdaZCkWCrTi0kDTAav42ksbAlp7HvwAVKc/pub?output=csv",
  };
  const SHEET_URL = SHEET_URLS[SHEET_NAME];

  const TERMS_PER_LEVEL = 7;
  const BASE_SPEED      = 30;
  const SPEED_INC       = 20;
  const MAX_ASTEROIDS   = 3;
  const W = 2560, H = 1080;

  const canvas   = document.getElementById("gc");
  const ctx      = canvas.getContext("2d");
  const inputEl  = document.getElementById("answer-input");
  const inputBar = document.getElementById("input-bar");

  function loadImg(src) {
    return new Promise((res, rej) => {
      const img = new Image();
      img.onload = () => res(img);
      img.onerror = () => rej(new Error("Failed: " + src));
      img.src = src;
    });
  }

  let bgImg, iconImg, asteroidImgs;
  try {
    [bgImg, iconImg, ...asteroidImgs] = await Promise.all([
      loadImg("Images/txt_wallpaper.jpg"),
      loadImg("Images/txt_logo_v3.png"),
      loadImg("Images/txt_stars_1.jpg"),
      loadImg("Images/txt_stars_2.jpg"),
      loadImg("Images/txt_stars_3.jpg"),
    ]);
  } catch (e) {
    console.warn("Some images failed to load, using fallbacks.", e);
  }

  let byteFont = null;
  try {
    const ff = new FontFace("Bytesized", "url(Fonts/Bytesized-Regular.ttf)");
    byteFont = await ff.load();
    document.fonts.add(byteFont);
  } catch (e) {
    console.warn("Bytesized font not found, using monospace fallback.");
  }

  let vocab = [];
  try {
    const result = await new Promise((res, rej) => {
      Papa.parse(SHEET_URL, {
        download: true,
        header: false,
        skipEmptyLines: true,
        complete: res,
        error: rej,
      });
    });
    for (let i = 1; i < result.data.length; i++) {
      const row = result.data[i];
      if (row.length >= 3) {
        vocab.push({ english: row[0].trim(), japanese: row[1].trim(), hiragana: row[2].trim() });
      }
    }
  } catch (e) {
    ctx.fillStyle = "#fff";
    ctx.font = "18px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Failed to load vocab. Is the Google Sheet public?", W / 2, H / 2);
    return;
  }

  function shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  // Turns the raw vocab list into a shuffled deck of { shown, answer, hiragana } cards for the chosen mode.
  // `shown` stays exactly as it was before per mode (hiragana only visually embedded in "back" mode's
  // shown string, same as originally). `hiragana` is now always carried as its own field regardless of
  // mode, so feedback can show it every time.
  function buildCards(mode) {
    const result = [];
    for (const v of vocab) {
      if (mode === "front") {
        result.push({ shown: v.english, answer: v.japanese, hiragana: v.hiragana });
      }
      if (mode === "back") {
        result.push({ shown: `${v.japanese} (${v.hiragana})`, answer: v.english, hiragana: v.hiragana });
      }
      if (mode === "random") {
        if (Math.random() < 0.5) {
          result.push({ shown: v.english, answer: v.hiragana, hiragana: v.hiragana });
        } else {
          result.push({ shown: `${v.japanese} (${v.hiragana})`, answer: v.english, hiragana: v.hiragana });
        }
      }
    }
    return shuffle(result);
  }

  let gameState  = "menu";
  let mode       = null;
  let deck       = [];
  let retry      = [];
  let asteroids  = [];
  let level      = 1;
  let cleared    = 0;
  let spawnTimer = 0;
  let feedback   = "";
  let feedbackTimer = 0;
  let score      = { points: 0, correct: 0, incorrect: 0 };
  let deathTimer = null;
  let lastTs     = null;
  let mousePos   = { x: 0, y: 0 };

  function spawnAsteroid() {
    if (asteroids.length >= MAX_ASTEROIDS) return;
    if (!deck.length && !retry.length) return;

    let card, red = false;
    if (retry.length && (!deck.length || Math.random() < 0.4)) {
      card = retry.shift();
      red = true;
    } else {
      card = deck.shift();
    }

    asteroids.push({
      shown:    card.shown,
      answer:   card.answer,
      hiragana: card.hiragana,
      x:        100 + Math.random() * (W - 200),
      y:        -50,
      speed:    BASE_SPEED + SPEED_INC * (level - 1),
      red,
      imgIndex: Math.floor(Math.random() * 3),
      rotation: Math.random() * Math.PI * 2,
      rotSpeed: (Math.random() - 0.5) * 0.5,
    });
  }

  const MENU_BUTTONS = [
    { label: "Front",  mode: "front" },
    { label: "Back",   mode: "back" },
    { label: "Random", mode: "random" },
  ];
  function btnRect(i) {
    return { x: W / 2 - 100, y: H / 2 - 115 + i * 60, w: 200, h: 50 };
  }

  function drawMenu() {
    if (bgImg) {
      ctx.drawImage(bgImg, 0, 0, W, H);
    } else {
      ctx.fillStyle = "#0a0a1e";
      ctx.fillRect(0, 0, W, H);
    }

    if (iconImg) ctx.drawImage(iconImg, 10, 10, 180, 90);

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 26px 'Noto Sans JP'";
    ctx.textAlign = "center";
    ctx.fillText("Select Mode", W / 2, H / 2 - 145);

    MENU_BUTTONS.forEach((btn, i) => {
      const r = btnRect(i);
      const hovered = mousePos.x >= r.x && mousePos.x <= r.x + r.w &&
                      mousePos.y >= r.y && mousePos.y <= r.y + r.h;
      ctx.fillStyle = hovered ? "#5a5ab0" : "#3c3c78";
      roundRect(r.x, r.y, r.w, r.h, 8);
      ctx.fill();
      ctx.fillStyle = "#ffffff";
      ctx.font = "20px 'Noto Sans JP'";
      ctx.textAlign = "center";
      ctx.fillText(btn.label, r.x + r.w / 2, r.y + r.h / 2 + 7);
    });
  }

  function drawGame() {
    if (bgImg) {
      ctx.drawImage(bgImg, 0, 0, W, H);
    } else {
      ctx.fillStyle = "#0a0a1e";
      ctx.fillRect(0, 0, W, H);
    }

    for (const ast of asteroids) {
      ctx.save();
      ctx.translate(ast.x, ast.y);
      ctx.rotate(ast.rotation);
      if (asteroidImgs && asteroidImgs[ast.imgIndex]) {
        ctx.drawImage(asteroidImgs[ast.imgIndex], -125, -125, 250, 250);
      } else {
        ctx.fillStyle = ast.red ? "#551133" : "#334";
        ctx.beginPath();
        ctx.arc(0, 0, 80, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();

      ctx.fillStyle = ast.red ? "#e0218a" : "#000000";
      ctx.font = "bold 20px 'Noto Sans JP'";
      ctx.textAlign = "center";
      ctx.fillText(ast.shown, ast.x, ast.y + 7);
    }

    if (iconImg) ctx.drawImage(iconImg, 10, 10, 180, 90);

    ctx.fillStyle = "#ffffff";
    ctx.font = "22px 'Noto Sans JP'";
    ctx.textAlign = "right";
    ctx.fillText(`Score: ${score.points}`, W - 40, 50);

    if (feedback) {
      ctx.fillStyle = "#FFFFFF";
      ctx.font = "16px 'Noto Sans JP'";
      ctx.textAlign = "left";
      ctx.fillText(feedback, 30, 40 + 90 - 9);
    }

    if (gameState === "dead") {
      ctx.fillStyle = "#b3ebf2";
      ctx.font = `bold 80px ${byteFont ? "Bytesized" : "monospace"}`;
      ctx.textAlign = "center";
      ctx.fillText("GAME OVER", W / 2, H / 2);
    }
  }

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  function gameLoop(ts) {
    const delta = lastTs ? Math.min((ts - lastTs) / 1000, 0.1) : 0;
    lastTs = ts;

    if (gameState === "menu") {
      drawMenu();

    } else if (gameState === "playing") {
      spawnTimer += delta;
      if (feedbackTimer > 0) {
        feedbackTimer -= delta;
        if (feedbackTimer <= 0) feedback = "";
      }
      if (spawnTimer >= 2.0) {
        spawnTimer = 0;
        spawnAsteroid();
      }

      for (const ast of [...asteroids]) {
        ast.y        += ast.speed * delta;
        ast.rotation += ast.rotSpeed * delta;
        if (ast.y > H - 80) {
          if (ast.red) {
            gameState  = "dead";
            deathTimer = performance.now();
          } else {
            retry.push({ shown: ast.shown, answer: ast.answer, hiragana: ast.hiragana });
          }
          asteroids.splice(asteroids.indexOf(ast), 1);
        }
      }

      if (!deck.length && !retry.length && !asteroids.length) {
        deck = buildCards(mode);
      }
      drawGame();

    } else if (gameState === "dead") {
      drawGame();
      if (deathTimer && performance.now() - deathTimer >= 2000) {
        gameState  = "menu";
        mode       = null;
        deathTimer = null;
        score      = { points: 0, correct: 0, incorrect: 0 };
        level = 1;
        cleared = 0;
        asteroids = [];
        deck = [];
        retry = [];
        feedback = "";
        feedbackTimer = 0;
        inputEl.value = "";
        inputBar.style.display = "none";
      }
    }

    requestAnimationFrame(gameLoop);
  }

  function canvasCoords(e) {
    const rect   = canvas.getBoundingClientRect();
    const scaleX = W / rect.width;
    const scaleY = H / rect.height;
    return { x: (e.clientX - rect.left) * scaleX, y: (e.clientY - rect.top) * scaleY };
  }

  canvas.addEventListener("mousemove", e => { mousePos = canvasCoords(e); });

  canvas.addEventListener("click", e => {
    if (gameState !== "menu") return;
    const { x, y } = canvasCoords(e);
    MENU_BUTTONS.forEach((btn, i) => {
      const r = btnRect(i);
      if (x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h) {
        mode       = btn.mode;
        deck       = buildCards(mode);
        retry      = [];
        asteroids  = [];
        spawnTimer = 0;
        level = 1;
        cleared = 0;
        score      = { points: 0, correct: 0, incorrect: 0 };
        gameState  = "playing";
        inputBar.style.display = "flex";
        inputEl.focus();
      }
    });
  });

  inputEl.addEventListener("compositionend", () => {
    inputEl.focus();
  });

  inputEl.addEventListener("keyup", e => {
    if (gameState !== "playing") return;
    if (e.key !== "Enter" && e.key !== "Escape") return;
    if (!asteroids.length) return;

    const target = asteroids.reduce((a, b) => (a.y > b.y ? a : b));

    const guess = e.key === "Escape" ? null : inputEl.value.trim().toLowerCase();
    if (e.key === "Enter" && !guess) return;

    if (guess !== null && guess === target.answer.trim().toLowerCase()) {
      score.points += 10 * level;
      score.correct++;
      asteroids.splice(asteroids.indexOf(target), 1);
      cleared++;
      if (cleared >= TERMS_PER_LEVEL) {
        level++;
        cleared = 0;
      }
      inputEl.value = "";
    } else {
      inputEl.value = "";
      score.incorrect++;
      // Feedback always includes hiragana now, regardless of mode.
      feedback = `${target.shown}  ${target.answer} ${target.hiragana}`;
      feedbackTimer = 1.0;
      if (target.red) {
        gameState  = "dead";
        deathTimer = performance.now();
      } else {
        retry.push({ shown: target.shown, answer: target.answer, hiragana: target.hiragana });
        asteroids.splice(asteroids.indexOf(target), 1);
      }
    }
  });

  document.addEventListener("click", () => {
    if (gameState === "playing") inputEl.focus();
  });

  requestAnimationFrame(gameLoop);
})();