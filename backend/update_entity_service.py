import re

with open('app/services/entity_service.py', 'r') as f:
    content = f.read()

# Remove imports
content = re.sub(r'from app.schemas.source import Source\n', '', content)
content = re.sub(r'from app.schemas.scholarly import ScholarlyList, ScholarlyDetail\n', '', content)

# Remove _get_source_filter
content = re.sub(r'    def _get_source_filter\(self, source_id: Optional\[str\], var_name: str = "uri"\) -> str:\n(?:        .*?\n)*', '', content)

# Remove list_sources
content = re.sub(r'    def list_sources\(self\) -> List\[dict\]:\n(?:        .*?\n)*?    def list_languages', '    def list_languages', content)

# Remove list_scholarly_works and get_scholarly_detail
content = re.sub(r'    def list_scholarly_works\(self,.*?\n(?:        .*?\n)*?    def get_scholarly_detail\(self,.*?\n(?:        .*?\n)*?    def get_geo_json', '    def get_geo_json', content)

# Remove source= parameters from method signatures
content = re.sub(r'source: Optional\[str\]( = None)?, ', '', content)
content = re.sub(r'source: Optional\[str\]( = None)?', '', content)

# Remove sf assignments
content = re.sub(r'        sf = self._get_source_filter\(.*?\)\n', '', content)
content = re.sub(r'        sf = "" .*?\n', '', content)

# Replace source_filter=sf with just removing it
content = re.sub(r'source_filter=sf, ', '', content)
content = re.sub(r', source_filter=sf', '', content)
content = re.sub(r'source_filter=".*?", ', '', content)
content = re.sub(r', source_filter=".*?"', '', content)
content = re.sub(r'source_filter=sf', '', content)
content = re.sub(r'source_filter=""', '', content)

# Update get_person_detail
# Remove authorities
content = re.sub(r'        authorities = \[\]\n(?:        .*?\n)*?        works = \[\]', '        works = []', content)
# Remove sources
content = re.sub(r'        sources = \[\]\n(?:        .*?\n)*?        authorities = \[\]', '        authorities = []', content) # if authorities wasn't matched properly
content = re.sub(r'        sources = \[\]\n(?:        .*?\n)*?        works = \[\]', '        works = []', content)
# Remove scholarly mentions
content = re.sub(r'        scholarly = \[\]\n(?:        .*?\n)*?        places = \[\]', '        places = []', content)
# Remove from PersonDetail instantiation
content = re.sub(r'            sources=sources,\n', '', content)
content = re.sub(r'            authorities=authorities,\n', '', content)
content = re.sub(r'            scholarly=scholarly,\n', '', content)

# Update get_network
content = re.sub(r'source=source', '', content)
content = re.sub(r'source=\w+', '', content)

with open('app/services/entity_service.py', 'w') as f:
    f.write(content)
