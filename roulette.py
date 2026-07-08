import json

import streamlit.components.v1 as components


def render_roulette(contestants: list[dict], winner_index: int, spin_id: int) -> None:
    payload = json.dumps(
        {
            "contestants": contestants,
            "winnerIndex": winner_index,
            "spinId": spin_id,
        },
        ensure_ascii=False,
    )

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;900&family=Outfit:wght@300;500;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Outfit', sans-serif;
    background: radial-gradient(ellipse at center, #0f2b1d 0%, #040a07 70%);
    color: #f8f4e8;
    overflow: hidden;
    min-height: 760px;
  }}
  .stage {{
    position: relative;
    width: 100%;
    min-height: 760px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 12px 8px 28px;
  }}
  .ambient {{
    position: absolute;
    inset: 0;
    background:
      radial-gradient(circle at 20% 20%, rgba(212,175,55,0.12), transparent 35%),
      radial-gradient(circle at 80% 80%, rgba(46,125,87,0.18), transparent 40%);
    pointer-events: none;
  }}
  .title {{
    font-family: 'Cinzel', serif;
    font-size: clamp(1.3rem, 2.5vw, 2rem);
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: #d4af37;
    text-shadow: 0 0 24px rgba(212,175,55,0.45);
    margin-bottom: 6px;
    z-index: 2;
  }}
  .subtitle {{
    font-size: 0.95rem;
    opacity: 0.75;
    margin-bottom: 18px;
    z-index: 2;
  }}
  .wheel-wrap {{
    position: relative;
    width: min(92vw, 520px);
    height: min(92vw, 520px);
    z-index: 2;
  }}
  .outer-ring {{
    position: absolute;
    inset: -10px;
    border-radius: 50%;
    border: 3px solid rgba(212,175,55,0.55);
    box-shadow:
      0 0 30px rgba(212,175,55,0.25),
      inset 0 0 30px rgba(0,0,0,0.45);
    animation: pulseRing 2.4s ease-in-out infinite;
  }}
  .bulb {{
    position: absolute;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #ffd76b;
    box-shadow: 0 0 12px #ffd76b;
    top: 50%;
    left: 50%;
    transform-origin: 0 0;
    animation: blink 1.2s ease-in-out infinite alternate;
  }}
  .pointer {{
    position: absolute;
    top: -8px;
    left: 50%;
    transform: translateX(-50%);
    width: 0;
    height: 0;
    border-left: 18px solid transparent;
    border-right: 18px solid transparent;
    border-top: 34px solid #d4af37;
    filter: drop-shadow(0 6px 10px rgba(0,0,0,0.55));
    z-index: 20;
  }}
  .pointer-cap {{
    position: absolute;
    top: 24px;
    left: 50%;
    transform: translateX(-50%);
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: linear-gradient(145deg, #f7e6a7, #b8891d);
    border: 2px solid #fff2c7;
    z-index: 21;
  }}
  #wheel {{
    position: absolute;
    inset: 18px;
    border-radius: 50%;
    overflow: hidden;
    border: 6px solid #1d3b2a;
    box-shadow:
      inset 0 0 40px rgba(0,0,0,0.55),
      0 18px 50px rgba(0,0,0,0.45);
    transition: transform 0.1s linear;
    will-change: transform;
  }}
  .slice {{
    position: absolute;
    top: 50%;
    left: 50%;
    width: 50%;
    height: 50%;
    transform-origin: 0% 0%;
    overflow: hidden;
    clip-path: polygon(0 0, 100% 0, 0 100%);
  }}
  .slice-bg {{
    position: absolute;
    inset: 0;
    opacity: 0.95;
  }}
  .slice-content {{
    position: absolute;
    left: 58%;
    top: 18%;
    transform: rotate(18deg);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    width: 72px;
    text-align: center;
  }}
  .avatar {{
    width: 34px;
    height: 34px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid rgba(255,255,255,0.85);
    box-shadow: 0 4px 10px rgba(0,0,0,0.35);
    background: #234434;
  }}
  .avatar-fallback {{
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    font-size: 0.8rem;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(145deg, #2f6a4d, #17402d);
    border: 2px solid rgba(255,255,255,0.85);
  }}
  .name {{
    font-size: 0.58rem;
    line-height: 1.1;
    font-weight: 600;
    color: #fff;
    text-shadow: 0 1px 3px rgba(0,0,0,0.65);
    max-width: 72px;
    word-break: break-word;
  }}
  .hub {{
    position: absolute;
    inset: 34%;
    border-radius: 50%;
    background: radial-gradient(circle, #f6e7b8 0%, #c89b2b 45%, #7a5a14 100%);
    border: 4px solid #fff4cc;
    box-shadow: 0 0 24px rgba(212,175,55,0.55);
    display: grid;
    place-items: center;
    z-index: 10;
    text-align: center;
    padding: 8px;
  }}
  .hub-title {{
    font-family: 'Cinzel', serif;
    font-size: 0.72rem;
    font-weight: 900;
    color: #2d1f05;
    letter-spacing: 0.08em;
    line-height: 1.2;
  }}
  .hub-sub {{
    font-size: 0.55rem;
    color: #4a3508;
    margin-top: 2px;
  }}
  .spin-btn {{
    margin-top: 22px;
    z-index: 5;
    border: none;
    padding: 14px 42px;
    border-radius: 999px;
    font-family: 'Cinzel', serif;
    font-size: 1rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #1d1404;
    background: linear-gradient(135deg, #f8e7b0 0%, #d4af37 45%, #9f7c16 100%);
    box-shadow:
      0 10px 30px rgba(212,175,55,0.35),
      inset 0 1px 0 rgba(255,255,255,0.55);
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }}
  .spin-btn:hover {{ transform: translateY(-2px) scale(1.02); }}
  .spin-btn:disabled {{
    opacity: 0.55;
    cursor: not-allowed;
    transform: none;
  }}
  .status {{
    margin-top: 14px;
    min-height: 24px;
    font-size: 0.95rem;
    letter-spacing: 0.06em;
    z-index: 5;
    color: #d8c89a;
  }}
  .winner-overlay {{
    position: fixed;
    inset: 0;
    background: rgba(2,8,5,0.82);
    backdrop-filter: blur(8px);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 100;
    animation: fadeIn 0.8s ease forwards;
  }}
  .winner-card {{
    width: min(92vw, 420px);
    border-radius: 24px;
    padding: 28px 24px 24px;
    background: linear-gradient(160deg, rgba(24,58,40,0.95), rgba(8,20,14,0.98));
    border: 1px solid rgba(212,175,55,0.45);
    box-shadow: 0 30px 80px rgba(0,0,0,0.55);
    text-align: center;
    transform: scale(0.88);
    animation: popIn 0.9s cubic-bezier(.2,1.1,.2,1) forwards;
  }}
  .winner-label {{
    font-family: 'Cinzel', serif;
    color: #d4af37;
    letter-spacing: 0.22em;
    font-size: 0.85rem;
    text-transform: uppercase;
  }}
  .winner-avatar {{
    width: 110px;
    height: 110px;
    border-radius: 50%;
    object-fit: cover;
    margin: 18px auto 12px;
    border: 4px solid #d4af37;
    box-shadow: 0 0 30px rgba(212,175,55,0.45);
  }}
  .winner-name {{
    font-family: 'Cinzel', serif;
    font-size: 1.55rem;
    margin-bottom: 8px;
    color: #fff8e7;
  }}
  .winner-comment {{
    font-size: 0.92rem;
    line-height: 1.5;
    opacity: 0.85;
    margin-bottom: 12px;
    padding: 0 8px;
  }}
  .winner-link a {{
    color: #8fd6ad;
    text-decoration: none;
    font-weight: 600;
  }}
  .confetti {{
    position: fixed;
    width: 8px;
    height: 14px;
    top: -20px;
    opacity: 0.9;
    z-index: 120;
    animation: fall linear forwards;
  }}
  @keyframes pulseRing {{
    0%, 100% {{ box-shadow: 0 0 30px rgba(212,175,55,0.2), inset 0 0 30px rgba(0,0,0,0.45); }}
    50% {{ box-shadow: 0 0 46px rgba(212,175,55,0.42), inset 0 0 30px rgba(0,0,0,0.45); }}
  }}
  @keyframes blink {{
    from {{ opacity: 0.45; }}
    to {{ opacity: 1; }}
  }}
  @keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
  }}
  @keyframes popIn {{
    to {{ transform: scale(1); }}
  }}
  @keyframes fall {{
    to {{ transform: translateY(110vh) rotate(720deg); opacity: 0; }}
  }}
</style>
</head>
<body>
  <div class="stage">
    <div class="ambient"></div>
    <div class="title">Green Avenue</div>
    <div class="subtitle">Property Draw · {len(contestants)} Finalists</div>

    <div class="wheel-wrap">
      <div class="outer-ring" id="outerRing"></div>
      <div class="pointer"></div>
      <div class="pointer-cap"></div>
      <div id="wheel"></div>
      <div class="hub">
        <div class="hub-title">LIVE<br>ROULETTE</div>
        <div class="hub-sub">Spin to Win</div>
      </div>
    </div>

    <button class="spin-btn" id="spinBtn">Spin the Wheel</button>
    <div class="status" id="status">Press spin when you are ready...</div>
  </div>

  <div class="winner-overlay" id="winnerOverlay">
    <div class="winner-card" id="winnerCard"></div>
  </div>

  <script>
    const data = {payload};
    const contestants = data.contestants || [];
    const winnerIndex = data.winnerIndex;
    const colors = ["#1f5a3d", "#2a6e4c", "#174734", "#2f7d57", "#1a4d36", "#256b49"];
    const wheel = document.getElementById("wheel");
    const statusEl = document.getElementById("status");
    const spinBtn = document.getElementById("spinBtn");
    const outerRing = document.getElementById("outerRing");
    const overlay = document.getElementById("winnerOverlay");
    const winnerCard = document.getElementById("winnerCard");

    let currentRotation = 0;
    let spinning = false;

    function escapeHtml(value) {{
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }}

    function initials(name) {{
      return name.trim().charAt(0).toUpperCase() || "?";
    }}

    function buildBulbs() {{
      const total = 24;
      for (let i = 0; i < total; i++) {{
        const bulb = document.createElement("div");
        bulb.className = "bulb";
        const angle = (360 / total) * i;
        bulb.style.transform = `rotate(${{angle}}deg) translate(248px, -5px)`;
        bulb.style.animationDelay = `${{(i % 5) * 0.15}}s`;
        outerRing.appendChild(bulb);
      }}
    }}

    function buildWheel() {{
      const n = contestants.length;
      const sliceAngle = 360 / n;
      contestants.forEach((contestant, index) => {{
        const slice = document.createElement("div");
        slice.className = "slice";
        slice.style.transform = `rotate(${{index * sliceAngle}}deg) skewY(-${{90 - sliceAngle}}deg)`;

        const bg = document.createElement("div");
        bg.className = "slice-bg";
        bg.style.background = colors[index % colors.length];
        slice.appendChild(bg);

        const content = document.createElement("div");
        content.className = "slice-content";
        content.style.transform = `skewY(${{90 - sliceAngle}}deg) rotate(${{sliceAngle / 2}}deg)`;

        if (contestant.avatar_url) {{
          const img = document.createElement("img");
          img.className = "avatar";
          img.src = contestant.avatar_url;
          img.alt = contestant.username;
          img.onerror = () => {{
            const fallback = document.createElement("div");
            fallback.className = "avatar-fallback";
            fallback.textContent = initials(contestant.username);
            img.replaceWith(fallback);
          }};
          content.appendChild(img);
        }} else {{
          const fallback = document.createElement("div");
          fallback.className = "avatar-fallback";
          fallback.textContent = initials(contestant.username);
          content.appendChild(fallback);
        }}

        const name = document.createElement("div");
        name.className = "name";
        name.textContent = contestant.username;
        content.appendChild(name);

        slice.appendChild(content);
        wheel.appendChild(slice);
      }});
    }}

    function launchConfetti() {{
      const colors = ["#d4af37", "#f8f4e8", "#4caf79", "#ff6b6b", "#8fd6ad"];
      for (let i = 0; i < 80; i++) {{
        const piece = document.createElement("div");
        piece.className = "confetti";
        piece.style.left = Math.random() * 100 + "vw";
        piece.style.background = colors[i % colors.length];
        piece.style.animationDuration = (2 + Math.random() * 2.5) + "s";
        piece.style.animationDelay = (Math.random() * 0.8) + "s";
        document.body.appendChild(piece);
        setTimeout(() => piece.remove(), 5000);
      }}
    }}

    function showWinner() {{
      const winner = contestants[winnerIndex];
      const avatarHtml = winner.avatar_url
        ? `<img class="winner-avatar" src="${{escapeHtml(winner.avatar_url)}}" alt="${{escapeHtml(winner.username)}}" />`
        : `<div class="winner-avatar" style="display:grid;place-items:center;font-size:2.4rem;background:#2f6a4d;">${{escapeHtml(initials(winner.username))}}</div>`;

      winnerCard.innerHTML = `
        <div class="winner-label">Grand Prize Winner</div>
        ${{avatarHtml}}
        <div class="winner-name">${{escapeHtml(winner.username)}}</div>
        <div class="winner-comment">"${{escapeHtml(winner.comment)}}"</div>
        <div class="winner-link">${{winner.profile_url ? `<a href="${{escapeHtml(winner.profile_url)}}" target="_blank" rel="noopener">View ${{escapeHtml(winner.source)}} Profile</a>` : ""}}</div>
      `;
      overlay.style.display = "flex";
      launchConfetti();
    }}

    function spinWheel() {{
      if (spinning || !contestants.length) return;
      spinning = true;
      spinBtn.disabled = true;
      overlay.style.display = "none";
      statusEl.textContent = "The wheel is spinning...";

      const n = contestants.length;
      const sliceAngle = 360 / n;
      const extraSpins = 7 + Math.floor(Math.random() * 3);
      const target = (extraSpins * 360) + (360 - (winnerIndex * sliceAngle) - (sliceAngle / 2));
      const start = currentRotation;
      const delta = target - start;
      const duration = 7000 + Math.random() * 1500;
      const startTime = performance.now();

      function frame(now) {{
        const t = Math.min((now - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - t, 4);
        const angle = start + (delta * eased);
        wheel.style.transform = `rotate(${{angle}}deg)`;
        if (t < 1) {{
          requestAnimationFrame(frame);
        }} else {{
          currentRotation = angle % 360;
          spinning = false;
          statusEl.textContent = "We have a winner!";
          setTimeout(showWinner, 700);
        }}
      }}
      requestAnimationFrame(frame);
    }}

    buildBulbs();
    buildWheel();
    spinBtn.addEventListener("click", spinWheel);

    setTimeout(() => {{
      statusEl.textContent = "Ready. Tap SPIN THE WHEEL";
      spinBtn.focus();
    }}, 500);
  </script>
</body>
</html>
"""
    components.html(html, height=820, scrolling=False)
