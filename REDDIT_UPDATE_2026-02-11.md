# Update del proyecto FIRE (11 Feb 2026)

Hola a todos, gracias por el feedback del hilo. He aplicado una ronda grande de mejoras P0/P1:

## Qué se ha mejorado

1. Fiscalidad por CCAA más trazable
- Añadido desglose auditable de cálculo fiscal en la web (base, tramos y cuota para IRPF ahorro + Patrimonio + ISGF).
- Tax Pack con validación de metadatos mínimos y fecha de revisión.

2. Modelos de simulación más robustos
- Ya no solo Monte Carlo normal.
- Añadidos:
  - Monte Carlo con bootstrap histórico.
  - Backtesting histórico por ventanas móviles.

3. Paridad CLI/Web (avance real)
- SWR ahora configurable también en la web (antes estaba fija en 4% en objetivo base).
- Comparativa de modelos añadida en CLI.

4. Documentación y límites
- Documentadas limitaciones importantes y pendientes reales.
- Backlog priorizado P0/P1/P2 publicado en el repo.

## Qué sigue pendiente

- Validación jurídica/fiscal externa por CCAA (más allá del motor técnico).
- Automatización completa de actualización anual del Tax Pack.
- Backtesting de cartera multi-activo personalizable con rebalanceo.
- Export detallado por ventana histórica.
- Tests de paridad end-to-end CLI vs web.
- Refactor para reducir complejidad de `app.py`/`cli.py`.

## Nota importante

Sigue siendo una herramienta educativa de planificación, no asesoría fiscal o legal.

Si queréis, el siguiente foco lo pongo en:
1) export detallado de backtesting,
2) refactor técnico,
3) validación de casos fiscales canónicos por CCAA.
