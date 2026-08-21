# -*- coding: utf-8 -*-
"""JSON 파일 기반 응시 기록 저장소.

data/submissions.json 하나에 모든 응시자를 담는다.
쓰기는 프로세스 내 Lock + 임시 파일 교체(atomic replace)로 처리해
동시 제출 중 파일이 깨지는 상황을 막는다.
"""

import json
import os
import tempfile
import threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "submissions.json")

_lock = threading.RLock()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def student_key(name):
    """이름을 저장소 키로 정규화한다(앞뒤 공백 제거 + 소문자)."""
    return " ".join(str(name).split()).lower()


def _empty_db():
    return {"students": {}}


def _load_raw():
    if not os.path.exists(DATA_FILE):
        return _empty_db()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as fp:
            data = json.load(fp)
    except (ValueError, OSError):
        # 파일이 손상된 경우 백업해두고 새로 시작한다.
        broken = DATA_FILE + ".broken-" + datetime.now().strftime("%Y%m%d%H%M%S")
        try:
            os.replace(DATA_FILE, broken)
        except OSError:
            pass
        return _empty_db()
    if not isinstance(data, dict) or "students" not in data:
        return _empty_db()
    return data


def _save_raw(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=DATA_DIR, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
        os.replace(tmp_path, DATA_FILE)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def load_all():
    """전체 응시자 레코드를 리스트로 돌려준다(이름 순)."""
    with _lock:
        data = _load_raw()
    students = list(data["students"].values())
    students.sort(key=lambda s: s.get("name", ""))
    return students


def get_student(name):
    with _lock:
        data = _load_raw()
        return data["students"].get(student_key(name))


def start_student(name):
    """응시 시작. 미제출 상태의 기존 기록은 초기화하고 새로 시작한다.

    이미 제출을 마친 이름이면 기존 기록을 그대로 돌려준다(제출 기록 보호).
    """
    key = student_key(name)
    display = " ".join(str(name).split())
    with _lock:
        data = _load_raw()
        existing = data["students"].get(key)
        if existing and existing.get("submitted"):
            return existing
        record = {
            "key": key,
            "name": display,
            "answers": {},
            "submitted": False,
            "started_at": _now(),
            "submitted_at": None,
            "overrides": {},
        }
        data["students"][key] = record
        _save_raw(data)
        return record


def save_answer(name, qid, value):
    """문항 하나의 답을 저장한다. 제출 완료 상태면 무시한다."""
    key = student_key(name)
    with _lock:
        data = _load_raw()
        record = data["students"].get(key)
        if record is None or record.get("submitted"):
            return record
        record.setdefault("answers", {})[str(qid)] = value
        _save_raw(data)
        return record


def submit(name):
    """제출 처리. (성공여부, 레코드) 를 돌려준다."""
    key = student_key(name)
    with _lock:
        data = _load_raw()
        record = data["students"].get(key)
        if record is None:
            return False, None
        if record.get("submitted"):
            return True, record
        record["submitted"] = True
        record["submitted_at"] = _now()
        _save_raw(data)
        return True, record


def reset_student(name):
    """관리자 초기화: 답안·제출 상태·수동 채점을 모두 지운다."""
    key = student_key(name)
    with _lock:
        data = _load_raw()
        record = data["students"].get(key)
        if record is None:
            return False
        record["answers"] = {}
        record["submitted"] = False
        record["started_at"] = _now()
        record["submitted_at"] = None
        record["overrides"] = {}
        _save_raw(data)
        return True


def delete_student(name):
    key = student_key(name)
    with _lock:
        data = _load_raw()
        if key not in data["students"]:
            return False
        del data["students"][key]
        _save_raw(data)
        return True


def set_override(name, qid, verdict):
    """주관식 수동 채점. verdict 는 True / False / None(자동 채점으로 되돌림)."""
    key = student_key(name)
    with _lock:
        data = _load_raw()
        record = data["students"].get(key)
        if record is None:
            return False
        overrides = record.setdefault("overrides", {})
        if verdict is None:
            overrides.pop(str(qid), None)
        else:
            overrides[str(qid)] = bool(verdict)
        _save_raw(data)
        return True
