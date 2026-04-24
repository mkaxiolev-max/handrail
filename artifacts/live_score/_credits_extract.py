import json, sys
try:
    d = json.load(open(sys.argv[1]))
    c = d.get("credits", {})
    agg = {}
    for k, v in c.items():
        inst = k.split(".")[0]
        try:
            v = float(v)
        except Exception:
            continue
        agg[inst] = agg.get(inst, 0) + v
    for k, v in agg.items():
        print(k + "=" + str(v))
except Exception:
    pass
