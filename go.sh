clear
cd "/home/baltimora/Progetti/labs/lotto-digit-coverage-dynamics"

echo "===== AGGIORNAMENTO ARCHIVIO ====="
./lotto.py db update

echo
echo "===== ESTRAZIONE DEL 18 SETTEMBRE 2026 ====="
python3 - <<'PY'
import sqlite3
from pathlib import Path

draw_date = "2026-09-18"
database = Path("data/lotto-current.sqlite3")
uri = f"file:{database.resolve()}?mode=ro"

with sqlite3.connect(uri, uri=True) as connection:
    rows = connection.execute(
        """
        SELECT draw_number, draw_date, wheel, position, value
        FROM v_draw_numbers
        WHERE draw_date = ?
        ORDER BY draw_number, wheel_order, position
        """,
        (draw_date,),
    ).fetchall()

if not rows:
    print(f"NESSUNA_ESTRAZIONE_TROVATA_PER_{draw_date}")
else:
    print(f"Concorso: n. {rows[0][0]}")
    print(f"Data:      {rows[0][1]}")

    grouped = {}
    for _, _, wheel, _, value in rows:
        grouped.setdefault(wheel, []).append(value)

    for wheel, numbers in grouped.items():
        rendered = " ".join(f"{number:02d}" for number in numbers)
        print(f"{wheel:<10} {rendered}")
PY

echo
echo "===== STATO AGGIORNATO DEI CICLI ====="
./lotto.py current
