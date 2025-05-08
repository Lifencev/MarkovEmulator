document.addEventListener("DOMContentLoaded", () => {

  console.log("main.js loaded");

  const form   = document.getElementById("run-form");
  const output = document.getElementById("output");
  const trace  = document.getElementById("trace");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    output.textContent = "…running…";
    trace.innerHTML = "";
    output.classList.remove("error");

    try {
      const runRes = await fetch("/api/run", {
        method : "POST",
        headers: { "Content-Type": "application/json" },
        body   : JSON.stringify({
          word : document.getElementById("word").value,
          rules: document.getElementById("rules").value
        })
      });

      const runData = await runRes.json();
      if (!runRes.ok) throw new Error(runData.error || runRes.statusText);

      output.textContent = `${runData.output}   (steps: ${runData.steps})`;
      output.classList.remove("error");

      runData.trace.forEach(t => {
        const li = document.createElement("li");
        li.textContent = `step ${t.step}: ${t.word} (rule "${t.rule}")`;
        trace.appendChild(li);
      });

      let longest = { step: runData.steps, word: runData.output };
      runData.trace.forEach(t => {
        if (t.word.length > longest.word.length) {
          longest = t;
        }
      });
      const longestLength = longest.word.length;
      output.textContent +=
        `\n\nlongest word: ${longest.word} (step ${longest.step}, length ${longestLength})`;

      const timeRes = await fetch("/api/time", {
        method : "POST",
        headers: { "Content-Type": "application/json" },
        body   : JSON.stringify({
          word  : document.getElementById("word").value,
          rules : document.getElementById("rules").value
        })
      });

      if (timeRes.ok) {
        const timeData = await timeRes.json();
        const timeSampleLine = (timeData.samples || [])
          .map(([k, steps]) => `×${k}→${steps}`)
          .join(", ");

        output.textContent +=
          `\n\ntime complexity ≈ ${timeData.big_o}\n` +
          `samples: ${timeSampleLine}`;
      } else {
        console.warn("/api/time error", await timeRes.text());
      }

      const spaceRes = await fetch("/api/space", {
        method : "POST",
        headers: { "Content-Type": "application/json" },
        body   : JSON.stringify({
          word  : document.getElementById("word").value,
          rules : document.getElementById("rules").value
        })
      });

      if (spaceRes.ok) {
        const spaceData = await spaceRes.json();
        const spaceSampleLine = (spaceData.samples || [])
          .map(([k, s]) => `×${k}→${s}`)
          .join(", ");

        output.textContent +=
          `\n\nspace complexity ≈ ${spaceData.big_o || "?"}\n` +
          `samples: ${spaceSampleLine}`;
      } else {
        console.warn("/api/space error", await spaceRes.text());
      }

    } catch (err) {
      output.textContent = err.message;
      output.classList.add("error");
    }
  });
});
