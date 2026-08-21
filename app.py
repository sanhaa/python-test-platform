# -*- coding: utf-8 -*-
"""2026-AI-PD 실습 기초 사전 테스트 플랫폼.

실행:  python app.py   →  http://0.0.0.0:5000
"""

import csv
import io
import os

from flask import (Flask, jsonify, redirect, render_template, request,
                   session, url_for, Response, flash)

import storage
from questions import (MAX_SCORE, POINT_PER_QUESTION, QUESTIONS, QUESTION_BY_ID,
                       SUBTITLE, TITLE, TOTAL_QUESTIONS, answer_label, is_correct)

ADMIN_NAME = "admin-123456"

# 학생 결과 화면에 정답/점수를 함께 보여줄지.
SHOW_ANSWERS_TO_STUDENT = True

app = Flask(__name__)
app.secret_key = os.environ.get("TEST_PLATFORM_SECRET", "2026-ai-pd-pretest-secret")


# --------------------------------------------------------------------------
# 채점
# --------------------------------------------------------------------------

def grade(record):
    """레코드 하나를 채점해 문항별 결과와 총점을 돌려준다."""
    answers = record.get("answers", {}) or {}
    overrides = record.get("overrides", {}) or {}
    details = []
    score = 0
    for q in QUESTIONS:
        qid = str(q["id"])
        raw = answers.get(qid)
        auto = is_correct(q, raw)
        overridden = qid in overrides
        correct = bool(overrides[qid]) if overridden else auto
        if correct:
            score += POINT_PER_QUESTION
        details.append({
            "id": q["id"],
            "type": q["type"],
            "title": q["title"],
            "answer_raw": raw,
            "answer_text": answer_label(q, raw),
            "correct_text": answer_label(q, q["answer"]),
            "auto": auto,
            "correct": correct,
            "overridden": overridden,
        })
    return {"details": details, "score": score, "max_score": MAX_SCORE}


def current_student():
    return session.get("student")


# --------------------------------------------------------------------------
# 로그인 / 로그아웃
# --------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = " ".join((request.form.get("name") or "").split())
        if not name:
            flash("이름을 입력해 주세요.")
            return redirect(url_for("login"))

        if name.lower() == ADMIN_NAME:
            session["is_admin"] = True
            return redirect(url_for("admin"))

        session.pop("is_admin", None)
        record = storage.start_student(name)
        session["student"] = record["name"]
        if record.get("submitted"):
            return redirect(url_for("result"))
        return redirect(url_for("exam"))

    return render_template("login.html", title=TITLE, subtitle=SUBTITLE,
                           total=TOTAL_QUESTIONS)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --------------------------------------------------------------------------
# 응시
# --------------------------------------------------------------------------

@app.route("/exam")
def exam():
    name = current_student()
    if not name:
        return redirect(url_for("login"))
    record = storage.get_student(name)
    if record is None:
        session.clear()
        return redirect(url_for("login"))
    if record.get("submitted"):
        return redirect(url_for("result"))
    return render_template("exam.html", title=TITLE, subtitle=SUBTITLE,
                           questions=QUESTIONS, total=TOTAL_QUESTIONS,
                           name=record["name"], answers=record.get("answers", {}))


@app.route("/api/answer", methods=["POST"])
def api_answer():
    """문항 답안 자동 저장."""
    name = current_student()
    if not name:
        return jsonify({"ok": False, "error": "not_logged_in"}), 401
    payload = request.get_json(silent=True) or {}
    qid = payload.get("qid")
    value = payload.get("value")
    if qid is None or int(qid) not in QUESTION_BY_ID:
        return jsonify({"ok": False, "error": "bad_question"}), 400

    record = storage.save_answer(name, qid, value)
    if record is None:
        return jsonify({"ok": False, "error": "no_record"}), 404
    if record.get("submitted"):
        return jsonify({"ok": False, "error": "already_submitted"}), 409

    answers = record.get("answers", {})
    answered = [q["id"] for q in QUESTIONS
                if str(answers.get(str(q["id"]), "")).strip() != ""]
    return jsonify({"ok": True, "answered": answered,
                    "complete": len(answered) == TOTAL_QUESTIONS})


@app.route("/submit", methods=["POST"])
def submit():
    name = current_student()
    if not name:
        return redirect(url_for("login"))
    record = storage.get_student(name)
    if record is None:
        session.clear()
        return redirect(url_for("login"))
    if record.get("submitted"):
        return redirect(url_for("result"))

    answers = record.get("answers", {})
    missing = [q["id"] for q in QUESTIONS
               if str(answers.get(str(q["id"]), "")).strip() == ""]
    if missing:
        flash("아직 답하지 않은 문항이 있습니다: %s번" %
              ", ".join(str(m) for m in missing))
        return redirect(url_for("exam"))

    storage.submit(name)
    return redirect(url_for("result"))


