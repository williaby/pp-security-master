# Portfolio-Performance Security-Master & Classification

> **📋 Start Here**: [MVP Definition](docs/project/MVP.md) | [Complete Project Plan](docs/project/PROJECT_PLAN.md) | [Architecture Decisions](docs/adr/)

[Portfolio Performance App](https://www.portfolio-performance.info/en/) | [Forum](https://forum.portfolio-performance.info/) | [Manual](https://help.portfolio-performance.info/en/)

---

## Overview

Portfolio Performance (PP) is a powerful open-source desktop portfolio tracker. However, it lacks an enterprise-grade security master for consistent asset classification and analytics. This project provides a dedicated Security-Master Service that:

- **Data Sovereignty**: Complete Portfolio Performance backup generation and restoration
- **Institution Integration**: Import transactions from Wells Fargo, Interactive Brokers, AltoIRA
- **Advanced Classification**: Automated taxonomy assignment via OpenFIGI and pp-portfolio-classifier
- **Cross-Validation**: Compare institution data with Kubera aggregated holdings
- **Database-Centric**: PostgreSQL 17 as authoritative source for all financial data

**Goal:** Transform Portfolio Performance from desktop-only to enterprise-grade with complete data control.

---

## Key Features

### **MVP (8 weeks)**
- **Complete PP Backup Restoration**: Generate/import full Portfolio Performance XML backups
- **Institution Transaction Import**: Wells Fargo CSV and Interactive Brokers Flex Query parsing
- **Basic Security Classification**: Manual taxonomy assignment with database storage
- **CLI Interface**: Command-line tools for all import/export operations

### **Future Releases** *(See [MVP.md](docs/project/MVP.md) for timeline)*
- **Automated Classification**: OpenFIGI API and pp-portfolio-classifier integration
- **Kubera Integration**: Cross-institution validation and variance detection
- **Web UI**: Browser-based classification and account management
- **Advanced Analytics**: SQL-based reporting and data quality monitoring

---

## Quick Start *(Development Phase)*

> **Current Status**: Foundation phase - Core architecture and database models implemented

1. **Setup Database**: Install PostgreSQL 17 via Unraid Community Apps
2. **Clone Repository**: `git clone [repository-url] && cd pp-security-master`
3. **Install Dependencies**: `poetry install`
4. **Configure Environment**: Copy `.env.example` to `.env` and configure database connection
5. **Run Tests**: `poetry run pytest -v --cov=src --cov-report=html`
6. **Code Quality**: `poetry run nox -s lint` for formatting and linting

> **Note**: Database migrations and CLI commands are currently under development

> **Detailed Setup**: See [MVP.md](docs/project/MVP.md) for complete MVP scope and [PROJECT_PLAN.md](docs/project/PROJECT_PLAN.md) for infrastructure details.

---

## Repository Structure

```
pp-security-master/
├─ README.md                        # This file
├─ CLAUDE.md                        # Claude Code configuration
├─ LICENSE                          # MIT License
├─ Makefile                         # Build automation
├─ pyproject.toml                   # Dependencies and project configuration
├─ poetry.lock                      # Dependency lock file
├─ noxfile.py                       # Test automation
├─ codecov.yaml                     # Coverage configuration
├─ docs/
│  ├─ adr/                          # Architecture Decision Records
│  ├─ planning/                     # Phase-based development plans
│  └─ project/                      # Project documentation
│     ├─ MVP.md                     # Minimum viable product definition
│     ├─ PROJECT_PLAN.md            # Complete roadmap and technical details
│     ├─ TAXONOMY_GUIDE.md          # Classification standards
│     └─ ...                        # Additional project docs
├─ src/security_master/
│  ├─ storage/
│  │  ├─ models.py                  # Core database models
│  │  ├─ pp_models.py               # Portfolio Performance models
│  │  ├─ transaction_models.py      # Institution transaction models
│  │  ├─ views.py                   # Consolidated export views
│  │  └─ schema_export.py           # Database visualization generators
│  ├─ extractor/                    # Institution-specific parsers
│  ├─ classifier/                   # Classification engines
│  ├─ patch/
│  │  └─ pp_xml_export.py           # PP XML backup generation
│  ├─ cli.py                        # Command-line interface
│  └─ utils.py                      # Shared utilities
├─ tests/                           # Test suite
├─ sample_data/                     # Portfolio Performance and broker samples
├─ schema_exports/                  # Database visualizations (PlantUML, DBML, SQL)
├─ scripts/                         # Setup and utility scripts
├─ sql/                             # Database migrations and schema
└─ pytest_plugins/                  # Custom pytest extensions
```

---

## Documentation

- **📋 [MVP Definition](docs/project/MVP.md)** - Immediate deliverables and success criteria
- **📊 [Complete Project Plan](docs/project/PROJECT_PLAN.md)** - Full roadmap and technical specifications  
- **🏗️ [Architecture Decisions](docs/adr/)** - Technical design rationale
- **📈 [Development Planning](docs/planning/)** - Phase-based execution guides
- **🏷️ [Taxonomy Guide](docs/project/TAXONOMY_GUIDE.md)** - Classification standards (GICS, TRBC, CFI)
- **🗄️ [Database Schema](schema_exports/)** - Visual database diagrams (PlantUML, DBML, SQL)
- **📂 [Sample Data](sample_data/)** - Portfolio Performance and broker examples

---

## License

This project is open-source and available under the MIT License.

---

## References

- [Portfolio Performance App](https://www.portfolio-performance.info/en/)
- [Portfolio Performance Forum](https://forum.portfolio-performance.info/)
- [Portfolio Performance Manual](https://help.portfolio-performance.info/en/)# pp-security-master