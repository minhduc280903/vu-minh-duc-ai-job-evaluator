with open('analyze_output.txt', 'rb') as f:
    text = f.read().decode('utf-16le', errors='replace')

lines = text.split('\n')
for i, line in enumerate(lines):
    if "phát hiện" in line.lower() or "jobs phù hợp" in line.lower() or "🏆" in line:
        print("\n".join(lines[i:]))
        break
