import json
from app.extraction.llm_provider import GroqProvider


def test_valid_json_with_code_braces_and_escaped_quote_is_complete():
    guard=GroqProvider.__new__(GroqProvider)
    for text in ['if (x) {','Print "hello"','a closing bracket ] and an opening {','...']:
        assert not guard._has_truncation_indicators(json.dumps({'text':text}))
    assert guard._has_truncation_indicators('{"text":"unfinished')
