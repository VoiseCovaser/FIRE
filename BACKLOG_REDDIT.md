# Backlog Ejecutable (Comentarios Reddit)

Este backlog traduce propuestas de la comunidad a entregables técnicos verificables.
Objetivo: cerrar primero riesgos de precisión/confianza (P0), luego robustez de modelo (P1), y finalmente UX/deuda técnica (P2).

## Estado resumido

- Cerrado/parcial:
  - Fiscalidad por `Tax Pack` y CCAA en web (parcial, modelo simplificado anual).
  - Trazabilidad fiscal en web (desglose de tramos/base/cuota para IRPF ahorro e IP/ISGF).
  - Validación mínima de metadatos del Tax Pack (`lastReviewed`, `sources`, etc.).
  - Modelos P1 en web/CLI: Monte Carlo normal, bootstrap histórico y backtesting por ventanas.
  - SWR configurable en web (paridad con CLI en objetivo FIRE).
  - Limitaciones visibles en arranque (CLI y web).
  - CLI con modo custom y SWR configurable.
- Pendiente:
  - Backtesting histórico real.
  - Paridad completa CLI/Web (perfiles + SWR configurable en web).
  - Trazabilidad fiscal detallada por cálculo y más validación legal por CCAA.
  - Ajustes de UX en inputs clave.

## Orden de ejecución recomendado

1. P0-1, P0-2, P0-3
2. P1-1, P1-2, P1-3
3. P2-1, P2-2, P2-3

---

## P0 (Crítico)

### P0-1 Fiscalidad trazable por CCAA/año

- Objetivo:
  - Mostrar de forma auditable cómo se calcula cada impuesto (base, tramos, tipo, cuota) para un escenario dado.
- Alcance:
  - Añadir salida de desglose fiscal en web y CLI.
  - Exponer metadatos del `Tax Pack` usado (país, año, versión, región).
- Criterios de aceptación:
  - Para una simulación, el usuario puede ver:
    - Base del ahorro aplicada.
    - Tramos usados y cuota resultante.
    - Cálculo de Patrimonio e ISGF y relación entre ambos.
  - La salida indica explícitamente que es aproximación anual de simulación.
- Validación:
  - Tests unitarios de `src/tax_engine.py` con casos de referencia por región.
  - Snapshot de salida de desglose (CLI y web).

### P0-2 Validación normativa mínima por CCAA

- Objetivo:
  - Reducir riesgo de desalineación entre `Tax Pack` y normativa oficial vigente.
- Alcance:
  - Checklist de revisión anual por región y enlaces a fuente oficial.
  - Campo `sources` y `last_reviewed` en pack.
- Criterios de aceptación:
  - `data/taxpacks/es-2026.json` incluye metadatos de fuente y fecha de revisión.
  - Documento de proceso de actualización anual publicado en repo.
- Validación:
  - Test que falla si faltan metadatos mínimos en pack.
  - Revisión manual anual registrada.

### P0-3 Paridad legal/comunicación en producto

- Objetivo:
  - Evitar que el usuario interprete la simulación como asesoría fiscal vinculante.
- Alcance:
  - Consistencia de disclaimer en CLI, web y docs.
  - Etiquetas de riesgo por nivel de exactitud de cada módulo.
- Criterios de aceptación:
  - Mensaje consistente en `README.md`, `WEB_APP_README.md`, `src/cli.py` y `app.py`.
  - Cada vista que muestre fiscalidad incluye etiqueta "aproximación anual".
- Validación:
  - Checklist de contenido y revisión de copy.

---

## P1 (Alto impacto)

### P1-1 Backtesting histórico

- Objetivo:
  - Contrastar supuestos del modelo con periodos históricos.
- Alcance:
  - Motor de backtesting por ventanas móviles (10/20/30 años).
  - Métricas: tasa de éxito, peor caso, mediana, percentiles.
- Criterios de aceptación:
  - Usuario puede elegir modo "Monte Carlo" o "Backtesting".
  - Export CSV con resultados por ventana histórica.
- Validación:
  - Tests de integridad de series y reproducibilidad.

### P1-2 Motor probabilístico alternativo (bootstrap)

- Objetivo:
  - Reducir dependencia del supuesto de normalidad en retornos.
- Alcance:
  - Implementar bootstrap de retornos históricos como alternativa.
  - Comparativa visual contra Monte Carlo normal.
- Criterios de aceptación:
  - Selector de modelo estocástico disponible en web.
  - Reporte muestra diferencias de probabilidad de éxito por modelo.
- Validación:
  - Tests de determinismo con semilla y límites estadísticos básicos.

### P1-3 Paridad CLI/Web de perfiles y SWR

- Objetivo:
  - Reproducir en web capacidades actuales del CLI.
- Alcance:
  - Selector de perfiles FIRE preconfigurados en web.
  - SWR configurable en web para objetivo FIRE (no fija al 4%).
- Criterios de aceptación:
  - Resultado web coincide con CLI en mismos inputs (tolerancia definida).
  - `README.md` deja de listar la asimetría de SWR como limitación.
- Validación:
  - Tests de paridad para casos canónicos.

---

## P2 (Importante no bloqueante)

### P2-1 UX de inputs críticos

- Objetivo:
  - Mejorar precisión de entrada y evitar fricción en valores altos.
- Alcance:
  - Revisar sliders críticos (`patrimonio`, `aportación`, `gastos`) y ofrecer input numérico directo.
  - Mantener ayudas de contexto.
- Criterios de aceptación:
  - Usuario puede introducir valores grandes con exactitud sin arrastre fino.
  - No se rompe la experiencia móvil/escritorio.
- Validación:
  - Pruebas manuales de usabilidad en desktop y móvil.

### P2-2 Refactor de complejidad ciclomática

- Objetivo:
  - Mejorar mantenibilidad y testabilidad sin cambiar comportamiento.
- Alcance:
  - Dividir `app.py` y `src/cli.py` en módulos por responsabilidad.
  - Extraer validación, presentación, cálculo y export.
- Criterios de aceptación:
  - Reducción medible de complejidad por función.
  - Cobertura de tests no disminuye.
- Validación:
  - Ejecutar suite de tests + lint estático.

### P2-3 Observabilidad y errores de usuario

- Objetivo:
  - Facilitar diagnóstico de errores funcionales y soporte.
- Alcance:
  - Logging estructurado para cálculos y errores de validación.
  - Mensajes de error accionables (CLI y web).
- Criterios de aceptación:
  - Errores comunes muestran causa probable y siguiente acción.
  - Logs permiten reproducir escenarios sin datos sensibles.
- Validación:
  - Tests de rutas de error y revisión de mensajes.

---

## Definición de Done por ticket

- Código implementado.
- Tests relevantes añadidos/actualizados.
- Docs de usuario y técnicas actualizadas.
- Limitaciones y supuestos reflejados en UI/CLI.
- Validación manual de un caso realista de extremo a extremo.
