"""第5回 宿題（発展）: --hybrid の検索。同梱の索引と保存済みの埋め込みを使い、APIは呼ばない。"""

import json
import struct
import sqlite3

import pytest
import sqlite_vec

from app import retrieval, tools
from app.agent import agent, HYBRID_INSTRUCTIONS
from pydantic_ai.models.test import TestModel


def stored_vector(page_id: str) -> list[float]:
    """索引に保存済みのページ埋め込みを、質問ベクトルの代わりに使う。"""
    db = sqlite3.connect(retrieval.RAG_DB)
    blob = db.execute("SELECT embedding FROM chunks WHERE page_id = ?", (page_id,)).fetchone()[0]
    db.close()
    return list(struct.unpack(f"{len(blob) // 4}f", blob))


@pytest.fixture
def query_like(monkeypatch):
    def use(page_id):
        monkeypatch.setattr(retrieval, "embed_text", lambda *_: stored_vector(page_id))
    return use


def test_preview_skips_title_and_progress_header():
    pages = {p["page_id"]: p for p in retrieval.load_pages()}
    lora = retrieval.preview_line(pages["lec02-main-p052"])
    assert not lora.startswith("4/4") and "LoRA" in lora
    memory = retrieval.preview_line(pages["lec03-main-p040"])
    assert memory != pages["lec03-main-p040"]["title"] and "長期メモリ" in memory


def test_hybrid_returns_full_seeds_and_ranked_previews(query_like):
    query_like("lec03-main-p039")
    result = retrieval.search_hybrid("コンパクションとメモリの違い")
    seeds, candidates = result["seeds"], result["candidates"]
    assert seeds[0]["page_id"] == "lec03-main-p039" and seeds[0]["distance"] == pytest.approx(0, abs=1e-4)
    assert len(seeds) == retrieval.HYBRID_SEEDS and all(s["content"] for s in seeds)
    assert 0 < len(candidates) <= retrieval.HYBRID_PREVIEWS
    assert {c["page_id"] for c in candidates}.isdisjoint(s["page_id"] for s in seeds)
    assert [c["distance"] for c in candidates] == sorted(c["distance"] for c in candidates)
    assert all("content" not in c and c["preview"] for c in candidates)


def test_read_page_tool_returns_full_text_and_errors_as_json():
    page = json.loads(tools.read_page("lec03-main-p013"))
    assert page["page"] == 13 and "メモリ" in page["content"]
    assert "error" in json.loads(tools.read_page("lec99-main-p001"))


def test_hybrid_tools_reach_the_model(query_like):
    query_like("lec02-main-p052")
    model = TestModel(call_tools=["search_hybrid"])
    with agent.override(instructions=HYBRID_INSTRUCTIONS, tools=[tools.search_hybrid, tools.read_page]):
        result = agent.run_sync("LoRAは何を固定する？", model=model)
    names = {t.name for t in model.last_model_request_parameters.function_tools}
    assert names == {"search_hybrid", "read_page"}
    assert "lec02-main-p052" in result.output
