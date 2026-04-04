# tests/test_ner.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pdf_ocr_qt.ner import Entity, NERResult, ENTITY_TYPES


def test_entity_fields():
    e = Entity(text="João Silva", type="PER", page=1, bbox=(10, 20, 80, 15))
    assert e.text == "João Silva"
    assert e.type == "PER"
    assert e.page == 1
    assert e.bbox == (10, 20, 80, 15)


def test_ner_result_empty():
    r = NERResult(entities=[])
    assert r.entities == []


def test_ner_result_with_entities():
    e1 = Entity("Ana", "PER", 1, (0, 0, 30, 12))
    e2 = Entity("São Paulo", "LOC", 2, (5, 5, 60, 12))
    r = NERResult(entities=[e1, e2])
    assert len(r.entities) == 2
    assert r.entities[0].type == "PER"


def test_entity_types_keys():
    for k in ("PER", "ORG", "LOC", "MISC"):
        assert k in ENTITY_TYPES
