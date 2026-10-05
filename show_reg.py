import re, html, sys
t = open(sys.argv[1], encoding="utf-8", errors="replace").read()
t = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", t)
t = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>", "\n", t)
t = re.sub(r"<[^>]+>", " ", t)
t = html.unescape(t)
t = re.sub(r"[ \t]+", " ", t)
t = re.sub(r"\n\s*\n+", "\n\n", t)
lines = [l.strip() for l in t.split("\n")]
out, keep = [], False
for l in lines:
    if re.search(r"399\.81", l):
        keep = True
    if keep and l:
        out.append(l)
print("\n".join(out[:120]))
