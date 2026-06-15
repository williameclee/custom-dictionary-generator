from pathlib import Path
import tempfile
import pytest
from eaps_dict.parser import parse_nws_glossary, parse_naer_translations

def test_parse_nws_glossary():
    sample_data = (
        "Entry\tAcronym\tDescription\tType\tSynonyms\tSeeAlso\tAliases\n"
        "AA\tAA\tAA\tAA\tAA\tAA\tAA\n"  # should be skipped
        "A\t\tsymbol used on long-term climate outlooks\t\t\t\t\n"
        "abundant\tABNDT\tplentiful\tmeteorology\t\t\t\n"
        "abundant\t\trich\tgeology\t\t\t\n"  # duplicate Entry to test grouping
    )
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp:
        temp.write(sample_data)
        temp_path = temp.name

    try:
        entries = parse_nws_glossary(temp_path)
        
        # We expect 2 grouped entries: 'A' and 'abundant'
        assert len(entries) == 2
        
        # 'A' details
        assert entries[0]["entry_id"] == "A"
        assert entries[0]["descriptions"] == ["symbol used on long-term climate outlooks"]
        assert entries[0]["acronyms"] == []
        
        # 'abundant' details (grouped)
        assert entries[1]["entry_id"] == "abundant"
        # Type 'meteorology' -> capitalized 'Meteorology'
        # Type 'geology' -> capitalized 'Geology'
        assert entries[1]["descriptions"] == [
            '<span class="type">Geology</span>rich',
            '<span class="type">Meteorology</span>plentiful'
        ]
        assert entries[1]["acronyms"] == ["ABNDT"]
    finally:
        Path(temp_path).unlink()

def test_parse_naer_translations():
    # Columns: English, TraditionalChinese, Parent, Field, Var5, Aliases, Notes, Acronym
    sample_data = (
        "a priori probability\t先驗機率\t\t大氣學\t\t\t\t\n"
        "English\tTraditionalChinese\tParent\tField\tVar5\tAliases\tNotes\tAcronym\n" # header in middle, should be skipped
        " A horizon\tA層；表土層\t\t地理學\t\t\t\t\n"  # leading space, should be stripped
        "ablation\t剝蝕\t\t水文學\t溶蝕\t\t地質\t\n" # Var5 = 溶蝕, Notes = 地質
        "ablation\t冰融\t\t海洋地質學\t融化\t\t\t\n" # Var5 = 融化, Notes empty
        "abrasion\t剝蝕\t\t地質學\t\t\t\t\n" # Shares translation '剝蝕' with ablation
    )
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp:
        temp.write(sample_data)
        temp_path = temp.name

    try:
        entries = parse_naer_translations(temp_path)
        
        # Sorted order should be: 'A horizon', 'a priori probability', 'ablation', 'abrasion'
        assert len(entries) == 4
        
        # 'A horizon'
        assert entries[0]["entry_id"] == "A" + " horizon"
        assert entries[0]["descriptions"] == ['<span class="type">地理學</span>A層；表土層']
        assert entries[0]["synonyms"] == []
        
        # 'a priori probability'
        assert entries[1]["entry_id"] == "a priori probability"
        assert entries[1]["descriptions"] == ['<span class="type">大氣學</span>先驗機率']
        assert entries[1]["synonyms"] == []
        
        # 'ablation' (grouped)
        assert entries[2]["entry_id"] == "ablation"
        assert entries[2]["descriptions"] == [
            '<span class="type">水文學</span>剝蝕（同：溶蝕）（地質）<br/><span class="entry-synonyms">abrasion</span>',
            '<span class="type">海洋地質學</span>冰融（同：融化）'
        ]
        assert entries[2]["synonyms"] == ["abrasion"]
        
        # 'abrasion'
        assert entries[3]["entry_id"] == "abrasion"
        assert entries[3]["descriptions"] == ['<span class="type">地質學</span>剝蝕<br/><span class="entry-synonyms">ablation</span>']
        assert entries[3]["synonyms"] == ["ablation"]
    finally:
        Path(temp_path).unlink()
