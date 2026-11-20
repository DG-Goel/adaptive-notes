"""
Independent audit of rendered_notes.md for quality issues:
- Duplicates and repetition
- Missing definitions or broken references
- Malformed markdown (tables, lists, code blocks)
- Incorrect mathematical notation
- Unsupported claims (statements without provenance)
"""

import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

def load_rendered_notes(path: Path) -> str:
    """Load rendered markdown"""
    with open(path, encoding='utf-8') as f:
        return f.read()

def load_knowledge(path: Path) -> dict:
    """Load knowledge document for verification"""
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def extract_sections(markdown: str) -> List[Tuple[str, str, str]]:
    """Extract sections with headers and content"""
    sections = []
    lines = markdown.split('\n')
    current_header = None
    current_level = None
    current_content = []
    
    for line in lines:
        header_match = re.match(r'^(#+)\s+(.+)$', line)
        if header_match:
            if current_header:
                sections.append((current_level, current_header, '\n'.join(current_content)))
            current_level = header_match.group(1)
            current_header = header_match.group(2)
            current_content = []
        else:
            current_content.append(line)
    
    if current_header:
        sections.append((current_level, current_header, '\n'.join(current_content)))
    
    return sections

def detect_duplicates(sections: List[Tuple[str, str, str]]) -> List[dict]:
    """Detect duplicate or near-duplicate sections"""
    issues = []
    content_map = defaultdict(list)
    
    for idx, (level, header, content) in enumerate(sections):
        # Normalize content (remove whitespace variations)
        normalized = ' '.join(content.split())
        if len(normalized) > 50:  # Ignore very short sections
            content_map[normalized].append((idx, level, header))
    
    for normalized, occurrences in content_map.items():
        if len(occurrences) > 1:
            issues.append({
                'type': 'DUPLICATE_CONTENT',
                'severity': 'HIGH',
                'occurrences': len(occurrences),
                'sections': [{'index': idx, 'level': level, 'header': header} 
                           for idx, level, header in occurrences],
                'sample': normalized[:200] + '...' if len(normalized) > 200 else normalized
            })
    
    return issues

def detect_broken_markdown(markdown: str) -> List[dict]:
    """Detect malformed markdown structures"""
    issues = []
    lines = markdown.split('\n')
    
    # Check for unclosed code blocks
    code_block_pattern = r'^```'
    code_blocks = [i for i, line in enumerate(lines, 1) if re.match(code_block_pattern, line)]
    if len(code_blocks) % 2 != 0:
        issues.append({
            'type': 'UNCLOSED_CODE_BLOCK',
            'severity': 'HIGH',
            'line': code_blocks[-1] if code_blocks else None,
            'detail': f'Found {len(code_blocks)} code block markers (should be even)'
        })
    
    # Check for malformed tables
    for i, line in enumerate(lines, 1):
        if '|' in line and line.strip().startswith('|'):
            # Check if it's a proper table row
            cells = [c.strip() for c in line.split('|')]
            if len(cells) < 3:  # Need at least |cell1|cell2|
                issues.append({
                    'type': 'MALFORMED_TABLE',
                    'severity': 'MEDIUM',
                    'line': i,
                    'detail': line.strip()[:100]
                })
    
    # Check for broken links
    link_pattern = r'\[([^\]]+)\]\(([^\)]*)\)'
    for i, line in enumerate(lines, 1):
        for match in re.finditer(link_pattern, line):
            text, url = match.groups()
            if not url.strip():
                issues.append({
                    'type': 'EMPTY_LINK',
                    'severity': 'MEDIUM',
                    'line': i,
                    'link_text': text,
                    'detail': match.group(0)
                })
    
    return issues

def detect_unsupported_claims(markdown: str, knowledge: dict) -> List[dict]:
    """Detect statements that might be unsupported claims"""
    issues = []
    
    # Extract all knowledge IDs from markdown
    id_pattern = r'\*\*Knowledge ID:\*\*\s*([A-Z]{3}_\d{4})'
    found_ids = set(re.findall(id_pattern, markdown))
    
    # Count all knowledge items
    all_ids = set()
    for category in ['concepts', 'definitions', 'explanations', 'examples', 
                     'facts', 'formulas', 'procedures', 'relationships']:
        if category in knowledge:
            for item in knowledge[category]:
                all_ids.add(item['knowledge_id'])
    
    # Find missing IDs
    missing = all_ids - found_ids
    if missing:
        issues.append({
            'type': 'MISSING_KNOWLEDGE_IDS',
            'severity': 'MEDIUM',
            'count': len(missing),
            'sample': list(sorted(missing))[:10],
            'detail': f'{len(missing)} knowledge items not referenced in output'
        })
    
    # Find IDs in markdown not in knowledge
    extra = found_ids - all_ids
    if extra:
        issues.append({
            'type': 'EXTRA_KNOWLEDGE_IDS',
            'severity': 'HIGH',
            'count': len(extra),
            'ids': list(sorted(extra)),
            'detail': 'Knowledge IDs in output not found in knowledge.json'
        })
    
    return issues

def detect_repeated_explanations(sections: List[Tuple[str, str, str]]) -> List[dict]:
    """Detect concepts with multiple similar explanations"""
    issues = []
    
    # Group sections by topic (using header text)
    topic_content = defaultdict(list)
    for level, header, content in sections:
        # Normalize header
        topic = re.sub(r'[^a-z0-9\s]', '', header.lower()).strip()
        topic_content[topic].append((level, header, content))
    
    # Find topics with multiple sections
    for topic, entries in topic_content.items():
        if len(entries) > 1 and topic not in ['', 'notes', 'document', 'java']:
            issues.append({
                'type': 'REPEATED_TOPIC',
                'severity': 'MEDIUM',
                'topic': topic,
                'occurrences': len(entries),
                'headers': [header for _, header, _ in entries]
            })
    
    return issues

