from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from database import get_db, init_db
from typing import Optional

app = FastAPI(title="Veervrat CMS")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.on_event("startup")
def startup():
    init_db()


def flash(request: Request, msg: str, kind: str = "success"):
    pass  # handled inline via redirect query params


# ═══════════════════════════════════════════════
# DATA MODEL PAGE
# ═══════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
def data_model(request: Request):
    db = get_db()
    counts = {
        t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in ["virtue", "subvirtue", "weakness", "sentence", "exposure", "resolution", "challenge"]
    }
    db.close()
    return templates.TemplateResponse(request, "data_model.html", {"counts": counts})


# ═══════════════════════════════════════════════
# VIRTUES
# ═══════════════════════════════════════════════

@app.get("/virtues", response_class=HTMLResponse)
def list_virtues(request: Request, msg: str = ""):
    db = get_db()
    virtues = db.execute("""
        SELECT v.*, COUNT(sv.id) AS subvirtue_count
        FROM virtue v
        LEFT JOIN subvirtue sv ON sv.virtue_id = v.id
        GROUP BY v.id ORDER BY v.id
    """).fetchall()
    db.close()
    return templates.TemplateResponse(request, "virtues.html", {"virtues": virtues, "msg": msg})


@app.post("/virtues/new")
def create_virtue(name_en: str = Form(...), name_mr: str = Form("")):
    db = get_db()
    db.execute("INSERT INTO virtue (name_en, name_mr) VALUES (?, ?)", (name_en.strip(), name_mr.strip()))
    db.commit()
    db.close()
    return RedirectResponse("/virtues?msg=Virtue+created", status_code=303)


@app.post("/virtues/{vid}/edit")
def edit_virtue(vid: int, name_en: str = Form(...), name_mr: str = Form("")):
    db = get_db()
    db.execute("UPDATE virtue SET name_en=?, name_mr=? WHERE id=?", (name_en.strip(), name_mr.strip(), vid))
    db.commit()
    db.close()
    return RedirectResponse("/virtues?msg=Saved", status_code=303)


@app.post("/virtues/{vid}/delete")
def delete_virtue(vid: int):
    db = get_db()
    db.execute("DELETE FROM virtue WHERE id=?", (vid,))
    db.commit()
    db.close()
    return RedirectResponse("/virtues?msg=Deleted", status_code=303)


# ═══════════════════════════════════════════════
# SUBVIRTUES
# ═══════════════════════════════════════════════

@app.get("/subvirtues", response_class=HTMLResponse)
def list_subvirtues(request: Request, msg: str = ""):
    db = get_db()
    subvirtues = db.execute("""
        SELECT sv.*, v.name_en AS virtue_name, COUNT(s.id) AS sentence_count
        FROM subvirtue sv
        JOIN virtue v ON v.id = sv.virtue_id
        LEFT JOIN sentence s ON s.subvirtue_id = sv.id
        GROUP BY sv.id ORDER BY sv.id
    """).fetchall()
    virtues = db.execute("SELECT * FROM virtue ORDER BY id").fetchall()
    db.close()
    return templates.TemplateResponse(request, "subvirtues.html", {"subvirtues": subvirtues, "virtues": virtues, "msg": msg})


@app.post("/subvirtues/new")
def create_subvirtue(name_en: str = Form(...), name_mr: str = Form(""), virtue_id: int = Form(...)):
    db = get_db()
    db.execute("INSERT INTO subvirtue (name_en, name_mr, virtue_id) VALUES (?, ?, ?)", (name_en.strip(), name_mr.strip(), virtue_id))
    db.commit()
    db.close()
    return RedirectResponse("/subvirtues?msg=Subvirtue+created", status_code=303)


