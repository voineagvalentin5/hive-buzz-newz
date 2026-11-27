const dashboard = document.querySelector("#global-state");
const trend = dashboard?.querySelector(".trend-panel");
const archive = dashboard?.querySelector(".archive-panel");
const edition = dashboard?.querySelector(".edition-reading");
const chips = [...(archive?.querySelectorAll("[data-reading]") ?? [])];
let selected = chips.find(chip => chip.hasAttribute("aria-current")) ?? chips.at(-1);

if (trend && edition && selected) {
  const ranges = trend.querySelector(".trend-ranges");
  const buttons = [...ranges.querySelectorAll("button")];
  const all = trend.querySelector('[data-chart-view="all"]');
  let view = all;

  function highlight() {
    const point = [...view.querySelectorAll("[data-point]")]
      .find(dot => dot.dataset.point === selected.dataset.reading);
    const callout = view.querySelector(".trend-callout");
    callout.classList.toggle("out-of-view", !point);
    if (!point) return;
    const x = point.getAttribute("cx");
    const y = Number(point.getAttribute("cy"));
    const labelOffset = y < 57 ? 56 : 0;
    callout.setAttribute("transform", `translate(${x} ${y})`);
    callout.querySelector("path").setAttribute("d", `M0 ${23 - y}V${258 - y}`);
    callout.querySelector("rect").setAttribute("y", String(-36 + labelOffset));
    const label = callout.querySelector("text");
    label.setAttribute("y", String(-19 + labelOffset));
    label.textContent = selected.dataset.score;
  }

  function switchRange(range) {
    if (view !== all) view.remove();
    all.hidden = range !== "all";
    view = all;
    if (all.hidden) {
      const template = trend.querySelector(`template[data-range="${range}"]`);
      view = template.content.firstElementChild.cloneNode(true);
      view.hidden = false;
      all.after(view);
    }
    buttons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.setRange === range)));
    highlight();
  }

  function showReading(chip) {
    selected.removeAttribute("aria-current");
    selected = chip;
    chip.setAttribute("aria-current", "date");
    const { day, basis, score, level } = chip.dataset;
    const published = basis === "Published edition";
    edition.querySelector("[data-edition-date]").textContent = day;
    edition.querySelector("[data-edition-basis]").textContent = ` · ${basis}`;
    edition.querySelector("[data-edition-score]").textContent = `${score} / 100 · ${level}`;
    edition.querySelector("[data-edition-note]").textContent = published
      ? "This reading is based on a published Hive Buzz Newz edition."
      : "This reading was reconstructed for a day without an edition.";
    const editionLink = edition.querySelector("[data-edition-link]");
    editionLink.hidden = !published;
    if (published) editionLink.href = chip.href;
    edition.open = true;
    if (!view.querySelector(`[data-point="${chip.dataset.reading}"]`)) switchRange("all");
    else highlight();
  }

  ranges.hidden = false;
  ranges.addEventListener("click", event => {
    const button = event.target.closest("[data-set-range]");
    if (button) switchRange(button.dataset.setRange);
  });

  archive.addEventListener("click", event => {
    const chip = event.target.closest("[data-reading]");
    if (!chip || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    showReading(chip);
    edition.querySelector("summary").focus({ preventScroll: true });
    edition.scrollIntoView({ block: "nearest" });
  });

  trend.addEventListener("click", event => {
    const point = event.target.closest("[data-point]");
    const chip = point && chips.find(item => item.dataset.reading === point.dataset.point);
    if (chip) showReading(chip);
  });

  if (chips.some(chip => chip.hasAttribute("aria-current"))) highlight();
}

const strip = archive?.querySelector(".archive-chips");
if (strip) {
  const arrows = [...archive.querySelectorAll("[data-scroll]")];
  let positioned = false;

  function updateArrows() {
    const maximum = strip.scrollWidth - strip.clientWidth;
    arrows[0].disabled = strip.scrollLeft < 2;
    arrows[1].disabled = strip.scrollLeft > maximum - 2;
  }

  function sizeStrip() {
    arrows.forEach(arrow => { arrow.hidden = true; });
    if (strip.clientWidth && strip.scrollWidth > strip.clientWidth + 1) {
      arrows.forEach(arrow => { arrow.hidden = false; });
    }
    if (strip.clientWidth && !positioned) {
      strip.scrollLeft = strip.scrollWidth;
      positioned = true;
    }
    updateArrows();
  }

  arrows.forEach(arrow => arrow.addEventListener("click", () => {
    strip.scrollBy({ left: Number(arrow.dataset.scroll) * strip.clientWidth * 0.8 });
  }));
  strip.addEventListener("scroll", updateArrows, { passive: true });
  archive.addEventListener("toggle", sizeStrip);
  window.addEventListener("resize", sizeStrip);
  sizeStrip();
}

const nav = [...document.querySelectorAll(".edition-masthead nav a")];
function revealAnchor() {
  const hash = location.hash;
  const target = document.getElementById(hash.slice(1));
  for (let parent = target; parent; parent = parent.parentElement) {
    if (parent instanceof HTMLDetailsElement) parent.open = true;
  }
  const active = nav.find(link => link.hash === hash) ?? nav[0];
  nav.forEach(link => {
    if (link === active) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });
}

document.addEventListener("click", event => {
  const link = event.target.closest('a[href^="#"]');
  const target = link && document.getElementById(link.hash.slice(1));
  for (let parent = target; parent; parent = parent.parentElement) {
    if (parent instanceof HTMLDetailsElement) parent.open = true;
  }
});
window.addEventListener("hashchange", revealAnchor);
revealAnchor();
