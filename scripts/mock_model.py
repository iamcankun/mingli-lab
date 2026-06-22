from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class CompletionRequest(BaseModel):
    model: str
    messages: list[dict[str, str]]


@app.post("/v1/chat/completions")
def complete(body: CompletionRequest):
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "# 事业结构判断\n\n命盘显示专业积累是主要验证方向。建议持续记录实际职业节点，与命理判断交叉验证。",
                }
            }
        ],
        "usage": {"prompt_tokens": 128, "completion_tokens": 42, "total_tokens": 170},
    }

