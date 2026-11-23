"""第5回 宿題（発展）: APIを呼ばずに、検索結果に根拠ページが入るかを比べる。

質問の埋め込みの代わりに、索引に保存済みのページ埋め込み（根拠ページ、またはその平均）を使う。
使い方: uv run python -m scripts.lec05_proxy_eval
"""
import json, struct, sqlite3, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import retrieval

db = sqlite3.connect(retrieval.RAG_DB)
def vec(pid):
    b = db.execute("select embedding from chunks where page_id=?", (pid,)).fetchone()[0]
    return list(struct.unpack(f"{len(b)//4}f", b))
def mean(pids):
    vs = [vec(p) for p in pids]; m = [sum(x)/len(vs) for x in zip(*vs)]; n = math.hypot(*m); return [x/n for x in m]

cases = {
 "Q1 LoRA (single page)": (["lec02-main-p052"], {"lec02-main-p052"}),
 "Q2 memory (multi page)": (["lec03-main-p039", "lec03-main-p040"], {"lec03-main-p013", "lec03-main-p039", "lec03-main-p040"}),
}
proxies = []
for name, (qp, ev) in cases.items():
    proxies.append((name, "mean of " + "+".join(p[-4:] for p in qp), mean(qp), ev))
    for p in sorted(ev):
        proxies.append((name, "page " + p[-4:], vec(p), ev))

rows = []
for name, label, v, ev in proxies:
    retrieval.embed_text = lambda *_, v=v: v
    vr = retrieval.search("x"); g = retrieval.search_graph("x"); h = retrieval.search_hybrid("x")
    vf = {r["page_id"] for r in vr}
    gf = {r["page_id"] for r in g["seeds"] + g["expanded"]}
    hf = {r["page_id"] for r in h["seeds"]}; hp = {r["page_id"] for r in h["candidates"]}
    size = lambda o: len(json.dumps(o, ensure_ascii=False))
    rows.append(dict(q=name, proxy=label,
        vector=f"{len(vf & ev)}/{len(ev)}", vector_chars=size({"results": vr}),
        graph=f"{len(gf & ev)}/{len(ev)}", graph_chars=size(g),
        hybrid_full=f"{len(hf & ev)}/{len(ev)}", hybrid_full_or_preview=f"{len((hf|hp) & ev)}/{len(ev)}", hybrid_chars=size(h),
        missing_vector=sorted(p[-4:] for p in ev - vf), missing_graph=sorted(p[-4:] for p in ev - gf),
        missing_hybrid=sorted(p[-4:] for p in ev - hf - hp)))
for r in rows: print(json.dumps(r, ensure_ascii=False))
print("full-context chars:", len(retrieval.get_all_materials()))
