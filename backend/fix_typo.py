import re
with open('app/core/queries.py', 'r') as f:
    c = f.read()

c = c.replace('?tdb jp:timeUntil ?dy', '?tdd jp:timeUntil ?dy')
with open('app/core/queries.py', 'w') as f:
    f.write(c)
