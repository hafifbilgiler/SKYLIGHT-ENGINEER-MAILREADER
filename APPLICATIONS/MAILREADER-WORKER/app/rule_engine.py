def apply_rules(mail, rules):
    for r in rules:
        for cond in r["conditions"]:
            field = cond["field"]
            value = cond["value"].lower()

            target = mail.get(field, "").lower()
            if value in target:
                return r["action"], r["name"]

    return None, None
