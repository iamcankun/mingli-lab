from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ChartCalculateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    gender: Literal["male", "female"]
    birth_date: str
    birth_time: str
    province: str = ""
    city: str = ""
    persist: bool = True


class ModelSettingsRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    base_url: str
    api_key: str = ""
    model_id: str
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1600, ge=1, le=128000)
    top_p: float = Field(default=1.0, ge=0, le=1)


class TemporaryChart(BaseModel):
    bazi: str
    day_master: str = ""
    chart: dict[str, Any] = Field(default_factory=dict)


class InferenceRequest(BaseModel):
    chart_id: int | None = None
    temporary_chart: TemporaryChart | None = None
    analysis_type: str = "全局分析"
    custom_request: str = ""
    system_prompt: str | None = None
    user_prompt: str | None = None

    @model_validator(mode="after")
    def validate_source(self):
        if bool(self.chart_id) == bool(self.temporary_chart):
            raise ValueError("Provide exactly one of chart_id or temporary_chart")
        return self
