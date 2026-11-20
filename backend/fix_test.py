import re

path = 'tests/test_evaluation_unit.py'
content = open(path, 'r', encoding='utf-8').read()

# Fix AssembledItem - add missing required fields
old_pattern = r'AssembledItem\(\s+knowledge_id="K001",\s+document_id="TEST_DOC",\s+source_unit_ids=\["S001"\],\s+primary_format=RepresentationFormat\.STANDARD_TEXT,\s+format_content=\{"content": "test"\}\s+\)'
new_text = '''AssembledItem(
                            knowledge_id="K001",
                            document_id="TEST_DOC",
                            knowledge_type="concept",
                            source_unit_ids=["S001"],
                            primary_format=RepresentationFormat.STANDARD_TEXT,
                            selection_confidence=0.8,
                            confidence_label="high",
                            selection_reasoning="test",
                            format_content={"content": "test"},
                            position_in_section=0,
                            ordering_rationale="test"
                        )'''

content = re.sub(old_pattern, new_text, content)

open(path, 'w', encoding='utf-8').write(content)
print('Fixed AssembledItem construction')
