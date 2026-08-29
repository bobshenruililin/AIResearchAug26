(function () {
  Storm.rain(document.getElementById("rain"));
  const code = Storm.codeFromPath("t");
  const embed = new URLSearchParams(location.search).has("embed");
  if (embed) document.body.classList.add("embed");
  const id = code === "FENZHI" ? "teacher-1" : localStorage.getItem("storm_tid") || Storm.uid("t-");
  localStorage.setItem("storm_tid", id);
  const c = new Storm.Client({ code, role: "teacher", id, name: "沈老师" });
  let tab = "roster";
  let lastRoll = "";

  document.getElementById("code").textContent = code;
  document.getElementById("proj").href = "/p/" + code;
  document.getElementById("rep").href = "/report/" + code;
  document.getElementById("stu").href = "/s/" + code;

  const tabs = document.querySelectorAll(".tabs button");
  tabs.forEach((b) =>
    b.addEventListener("click", () => {
      tabs.forEach((x) => x.classList.remove("on"));
      b.classList.add("on");
      tab = b.dataset.tab;
      paint();
    })
  );

  function loc() { return c.locale; }

  function paint() {
    const room = c.room;
    if (!room) return;
    const L = loc();
    document.getElementById("lang").textContent = c.t("lang");
    document.getElementById("present").textContent = room.present;
    document.getElementById("checked").textContent = room.checked_in;
    document.getElementById("seq").textContent = room.seq;
    const sl = Storm.currentSlide(room);
    document.getElementById("kicker").textContent =
      `${room.slide_index + 1} / ${room.slides.length}  ·  ${code}`;
    document.getElementById("title").textContent = Storm.txt(room, sl.title_zh, sl.title_en, L);
    document.getElementById("body").textContent = Storm.txt(room, sl.body_zh, sl.body_en, L);
    const vis = document.getElementById("visual");
    vis.className = "slide-visual vis-" + (sl.visual || "");

    const heat = document.getElementById("heat");
    heat.innerHTML = "";
    const maxC = Math.max(1, ...room.slides.map((s) => s.confused || 0));
    room.slides.forEach((s, i) => {
      const h = document.createElement("div");
      h.className = "heat";
      h.title = (L === "en" ? s.title_en : s.title_zh) + " · 不懂 " + s.confused;
      const inner = document.createElement("i");
      inner.style.width = ((s.confused || 0) / maxC) * 100 + "%";
      if (i === room.slide_index) h.style.outline = "1px solid #e8c07a";
      h.appendChild(inner);
      h.onclick = () => c.action({ type: "goto_slide", index: i });
      heat.appendChild(h);
    });

    const qb = document.getElementById("quizbar");
    const q = room.quiz;
    if (!q) {
      const onSlide = sl.quiz_id;
      qb.innerHTML = onSlide
        ? `<div class="quiz-prompt">${c.t("idle")} · ${onSlide}</div>`
        : `<div class="quiz-prompt" style="color:#8a9aab">${c.t("keys")}</div>`;
    } else {
      const acc = Math.round((q.accuracy || 0) * 100);
      let opts = "";
      (q.options || []).forEach((o, i) => {
        const n = (q.histogram && q.histogram[o.id]) || 0;
        const tot = q.answered || 1;
        const mark =
          q.state === "revealed" && (q.correct_ids || []).includes(o.id) ? " correct" : "";
        opts += `<div class="opt${mark}"><span class="key">${Storm.optionLabel(i)}</span><span>${Storm.esc(
          Storm.txt(room, o.text_zh, o.text_en, L)
        )}</span><span class="hist"><i style="width:${(n / tot) * 100}%"></i></span><span>${n}</span></div>`;
      });
      qb.innerHTML = `<div class="quiz-prompt">${Storm.esc(
        Storm.txt(room, q.prompt_zh, q.prompt_en, L)
      )} <span style="color:#8a9aab">· ${q.answered}/${q.present} · ${c.t("accuracy")} ${acc}%</span></div>
        <div class="options">${opts}</div>`;
    }

    if (room.rollcall && room.rollcall.student_id !== lastRoll) {
      lastRoll = room.rollcall.student_id;
      const box = document.getElementById("lottery");
      box.classList.add("show");
      const names = (room.students || []).map((s) => s.name);
      let i = 0;
      const t0 = Date.now();
      const iv = setInterval(() => {
        box.textContent = names[i++ % names.length] || room.rollcall.name;
        if (Date.now() - t0 > 1100) {
          clearInterval(iv);
          box.textContent = room.rollcall.name;
          setTimeout(() => box.classList.remove("show"), 1400);
        }
      }, 70);
    }

    const side = document.getElementById("side");
    if (tab === "roster") {
      side.innerHTML = (room.students || [])
        .map(
          (s) => `<div class="person"><i class="dot ${s.team}"></i><span>${Storm.esc(s.name)}${
            s.bot ? " · bot" : ""
          }${s.checked_in ? "" : " ·"} </span><span class="xp">${s.xp}</span></div>`
        )
        .join("");
    } else if (tab === "dan") {
      side.innerHTML =
        `<div class="dan-list">` +
        (room.danmaku || [])
          .slice()
          .reverse()
          .map((d) => `<div class="dan-item"><b>${Storm.esc(d.name)}</b>${Storm.esc(d.text)}</div>`)
          .join("") +
        `</div>`;
    } else if (tab === "cloud") {
      side.innerHTML = `<div class="cloud" id="cloud"></div>`;
      Storm.renderCloud(document.getElementById("cloud") || side.firstChild, room.wordcloud);
    } else if (tab === "mastery") {
      const reteach = room.reteach
        ? `<div class="reteach"><b>${c.t("reteach")}</b> ${Storm.esc(
            L === "en" ? room.reteach.reason_en : room.reteach.reason_zh
          )}</div>`
        : "";
      const pk = room.pk || {};
      const tot = Math.max(1, (pk.red || 0) + (pk.blue || 0));
      side.innerHTML = `${reteach}
        <div class="pk"><span>红 ${pk.red || 0}</span>
          <div class="bar"><div class="r" style="width:${((pk.red || 0) / tot) * 100}%"></div>
          <div class="b" style="width:${((pk.blue || 0) / tot) * 100}%"></div></div>
          <span>蓝 ${pk.blue || 0}</span></div>
        <svg class="radar" viewBox="0 0 320 220" id="radar"></svg>
        <div class="dan-list" style="margin-top:8px">${(room.leaderboard || [])
          .map((x) => `<div class="person"><i class="dot ${x.team}"></i><span>${x.rank}. ${Storm.esc(
            x.name
          )}</span><span class="xp">${x.xp}</span></div>`)
          .join("")}</div>`;
      const mean = {};
      const nn = {};
      for (const kc of room.kcs || []) {
        const cell = room.mastery_class && room.mastery_class[kc.id];
        mean[kc.id] = cell && cell.mean != null ? cell.mean : 0.5;
        nn[kc.id] = cell ? cell.n : 0;
      }
      mean._n = nn;
      Storm.renderRadar(document.getElementById("radar"), room.kcs, mean, L);
    } else if (tab === "posts") {
      side.innerHTML = (room.posts || [])
        .map(
          (p) =>
            `<div class="dan-item"><b>${Storm.esc(p.name)}</b>${Storm.esc(p.text)}
            ${p.broadcast ? "" : ` <button data-post="${p.id}" class="iconbtn">投屏</button>`}</div>`
        )
        .join("") || "—";
      side.querySelectorAll("[data-post]").forEach((b) => {
        b.onclick = () => c.action({ type: "broadcast_post", id: Number(b.dataset.post) });
      });
    }

    document.getElementById("bots").classList.toggle("on", room.bots_enabled);
    document.getElementById("mute").classList.toggle("on", room.danmaku_muted);
    document.getElementById("pk").classList.toggle("on", room.pk && room.pk.on);
  }

  document.getElementById("prev").onclick = () => c.action({ type: "slide_prev" });
  document.getElementById("next").onclick = () => c.action({ type: "slide_next" });
  document.getElementById("push").onclick = () => c.action({ type: "push_quiz", time_limit_sec: 28 });
  document.getElementById("lock").onclick = () => c.action({ type: "lock_quiz" });
  document.getElementById("reveal").onclick = () => c.action({ type: "reveal_quiz" });
  document.getElementById("roll").onclick = () => c.action({ type: "rollcall" });
  document.getElementById("mute").onclick = () =>
    c.action({ type: "danmaku_mute", on: !(c.room && c.room.danmaku_muted) });
  document.getElementById("pk").onclick = () =>
    c.action({ type: c.room && c.room.pk && c.room.pk.on ? "pk_end" : "pk_start" });
  document.getElementById("bots").onclick = () =>
    c.action({ type: "bots", on: !(c.room && c.room.bots_enabled) });
  document.getElementById("lang").onclick = () => c.toggleLocale();

  addEventListener("keydown", (e) => {
    if (e.target.matches("input,textarea")) return;
    if (e.key === "ArrowRight") c.action({ type: "slide_next" });
    if (e.key === "ArrowLeft") c.action({ type: "slide_prev" });
    if (e.key === " ") {
      e.preventDefault();
      c.action({ type: "push_quiz", time_limit_sec: 28 });
    }
    if (e.key === "r" || e.key === "R") c.action({ type: "rollcall" });
    if (e.key === "d" || e.key === "D")
      c.action({ type: "danmaku_mute", on: !(c.room && c.room.danmaku_muted) });
    if (e.key === "p" || e.key === "P")
      c.action({ type: c.room && c.room.pk && c.room.pk.on ? "pk_end" : "pk_start" });
  });

  c.on(paint);
  c.join().then(() => {
    c.snapshot();
    c.stream();
  });
})();
