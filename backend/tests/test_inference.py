import pytest

from app.services.inference import PromptRenderError, render_prompt


def test_prompt_renderer_replaces_known_variables():
    rendered = render_prompt(
        "分析 {{analysis_type}}：{{bazi}}，日主 {{day_master}}。{{custom_request}}",
        {
            "analysis_type": "事业分析",
            "bazi": "甲戌 丁丑 乙卯 甲申",
            "day_master": "乙",
            "custom_request": "关注职业转型",
        },
    )
    assert rendered == "分析 事业分析：甲戌 丁丑 乙卯 甲申，日主 乙。关注职业转型"


def test_prompt_renderer_rejects_unresolved_variables():
    with pytest.raises(PromptRenderError):
        render_prompt("分析 {{missing}}", {})

