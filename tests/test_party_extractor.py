import pytest
from pipeline.party_extractor import extract_mentions

def test_extract_dmk_english():
    mentions = extract_mentions("I support DMK in this election")
    parties = [m[0] for m in mentions]
    assert "DMK" in parties

def test_extract_dmk_tamil_script():
    mentions = extract_mentions("திமுக இந்த தேர்தலில் வெல்லும்")
    parties = [m[0] for m in mentions]
    assert "DMK" in parties

def test_extract_candidate_name_direct_type():
    mentions = extract_mentions("Stalin is a great leader for Tamil Nadu")
    parties = [m[0] for m in mentions]
    assert "DMK" in parties
    types = [m[1] for m in mentions if m[0] == "DMK"]
    assert "candidate" in types

def test_extract_hashtag_type():
    mentions = extract_mentions("#DMK is trending today in Tamil Nadu")
    parties = [m[0] for m in mentions]
    assert "DMK" in parties
    types = [m[1] for m in mentions if m[0] == "DMK"]
    assert "hashtag" in types

def test_extract_multiple_parties():
    mentions = extract_mentions("DMK and AIADMK are competing fiercely in Tamil Nadu 2026")
    parties = [m[0] for m in mentions]
    assert "DMK" in parties
    assert "AIADMK" in parties

def test_no_party_mention():
    mentions = extract_mentions("The weather today is nice in Chennai")
    assert mentions == []

def test_extract_bjp_candidate():
    mentions = extract_mentions("Annamalai held a rally in Coimbatore")
    parties = [m[0] for m in mentions]
    assert "BJP" in parties

def test_extract_aiadmk_eps():
    mentions = extract_mentions("EPS addressed a press conference about Tamil Nadu")
    parties = [m[0] for m in mentions]
    assert "AIADMK" in parties

def test_no_duplicate_party_in_result():
    mentions = extract_mentions("DMK DMK DMK wins the election")
    dmk_mentions = [m for m in mentions if m[0] == "DMK"]
    assert len(dmk_mentions) == 1
