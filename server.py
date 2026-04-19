from flask import Flask, request, jsonify

app = Flask(__name__)

# -------------------------
# SAFE ENV
# -------------------------
def new_env():
    return {"vars": {}}


# -------------------------
# EXPRESSION EVAL
# -------------------------
def eval_expr(expr, env):
    expr = str(expr).strip()

    for k, v in env["vars"].items():
        expr = expr.replace(k, str(v))

    try:
        return eval(expr, {"__builtins__": {}}, {})
    except:
        return expr


# -------------------------
# EXECUTOR
# -------------------------
def run_code(lines):
    env = new_env()
    output = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # ---------------- local
        if line.startswith("local "):
            try:
                line = line.replace("local ", "")
                name, value = line.split("=")
                env["vars"][name.strip()] = eval_expr(value, env)
            except:
                output.append(f"Error: invalid variable declaration at line {i+1}")

        # ---------------- print(x)
        elif line.startswith("print"):
            expr = line.replace("print", "").strip()

            if not (expr.startswith("(") and expr.endswith(")")):
                output.append(f"Error line {i+1}: use print(x)")
            else:
                expr = expr[1:-1]
                output.append(str(eval_expr(expr, env)))

        # ---------------- if
        elif line.startswith("if ") and "then" in line:
            condition = line[3:].replace("then", "").strip()

            then_block = []
            else_block = []

            i += 1
            mode = "then"

            while i < len(lines) and lines[i].strip() != "end":
                l = lines[i].strip()

                if l.startswith("ifnot"):
                    mode = "else"
                else:
                    if mode == "then":
                        then_block.append(l)
                    else:
                        else_block.append(l)

                i += 1

            try:
                cond = eval(str(eval_expr(condition, env)))
            except:
                cond = False

            output.extend(run_code(then_block if cond else else_block))

        i += 1

    return output


# -------------------------
# API ROUTE
# -------------------------
@app.route("/run", methods=["POST"])
def run():
    try:
        code = request.json["code"]
        lines = code.split("\n")

        result = run_code(lines)

        return jsonify({
            "output": "\n".join(result),
            "error": None
        })

    except Exception as e:
        return jsonify({
            "output": "",
            "error": str(e)
        })


# -------------------------
# START SERVER
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