@app.post("/subvirtues/{svid}/edit")
def edit_subvirtue(svid: int, name_en: str = Form(...), name_mr: str = Form(""), virtue_id: int = Form(...)):
    db = get_db()
    db.execute("UPDATE subvirtue SET name_en=?, name_mr=?, virtue_id=? WHERE id=?", (name_en.strip(), name_mr.strip(), virtue_id, svid))
    db.commit()
    db.close()
    return RedirectResponse("/subvirtues?msg=Saved", status_code=303)


@app.post("/subvirtues/{svid}/delete")
def delete_subvirtue(svid: int):
    db = get_db()
    db.execute("DELETE FROM subvirtue WHERE id=?", (svid,))
    db.commit()
    db.close()
    return RedirectResponse("/subvirtues?msg=Deleted", status_code=303)


# ═══════════════════════════════════════════════
# WEAKNESSES
# ═══════════════════════════════════════════════

@app.get("/weaknesses", response_class=HTMLResponse)
def list_weaknesses(request: Request, msg: str = ""):
    db = get_db()
    weaknesses = db.execute("""
        SELECT w.*, COUNT(DISTINCT ws.subvirtue_id) AS sv_count
        FROM weakness w
        LEFT JOIN weakness_subvirtue ws ON ws.weakness_id = w.id
        GROUP BY w.id ORDER BY w.id
    """).fetchall()
    db.close()
    return templates.TemplateResponse(request, "weaknesses.html", {"weaknesses": weaknesses, "msg": msg})


@app.get("/weaknesses/{wid}", response_class=HTMLResponse)
def view_weakness(request: Request, wid: int, msg: str = ""):
    db = get_db()
    weakness = db.execute("SELECT * FROM weakness WHERE id=?", (wid,)).fetchone()
    if not weakness:
        raise HTTPException(404)
    linked_svs = db.execute("""
        SELECT sv.*, v.name_en AS virtue_name, ws.priority
        FROM weakness_subvirtue ws
        JOIN subvirtue sv ON sv.id = ws.subvirtue_id
        JOIN virtue v ON v.id = sv.virtue_id
        WHERE ws.weakness_id = ?
        ORDER BY ws.priority, sv.name_en
    """, (wid,)).fetchall()
    all_svs = db.execute("""
        SELECT sv.*, v.name_en AS virtue_name FROM subvirtue sv
        JOIN virtue v ON v.id = sv.virtue_id
        ORDER BY v.name_en, sv.name_en
    """).fetchall()
    db.close()
    return templates.TemplateResponse(request, "weakness_detail.html", {
        "weakness": weakness,
        "linked_svs": linked_svs, "all_svs": all_svs, "msg": msg
    })


@app.post("/weaknesses/new")
def create_weakness(name_en: str = Form(...), name_mr: str = Form(""), category: str = Form(...)):
    db = get_db()
    db.execute("INSERT INTO weakness (name_en, name_mr, category) VALUES (?, ?, ?)", (name_en.strip(), name_mr.strip(), category))
    db.commit()
    db.close()
    return RedirectResponse("/weaknesses?msg=Weakness+created", status_code=303)


@app.post("/weaknesses/{wid}/edit")
def edit_weakness(wid: int, name_en: str = Form(...), name_mr: str = Form(""), category: str = Form(...)):
    db = get_db()
    db.execute("UPDATE weakness SET name_en=?, name_mr=?, category=? WHERE id=?", (name_en.strip(), name_mr.strip(), category, wid))
    db.commit()
    db.close()
    return RedirectResponse(f"/weaknesses/{wid}?msg=Saved", status_code=303)


@app.post("/weaknesses/{wid}/delete")
def delete_weakness(wid: int):
    db = get_db()
    db.execute("DELETE FROM weakness WHERE id=?", (wid,))
    db.commit()
    db.close()
    return RedirectResponse("/weaknesses?msg=Deleted", status_code=303)


