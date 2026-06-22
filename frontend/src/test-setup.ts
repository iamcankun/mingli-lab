import "@testing-library/jest-dom/vitest";

globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
  const url = String(input);
  const payload = url.includes("/api/settings/model")
    ? { base_url: "", model_id: "", temperature: 0.2, max_tokens: 1600, top_p: 1, api_key_configured: false }
    : { items: [] };
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}) as typeof fetch;
