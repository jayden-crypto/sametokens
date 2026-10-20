// Line-oriented JSON server exposing transformers.js tokenizers and chat templates.
// stdin:  {"id": 1, "op": "encode", "model": "qwen2.5", "text": "..."}
//         {"id": 2, "op": "template", "model": "qwen2.5", "messages": [...], "add_generation_prompt": true}
// stdout: {"id": 1, "ok": true, "result": [...]}  or  {"id": 1, "ok": false, "error": "..."}
import { createInterface } from "node:readline";
import { AutoTokenizer, env } from "@huggingface/transformers";

env.allowRemoteModels = false;
env.allowLocalModels = true;
env.localModelPath = process.argv[2];

const tokenizers = new Map();
async function load(model) {
  if (!tokenizers.has(model)) tokenizers.set(model, await AutoTokenizer.from_pretrained(model));
  return tokenizers.get(model);
}

const rl = createInterface({ input: process.stdin });
for await (const line of rl) {
  if (!line.trim()) continue;
  const req = JSON.parse(line);
  let reply;
  try {
    const tok = await load(req.model);
    let result;
    if (req.op === "encode") {
      result = tok.encode(req.text, { add_special_tokens: false });
    } else if (req.op === "template") {
      result = tok.apply_chat_template(req.messages, {
        tokenize: false,
        add_generation_prompt: req.add_generation_prompt ?? true,
        ...(req.kwargs || {}),
      });
    } else {
      throw new Error(`unknown op ${req.op}`);
    }
    reply = { id: req.id, ok: true, result };
  } catch (e) {
    reply = { id: req.id, ok: false, error: String(e && e.message ? e.message : e).slice(0, 300) };
  }
  process.stdout.write(JSON.stringify(reply) + "\n");
}
