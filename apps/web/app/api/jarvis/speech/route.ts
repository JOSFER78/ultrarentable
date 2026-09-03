import { NextResponse } from "next/server";
import https from "https";

const OMNIROUTE_SPEECH_URL = "https://143-47-35-167.sslip.io/pro/omniroute/v1/audio/speech";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const text: string = (body.text || "").trim();
    const voiceModel: string = body.model || "deepgram/aura-2-alvaro-es";

    if (!text) {
      return NextResponse.json({ error: "Texto vacío" }, { status: 400 });
    }

    // Limpieza de Markdown antes de enviar a Deepgram
    const cleanText = text
      .replace(/```[\s\S]*?```/g, ", bloque de código omitido, ")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/!\[.*?\]\(.*?\)/g, "")
      .replace(/\[([^\]]+)\]\(.*?\)/g, "$1")
      .replace(/https?:\/\/\S+/gi, "un enlace")
      .replace(/[a-f0-9]{32,64}/gi, "")
      .replace(/[#*_~>]/g, "")
      .replace(/\s+/g, " ")
      .trim();

    const voiceCode = voiceModel.replace("deepgram/aura-2-", "").replace("-es", "");

    const payload = JSON.stringify({
      model: voiceModel,
      input: cleanText,
      voice: voiceCode,
    });

    // Petición https con agent que ignora certificados autofirmados
    const audioBuffer = await new Promise<Buffer>((resolve, reject) => {
      const agent = new https.Agent({
        rejectUnauthorized: false,
      });

      const options = {
        method: "POST",
        agent,
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(payload),
        },
      };

      const request = https.request(OMNIROUTE_SPEECH_URL, options, (res) => {
        if (res.statusCode !== 200) {
          let errBody = "";
          res.on("data", (chunk) => (errBody += chunk));
          res.on("end", () => {
            reject(
              new Error(
                `Deepgram TTS falló con HTTP ${res.statusCode}: ${errBody}`
              )
            );
          });
          return;
        }

        const chunks: Buffer[] = [];
        res.on("data", (chunk) => chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)));
        res.on("end", () => resolve(Buffer.concat(chunks)));
      });

      request.on("error", (err) => reject(err));
      request.write(payload);
      request.end();
    });

    return new NextResponse(audioBuffer, {
      status: 200,
      headers: {
        "Content-Type": "audio/mpeg",
        "Cache-Control": "public, max-age=86400",
      },
    });
  } catch (err: any) {
    console.error("Error en /api/jarvis/speech:", err);
    return NextResponse.json(
      { error: err.message || "Error sintetizando voz en Deepgram" },
      { status: 500 }
    );
  }
}
