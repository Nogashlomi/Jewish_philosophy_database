import re
import os

api_dir = 'app/api'
for filename in os.listdir(api_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(api_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()

        # Remove source query param from defs
        content = re.sub(r',\s*source:\s*Optional\[str\]\s*=\s*Query\([^)]*\)', '', content)
        content = re.sub(r'source:\s*Optional\[str\]\s*=\s*Query\([^)]*\),\s*', '', content)
        content = re.sub(r'source:\s*Optional\[str\]\s*=\s*Query\([^)]*\)', '', content)
        
        # Remove source argument from entity_service calls
        content = re.sub(r',\s*source=source', '', content)
        content = re.sub(r'source=source,\s*', '', content)
        content = re.sub(r'source=source', '', content)

        with open(filepath, 'w') as f:
            f.write(content)
