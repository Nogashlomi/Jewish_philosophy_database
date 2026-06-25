import re

with open('app/core/queries.py', 'r') as f:
    content = f.read()

# Replace time queries on TimeRelation (?tr or ?rel)
# E.g. OPTIONAL { ?tr jp:timeFrom ?birthYear }
# We need to change to: OPTIONAL { ?tr jp:hasTimeData ?td . ?td jp:timeFrom ?birthYear }

# But in LIST_PERSONS we have:
# OPTIONAL {{ ?tr jp:birthYear|jp:timeFrom ?birthYear }}
content = re.sub(r'OPTIONAL \{\{ \?tr jp:birthYear\|jp:timeFrom \?birthYear \}\}', 'OPTIONAL {{ ?tr jp:hasTimeData ?td . ?td jp:timeFrom ?birthYear }}', content)

# In GET_PERSON_TIMES:
# OPTIONAL { ?rel jp:timeFrom ?start }
content = re.sub(r'OPTIONAL \{ \?rel jp:timeFrom \?start \}', 'OPTIONAL { ?rel jp:hasTimeData ?td . ?td jp:timeFrom ?start }', content)
content = re.sub(r'OPTIONAL \{ \?rel jp:timeUntil \?end \}', 'OPTIONAL { ?rel jp:hasTimeData ?td . ?td jp:timeUntil ?end }', content)
content = re.sub(r'OPTIONAL \{ \?rel jp:timeLabel \?label \}', 'OPTIONAL { ?rel jp:hasTimeData ?td . ?td jp:timeLabel ?label }', content)

# In GET_PERSON_DETAIL:
content = re.sub(r'OPTIONAL \{\{ \?tr jp:timeFrom \?by \}\}', 'OPTIONAL {{ ?tr jp:hasTimeData ?tdb . ?tdb jp:timeFrom ?by }}', content)
content = re.sub(r'OPTIONAL \{\{ \?tr jp:timeUntil \?dy \}\}', 'OPTIONAL {{ ?tr jp:hasTimeData ?tdd . ?tdb jp:timeUntil ?dy }}', content)

with open('app/core/queries.py', 'w') as f:
    f.write(content)
