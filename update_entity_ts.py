import re

with open('frontend/src/types/entity.ts', 'r') as f:
    content = f.read()

# Remove interfaces
interfaces_to_remove = [
    r'export interface Scholar {[^}]*}',
    r'export interface Source {[^}]*}',
    r'export interface ScholarlyList {[^}]*}',
    r'export interface ScholarlyMention {[^}]*}'
]

for p in interfaces_to_remove:
    content = re.sub(p, '', content)

# Remove fields from PersonDetail
content = re.sub(r'\s*sources:\s*string\[\]', '', content)
content = re.sub(r'\s*authorities:\s*string\[\]', '', content)
content = re.sub(r'\s*scholarly:\s*ScholarlyMention\[\]', '', content)

with open('frontend/src/types/entity.ts', 'w') as f:
    f.write(content)
