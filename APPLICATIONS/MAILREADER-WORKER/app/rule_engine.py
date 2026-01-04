def _match_condition(mail: dict, cond: dict) -> bool:
    field = (cond.get("field") or "").strip()
    op = (cond.get("op") or "icontains").strip().lower()
    value = (cond.get("value") or "").strip()

    target = str(mail.get(field, "") or "")

    if op in ("icontains", "contains"):
        return value.lower() in target.lower()
    if op in ("eq", "equals"):
        return target.strip().lower() == value.strip().lower()

    # default fallback
    return value.lower() in target.lower()


def apply_rules(mail: dict, rules: list):
    """
    Returns: (action_dict, rule_name) or (None, None)
    Rule schema:
      conditions: [{"field":"subject","op":"icontains","value":"invoice"}]
      action: {"set_category":"important"}  OR {"set_category":"spam"}
    """
    for r in rules:
        conditions = r.get("conditions") or []
        if not isinstance(conditions, list):
            continue

        for cond in conditions:
            if not isinstance(cond, dict):
                continue
            if _match_condition(mail, cond):
                return r.get("action") or {}, r.get("name") or "rule"

    return None, None
