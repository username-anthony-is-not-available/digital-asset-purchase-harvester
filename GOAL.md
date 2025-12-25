# Vision: digital-asset-purchase-harvester

> Extract cryptocurrency purchase records from email archives for tax and portfolio tracking.

## Target Users

- **Primary**: Crypto investors with years of exchange emails to process
- **Secondary**: Accountants reconciling client crypto transaction histories

## Strategic Priorities (2025)

1. Improve extraction accuracy for major exchanges (Coinbase, Binance, Kraken)
2. Add confidence scoring and manual review workflows
3. Integrate output with tax calculators (Koinly format, CRA-ready)
4. Support additional email formats beyond mbox

## In Scope

- Email parsing from mbox files
- LLM-powered purchase detection (Ollama)
- Exchange-specific pattern recognition (30+ exchanges)
- CSV output in tax-tool-compatible formats
- Confidence scoring and validation

## Out of Scope

- Real-time email monitoring (batch processing only)
- Direct exchange API integration (email-based)
- Tax calculation (export data for other tools)

## Success Metrics

| Metric                      | Current | Target          |
| --------------------------- | ------- | --------------- |
| Exchange detection accuracy | ~80%    | 95%+            |
| False positive rate         | ~20%    | <5%             |
| Processing speed            | Varies  | 100+ emails/min |

## Competitive Positioning

- **Primary competitors**: Manual spreadsheet work, exchange-specific exports
- **Differentiation**: Multi-exchange, historical email mining, local LLM (privacy), open-source