@app.post("/weaknesses/{wid}/link-subvirtue")
def link_subvirtue(wid: int, subvirtue_id: int = Form(...), priority: int = Form(0)):
    db = get_db()
    db.execute(
        "INSERT OR IGNORE INTO weakness_subvirtue (weakness_id, subvirtue_id, priority) VALUES (?, ?, ?)",
        (wid, subvirtue_id, priority)
    )
    db.commit()
    db.close()
    return RedirectResponse(f"/weaknesses/{wid}?msg=Subvirtue+linked", status_code=303)


@app.post("/weaknesses/{wid}/unlink-subvirtue/{svid}")
def unlink_subvirtue(wid: int, svid: int):
    db = get_db()
    db.execute("DELETE FROM weakness_subvirtue WHERE weakness_id=? AND subvirtue_id=?", (wid, svid))
    db.commit()
    db.close()
    return RedirectResponse(f"/weaknesses/{wid}?msg=Unlinked", status_code=303)


# ═══════════════════════════════════════════════
# SENTENCES
# ═══════════════════════════════════════════════

@app.get("/sentences", response_class=HTMLResponse)
def list_sentences(request: Request, virtue_id: Optional[int] = None, subvirtue_id: Optional[int] = None, msg: str = ""):
    db = get_db()
    erc_q = """
        SELECT s.*, sv.name_en AS subvirtue_name,
               COUNT(DISTINCT e.id) AS exp_count,
               COUNT(DISTINCT r.id) AS res_count,
               COUNT(DISTINCT ch.id) AS cha_count
        FROM sentence s
        JOIN subvirtue sv ON sv.id = s.subvirtue_id
        LEFT JOIN exposure e ON e.sentence_id = s.id
        LEFT JOIN resolution r ON r.sentence_id = s.id
        LEFT JOIN challenge ch ON ch.sentence_id = s.id
    """
    if subvirtue_id:
        sentences = db.execute(erc_q + " WHERE s.subvirtue_id = ? GROUP BY s.id ORDER BY s.id", (subvirtue_id,)).fetchall()
    elif virtue_id:
        sentences = db.execute(erc_q + " WHERE sv.virtue_id = ? GROUP BY s.id ORDER BY s.id", (virtue_id,)).fetchall()
    else:
        sentences = db.execute(erc_q + " GROUP BY s.id ORDER BY s.id").fetchall()
    virtues = db.execute("SELECT * FROM virtue ORDER BY id").fetchall()
    # subvirtues scoped to selected virtue, or all
    if virtue_id:
        subvirtues = db.execute("SELECT * FROM subvirtue WHERE virtue_id = ? ORDER BY id", (virtue_id,)).fetchall()
    else:
        subvirtues = db.execute("SELECT * FROM subvirtue ORDER BY id").fetchall()
    db.close()
    return templates.TemplateResponse(request, "sentences.html", {
        "sentences": sentences,
        "virtues": virtues, "subvirtues": subvirtues,
        "filter_vid": virtue_id, "filter_svid": subvirtue_id, "msg": msg
    })


@app.post("/sentences/new")
def create_sentence(
    text_en: str = Form(...), text_mr: str = Form(""), subvirtue_id: int = Form(...),
    virtue_id: Optional[int] = None, subvirtue_id_filter: Optional[int] = None
):
    db = get_db()
    db.execute("INSERT INTO sentence (text_en, text_mr, subvirtue_id) VALUES (?, ?, ?)", (text_en.strip(), text_mr.strip(), subvirtue_id))
    db.commit()
    # resolve virtue_id from subvirtue if not passed
    if not virtue_id:
        row = db.execute("SELECT virtue_id FROM subvirtue WHERE id=?", (subvirtue_id,)).fetchone()
        virtue_id = row["virtue_id"] if row else None
    db.close()
    return RedirectResponse(f"/sentences?virtue_id={virtue_id or ''}&subvirtue_id={subvirtue_id}&msg=Sentence+added", status_code=303)


