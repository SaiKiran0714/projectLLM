# core/extract.py
import os, re, json
from typing import Optional, Dict
from pydantic import BaseModel, Field, ValidationError

# -------- Pydantic output schemas --------
class ReqJSON(BaseModel):
    metric: Optional[str]
    comparator: Optional[str]  # one of ≥, ≤, =, <, >
    value: Optional[float]
    unit: Optional[str]
    component: Optional[str]
    condition: Optional[str]

class ChatFilter(BaseModel):
    component: Optional[str] = None
    metric: Optional[str] = None
    status: Optional[str] = None  # pass/fail/unknown
    min_value: Optional[float] = None
    unit: Optional[str] = None

# --------- simple fallback regex tools ----------
METRIC_ALIASES = {
    "shear": "shear_strength",
    "shear_strength": "shear_strength",
    "gap": "gap",
    "rigidity": "rigidity",
}

def _alias_metric(txt: str) -> Optional[str]:
    for k,v in METRIC_ALIASES.items():
        if re.search(rf"\b{k}\b", txt, re.I):
            return v
    return None

def _regex_req(text: str) -> Dict:
    # find number + unit
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kN|N|mm)\b", text, re.I)
    val, unit = (float(m.group(1)), m.group(2)) if m else (None, None)
    # find comparator words/symbols
    comp = None
    if re.search(r"≥|>=|at\s+least|minimum|min", text, re.I): comp = "≥"
    elif re.search(r"≤|<=|not\s+exceed|maximum|max", text, re.I): comp = "≤"
    elif re.search(r"\bequals?\b|^=\b", text, re.I): comp = "="
    elif re.search(r"\bmore than\b|>", text, re.I): comp = ">"
    elif re.search(r"\bless than\b|<", text, re.I): comp = "<"
    metric = _alias_metric(text) or None
    # component and condition hints
    compo = None
    for c in ["door_frame","panel","b_pillar","roof","hood","door"]:
        if re.search(rf"\b{c}\b", text, re.I): compo = c; break
    cond = None
    if re.search(r"-?\d+\s*°\s*C", text): cond = re.search(r"(-?\d+\s*°\s*C)", text).group(1)
    if re.search(r"ambient|room temperature", text, re.I): cond = "ambient"
    return ReqJSON(metric=metric, comparator=comp, value=val, unit=unit, component=compo, condition=cond).model_dump()

# ------------- LLM Providers ---------------
def _have_llm():
    """Check if Groq provider is available"""
    from core.llm_providers import have_llm
    return have_llm()

def _llm_chat(messages: list, **kwargs) -> str:
    """Use Groq provider for LLM chat"""
    from core.llm_providers import llm_chat
    return llm_chat(messages, **kwargs)

REQ_SYS_PROMPT = """You extract structured requirement facts as JSON.
Return ONLY a JSON object with keys:
metric (snake_case), comparator (one of ≥, ≤, =, <, >), value (number), unit (kN/N/mm),
component (snake_case if present), condition (string or null).
If ambiguous, use nulls. Do not add extra keys."""
REQ_USER_TMPL = """Text:
---
{TEXT}
---"""

def extract_requirement_text_to_json(text: str) -> Dict:
    text = (text or "").strip()
    if not text:
        return ReqJSON().model_dump()
    # try LLM providers
    if _have_llm():
        msg = [
            {"role":"system","content": REQ_SYS_PROMPT},
            {"role":"user","content": REQ_USER_TMPL.format(TEXT=text)}
        ]
        try:
            content = _llm_chat(msg, temperature=0)
            # Extract JSON from response (some models add extra text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(content)
            
            # Clean data for validation
            clean_data = {k: v for k, v in data.items() if v is not None}
            return ReqJSON(**clean_data).model_dump(exclude_none=True)
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            pass
    # fallback: regex
    return _regex_req(text)

# ----------- Explanations (grounded) -----------
def explain_from_facts(facts: Dict) -> str:
    """
    facts = {
      "component":..., "metric":..., "status":"pass/fail/unknown",
      "measured_norm":..., "target":..., "unit":..., "run_id":...
    }
    """
    if not _have_llm():
        # deterministic template
        st = facts.get("status","unknown")
        if st == "pass":
            return (f"Pass: measured {facts.get('measured_norm'):.3g} {facts.get('unit')} "
                    f"meets target {facts.get('target')} {facts.get('unit')}.")
        if st == "fail":
            return (f"Fail: measured {facts.get('measured_norm'):.3g} {facts.get('unit')} "
                    f"is below/above target {facts.get('target')} {facts.get('unit')}.")
        return "Unknown: missing unit/comparator/data."
    # LLM concise explanation
    prompt = f"""Using ONLY these JSON facts, write 2 short bullets explaining the result.
Facts: {json.dumps(facts)}
"""
    try:
        content = _llm_chat([{"role":"user","content":prompt}], temperature=0.2)
        return content.strip()
    except Exception as e:
        print(f"LLM explanation failed: {e}")
        return "Explanation unavailable."

