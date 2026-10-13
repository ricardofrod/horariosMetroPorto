// Próximo metro Varziela <-> NorteShopping (Linha B) para o widget pequeno.
// 1) Troca USER e REPO pelo teu utilizador e repositório do GitHub.
// 2) A função proximoMetro() é JavaScript puro e está testada em Node.
//    A ligação aos blocos de texto do Widgy (ler o resultado e pô-lo nas camadas)
//    depende da API de scripts do Widgy: adapta apenas a última secção.

const URL = "https://raw.githubusercontent.com/ricardofrod/horariosMetroPorto/main/horarios.json";

function iso(d) {
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
}

function tipoDia(H, d) {
  if (H.feriados_como_domingo.includes(iso(d))) return "domingo_feriado";
  const w = d.getDay();
  return w === 0 ? "domingo_feriado" : w === 6 ? "sabado" : "util";
}

function hhmm(m) {
  return String(Math.floor(m / 60) % 24).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0");
}

// sentido: "varziela_norteshopping" (para o Porto) ou "norteshopping_varziela" (para a Póvoa)
function proximoMetro(H, sentido, agora) {
  const hoje = iso(agora);
  if (hoje < H.valido_de || hoje > H.valido_ate) return { expirado: true };
  const ontem = new Date(agora);
  ontem.setDate(ontem.getDate() - 1);
  const m = agora.getHours() * 60 + agora.getMinutes();
  const cand = [];
  for (const [dia, off] of [[ontem, -1440], [agora, 0]]) {
    for (const [dep, , x] of H.sentidos[sentido][tipoDia(H, dia)]) cand.push({ dep: dep + off, x });
  }
  const seg = cand.filter((c) => c.dep >= m).sort((a, b) => a.dep - b.dep)[0];
  if (!seg) return { semMais: true };
  return { hora: hhmm(seg.dep), faltam: seg.dep - m, expresso: seg.x === "x" };
}

// ---- Ligação ao Widgy: adapta esta parte à API de scripts do Widgy ----
async function carregar() {
  const r = await fetch(URL);
  return await r.json();
}

if (typeof module !== "undefined") module.exports = { proximoMetro, tipoDia };