@app.post("/sentences/{sid}/edit")
def edit_sentence(
    sid: int, text_en: str = Form(...), text_mr: str = Form(""), subvirtue_id: int = Form(...),
    virtue_id: Optional[int] = None
):
    db = get_db()
    db.execute("UPDATE sentence SET text_en=?, text_mr=?, subvirtue_id=? WHERE id=?", (text_en.strip(), text_mr.strip(), subvirtue_id, sid))
    db.commit()
    if not virtue_id:
        row = db.execute("SELECT virtue_id FROM subvirtue WHERE id=?", (subvirtue_id,)).fetchone()
        virtue_id = row["virtue_id"] if row else None
    db.close()
    return RedirectResponse(f"/sentences?virtue_id={virtue_id or ''}&subvirtue_id={subvirtue_id}&msg=Saved", status_code=303)


@app.post("/sentences/{sid}/delete")
def delete_sentence(sid: int):
    db = get_db()
    row = db.execute("""
        SELECT s.subvirtue_id, sv.virtue_id FROM sentence s
        JOIN subvirtue sv ON sv.id = s.subvirtue_id WHERE s.id=?
    """, (sid,)).fetchone()
    svid = row["subvirtue_id"] if row else ""
    vid = row["virtue_id"] if row else ""
    db.execute("DELETE FROM sentence WHERE id=?", (sid,))
    db.commit()
    db.close()
    return RedirectResponse(f"/sentences?virtue_id={vid}&subvirtue_id={svid}&msg=Deleted", status_code=303)


# ═══════════════════════════════════════════════
# SENTENCE DETAIL (ERC — Exposure/Resolution/Challenge)
# ═══════════════════════════════════════════════

@app.get("/sentences/{sid}", response_class=HTMLResponse)
def view_sentence(request: Request, sid: int, msg: str = ""):
    db = get_db()
    sentence = db.execute("""
        SELECT s.*, sv.name_en AS subvirtue_name, v.name_en AS virtue_name, v.id AS virtue_id
        FROM sentence s
        JOIN subvirtue sv ON sv.id = s.subvirtue_id
        JOIN virtue v ON v.id = sv.virtue_id
        WHERE s.id = ?
    """, (sid,)).fetchone()
    if not sentence:
        raise HTTPException(404)
    exposures = db.execute("SELECT * FROM exposure WHERE sentence_id=? ORDER BY tier, sort_order, id", (sid,)).fetchall()
    resolutions = db.execute("SELECT * FROM resolution WHERE sentence_id=? ORDER BY sort_order, id", (sid,)).fetchall()
    challenges = db.execute("SELECT * FROM challenge WHERE sentence_id=? ORDER BY id", (sid,)).fetchall()
    db.close()
    return templates.TemplateResponse(request, "sentence_detail.html", {
        "sentence": sentence,
        "exposures": exposures, "resolutions": resolutions, "challenges": challenges,
        "msg": msg
    })


@app.post("/sentences/{sid}/edit-meta")
def edit_sentence_meta(sid: int, source_file: str = Form(""), notes: str = Form("")):
    db = get_db()
    db.execute("UPDATE sentence SET source_file=?, notes=? WHERE id=?",
               (source_file.strip(), notes.strip(), sid))
    db.commit()
    db.close()
    return RedirectResponse(f"/sentences/{sid}?msg=Saved", status_code=303)


# ── Exposures ────────────────────────────────

@app.post("/sentences/{sid}/exposures/new")
def create_exposure(sid: int, title: str = Form(...), tier: str = Form("local"), description: str = Form(""), sort_order: int = Form(0)):
    db = get_db()
    db.execute("INSERT INTO exposure (sentence_id, title, tier, description, sort_order) VALUES (?, ?, ?, ?, ?)",
               (sid, title.strip(), tier, description.strip(), sort_order))
    db.commit()
    db.close()
    return RedirectResponse(f"/sentences/{sid}?msg=Exposure+added", status_code=303)


