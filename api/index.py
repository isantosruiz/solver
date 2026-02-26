from __future__ import annotations

import re
from typing import Iterable

from flask import Flask, jsonify, render_template, request
from sympy import E, I, Eq, Float, Function, Integer, Rational, Symbol, factorial, latex, pi, solve
from sympy.functions import (
    Abs,
    acos,
    asin,
    atan,
    cos,
    cosh,
    exp,
    log,
    sin,
    sinh,
    sqrt,
    tan,
    tanh,
)
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

app = Flask(__name__, template_folder="../templates", static_folder="../static")

VAR_NAME_PATTERN = re.compile(r"^[A-Za-z_]\w*$")
TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)
SAFE_GLOBALS = {
    "__builtins__": {},
    "Symbol": Symbol,
    "Function": Function,
    "Integer": Integer,
    "Rational": Rational,
    "Float": Float,
    "factorial": factorial,
}


def log10(value):
    return log(value, 10)


SAFE_LOCALS = {
    "sin": sin,
    "sen": sin,
    "cos": cos,
    "tan": tan,
    "asin": asin,
    "acos": acos,
    "atan": atan,
    "sinh": sinh,
    "cosh": cosh,
    "tanh": tanh,
    "exp": exp,
    "log": log,
    "ln": log,
    "log10": log10,
    "sqrt": sqrt,
    "Abs": Abs,
    "pi": pi,
    "e": E,
    "E": E,
    "I": I,
}


def parse_variables(raw_variables: str) -> list[Symbol]:
    if not raw_variables.strip():
        return []

    names = []
    for token in raw_variables.replace(";", ",").split(","):
        name = token.strip()
        if not name:
            continue
        if not VAR_NAME_PATTERN.match(name):
            raise ValueError(
                f"Nombre de incógnita inválido: '{name}'. Usa letras, números y guion bajo."
            )
        names.append(name)

    if not names:
        return []

    ordered_unique_names = list(dict.fromkeys(names))
    return [Symbol(name) for name in ordered_unique_names]


def parse_expression(raw_expression: str, variables: Iterable[Symbol]):
    local_symbols = {str(symbol): symbol for symbol in variables}
    local_dict = {**SAFE_LOCALS, **local_symbols}
    return parse_expr(
        raw_expression,
        transformations=TRANSFORMATIONS,
        local_dict=local_dict,
        global_dict=SAFE_GLOBALS,
        evaluate=True,
    )


def parse_equations(raw_equations: str, variables: list[Symbol]) -> list[Eq]:
    lines = [line.strip() for line in raw_equations.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Debes escribir al menos una ecuación.")

    equations = []
    for index, line in enumerate(lines, start=1):
        try:
            if "=" in line:
                lhs_raw, rhs_raw = line.split("=", 1)
                if not lhs_raw.strip() or not rhs_raw.strip():
                    raise ValueError(f"La ecuación {index} no tiene ambos lados completos.")
                lhs = parse_expression(lhs_raw.strip(), variables)
                rhs = parse_expression(rhs_raw.strip(), variables)
                equations.append(Eq(lhs, rhs))
            else:
                expression = parse_expression(line, variables)
                equations.append(Eq(expression, 0))
        except ValueError:
            raise
        except Exception as error:
            raise ValueError(
                f"No se pudo interpretar la ecuación {index}: '{line}'. Detalle: {error}"
            ) from error
    return equations


def infer_variables(equations: list[Eq]) -> list[Symbol]:
    inferred = {symbol for equation in equations for symbol in equation.free_symbols}
    return sorted(inferred, key=lambda symbol: symbol.sort_key())


def solve_equations(equations: list[Eq], variables: list[Symbol]):
    final_variables = variables or infer_variables(equations)
    if not final_variables:
        raise ValueError("No se pudieron deducir incógnitas de las ecuaciones enviadas.")

    raw_solutions = solve(equations, final_variables, dict=True)
    if isinstance(raw_solutions, dict):
        raw_solutions = [raw_solutions]

    normalized_solutions = []
    for solution in raw_solutions:
        if isinstance(solution, dict):
            normalized_solutions.append(solution)
        elif len(final_variables) == 1:
            normalized_solutions.append({final_variables[0]: solution})
    return final_variables, normalized_solutions


def solutions_to_latex(
    solutions: list[dict[Symbol, object]], variables: list[Symbol]
) -> list[str]:
    output = []
    for solution in solutions:
        assignments = []
        for variable in variables:
            if variable in solution:
                assignments.append(f"{latex(variable)} = {latex(solution[variable])}")
        if not assignments:
            for variable, value in solution.items():
                assignments.append(f"{latex(variable)} = {latex(value)}")

        if assignments:
            output.append(r"\begin{aligned}" + r" \\ ".join(assignments) + r"\end{aligned}")
    return output


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/solve")
def solve_route():
    payload = request.get_json(silent=True) or request.form
    raw_equations = (payload.get("equations") or "").strip()
    raw_variables = (payload.get("variables") or "").strip()

    try:
        variables = parse_variables(raw_variables)
        equations = parse_equations(raw_equations, variables)
        solved_variables, solutions = solve_equations(equations, variables)
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 400

    response = {
        "ok": True,
        "equations_latex": [latex(equation) for equation in equations],
        "variables_latex": [latex(variable) for variable in solved_variables],
        "solutions_latex": solutions_to_latex(solutions, solved_variables),
    }
    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
