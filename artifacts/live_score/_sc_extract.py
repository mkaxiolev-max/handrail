import json, sys
d = json.load(open(sys.argv[1]))
inst = d.get("instruments", {})
for k in ["I1","I2","I3","I4","I5","I6","I7"]:
    v = inst.get(k, {}).get("current_live")
    if v is not None:
        print(k + "=" + str(v))