@app.route("/result")
def result():
    name = current_student()
    if not name:
        return redirect(url_for("login"))
    record = storage.get_student(name)
    if record is None:
        session.clear()
        return redirect(url_for("login"))
    if not record.get("submitted"):
        return redirect(url_for("exam"))

    graded = grade(record) if SHOW_ANSWERS_TO_STUDENT else None
    return render_template("result.html", title=TITLE, subtitle=SUBTITLE,
                           questions=QUESTIONS, record=record,
                           answers=record.get("answers", {}),
                           graded=graded, show_answers=SHOW_ANSWERS_TO_STUDENT,
                           answer_label=answer_label)


# --------------------------------------------------------------------------
# 관리자
# --------------------------------------------------------------------------

def _require_admin():
    return bool(session.get("is_admin"))


@app.route("/admin")
def admin():
    if not _require_admin():
        return redirect(url_for("login"))

    rows = []
    for record in storage.load_all():
        graded = grade(record)
        answers = record.get("answers", {})
        answered = sum(1 for q in QUESTIONS
                       if str(answers.get(str(q["id"]), "")).strip() != "")
        rows.append({"record": record, "graded": graded, "answered": answered})

    submitted = [r for r in rows if r["record"].get("submitted")]
    avg = round(sum(r["graded"]["score"] for r in submitted) / len(submitted), 1) \
        if submitted else 0

    # 문항별 정답률 (제출자 기준)
    per_question = []
    for idx, q in enumerate(QUESTIONS):
        hits = sum(1 for r in submitted if r["graded"]["details"][idx]["correct"])
        rate = round(hits * 100.0 / len(submitted)) if submitted else 0
        per_question.append({"id": q["id"], "title": q["title"],
                             "type": q["type"], "hits": hits, "rate": rate})

    return render_template("admin.html", title=TITLE, questions=QUESTIONS,
                           rows=rows, total=TOTAL_QUESTIONS,
                           submitted_count=len(submitted), avg=avg,
                           per_question=per_question, max_score=MAX_SCORE)


@app.route("/admin/student/<path:key>")
def admin_student(key):
    if not _require_admin():
        return redirect(url_for("login"))
    record = storage.get_student(key)
    if record is None:
        flash("해당 응시자를 찾을 수 없습니다.")
        return redirect(url_for("admin"))
    return render_template("admin_student.html", title=TITLE,
                           questions=QUESTIONS, record=record,
                           graded=grade(record), answer_label=answer_label)


@app.route("/admin/reset", methods=["POST"])
def admin_reset():
    if not _require_admin():
        return redirect(url_for("login"))
    key = request.form.get("key", "")
    record = storage.get_student(key)
    if record and storage.reset_student(key):
        flash("'%s' 님의 답안을 초기화했습니다. 다시 응시할 수 있습니다." % record["name"])
    else:
        flash("초기화할 응시자를 찾지 못했습니다.")
    return redirect(request.form.get("next") or url_for("admin"))


@app.route("/admin/delete", methods=["POST"])
def admin_delete():
    if not _require_admin():
        return redirect(url_for("login"))
    key = request.form.get("key", "")
    record = storage.get_student(key)
    if record and storage.delete_student(key):
        flash("'%s' 님의 기록을 삭제했습니다." % record["name"])
    return redirect(url_for("admin"))


@app.route("/admin/override", methods=["POST"])
def admin_override():
    if not _require_admin():
        return redirect(url_for("login"))
    key = request.form.get("key", "")
    qid = request.form.get("qid", "")
    verdict = request.form.get("verdict", "")
    value = {"correct": True, "wrong": False}.get(verdict)  # 그 외에는 None = 자동
    storage.set_override(key, qid, value)
    return redirect(url_for("admin_student", key=key))


@app.route("/admin/export.csv")
def admin_export():
    if not _require_admin():
        return redirect(url_for("login"))

    buf = io.StringIO()
    writer = csv.writer(buf)
    header = ["이름", "제출여부", "제출시각", "점수"]
    header += ["%d번" % q["id"] for q in QUESTIONS]
    header += ["%d번 답안" % q["id"] for q in QUESTIONS]
    writer.writerow(header)

    for record in storage.load_all():
        graded = grade(record)
        row = [record.get("name", ""),
               "제출" if record.get("submitted") else "미제출",
               record.get("submitted_at") or "",
               graded["score"] if record.get("submitted") else ""]
        row += ["O" if d["correct"] else "X" for d in graded["details"]]
        row += [d["answer_text"] for d in graded["details"]]
        writer.writerow(row)

    csv_bytes = buf.getvalue().encode("utf-8-sig")  # 엑셀 한글 깨짐 방지
    return Response(csv_bytes, mimetype="text/csv", headers={
        "Content-Disposition": "attachment; filename=pretest-results.csv"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
