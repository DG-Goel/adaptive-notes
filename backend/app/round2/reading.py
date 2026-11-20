"""Format the existing Round 2 content for reading."""
import re

JAVA_TOPICS = {
    1: 'Course overview', 3: 'Java setup and tools', 5: 'Methods, classes and naming',
    9: 'Projects and packages', 11: 'Compiling and running Java', 19: 'The Java platform',
    22: 'Variables and primitive types', 31: 'Objects and references', 38: 'Strings and string methods',
    46: 'Arrays and matrices', 53: 'Constants and arithmetic', 59: 'Casting and parsing',
    68: 'Formatting numbers', 73: 'Reading input', 77: 'Mortgage calculator walkthrough',
    83: 'Control flow and comparisons', 90: 'Conditional statements',
    97: 'Switch statements and FizzBuzz', 104: 'Loops and iteration',
}


def reading_markdown(refined, *, java_layout=False):
    """Retain generated prose and visual blocks in their existing order."""
    result = ['# Java study notes' if java_layout else '# Study notes']
    for block in re.split(r'\n\s*\n', refined.strip()):
        block = block.strip()
        if block.startswith(('*Render complete:', '### Additional details:', 'Source information not completed:')):
            break
        source = re.fullmatch(r'## Source G(\d+)', block)
        if source:
            topic = JAVA_TOPICS.get(int(source[1])) if java_layout else None
            if topic:
                result.append(f'## {topic}')
            continue
        if block.startswith(('> ', '*[Knowledge ID:', '*Source:', '*Based on Round 1',
                             '*Generated from assembled notes', 'Available source excerpt:',
                             '# Study notes:', '### Source gaps without')) or block == '---':
            continue
        if block.startswith(('#', '|', '![', '```', '- ', '* ', '1. ')):
            if result[-1].startswith('## ') and block.startswith('### ') and result[-1][3:] == block[4:]:
                continue
            result.append(block)
        else:
            bullet = '- ' + ' '.join(line.strip() for line in block.splitlines())
            if result[-1].startswith('- '):
                result[-1] += '\n' + bullet
            else:
                result.append(bullet)
    return '\n\n'.join(result) + '\n'
