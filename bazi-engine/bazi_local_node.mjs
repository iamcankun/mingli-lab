import { readFileSync } from "node:fs";
import { getBaziDetail } from "bazi-mcp";

function cleanArgs(input) {
  if (!input.solarDatetime) {
    throw new Error("solarDatetime is required");
  }
  return {
    solarDatetime: String(input.solarDatetime),
    gender: Number(input.gender) === 0 ? 0 : 1,
    eightCharProviderSect: Number(input.eightCharProviderSect) === 2 ? 2 : 1,
  };
}

try {
  const raw = readFileSync(0, "utf8").trim();
  const input = raw ? JSON.parse(raw) : {};
  if (input?.mode === "batch") {
    const items = Array.isArray(input.items) ? input.items : [];
    const data = [];
    for (const item of items) {
      data.push({ input: cleanArgs(item), chart: await getBaziDetail(cleanArgs(item)) });
    }
    process.stdout.write(JSON.stringify({ success: true, data }));
  } else {
    const data = await getBaziDetail(cleanArgs(input));
    process.stdout.write(JSON.stringify({ success: true, data }));
  }
} catch (error) {
  process.stderr.write(
    JSON.stringify({
      success: false,
      error_type: error?.name || "Error",
      error: error?.message || String(error),
    }),
  );
  process.exit(1);
}
