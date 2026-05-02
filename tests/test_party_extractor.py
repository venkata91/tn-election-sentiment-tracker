import pytest
from pipeline.party_extractor import extract_mentions

def test_extract_dmk_plus_english():
    mentions = extract_mentions("I support DMK in this election")
    parties = [m[0] for m in mentions]
    assert "DMK+" in parties

def test_extract_dmk_plus_tamil_script():
    mentions = extract_mentions("திமுக இந்த தேர்தலில் வெல்லும்")
    parties = [m[0] for m in mentions]
    assert "DMK+" in parties

def test_extract_dmk_plus_candidate_type():
    mentions = extract_mentions("Stalin is a great leader for Tamil Nadu")
    parties = [m[0] for m in mentions]
    assert "DMK+" in parties
    types = [m[1] for m in mentions if m[0] == "DMK+"]
    assert "candidate" in types

def test_extract_dmk_plus_hashtag_type():
    mentions = extract_mentions("#DMK is trending today in Tamil Nadu")
    parties = [m[0] for m in mentions]
    assert "DMK+" in parties
    types = [m[1] for m in mentions if m[0] == "DMK+"]
    assert "hashtag" in types

def test_extract_multiple_alliances():
    mentions = extract_mentions("DMK and AIADMK are competing fiercely in Tamil Nadu 2026")
    parties = [m[0] for m in mentions]
    assert "DMK+" in parties
    assert "ADMK+" in parties

def test_no_party_mention():
    mentions = extract_mentions("The weather today is nice in Chennai")
    assert mentions == []

def test_extract_admk_plus_bjp_candidate():
    mentions = extract_mentions("Annamalai held a rally in Coimbatore")
    parties = [m[0] for m in mentions]
    assert "ADMK+" in parties

def test_extract_admk_plus_eps():
    mentions = extract_mentions("EPS addressed a press conference about Tamil Nadu")
    parties = [m[0] for m in mentions]
    assert "ADMK+" in parties

def test_extract_tvk():
    mentions = extract_mentions("Thalapathy Vijay's TVK is gaining momentum")
    parties = [m[0] for m in mentions]
    assert "TVK" in parties

def test_extract_ntk_seeman():
    mentions = extract_mentions("Seeman NTK rally in Chennai draws huge crowd")
    parties = [m[0] for m in mentions]
    assert "NTK" in parties

def test_no_duplicate_party_in_result():
    mentions = extract_mentions("DMK DMK DMK wins the election")
    dmk_mentions = [m for m in mentions if m[0] == "DMK+"]
    assert len(dmk_mentions) == 1
