const rates = document.querySelector("#rates");
const chart = document.querySelector("#chart");
const updated = document.querySelector("#updated");
const SERIES_COLORS = ["#75d7eb", "#45a5ff", "#70d7b1", "#f2c66d"];
const SVG_NS = "http://www.w3.org/2000/svg";
const dayName = new Intl.DateTimeFormat("es-PY", { weekday: "short", timeZone: "UTC" });
const dayNumber = new Intl.DateTimeFormat("es-PY", { day: "2-digit", month: "2-digit", timeZone: "UTC" });
const money = new Intl.NumberFormat("es-PY", { maximumFractionDigits: 0 });
const date = new Intl.DateTimeFormat("es-PY", {
  dateStyle: "long",
  timeZone: "America/Asuncion",
});
const time = new Intl.DateTimeFormat("es-PY", {
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "America/Asuncion",
});

function validQuote(quote) {
  return quote && typeof quote.id === "string" &&
    typeof quote.name === "string" && typeof quote.url === "string" &&
    (quote.sale === null ||
      (typeof quote.sale === "number" && Number.isFinite(quote.sale) && quote.sale > 0));
}

function createCard(quote) {
  const card = document.createElement("article");
  card.className = "rate-card";
  const provider = document.createElement("div");
  provider.className = "provider";
  const name = document.createElement("strong");
  name.className = "provider-name";
  name.textContent = quote.name;
  const source = document.createElement("a");
  source.className = "source";
  source.href = quote.url;
  source.target = "_blank";
  source.rel = "noopener noreferrer";
  source.textContent = "Fuente oficial";
  provider.append(name, source);

  const quoteSide = document.createElement("div");
  quoteSide.className = "quote";
  const label = document.createElement("span");
  label.className = "quote-label";
  label.textContent = "VENTA";
  const value = document.createElement("span");
  if (quote.sale === null) {
    value.className = "unavailable";
    value.textContent = quote.status === "stale"
      ? "Dato anterior · verificar"
      : "Sin dato disponible";
  } else {
    value.className = "quote-value";
    value.textContent = `Gs. ${money.format(quote.sale)}`;
  }
  quoteSide.append(label, value);
  card.append(provider, quoteSide);
  return card;
}

function parseDay(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  return match
    ? new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])))
    : null;
}

function svgNode(name, attributes) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
  return node;
}

function stepFor(range) {
  const raw = range / 3;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const normalized = raw / magnitude;
  return (normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10) * magnitude;
}

function historySeries(quotes, history) {
  const days = history
    .filter((entry) => entry && typeof entry.date === "string" &&
      entry.quotes && typeof entry.quotes === "object")
    .map((entry) => {
      const parsed = parseDay(entry.date);
      return parsed ? { date: parsed, quotes: entry.quotes } : null;
    })
    .filter(Boolean)
    .sort((a, b) => a.date - b.date)
    .slice(-7);

  const series = quotes
    .map((quote, index) => ({
      name: quote.name,
      color: SERIES_COLORS[index % SERIES_COLORS.length],
      points: days
        .map((day, position) => ({ position, value: day.quotes[quote.id] }))
        .filter((point) => typeof point.value === "number" &&
          Number.isFinite(point.value) && point.value > 0),
    }))
    .filter((item) => item.points.length > 0);

  return { days, series };
}

function createHistoryChart(data) {
  const { days, series } = historySeries(
    data.quotes,
    Array.isArray(data.history) ? data.history : [],
  );

  if (!series.length) {
    const message = document.createElement("p");
    message.className = "message";
    message.textContent = "El histórico se irá completando con las actualizaciones diarias.";
    return message;
  }

  const width = 720;
  const height = 260;
  const pad = { top: 18, right: 18, bottom: 36, left: 64 };
  const innerWidth = width - pad.left - pad.right;
  const innerHeight = height - pad.top - pad.bottom;
  const values = series.flatMap((item) => item.points.map((point) => point.value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const step = stepFor(Math.max(max - min, 20));
  const yMin = max === min ? min - step : Math.floor((min - step / 2) / step) * step;
  const yMax = max === min ? max + step : Math.ceil((max + step / 2) / step) * step;
  const xFor = (position) => days.length === 1
    ? pad.left + innerWidth / 2
    : pad.left + (innerWidth * position) / (days.length - 1);
  const yFor = (value) => pad.top + innerHeight - ((value - yMin) / (yMax - yMin)) * innerHeight;

  const svg = svgNode("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": `Precio de venta del dólar en los últimos ${days.length} días`,
  });

  for (let value = yMin; value <= yMax; value += step) {
    const y = yFor(value);
    svg.append(svgNode("line", {
      x1: pad.left, x2: width - pad.right, y1: y, y2: y, class: "chart-grid",
    }));
    const label = svgNode("text", {
      x: pad.left - 10, y: y + 4, class: "chart-axis", "text-anchor": "end",
    });
    label.textContent = money.format(value);
    svg.append(label);
  }

  days.forEach((day, position) => {
    const label = svgNode("text", {
      x: xFor(position), y: height - 12, class: "chart-axis", "text-anchor": "middle",
    });
    label.textContent = `${dayName.format(day.date)} ${dayNumber.format(day.date)}`;
    svg.append(label);
  });

  for (const item of series) {
    const path = item.points
      .map((point, index) => `${index === 0 ? "M" : "L"}${xFor(point.position)} ${yFor(point.value)}`)
      .join(" ");
    svg.append(svgNode("path", {
      d: path,
      fill: "none",
      stroke: item.color,
      "stroke-width": 2.2,
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
    }));

    for (const point of item.points) {
      const dot = svgNode("circle", {
        cx: xFor(point.position), cy: yFor(point.value), r: 3.6, fill: item.color,
      });
      const title = svgNode("title", {});
      title.textContent = `${item.name} · ${dayNumber.format(days[point.position].date)}: Gs. ${money.format(point.value)}`;
      dot.append(title);
      svg.append(dot);
    }
  }

  const wrapper = document.createElement("div");
  const legend = document.createElement("div");
  legend.className = "chart-legend";
  for (const item of series) {
    const entry = document.createElement("span");
    const color = document.createElement("i");
    color.style.background = item.color;
    const name = document.createElement("span");
    name.textContent = item.name;
    entry.append(color, name);
    legend.append(entry);
  }
  wrapper.append(svg, legend);
  return wrapper;
}

async function load() {
  try {
    const response = await fetch("./data/cotizaciones.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`No se pudo leer el archivo de datos (HTTP ${response.status}).`);
    const data = await response.json();
    if (!data || !Array.isArray(data.quotes) || data.quotes.length < 2 || !data.quotes.every(validQuote)) {
      throw new Error("El archivo de cotizaciones tiene un formato inesperado.");
    }

    rates.replaceChildren(...data.quotes.map(createCard));
    chart.replaceChildren(createHistoryChart(data));
    const dateValue = data.updatedAt ? new Date(data.updatedAt) : null;
    updated.textContent = dateValue && !Number.isNaN(dateValue.getTime())
      ? `Consulta automática: ${date.format(dateValue)} · ${time.format(dateValue)}`
      : "Las fuentes automáticas aún no publicaron sus datos.";
  } catch (error) {
    const message = document.createElement("p");
    message.className = "message error";
    message.textContent = error instanceof Error ? error.message : "No se pudieron cargar las cotizaciones.";
    rates.replaceChildren(message);
    chart.replaceChildren(message.cloneNode(true));
    updated.textContent = "";
  } finally {
    rates.setAttribute("aria-busy", "false");
  }
}

load();
