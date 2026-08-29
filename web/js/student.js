(function () {
  Storm.rain(document.getElementById("rain"));
  const code = Storm.codeFromPath("s");
  document.getElementById("code").textContent = code;
  const q = new URLSearchParams(location.search);
  const id = q.get("id") || localStorage.getItem("storm_sid") || Storm.uid("s-");
  localStorage.setItem("storm_sid", id);
  const name = q.get("name") || localStorage.getItem("storm_sname") || "旁听生";
  localStorage.setItem("storm_sname", name);
  const c = new Storm.Client({ code, role: "student", id, name });
  let lastCall = "";

  function paint() {
    const room = c.room;
    if (!room) return;
    const L = c.locale;
    const sl = Storm.currentSlide(room);
    document.getElementById("kicker").textContent = `${room.slide_index + 1}/${room.slides.length} · ${
      room.you && room.you.team === "red" ? "红队" : "蓝队"
    } · ${room.you ? room.you.xp : 0} XP`;
    document.getElementById("title").textContent = Storm.txt(room, sl.title_zh, sl.title_en, L);
    document.getElementById("body").textContent = Storm.txt(room, sl.body_zh, sl.body_en, L);
    document.getElementById("confused").textContent = c.t("confused");
    document.getElementById("dan").placeholder = c.t("danPh");
    document.getElementById("send").textContent = c.t("send");

    const box = document.getElementById("quiz");
    const quiz = room.quiz;
    if (!quiz) {
      box.innerHTML = "";
    } else {
      let inner = `<div class="quiz-prompt">${Storm.esc(Storm.txt(room, quiz.prompt_zh, quiz.prompt_en, L))}</div>`;
      if (quiz.kind === "fill" || quiz.kind === "short") {
        inner += `<input id="fill" placeholder="${quiz.kind === "fill" ? c.t("fillPh") : c.t("shortPh")}" ${
          quiz.you_answered ? "disabled" : ""
        }/>
          <button class="iconbtn gold" id="ans" ${quiz.you_answered ? "disabled" : ""}>${c.t("send")}</button>`;
      } else {
        inner += `<div class="options">`;
        (quiz.options || []).forEach((o, i) => {
          const mark =
            quiz.state === "revealed" && (quiz.correct_ids || []).includes(o.id) ? " correct" : "";
          inner += `<div class="opt${mark}" data-oid="${o.id}"><span class="key">${Storm.optionLabel(i)}</span>${Storm.esc(
            Storm.txt(room, o.text_zh, o.text_en, L)
          )}</div>`;
        });
        inner += `</div>`;
      }
      if (quiz.you_answered && quiz.your_result) {
        inner += `<div style="margin-top:8px;color:${quiz.your_result.correct ? "#8fd19e" : "#e07a6a"}">${
          quiz.your_result.scored
            ? quiz.your_result.correct
              ? "✓ +" + quiz.your_result.xp
              : "✗"
            : "…"
        }</div>`;
      }
      box.innerHTML = inner;
      box.querySelectorAll(".opt").forEach((n) => {
        n.onclick = () => {
          if (quiz.you_answered || quiz.state !== "open") return;
          if (quiz.kind === "multi") {
            n.classList.toggle("on");
            n.style.borderColor = n.classList.contains("on") ? "#8be9fd" : "";
          } else if (quiz.kind === "truefalse") {
            c.action({
              type: "answer",
              answer: { value: n.dataset.oid === "true" },
            });
          } else {
            c.action({ type: "answer", answer: { option_id: n.dataset.oid } });
          }
        };
      });
      if (quiz.kind === "multi" && !quiz.you_answered && quiz.state === "open") {
        const b = document.createElement("button");
        b.className = "iconbtn gold";
        b.textContent = c.t("send");
        b.onclick = () => {
          const ids = [...box.querySelectorAll(".opt.on")].map((n) => n.dataset.oid);
          c.action({ type: "answer", answer: { option_ids: ids } });
        };
        box.appendChild(b);
      }
      const ans = document.getElementById("ans");
      if (ans) {
        ans.onclick = () => {
          const v = document.getElementById("fill").value;
          c.action({ type: "answer", answer: { text: v } });
        };
      }
    }

    if (room.rollcall && room.rollcall.student_id === id && lastCall !== room.rollcall.student_id + room.seq) {
      lastCall = room.rollcall.student_id + room.seq;
      const el = document.getElementById("called");
      el.textContent = c.t("called") + " · " + name;
      el.classList.add("show");
      setTimeout(() => el.classList.remove("show"), 2200);
    }
  }

  document.getElementById("confused").onclick = () => c.action({ type: "confused" });
  document.getElementById("send").onclick = () => {
    const t = document.getElementById("dan").value.trim();
    if (!t) return;
    c.action({ type: "danmaku", text: t });
    document.getElementById("dan").value = "";
  };
  document.getElementById("dan").addEventListener("keydown", (e) => {
    if (e.key === "Enter") document.getElementById("send").click();
  });

  c.on(paint);
  c.join().then(() => {
    c.snapshot();
    c.stream();
    c.action({ type: "checkin" });
  });
})();
