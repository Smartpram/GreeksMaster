import csv

with open('NSEScripMaster.txt', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    row = next(reader)
    
    print("First row - checking key formats and values:\n")
    for i, (k, v) in enumerate(list(row.items())[:30]):
        val_short = (v or '')[:35] if v else '(empty)'
        print(f"{i:2d}. {repr(k)[:50]:50s} => {repr(val_short)}")
