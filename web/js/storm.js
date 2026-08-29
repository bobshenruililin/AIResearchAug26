/* StormClass client: i18n, SSE, widgets */
(function (global) {
  const T = {
    zh: {
      product: "暴雨课堂",
      productEn: "STORMCLASS",
      tag: "比雨课堂更重的一场课",
      startDemo: "开始演示课堂",
      create: "创建空白教室",
      teacher: "教师",
      student: "学生",
      projection: "投屏",
      report: "课堂报告",
      present: "在场",
      checked: "签到",
      danmaku: "弹幕",
      cloud: "词云",
      roster: "名册",
      mastery: "掌握",
      posts: "投稿",
      pk: "红蓝 PK",
      sendQuiz: "发送此题",
      lock: "收卷",
      reveal: "揭晓",
      next: "下一页",
      prev: "上一页",
      roll: "随机点名",
      mute: "弹幕",
      unmute: "开弹幕",
      bots: "模拟学生",
      confused: "不懂",
      send: "发送",
      join: "进入课堂",
      name: "你的名字",
      called: "被点到了",
      reteach: "建议复讲",
      accuracy: "正确率",
      lang: "EN",
      live: "课堂进行中",
      idle: "待发题",
      open: "答题中",
      locked: "已收卷",
      revealed: "已揭晓",
      shortPh: "写下你的句子",
      fillPh: "填写答案",
      postPh: "匿名投稿给老师",
      danPh: "弹幕… 合并步不是免费的",
      footer: "本地 C++ 内核 · 无云 · 无微信",
      keys: "← → 翻页  ·  Space 发题  ·  R 点名  ·  D 弹幕  ·  P PK",
    },
    en: {
      product: "StormClass",
      productEn: "暴雨课堂",
      tag: "Heavier weather than Rain Classroom",
      startDemo: "Open the live demo",
      create: "Create empty room",
      teacher: "Teacher",
      student: "Student",
      projection: "Projection",
      report: "Report",
      present: "Present",
      checked: "Checked in",
      danmaku: "Danmaku",
      cloud: "Word cloud",
      roster: "Roster",
      mastery: "Mastery",
      posts: "Inbox",
      pk: "Team PK",
      sendQuiz: "Push this item",
      lock: "Lock",
      reveal: "Reveal",
      next: "Next",
      prev: "Prev",
      roll: "Roll call",
      mute: "Mute barrage",
      unmute: "Unmute",
      bots: "Simulated class",
      confused: "Confused",
      send: "Send",
      join: "Join",
      name: "Your name",
      called: "You're on",
      reteach: "Reteach now",
      accuracy: "Accuracy",
      lang: "中",
      live: "Live",
      idle: "Idle",
      open: "Open",
      locked: "Locked",
      revealed: "Revealed",
      shortPh: "One sentence",
      fillPh: "Type an answer",
      postPh: "Anonymous note to the teacher",
      danPh: "Danmaku… combine is not free",
      footer: "Local C++ kernel · no cloud · no WeChat",
      keys: "← → slides  ·  Space push  ·  R roll  ·  D mute  ·  P PK",
    },
  };

  function uid(prefix) {
    const a = new Uint8Array(8);
    crypto.getRandomValues(a);
    return (
      prefix +
      [...a].map((x) => x.toString(16).padStart(2, "0")).join("")
    );
  }

  function rain(canvas) {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const drops = [];
    function resize() {
      canvas.width = innerWidth;
      canvas.height = innerHeight;
      drops.length = 0;
      const n = Math.floor(canvas.width / 14);
      for (let i = 0; i < n; i++) {
        drops.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          l: 8 + Math.random() * 18,
          s: 4 + Math.random() * 8,
        });
      }
    }
    resize();
    addEventListener("resize", resize);
    function tick() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = "rgba(213,224,234,0.28)";
      ctx.lineWidth = 1;
      for (const d of drops) {
        ctx.beginPath();
        ctx.moveTo(d.x, d.y);
        ctx.lineTo(d.x + 0.6, d.y + d.l);
        ctx.stroke();
        d.y += d.s;
        if (d.y > canvas.height) {
          d.y = -20;
          d.x = Math.random() * canvas.width;
        }
      }
      requestAnimationFrame(tick);
    }
    tick();
  }

  class Client {
    constructor({ code, role, id, name }) {
      this.code = code;
      this.role = role;
      this.id = id;
      this.name = name;
      this.locale = localStorage.getItem("storm_locale") || "zh";
      this.room = null;
      this.seq = 0;
      this.es = null;
      this.listeners = [];
    }
    t(k) {
      return (T[this.locale] || T.zh)[k] || k;
    }
    toggleLocale() {
      this.locale = this.locale === "zh" ? "en" : "zh";
      localStorage.setItem("storm_locale", this.locale);
      this.emit();
    }
    on(fn) {
      this.listeners.push(fn);
    }
    emit() {
      for (const fn of this.listeners) fn(this.room, this);
    }
    async join() {
      const body = {
        type: "join",
        role: this.role,
        name: this.name,
        client_id: this.id,
        checkin: this.role === "student",
      };
      const r = await this.action(body);
      return r;
    }
    async action(body) {
      body.actor_id = body.actor_id || this.id;
      body.locale = this.locale;
      const res = await fetch(`/api/rooms/${this.code}/action`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Storm-Actor": this.id,
        },
        body: JSON.stringify(body),
      });
      const j = await res.json();
      if (j.room) {
        this.room = j.room;
        this.seq = j.seq || this.seq;
        this.emit();
      }
      return j;
    }
    async snapshot() {
      const res = await fetch(
        `/api/rooms/${this.code}?viewer=${encodeURIComponent(this.id)}&locale=${this.locale}`
      );
      const j = await res.json();
      if (j.room) {
        this.room = j.room;
        this.seq = j.room.seq;
        this.emit();
      }
      return j;
    }
    stream() {
      if (this.es) this.es.close();
      const url = `/api/rooms/${this.code}/stream?viewer=${encodeURIComponent(this.id)}&locale=${this.locale}&after=${this.seq}`;
      this.es = new EventSource(url);
      this.es.addEventListener("state", (ev) => {
        try {
          const j = JSON.parse(ev.data);
          if (j.room) {
            this.room = j.room;
            this.seq = j.room.seq;
            this.emit();
          }
        } catch (e) {}
      });
      this.es.onerror = () => {
        /* native EventSource retry; do not open a second socket */
      };
    }
  }

  function el(html) {
    const d = document.createElement("div");
    d.innerHTML = html.trim();
    return d.firstChild;
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function txt(room, zh, en, loc) {
    return loc === "en" ? en || zh : zh || en;
  }

  function optionLabel(i) {
    return String.fromCharCode(65 + i);
  }

  function renderRadar(svg, kcs, mastery, loc) {
    const n = kcs.length || 1;
    const cx = 160, cy = 110, r = 78;
    let pts = [];
    let axes = "";
    let labels = "";
    for (let i = 0; i < n; i++) {
      const ang = -Math.PI / 2 + (i * 2 * Math.PI) / n;
      const x = cx + r * Math.cos(ang);
      const y = cy + r * Math.sin(ang);
      axes += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="rgba(213,224,234,0.18)"/>`;
      const kc = kcs[i];
      const m = mastery && mastery[kc.id] ? mastery[kc.id] : 0.5;
      const nobs = mastery && mastery._n && mastery._n[kc.id] ? mastery._n[kc.id] : 0;
      const rr = r * (nobs === 0 ? 0.18 : m);
      pts.push([cx + rr * Math.cos(ang), cy + rr * Math.sin(ang)]);
      const lx = cx + (r + 18) * Math.cos(ang);
      const ly = cy + (r + 18) * Math.sin(ang);
      const name = loc === "en" ? kc.name_en : kc.name_zh;
      labels += `<text x="${lx}" y="${ly}" text-anchor="middle" font-size="10" fill="#8a9aab">${esc(name)}</text>`;
    }
    const poly = pts.map((p) => p.join(",")).join(" ");
    svg.innerHTML = `${axes}<polygon points="${poly}" fill="rgba(139,233,253,0.22)" stroke="#8be9fd" stroke-width="1.4"/>${labels}`;
  }

  function renderCloud(node, words) {
    node.innerHTML = "";
    if (!words || !words.length) {
      node.textContent = "—";
      return;
    }
    const max = words[0][1] || 1;
    for (const [w, c] of words) {
      const sp = document.createElement("span");
      const s = 12 + (c / max) * 28;
      sp.style.fontSize = s + "px";
      sp.style.opacity = String(0.45 + 0.55 * (c / max));
      sp.style.fontFamily = "Fraunces, Noto Serif SC, serif";
      sp.textContent = w;
      node.appendChild(sp);
    }
  }

  function currentSlide(room) {
    if (!room || !room.slides) return null;
    return room.slides[room.slide_index] || room.slides[0];
  }

  function codeFromPath(prefix) {
    const p = location.pathname.split("/").filter(Boolean);
    if (p[0] === prefix && p[1]) return p[1];
    const q = new URLSearchParams(location.search);
    return q.get("code") || "FENZHI";
  }

  global.Storm = {
    T,
    uid,
    rain,
    Client,
    el,
    esc,
    txt,
    optionLabel,
    renderRadar,
    renderCloud,
    currentSlide,
    codeFromPath,
  };
})(window);
