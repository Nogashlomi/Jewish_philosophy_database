import csv
import os

input_file = os.path.join(os.path.dirname(__file__), '../data/jewish_encyclopedia_raw.csv')
output_file = os.path.join(os.path.dirname(__file__), '../data/jewish_encyclopedia_philosophers.csv')

with open(input_file, 'r', encoding='utf-8') as f_in, open(output_file, 'w', newline='', encoding='utf-8') as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
    writer.writeheader()
    
    count = 0
    for row in reader:
        snippet = row.get('Raw Text Snippet', '')
        if snippet and 'philosopher' in snippet.lower():
            writer.writerow(row)
            count += 1
            
print(f"Filtered {count} philosophers to {output_file}")
