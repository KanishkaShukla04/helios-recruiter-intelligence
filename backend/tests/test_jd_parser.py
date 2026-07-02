from app.parser.jd_parser import JDParser


def test_parse_extracts_preferred_locations_and_industries():
    jd_text = (
        "We need 5+ years in python, docker, aws. "
        "Work in fintech and AI. Bangalore or remote."
    )

    result = JDParser().parse(jd_text).to_dict()

    assert result["preferred_locations"] == ["bangalore", "remote"]
    assert result["industries"] == ["fintech", "ai"]
