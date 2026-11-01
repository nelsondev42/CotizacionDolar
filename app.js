const rates = document.querySelector("#rates");
const updated = document.querySelector("#updated");
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

async function load() {
  try {
    const response = await fetch("./data/cotizaciones.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`No se pudo leer el archivo de datos (HTTP ${response.status}).`);
    const data = await response.json();
    if (!data || !Array.isArray(data.quotes) || data.quotes.length < 2 || !data.quotes.every(validQuote)) {
      throw new Error("El archivo de cotizaciones tiene un formato inesperado.");
    }

    rates.replaceChildren(...data.quotes.map(createCard));
    const dateValue = data.updatedAt ? new Date(data.updatedAt) : null;
    updated.textContent = dateValue && !Number.isNaN(dateValue.getTime())
      ? `Consulta automática: ${date.format(dateValue)} · ${time.format(dateValue)}`
      : "Las fuentes automáticas aún no publicaron sus datos.";
  } catch (error) {
    const message = document.createElement("p");
    message.className = "message error";
    message.textContent = error instanceof Error ? error.message : "No se pudieron cargar las cotizaciones.";
    rates.replaceChildren(message);
    updated.textContent = "";
  } finally {
    rates.setAttribute("aria-busy", "false");
  }
}

load();
