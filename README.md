<div align="center">

# (FPMS) Fuel Pump Management System

**The open-source, FBR-ready, OGRA-aware petrol pump ERP, built on Frappe & ERPNext.**

License: MIT · Frappe v16 · ERPNext v16 · Market: Pakistan 🇵🇰

</div>

---

FPMS layers a complete petrol-pump / fuel-station domain onto ERPNext's Stock, Selling, Buying, Accounts and HR modules. It is the only petrol-pump solution on the Frappe/ERPNext stack, purpose-built for the Pakistani dealer workflow (shift / nozzle / dip / credit-customer / OMC) with native awareness of OGRA fuel pricing and FBR digital invoicing.

## Highlights

| Area | What you get |
| ---- | ------------ |
| **Wet-stock reconciliation** | Shift-based nozzle totalizer + tank dip reconciliation with variance flagging (~0.5% escalation threshold). |
| **OGRA-aware pricing** | Effective-dated fuel price notifications that auto-generate dated ERPNext Item Prices: no reliance on Pricing Rule validity. |
| **Tanker receipts** | BOL-vs-dip decantation shortfall tracking that feeds ERPNext Purchase Receipts. |
| **Credit & fleet** | Corporate/fleet accounts, fuel cards, credit limits, statements and aging via standard ERPNext AR. |
| **FBR-ready** | Split-supply tax model (0% fuel / 18% lubricants & c-store), ready for FBR digital-invoicing on taxable items. |

## Features

### Fuel & Tank Inventory
- Each tank modelled as an ERPNext **Warehouse**; fuel grade as an **Item** (UOM = litre).
- **Tank** master with capacity and a dip/strapping chart; linear dip-to-volume interpolation.
- **Dip Reading** with variance against book stock (from `tabBin`); optional temperature/density/water-dip capture.

### Dispenser & Nozzle
- **Dispenser** and **Nozzle** masters with calibration tracking and Weights & Measures seal reminders.
- **Nozzle Reading** (opening / closing / testing litres → sale litres) per shift.

### Sales & Reconciliation
- **Shift Reconciliation** Opening/closing totalizers minus testing = sales; cash / card / wallet / credit collected reconciled against calculated sales, with shortage/excess flagging.
- Fuel sales posted as **non-taxable** invoice lines; optional stock relief per nozzle.

### Procurement
- **Tanker Receipt** captures BOL quantity, dip-before/after, temperature and density; flags delivery shortfall and creates a dip-verified Purchase Receipt.

### Pricing & Tax
- **Fuel Price Notification** records the OGRA price build-up (ex-depot, dealer commission, OMC margin, PDL, climate levy) and publishes an effective-dated Item Price.
- Item Tax Templates segregate non-taxable fuel from 18%-taxable lubricants and convenience items from day one.

### Compliance
- **License & Compliance Register** (OGRA / Explosives / Weights & Measures / Fire-safety / HDIP) with expiry reminders.

> **Note:** Tax and levy figures move constantly (the PDL ranged from ~Rs70 to Rs160/litre within a single year). Nothing is hard-coded. All rates are driven by the Fuel Price Notification and tax-template masters.

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/kodlyft/fpms --branch version-16
bench --site your-site.com install-app fpms
```

FPMS requires **ERPNext** (declared via `required_apps`).

## Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/fpms
pre-commit install
pre-commit install --hook-type commit-msg
```

Pre-commit is configured with:

- ruff (lint + format + import sort)
- prettier & eslint
- Frappe semgrep rules
- commitlint (Conventional Commits)

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## CI

GitHub Actions workflows:

- **CI** (`ci.yml`): Installs the app on a fresh bench and runs unit tests.
- **Linters** (`linters.yml`): Pre-commit, Frappe Semgrep Rules and pip-audit on every pull request.
- **Semantic Commits** (`semantic-commits.yml`): Validates commit titles.
- **Release** (`release.yml`): Semantic-release versioning on `version-16`.

## License

[MIT](LICENSE)
