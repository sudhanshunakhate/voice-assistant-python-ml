"""
Math: arithmetic and symbolic algebra/calculus via SymPy, plus short method hints.
"""

from __future__ import annotations

import ast
import operator
import re
from typing import Any

_MAX_INPUT_LEN = 500

# Safe numeric AST (no names, no attr calls)
_ALLOWED_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval_numeric_ast(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
        return _ALLOWED_UNARY[type(node.op)](_eval_numeric_ast(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](_eval_numeric_ast(node.left), _eval_numeric_ast(node.right))
    raise ValueError("unsupported expression")


def _try_pure_arithmetic(s: str) -> str | None:
    s = s.strip().replace("^", "**")
    if not s or len(s) > 200:
        return None
    # Allow scientific notation (1e3); reject variables like x, sin, etc.
    tmp = re.sub(r"(?<![a-zA-Z])[eE][+-]?\d+", "", s)
    if re.search(r"[a-zA-Z]", tmp):
        return None
    try:
        tree = ast.parse(s, mode="eval")
        v = _eval_numeric_ast(tree.body)
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        return str(v)
    except Exception:
        return None


def _strip_command(cmd: str) -> str:
    s = cmd.strip()
    low = s.lower()
    prefixes = (
        "calculate ",
        "compute ",
        "evaluate ",
        "what is the ",
        "what is ",
        "what's ",
        "how much is ",
        "find the value of ",
        "math ",
        "solve ",
        "simplify ",
        "factor ",
        "expand ",
        "integrate ",
        "integral of ",
        "integration of ",
        "derivative of ",
        "differentiate ",
        "limit of ",
        "determinant of ",
        "det ",
    )
    for p in prefixes:
        if low.startswith(p):
            return s[len(p) :].strip()
    # d/dx f(x)
    m = re.match(r"^d/dx\s*\(?\s*(.+)\)?\s*$", s, re.I)
    if m:
        return m.group(1).strip()
    return s


def _algorithm_advice_for_query(text: str) -> str:
    """When the user asks which algorithm to use (no single expression)."""
    t = text.lower()
    chunks: list[str] = []
    if re.search(r"\bgcd\b|\bgreatest common divisor\b", t):
        chunks.append("GCD of integers: Euclidean algorithm — O(log min(a,b)).")
    if re.search(r"\blcm\b|\bleast common multiple\b", t):
        chunks.append("LCM: lcm(a,b) = |a*b|/gcd(a,b); compute gcd with Euclid.")
    if re.search(r"\bprime\b|\bprimes\b|\bprimality\b", t):
        chunks.append("Primality: trial division for small n; Miller–Rabin for large integers.")
    if re.search(r"\bfibonacci\b|\bfib\b", t):
        chunks.append("Fibonacci: iterative O(n), or fast doubling / matrix exponentiation O(log n).")
    if re.search(r"\bsort\b|\bsorting\b", t):
        chunks.append(
            "Sorting: Timsort (Python lists) stable O(n log n); Quicksort average O(n log n); "
            "counting/radix when keys are small integers."
        )
    if re.search(r"\bshortest path\b|\bdijkstra\b|\bgraph\b|\bbfs\b|\bdfs\b", t):
        chunks.append(
            "Graphs: BFS shortest path on unweighted; Dijkstra non-negative edges; Bellman–Ford if negatives possible; A* with a heuristic when you have estimates."
        )
    if re.search(r"\bsearch\b|\bbinary search\b", t):
        chunks.append("Search in sorted array: binary search O(log n); hash table O(1) average for exact key lookup.")
    if re.search(r"\bintegrat\b|\bintegral\b", t):
        chunks.append("Integration: try substitution, by parts, partial fractions; numerically use Simpson or Gaussian quadrature.")
    if re.search(r"\bderivat\b|\bdifferentiat\b", t):
        chunks.append("Derivatives: symbolic rules; numerically use central differences for smooth functions.")
    if re.search(r"\bmatrix\b|\bdeterminant\b|\beigenvalue\b", t):
        chunks.append("Matrices: Gaussian elimination; LU for systems; QR/SVD for stability; eigenvalues via characteristic polynomial or iterative methods at scale.")
    if not chunks:
        chunks.append(
            "Choose by structure: discrete + ordering → sort/search; graphs → BFS/DFS/shortest-path; "
            "numbers → arithmetic or symbolic algebra; continuous → calculus (limits, integrals) or numerical methods."
        )
    return "\n".join(chunks)


def _algorithm_hints(expr_text: str, operation: str) -> str:
    """Short 'best approach' notes for the user (math + a few classic CS patterns)."""
    t = expr_text.lower()
    lines: list[str] = []

    if operation == "integrate":
        lines.append(
            "Best approach: symbolic antiderivative (SymPy). For hand work, try substitution, "
            "integration by parts, or partial fractions when the integrand is a rational or product."
        )
    elif operation == "diff":
        lines.append(
            "Best approach: symbolic differentiation (chain, product, and quotient rules applied). "
            "For numerics, use finite differences only if you need approximate values at a point."
        )
    elif operation == "solve":
        lines.append(
            "Best approach: algebraic solution when closed form exists; for polynomials, factor or use the quadratic formula; "
            "SymPy may return numerical approximations for transcendental equations."
        )
    elif operation == "limit":
        lines.append(
            "Best approach: simplify the expression, check left/right limits at discontinuities; "
            "L'Hopital's rule applies for 0/0 or infinity/infinity indeterminate forms after verification."
        )
    elif operation in ("factor", "expand", "simplify"):
        lines.append(
            "Best approach: algebraic manipulation — factor looks for multiplicative structure; "
            "expand distributes products; simplify merges like terms and cancels common factors."
        )
    elif operation in ("arithmetic", "symbolic"):
        lines.append(
            "Best approach: use standard operator precedence; for symbols, simplify before substituting numbers."
        )
    elif operation == "matrix":
        lines.append(
            "Best approach: for determinants, row reduction (Gaussian elimination) or Laplace expansion; "
            "for large sparse matrices in code, prefer stable LU-based routines."
        )
    else:
        lines.append(
            "Best approach: simplify the expression first, then evaluate; watch operator precedence and parentheses."
        )

    if re.search(r"\bgcd\b|\bgreatest common divisor\b", t):
        lines.append("For GCD of integers: Euclidean algorithm — O(log min(a,b)).")
    if re.search(r"\blcm\b|\bleast common multiple\b", t):
        lines.append("For LCM: use lcm(a,b) = |a*b|/gcd(a,b) after computing gcd with Euclid's algorithm.")
    if re.search(r"\bprime\b|\bprimes\b|\bprimality\b", t):
        lines.append("For primality: trial division for small n; Miller–Rabin for large integers (probabilistic).")
    if re.search(r"\bfibonacci\b|\bfib\b", t):
        lines.append("For Fibonacci: iterative O(n), or fast doubling / matrix exponentiation for O(log n).")
    if re.search(r"\bsort\b|\bsorting\b", t):
        lines.append(
            "For sorting: Timsort (Python lists) is stable O(n log n); Quicksort average O(n log n); "
            "counting/radix when keys are bounded integers."
        )
    if re.search(r"\bshortest path\b|\bdijkstra\b|\bgraph\b", t):
        lines.append("For shortest paths: Dijkstra (non-negative edges), Bellman–Ford if negative edges possible, A* with a heuristic when applicable.")
    if re.search(r"\bfactorial\b|!", t) and "factor" not in operation:
        lines.append("Factorial n! grows fast; use Stirling's approximation or log-gamma for huge n in analytics.")

    return "\n".join(lines)


def _parse_sympy(s: str) -> Any:
    from sympy import E, I, oo, pi
    from sympy.parsing.sympy_parser import implicit_multiplication_application, parse_expr, standard_transformations

    transformations = standard_transformations + (implicit_multiplication_application,)
    local_dict: dict[str, Any] = {"pi": pi, "E": E, "I": I, "oo": oo, "inf": oo}
    return parse_expr(s, transformations=transformations, local_dict=local_dict, evaluate=True)


def _sympy_str(obj: Any) -> str:
    from sympy import latex, sstr

    try:
        return sstr(obj, full_prec=False)
    except Exception:
        return str(obj)


def _handle_integrate(rest: str) -> tuple[str, str]:
    from sympy import Symbol, integrate

    op = "integrate"
    s = rest.strip().replace("^", "**")
    var = Symbol("x")
    m = re.search(r"\bdx\b|\bdt\b|\bd\s+x\b|\bd\s+t\b", s, re.I)
    if m:
        tok = m.group(0).lower().replace(" ", "")
        if tok == "dt":
            var = Symbol("t")
        s = re.sub(r"\b(d x|dx|d t|dt)\b", "", s, flags=re.I).strip()
    m2 = re.search(r"\bfrom\s+([^\s]+)\s+to\s+([^\s]+)\s*$", s, re.I)
    bounds = None
    if m2:
        s = s[: m2.start()].strip()
        try:
            a = _parse_sympy(m2.group(1).replace("^", "**"))
            b = _parse_sympy(m2.group(2).replace("^", "**"))
            bounds = (a, b)
        except Exception:
            pass
    expr = _parse_sympy(s)
    if bounds:
        r = integrate(expr, (var, bounds[0], bounds[1]))
    else:
        r = integrate(expr, var)
    return _sympy_str(r), op


def _handle_diff(rest: str) -> tuple[str, str]:
    from sympy import Symbol, diff

    s = rest.strip().replace("^", "**")
    var = Symbol("x")
    if re.search(r"\bd t\b|\bdt\b", s, re.I):
        var = Symbol("t")
    s = re.sub(r"\bwith respect to\s+[tx]\b|\bwrt\s+[tx]\b", "", s, flags=re.I)
    s = re.sub(r"\bd x\b|\bdx\b|\bd t\b|\bdt\b", "", s, flags=re.I).strip()
    expr = _parse_sympy(s)
    r = diff(expr, var)
    return _sympy_str(r), "diff"


def _handle_limit(rest: str) -> tuple[str, str]:
    import sympy as sp

    s = rest.strip().replace("^", "**")
    s = re.sub(r"^limit\s+of\s+", "", s, flags=re.I)
    s = re.sub(r"^limit\s+", "", s, flags=re.I).strip()
    var = sp.Symbol("x")
    point = _parse_sympy("0")
    expr_s = s
    if " as " in s.lower():
        parts = re.split(r"\s+as\s+", s, maxsplit=1, flags=re.I)
        if len(parts) == 2:
            expr_s, tail = parts[0].strip(), parts[1].strip()
        else:
            tail = ""
        m = re.match(
            r"^([a-z])\s*(?:->|→|approaches|goes\s+to)\s*(.+)$",
            tail,
            re.I,
        )
        if m:
            var = sp.Symbol(m.group(1))
            point = _parse_sympy(m.group(2).strip().replace("^", "**"))
        else:
            m2 = re.match(r"^([a-z])\s+approaches\s+(.+)$", tail, re.I)
            if m2:
                var = sp.Symbol(m2.group(1))
                point = _parse_sympy(m2.group(2).strip().replace("^", "**"))
    expr = _parse_sympy(expr_s)
    r = sp.limit(expr, var, point)
    return _sympy_str(r), "limit"


def solve_math(command: str) -> str:
    raw = (command or "").strip()
    if len(raw) > _MAX_INPUT_LEN:
        return "That expression is too long. Try something under 500 characters."

    low = raw.lower()
    if re.search(r"\b(best|which|what)\s+algorithm\b", low) or re.search(
        r"\balgorithm\s+(for|to)\b", low
    ):
        advice = _algorithm_advice_for_query(raw)
        return (
            f"Suggested approaches:\n{advice}\n\n"
            "For a concrete problem, try: calculate (2+3)*4, integrate x**2, derivative of sin(x), "
            "or solve x**2-4=0."
        )

    rest = _strip_command(raw)

    # Explicit operations first
    try:
        if low.startswith("integrate ") or low.startswith("integral of ") or low.startswith("integration of "):
            ans, op = _handle_integrate(rest)
            return f"Result: {ans}\n\n{_algorithm_hints(rest, op)}"
        if low.startswith("derivative of ") or low.startswith("differentiate ") or re.match(r"^d/dx", raw.strip(), re.I):
            ans, op = _handle_diff(rest)
            return f"Result: {ans}\n\n{_algorithm_hints(rest, op)}"
        if low.startswith("limit of ") or low.startswith("limit "):
            ans, op = _handle_limit(rest)
            return f"Result: {ans}\n\n{_algorithm_hints(rest, op)}"
        if low.startswith("simplify "):
            r = _parse_sympy(rest.replace("^", "**"))
            from sympy import simplify

            ans = _sympy_str(simplify(r))
            return f"Result: {ans}\n\n{_algorithm_hints(rest, 'simplify')}"
        if low.startswith("factor "):
            r = _parse_sympy(rest.replace("^", "**"))
            from sympy import factor

            ans = _sympy_str(factor(r))
            return f"Result: {ans}\n\n{_algorithm_hints(rest, 'factor')}"
        if low.startswith("expand "):
            r = _parse_sympy(rest.replace("^", "**"))
            from sympy import expand

            ans = _sympy_str(expand(r))
            return f"Result: {ans}\n\n{_algorithm_hints(rest, 'expand')}"
        if low.startswith("determinant of ") or low.startswith("det "):
            from sympy import Matrix

            inner = rest.strip()
            if inner.startswith("(") and inner.endswith(")"):
                inner = inner[1:-1]
            rows = []
            for line in inner.split(";"):
                line = line.strip()
                if not line:
                    continue
                nums = [_parse_sympy(x.strip().replace("^", "**")) for x in line.split(",")]
                rows.append(nums)
            M = Matrix(rows)
            ans = _sympy_str(M.det())
            return f"Result: {ans}\n\n{_algorithm_hints(rest, 'matrix')}"
    except Exception as e:
        return f"I could not solve that with the math engine ({e!s}). Check parentheses, use ** for powers, or try a simpler form."

    # Equation: ... = ...
    if "=" in rest and "==" not in rest:
        left, _, right = rest.partition("=")
        try:
            from sympy import Eq, solve

            l = _parse_sympy(left.strip().replace("^", "**"))
            r = _parse_sympy(right.strip().replace("^", "**"))
            sol = solve(Eq(l, r))
            ans = _sympy_str(sol)
            return f"Solution(s): {ans}\n\n{_algorithm_hints(rest, 'solve')}"
        except Exception as e:
            return f"I could not solve that equation ({e!s})."

    # Pure arithmetic fast path
    ar = _try_pure_arithmetic(rest.replace("^", "**"))
    if ar is not None:
        return f"Result: {ar}\n\n{_algorithm_hints(rest, 'arithmetic')}"

    # General symbolic simplify/evaluate
    try:
        from sympy import N, simplify

        expr = _parse_sympy(rest.replace("^", "**"))
        simple = simplify(expr)
        try:
            num = N(simple)
            if num.is_real and abs(num) < 10**12:
                ans = str(num.evalf(12))
            else:
                ans = _sympy_str(simple)
        except Exception:
            ans = _sympy_str(simple)
        return f"Result: {ans}\n\n{_algorithm_hints(rest, 'symbolic')}"
    except Exception as e:
        return (
            f"I could not parse that as math ({e!s}). "
            "Try e.g. calculate (2+3)*sqrt(16), integrate x**2, derivative of sin(x), or solve x**2-4=0."
        )


def matches(text: str) -> bool:
    t = text.lower().strip()
    if len(t) > _MAX_INPUT_LEN:
        return False

    if any(
        t.startswith(p)
        for p in (
            "calculate ",
            "compute ",
            "evaluate ",
            "solve ",
            "math ",
            "integrate ",
            "integral of ",
            "integration of ",
            "derivative of ",
            "differentiate ",
            "limit of ",
            "simplify ",
            "factor ",
            "expand ",
            "determinant of ",
            "det ",
            "gcd ",
            "lcm ",
        )
    ):
        return True
    if re.match(r"^d/dx\s*\S", t):
        return True
    if re.search(r"\b(best|which|what)\s+algorithm\b", t) or re.search(r"\balgorithm\s+(for|to)\b", t):
        return True

    # "what is ..." only when remainder looks like math (avoid stealing web queries)
    m = re.match(r"^(what is|what's|how much is)\s+(.+)$", t)
    if m:
        frag = m.group(2).strip()
        if len(frag) > 120:
            return False
        if re.search(r"\b(the|and|for|capital|president|meaning|definition|who|why|where|how)\b", frag):
            return False
        if re.fullmatch(r"[\d\s\+\-\*\/\^\(\)\.,eE]+", frag):
            return True
        if re.search(r"[\^*/+\-]", frag) and re.search(r"\d", frag):
            if not re.search(r"\b[a-z]{4,}\b", frag.replace("sqrt", "").replace("sin", "").replace("cos", "").replace("tan", "").replace("log", "").replace("pi", "")):
                return True
        if re.match(r"^(sqrt|sin|cos|tan|log|ln|exp|abs)\s*\(", frag, re.I):
            return True

    # Bare arithmetic line (digits + operators, optional parens / float e notation)
    bare = t.replace("^", "**")
    if re.fullmatch(r"[\d\s+\-*/().eE]+", bare) and re.search(r"[+*/-]", bare):
        return True

    return False
