"""
Tool dùng SymPy để verify tính toán trong giai_thich và check đáp án trùng.
"""
import re
from sympy import sympify, simplify
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)

def normalize_expression(expr_str: str) -> str:
    """Chuẩn hóa ký hiệu toán trước khi parse SymPy."""
    expr_str = expr_str.strip()
    expr_str = expr_str.replace("²", "**2")
    expr_str = expr_str.replace("³", "**3")
    expr_str = expr_str.replace("√", "sqrt")
    expr_str = expr_str.replace("^", "**")
    # chèn dấu * giữa số và biến: 3x -> 3*x
    expr_str = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr_str)
    return expr_str

def _parse_safe(expr_str: str):
    try:
        expr_str = normalize_expression(expr_str)
        expr_str = re.sub(r'[^\w\s\+\-\*\/\(\)\.\,\*\*]', '', expr_str)
        return parse_expr(expr_str, transformations=TRANSFORMATIONS)
    except Exception:
        return None


def check_duplicate_options(options: dict) -> dict:
    """Kiểm tra 4 đáp án A/B/C/D có trùng text nhau không."""
    values = list(options.values())
    seen   = set()
    dups   = []
    for v in values:
        if v in seen:
            dups.append(v)
        seen.add(v)
    if dups:
        return {"duplicate_check": "fail", "reason": f"Trùng đáp án: {dups}"}
    return {"duplicate_check": "pass", "reason": "OK"}


def verify_giai_thich(correct_answer_text: str, giai_thich: str) -> dict:
    """
    Verify giai_thich cho câu tính toán:
    - Extract kết quả cuối trong giai_thich (sau dấu '=' cuối cùng)
    - Parse bằng SymPy
    - So sánh với correct_answer_text
    Trả về: {sympy_check: pass/fail/skip, reason: ...}
    """
    # Tìm biểu thức sau dấu '=' cuối trong giai_thich
    matches = re.findall(r'=\s*([^\n=]+)', giai_thich)
    if not matches:
        return {"sympy_check": "skip", "reason": "Không tìm thấy biểu thức trong giai_thich"}

    result_str = matches[-1].strip()  # lấy kết quả cuối cùng

    expr_result  = _parse_safe(result_str)
    expr_correct = _parse_safe(correct_answer_text)

    if expr_result is None or expr_correct is None:
        return {"sympy_check": "skip", "reason": "Không parse được biểu thức"}

    try:
        if simplify(expr_result - expr_correct) == 0:
            return {"sympy_check": "pass", "reason": "Kết quả giai_thich khớp với correct_answer"}
        else:
            return {"sympy_check": "fail", "reason": f"giai_thich ra '{result_str}' nhưng correct_answer là '{correct_answer_text}'"}
    except Exception as e:
        return {"sympy_check": "skip", "reason": f"Không so sánh được: {e}"}
