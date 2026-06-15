import pytest

from eaps_dict.models import Meaning, populate_list_template


def test_populate_list_template():
    txt = populate_list_template(["a", "b", "c"], r"[{r}]", r"'{r}'", r"{r}")
    assert txt == r"['a' 'b' 'c']"


def test_meaning_init():
    m = Meaning("desc", acronyms="a")
    assert m.descriptions == ["desc"]
    assert m.field is None
    assert m.acronyms == ["a"]
    assert m.synonyms == []
    m = Meaning(["desc1", "desc2"], acronyms=["a1", "a2"])
    assert m.descriptions == ["desc1", "desc2"]
    assert m.field is None
    assert m.acronyms == ["a1", "a2"]
    assert m.synonyms == []
    m = Meaning("desc1; desc2", acronyms="a1; a2")
    assert m.descriptions == ["desc1", "desc2"]
    assert m.field is None
    assert m.acronyms == ["a1", "a2"]
    assert m.synonyms == []
