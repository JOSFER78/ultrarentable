const http = require("http");

// Test combining 1 Crypto (BTC) + 1 Future (NQ) + 1 Commodity (GC Oro) in Fondeo/Multi-Market
const payload = JSON.stringify({
  candidate_ids: ["UR_FONDEO_NQ_15M", "UR_FONDEO_GC_1H", "UR_FONDEO_EURUSD_1H"],
  route: "FONDEO",
  total_capital_usd: 50000.0
});

const req = http.request(
  {
    hostname: "127.0.0.1",
    port: 8000,
    path: "/api/v2/portfolio/synthesize",
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Content-Length": Buffer.byteLength(payload)
    }
  },
  (res) => {
    let data = "";
    res.on("data", (chunk) => (data += chunk));
    res.on("end", () => {
      console.log(`HTTP Status: ${res.statusCode}`);
      try {
        const json = JSON.parse(data);
        console.log("\n=======================================================");
        console.log(`🧬 META-PORTAFOLIO SINTETIZADO: ${json.name} (${json.ensemble_id})`);
        console.log(`🏆 Veredicto de Consenso: ${json.consensus_verdict}`);
        console.log(`🎯 Puntuación del Comité: ${json.consensus_score}/100`);
        console.log(`📈 ROI Anual Combinado: +${json.combined_annualized_roi_pct}%`);
        console.log(`🛡️ Max Drawdown Comprimido: ${json.combined_max_dd_pct}%`);
        console.log(`⚡ Sharpe Ratio: ${json.combined_sharpe_ratio}`);
        console.log(`📊 Diversification Ratio: ${json.diversification_ratio}x`);
        console.log(`🔗 Correlación Cruzada Promedio: ${json.avg_cross_correlation}`);
        console.log("=======================================================\n");
        
        console.log("⚖️ Ponderación Paridad de Riesgo (ERC):");
        json.components?.forEach((c) => {
          console.log(` - ${c.symbol} (${c.strategy_id}): ${c.weight_pct}% | Rol: ${c.role_in_ensemble} | DD: ${c.individual_max_dd_pct}%`);
        });

        console.log("\n💬 DELIBERACIÓN SEMÁNTICA DEL COMITÉ DE 5 AGENTES:");
        json.agents_debate?.forEach((agent) => {
          console.log(`\n▶ [${agent.agent_name}] -> Voto: ${agent.vote}`);
          console.log(`  Tesis: "${agent.thesis}"`);
          agent.findings?.forEach((f) => console.log(`   • ${f}`));
        });
      } catch (e) {
        console.log("Raw output:", data);
      }
    });
  }
);

req.on("error", (e) => console.error("Error:", e.message));
req.write(payload);
req.end();
