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


def student_key(knox_id):
    """Knox ID를 저장소 키로 정규화한다(공백 제거 + 소문자)."""
    return "".join(str(knox_id).split()).lower()


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
    for record in data["students"].values():
        # 이름으로 응시하던 시절의 기록을 Knox ID 형식으로 맞춰 준다.
        if "knox_id" not in record:
            record["knox_id"] = record.get("name", record.get("key", ""))
        record.pop("name", None)
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
    """전체 응시자 레코드를 리스트로 돌려준다(Knox ID 순)."""
    with _lock:
        data = _load_raw()
    students = list(data["students"].values())
    students.sort(key=lambda s: s.get("knox_id", "").lower())
    return students


def get_student(knox_id):
    with _lock:
        data = _load_raw()
        return data["students"].get(student_key(knox_id))


def start_student(knox_id):
    """응시 시작. 미제출 상태의 기존 기록은 초기화하고 새로 시작한다.

    이미 제출을 마친 Knox ID면 기존 기록을 그대로 돌려준다(제출 기록 보호).
    """
    key = student_key(knox_id)
    display = "".join(str(knox_id).split())
    with _lock:
        data = _load_raw()
        existing = data["students"].get(key)
        if existing and existing.get("submitted"):
            return existing
        record = {
            "key": key,
            "knox_id": display,
            "answers": {},
            "submitted": False,
            "started_at": _now(),
            "submitted_at": None,
            "overrides": {},
        }
        data["students"][key] = record
        _save_raw(data)
        return record


def save_answer(knox_id, qid, value):
    """문항 하나의 답을 저장한다. 제출 완료 상태면 무시한다."""
    key = student_key(knox_id)
    with _lock:
        data = _load_raw()
        record = data["students"].get(key)
        if record is None or record.get("submitted"):
            return record
        record.setdefault("answers", {})[str(qid)] = value
        _save_raw(data)
        return record


def submit(knox_id):
    """제출 처리. (성공여부, 레코드) 를 돌려준다."""
    key = student_key(knox_id)
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


def _clear(record):
    """레코드 하나를 미응시 상태로 되돌린다."""
    record["answers"] = {}
    record["submitted"] = False
    record["started_at"] = _now()
    record["submitted_at"] = None
    record["overrides"] = {}


def reset_student(knox_id):
    """관리자 초기화: 답안·제출 상태·수동 채점을 모두 지운다."""
    key = student_key(knox_id)
    with _lock:
        data = _load_raw()
        record = data["students"].get(key)
        if record is None:
            return False
        _clear(record)
        _save_raw(data)
        return True


def delete_student(knox_id):
    key = student_key(knox_id)
    with _lock:
        data = _load_raw()
        if key not in data["students"]:
            return False
        del data["students"][key]
        _save_raw(data)
        return True


def backup():
    """현재 저장 파일을 data/backup-<시각>.json 으로 복사해 둔다.

    전체 초기화·삭제처럼 되돌릴 수 없는 작업 직전에 호출한다.
    """
    with _lock:
        if not os.path.exists(DATA_FILE):
            return None
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(DATA_DIR, "backup-%s.json" % stamp)
        # 같은 초에 두 번 실행해도 앞선 백업을 덮어쓰지 않는다.
        serial = 2
        while os.path.exists(path):
            path = os.path.join(DATA_DIR, "backup-%s-%d.json" % (stamp, serial))
            serial += 1
        with open(DATA_FILE, "r", encoding="utf-8") as src:
            content = src.read()
        with open(path, "w", encoding="utf-8") as dst:
            dst.write(content)
        return path


def reset_all():
    """전체 응시자의 답안을 초기화한다. 명단은 남는다. (초기화된 인원 수, 백업 경로)"""
    with _lock:
        data = _load_raw()
        count = len(data["students"])
        if not count:
            return 0, None
        backup_path = backup()
        for record in data["students"].values():
            _clear(record)
        _save_raw(data)
        return count, backup_path


def delete_all():
    """전체 응시 기록을 삭제한다. 명단까지 비운다. (삭제된 인원 수, 백업 경로)"""
    with _lock:
        data = _load_raw()
        count = len(data["students"])
        if not count:
            return 0, None
        backup_path = backup()
        data["students"] = {}
        _save_raw(data)
        return count, backup_path


def set_override(knox_id, qid, verdict):
    """주관식 수동 채점. verdict 는 True / False / None(자동 채점으로 되돌림)."""
    key = student_key(knox_id)
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
