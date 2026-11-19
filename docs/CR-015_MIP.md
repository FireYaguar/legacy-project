# MIP — Maintenance Implementation Plan

**CR:** CR-015 (Corrective, Critical, Immediate)
**Складено:** __TIME__ — до першого рядка коду

| Розділ | Зміст |
|---|---|
| Гілка | fix/CR-015-negative-discount-validation |
| Scope | src/process.py: get_discount(), proc(); tests/test_process.py (новий); CHANGELOG.md. src/utils.py: calc() не змінюється |
| Підхід | get_discount(): якщо amount <= 0 повертати 0 (знижка не може бути від'ємною). proc(): у гілці status == 'paid' відхиляти замовлення з amount < 0 через errors.append, без запису в result і без внеску в total_revenue / total_tax |
| Нові тести | get_discount(0, 3) == 0; get_discount(-100, 3) == 0; calc(-50, 0.15) == -7.5 (документує, чому валідація потрібна вище); proc() відхиляє paid-замовлення з від'ємною сумою для ролей 2 і 3; proc() не змінює total_revenue через такі замовлення; amount == 0 і дрібна додатна сума обробляються як раніше |
| Критерій Done | get_discount(0, 3) -> 0; get_discount(-100, 3) -> 0; proc() не зберігає замовлення з від'ємним net; усі тести зелені (25 раніше існуючих + нові); py_compile без помилок |
| Відкат | git revert <hash fix-коміту> або видалення гілки до merge; зміна локальна, схеми даних і конфігів не торкається |
