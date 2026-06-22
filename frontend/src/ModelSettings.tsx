import { FormEvent, useEffect, useState } from "react";
import { api, type ModelSettings as Settings } from "./api";

const defaults: Settings = { base_url: "", model_id: "", temperature: .2, max_tokens: 1600, top_p: 1, api_key_configured: false };

export function ModelSettings() {
  const [settings, setSettings] = useState(defaults);
  const [message, setMessage] = useState("");
  useEffect(() => { api.getModel().then(setSettings).catch(() => undefined); }, []);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const saved = await api.saveModel({
      ...settings,
      base_url: String(data.get("base_url")),
      model_id: String(data.get("model_id")),
      api_key: String(data.get("api_key")),
      temperature: Number(data.get("temperature")),
      max_tokens: Number(data.get("max_tokens")),
      top_p: Number(data.get("top_p")),
    });
    setSettings(saved); setMessage("配置已加密保存");
  }
  return (
    <section className="settings-page panel">
      <div className="section-heading"><div><h2>模型设置</h2><p>当前推理模型 · OpenAI 兼容协议</p></div></div>
      <form className="settings-form" onSubmit={save}>
        <label>API Base URL<input name="base_url" value={settings.base_url} onChange={(e) => setSettings({...settings, base_url:e.target.value})} placeholder="https://api.example.com/v1" required/></label>
        <label>模型 ID<input name="model_id" value={settings.model_id} onChange={(e) => setSettings({...settings, model_id:e.target.value})} placeholder="deepseek-chat" required/></label>
        <label>API Key<input aria-label="API Key" name="api_key" type="password" placeholder={settings.api_key_configured ? "已配置，留空保持不变" : "输入密钥"} /></label>
        <div className="form-grid">
          <label>Temperature<input name="temperature" type="number" step=".1" value={settings.temperature} onChange={(e) => setSettings({...settings, temperature:Number(e.target.value)})}/></label>
          <label>Max Tokens<input name="max_tokens" type="number" value={settings.max_tokens} onChange={(e) => setSettings({...settings, max_tokens:Number(e.target.value)})}/></label>
          <label>Top P<input name="top_p" type="number" step=".1" value={settings.top_p} onChange={(e) => setSettings({...settings, top_p:Number(e.target.value)})}/></label>
        </div>
        <div className="actions"><button className="primary">保存配置</button><button type="button" className="secondary" onClick={() => api.testModel().then((x)=>setMessage(x.message)).catch((e)=>setMessage(e.message))}>测试连接</button></div>
        {message ? <p className="success">{message}</p> : null}
      </form>
    </section>
  );
}