# ----------- Chat → filters --------------------
CHAT_SYS = """You convert a user's query about tests into JSON filters with keys:
component, metric, status (pass/fail/unknown), min_value (number), unit.

IMPORTANT RULES:
- Words like "failed", "passing", "passed" are STATUS not component names
- Component names are physical parts like "door", "bumper", "engine", etc.
- Status values: "fail" for failed/failing, "pass" for passed/passing

Examples:
- "show failed components" → {"status": "fail"}  
- "show failed components with kN unit" → {"status": "fail", "unit": "kN"}
- "show tests with unit kN" → {"unit": "kN"}
- "show failed tests > 100 N" → {"status": "fail", "min_value": 100, "unit": "N"}
- "show door components with kN unit" → {"component": "door", "unit": "kN"}
- "show passed door tests" → {"component": "door", "status": "pass"}

Return ONLY JSON. If a key is absent, omit it."""
def _regex_filters(q: str) -> Dict:
    d = {}
    ql = q.lower()
    
    # Parse status FIRST and remove status words to avoid component conflicts
    status_processed_query = ql
    if "failed" in ql:
        d["status"] = "fail"
        status_processed_query = ql.replace("failed", "")
    elif "fail" in ql:
        d["status"] = "fail"
        status_processed_query = ql.replace("fail", "")
    elif "passed" in ql:
        d["status"] = "pass"  
        status_processed_query = ql.replace("passed", "")
    elif "pass" in ql:
        d["status"] = "pass"
        status_processed_query = ql.replace("pass", "")
    
    # Parse components from the processed query (status words removed)
    for c in ["door_frame","panel","b_pillar","roof","hood","door","bumper","trunk","fender","windshield","quarter_panel","spoiler","mirror","grille","tailgate","headlight","antenna","wheel_well","fuel_door","license_plate","exhaust","side_skirt","sunroof","dashboard","console","seat","airbag","steering","pedal","armrest","cupholder","visor","handle","vent","trim"]:
        if c in status_processed_query: 
            d["component"] = c
            break
    
    # Parse metrics
    for m in METRIC_ALIASES:
        if m in ql: 
            d["metric"] = METRIC_ALIASES[m]
            break
    
    # Look for unit filtering patterns (unit alone without numbers)
    unit_patterns = [
        r"(?:unit|units?)\s+(?:having|with|of|in|is|are)\s*(kn|n|mm)",
        r"(?:having|with)\s+unit\s+(kn|n|mm)",
        r"(?:in|with)\s+(kn|n|mm)\s+(?:unit|units?)",
        r"\b(kn|n|mm)\s+(?:unit|units?)",
        r"(?:unit|units?)\s+(?:=|equals?|is)\s*(kn|n|mm)",
        r"unit\s+having\s+(kn|n|mm)",  # Direct match for "unit having kN"
        r"with\s+(?:unit\s+)?having\s+(kn|n|mm)"  # "with unit having kN"
    ]
    
    for pattern in unit_patterns:
        m = re.search(pattern, ql, re.IGNORECASE)
        if m:
            # Normalize unit case
            unit = m.group(1).lower()
            if unit == "kn": 
                d["unit"] = "kN"
            elif unit == "n":
                d["unit"] = "N" 
            elif unit == "mm":
                d["unit"] = "mm"
            break
    
    # Look for number with unit (min_value + unit)
    if not d.get("unit"):  # Only if unit not already set from above
        m = re.search(r"(\d+(?:\.\d+)?)\s*(kn|n|mm)", ql, re.IGNORECASE)
        if m:
            d["min_value"] = float(m.group(1))
            # Normalize unit case
            unit = m.group(2).lower()
            if unit == "kn": 
                d["unit"] = "kN"
            elif unit == "n":
                d["unit"] = "N" 
            elif unit == "mm":
                d["unit"] = "mm"
        else:
            # Look for number without unit in "greater than", ">", "≥" contexts
            patterns = [
                r"(?:greater than|more than|above|>|≥)\s*(\d+(?:\.\d+)?)",
                r"(\d+(?:\.\d+)?)\s*(?:or more|or greater|plus)",
                r"measured_norm\s*[>≥]\s*(\d+(?:\.\d+)?)",
            ]
            for pattern in patterns:
                m = re.search(pattern, ql)
                if m:
                    d["min_value"] = float(m.group(1))
                    # Try to infer unit from context or use a sensible default
                    if any(unit in ql for unit in ["kn", "kilo"]):
                        d["unit"] = "kN"
                    elif "n" in ql and "mm" not in ql:
                        d["unit"] = "N"
                    elif "mm" in ql:
                        d["unit"] = "mm"
                    break
    
    return ChatFilter(**d).model_dump()
def parse_query_to_filters(q: str) -> Dict:
    if _have_llm():
        try:
            content = _llm_chat([
                {"role":"system","content":CHAT_SYS},
                {"role":"user","content":q}
            ], temperature=0)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(content)
            return ChatFilter(**data).model_dump()
        except Exception as e:
            print(f"LLM query parsing failed: {e}")
            pass
    return _regex_filters(q or "")