def check_mathematical_notation(markdown: str) -> List[dict]:
    """Check for incorrect mathematical notation"""
    issues = []
    lines = markdown.split('\n')
    
    # Look for common LaTeX/formula issues
    for i, line in enumerate(lines, 1):
        # Check for unescaped underscores in what might be formulas
        if '_' in line and '```' not in line:
            if not (line.strip().startswith('_') or line.strip().endswith('_')):
                # Might be a formula with unescaped underscore
                if any(marker in line for marker in ['=', '+', '-', '*', '/', '^']):
                    issues.append({
                        'type': 'POTENTIAL_FORMULA_ERROR',
                        'severity': 'LOW',
                        'line': i,
                        'detail': line.strip()[:100]
                    })
    
    return issues

def sample_content_audit(sections: List[Tuple[str, str, str]], count: int = 20) -> List[dict]:
    """Sample random sections for manual review"""
    import random
    
    if len(sections) <= count:
        sample = sections
    else:
        sample = random.sample(sections, count)
    
    audit_items = []
    for idx, (level, header, content) in enumerate(sample):
        audit_items.append({
            'sample_num': idx + 1,
            'header_level': level,
            'header': header,
            'content_length': len(content),
            'content_preview': content.strip()[:300] + '...' if len(content) > 300 else content.strip(),
            'checks': {
                'has_knowledge_id': bool(re.search(r'Knowledge ID:', content)),
                'has_source_reference': bool(re.search(r'Source:', content)),
                'has_substantive_content': len(content.strip()) > 100
            }
        })
    
    return audit_items

def main():
    print("=" * 80)
    print("RENDERED NOTES QUALITY AUDIT")
    print("=" * 80)
    
    validation_dir = Path("data/output/complete_e2e_validation/validation_20261101_174430")
    notes_path = validation_dir / "rendered_notes.md"
    knowledge_path = validation_dir / "knowledge_corrected.json"
    
    # Load files
    print("\nLoading files...")
    markdown = load_rendered_notes(notes_path)
    knowledge = load_knowledge(knowledge_path)
    
    print(f"  Markdown size: {len(markdown):,} chars")
    print(f"  Knowledge items: {knowledge.get('total_items', 'unknown')}")
    
    # Extract sections
    print("\nExtracting sections...")
    sections = extract_sections(markdown)
    print(f"  Found {len(sections)} sections")
    
    # Run audits
    all_issues = []
    
    print("\n1. Checking for duplicates...")
    duplicate_issues = detect_duplicates(sections)
    all_issues.extend(duplicate_issues)
    print(f"   Found {len(duplicate_issues)} duplicate issues")
    
    print("\n2. Checking markdown structure...")
    markdown_issues = detect_broken_markdown(markdown)
    all_issues.extend(markdown_issues)
    print(f"   Found {len(markdown_issues)} markdown issues")
    
    print("\n3. Checking for unsupported claims...")
    unsupported_issues = detect_unsupported_claims(markdown, knowledge)
    all_issues.extend(unsupported_issues)
    print(f"   Found {len(unsupported_issues)} unsupported claim issues")
    
    print("\n4. Checking for repeated explanations...")
    repetition_issues = detect_repeated_explanations(sections)
    all_issues.extend(repetition_issues)
    print(f"   Found {len(repetition_issues)} repetition issues")
    
    print("\n5. Checking mathematical notation...")
    formula_issues = check_mathematical_notation(markdown)
    all_issues.extend(formula_issues)
    print(f"   Found {len(formula_issues)} potential formula issues")
    
    print("\n6. Sampling content for manual review...")
    sample_audit = sample_content_audit(sections, 20)
    print(f"   Sampled {len(sample_audit)} sections")
    
    # Summary
    severity_counts = Counter(issue['severity'] for issue in all_issues)
    
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total issues found: {len(all_issues)}")
    for severity in ['HIGH', 'MEDIUM', 'LOW']:
        if severity in severity_counts:
            print(f"  {severity}: {severity_counts[severity]}")
    
    # Save report
    report = {
        'timestamp': '20261101_180000',
        'notes_path': str(notes_path),
        'markdown_size_chars': len(markdown),
        'section_count': len(sections),
        'total_issues': len(all_issues),
        'severity_summary': dict(severity_counts),
        'issues_by_type': {
            'duplicates': duplicate_issues,
            'markdown_structure': markdown_issues,
            'unsupported_claims': unsupported_issues,
            'repetition': repetition_issues,
            'formulas': formula_issues
        },
        'sample_audit': sample_audit
    }
    
    report_path = validation_dir / "rendered_notes_audit.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed report saved to: {report_path}")
    
    # Display samples of critical issues
    if duplicate_issues:
        print("\n⚠ CRITICAL: Duplicate content detected")
        for issue in duplicate_issues[:3]:
            print(f"  - {issue['occurrences']} occurrences of:")
            for section in issue['sections'][:2]:
                print(f"    {section['level']} {section['header']}")
    
    if [i for i in all_issues if i['type'] == 'EXTRA_KNOWLEDGE_IDS']:
        print("\n⚠ CRITICAL: Extra knowledge IDs in output (not in source)")
        for issue in [i for i in all_issues if i['type'] == 'EXTRA_KNOWLEDGE_IDS']:
            print(f"  IDs: {issue['ids']}")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
