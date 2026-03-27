from typing import Any,Dict
def should_run(condition:str|None,context:Dict[str,Any])->bool:
 if not condition:return True
 lhs,rhs=[x.strip()for x in condition.split("==",1)]
 parts=lhs.split(".")
 if len(parts)!=3 or parts[0]!="steps":raise ValueError(f"unsupported condition lhs: {lhs}")
 step_id,field=parts[1],parts[2]
 step_ctx=context.get("steps",{}).get(step_id,{})
 value=step_ctx.get(field)
 rhs_lower=rhs.lower()
 if rhs_lower=="true":expected=True
 elif rhs_lower=="false":expected=False
 elif rhs.startswith('"')and rhs.endswith('"'):expected=rhs[1:-1]
 else:raise ValueError(f"unsupported condition rhs: {rhs}")
 return value==expected
