# Horários Metro do Porto (widget)

Varziela ↔ NorteShopping (Linha B). `horarios.json` é gerado de `build_horarios.py`
a partir do GTFS oficial; o GitHub Action `atualizar-horarios` corre às segundas-feiras.

1. Cria um repositório público no GitHub e carrega estes ficheiros (mantém a pasta `.github/workflows`).
2. Separador Actions: corre "Atualizar horarios" uma vez à mão (Run workflow) e vê se fica verde.
3. Em `widgy/proximo_metro.js`, troca `USER/REPO` pelo teu repositório.