@app.post("/sentences/{sid}/exposures/{eid}/edit")
def edit_exposure(sid: int, eid: int, title: str = Form(...), tier: str = Form("local"), description: str = Form(""), sort_order: int = Form(0)):
    db = get_db()
    db.execute("UPDATE exposure SET title=?, tier=?, description=?, sort_order=? WHERE id=? AND sentence_id=?",
               (title.strip(), tier, description.strip(), sort_order, eid, sid))
    db.commit()
    db.close()
    return RedirectResponse(f"/sentences/{sid}?msg=Saved", status_code=303)


@app.post("/sentences/{sid}/exposures/{eid}/delete")
def delete_exposure(sid: int, eid: int):
    db = get_db()
    db.execute("DELETE FROM exposure WHERE id=? AND sentence_id=?", (eid, sid))
    db.commit()
    db.close()
    return RedirectResponse(f"/sentences/{sid}?msg=Deleted", status_code=303)


# ── Resolutions ──────────────────────────────

@app.post("/sentences/{sid}/resolutions/new")
def create_resolution(sid: int, title: str = Form(...), description: str = Form(""), duration_weeks: Optional[int] = Form(None), sort_order: int = Form(0)):
    db = get_db()
    db.execute("INSERT INTO resolution (sentence_id, title, description, duration_weeks, sort_order) VALUES (?, ?, ?, ?, ?)",
               (sid, title.strip(), description.strip(), duration_weeks, sort_order))
    db.commit()
    db.close()
    return RedirectResponse(f"/sentences/{sid}?msg=Resolution+added", status_code=303)


@app.post("/sentences/{sid}/resolutions/{rid}/edit")
def edit_resolution(sid: int, rid: int, title: str = Form(...), description: str = Form(""), duration_weeks: Optional[int] = Form(None), sort_order: int = Form(0)):
    db = get_db()
    db.execute("UPDATE resolution SET title=?, description=?, duration_weeks=?, sort_order=? WHERE id=? AND sentence_id=?",
               (title.strip(), description.strip(), duration_weeks, sort_order, rid, sid))
    db.commit()
    db.close()
    return RedirectResponse(f"/sentences/{sid}?msg=Saved", status_code=303)


@app.post("/sentences/{sid}/resolutions/{rid}/delete")
def delete_resolution(sid: int, rid: int):
    db = get_db()
    db.execute("DELETE FROM resolution WHERE id=? AND sentence_id=?", (rid, sid))
    db.commit()
    db.close()
    return RedirectResponse(f"/sentences/{sid}?msg=Deleted", status_code=303)


# ── Challenges ───────────────────────────────

@app.post("/sentences/{sid}/challenges/new")
def create_challenge(sid: int, title: str = Form(...), description: str = Form(""), duration_days: Optional[int] = Form(None)):
    db = get_db()
    db.execute("INSERT INTO challenge (sentence_id, title, description, duration_days) VALUES (?, ?, ?, ?)",
               (sid, title.strip(), description.strip(), duration_days))
    db.commit()
    db.close()
    return RedirectResponse(f"/sentences/{sid}?msg=Challenge+added", status_code=303)


@app.post("/sentences/{sid}/challenges/{cid}/edit")
def edit_challenge(sid: int, cid: int, title: str = Form(...), description: str = Form(""), duration_days: Optional[int] = Form(None)):
    db = get_db()
    db.execute("UPDATE challenge SET title=?, description=?, duration_days=? WHERE id=? AND sentence_id=?",
               (title.strip(), description.strip(), duration_days, cid, sid))
    db.commit()
    db.close()
    return RedirectResponse(f"/sentences/{sid}?msg=Saved", status_code=303)


@app.post("/sentences/{sid}/challenges/{cid}/delete")
def delete_challenge(sid: int, cid: int):
    db = get_db()
    db.execute("DELETE FROM challenge WHERE id=? AND sentence_id=?", (cid, sid))
    db.commit()
    db.close()
    return RedirectResponse(f"/sentences/{sid}?msg=Deleted", status_code=303)
