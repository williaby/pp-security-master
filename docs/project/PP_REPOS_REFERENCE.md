# Portfolio Performance Repository Reference

Reference file for Portfolio Performance related repositories, analyzed for potential integration with the Security-Master Service.

## Priority 1 - Essential Integration

### pp-portfolio-classifier (Alfons1Qto12)
- **Summary**: Auto-classifies ETFs/stocks using Morningstar holdings data; generates PP taxonomies
- **Utility**: Core functionality overlap with classifier/ module; provides GICS/TRBC classification
- **Integration**: Replace custom fund classification logic; use for taxonomy generation
- **Status**: Already referenced in CLAUDE.md as key dependency

### ppxml2db (pfalcon)
- **Summary**: Round-trip converter between PP XML and SQLite database
- **Utility**: Eliminates need for custom XML writers in patch/ module
- **Integration**: Use for bidirectional PP XML sync instead of custom implementation
- **Status**: High value for reducing custom XML handling code

## Priority 2 - High Value Components

### Portfolio-Performance-Export (dvett01)
- **Summary**: Python classes for reading PP XML files for downstream analysis
- **Utility**: Mature XML parsing logic for extractor/ module
- **Integration**: Replace custom PP XML parsers with tested library
- **Status**: Code reuse opportunity

### pp-data (havasd)
- **Summary**: Scraped instrument metadata with automatic updates
- **Utility**: Supplement OpenFIGI API data; reduce rate limit pressure
- **Integration**: Additional data source for classification pipeline
- **Status**: Data enrichment opportunity

### PortfolioPerformance-TableHelper (forReason)
- **Summary**: C# library for creating CSV entries compatible with Portfolio Performance
- **Utility**: Programmatic CSV generation patterns for custom data sources
- **Integration**: Reference for CSV output formatting in patch/ module
- **Status**: CSV generation reference

### pytr-org/pytr
- **Summary**: Terminal tool for TradeRepublic with document mass download
- **Utility**: API access patterns and bulk document processing
- **Integration**: Reference for broker API integration and batch processing
- **Status**: API integration reference

### pp-terminal (ma4nn)
- **Summary**: CLI analytics toolkit built on ppxml2db (German tax helper)
- **Utility**: Reference implementation for CLI design patterns
- **Integration**: Inspiration for cli.py enhancements
- **Status**: Design pattern reference

## Priority 3 - Deployment & Infrastructure

### totti-4-ever/docker.portfolio-performance
- **Summary**: Another Docker implementation for Portfolio Performance
- **Utility**: Alternative Docker deployment approach
- **Integration**: Docker deployment pattern comparison
- **Status**: Alternative Docker reference

### docker-portfolio (devben-io)
- **Summary**: General Dockerized Portfolio Performance for fast spin-up
- **Utility**: General deployment reference
- **Integration**: Docker patterns for service deployment
- **Status**: General deployment guidance

### ich777/docker-portfolio-performance
- **Summary**: Unraid-optimized Docker container with auto-update check
- **Utility**: Matches target Unraid infrastructure
- **Integration**: Deployment alongside PostgreSQL 17 setup
- **Status**: Infrastructure alignment

### portfolio-performance-docker (sunsided)
- **Summary**: Docker image running PP with X11; includes run.sh example
- **utility**: Simple Docker deployment pattern
- **Integration**: Reference for containerized deployment
- **Status**: Deployment option

### portfolio-performance-image (quallenbezwinger)
- **Summary**: Browser/VNC-served PP using GUI base image (no local X server)
- **Utility**: Web-based PP access without local display
- **Integration**: Alternative user interface approach
- **Status**: UI deployment option

### portfolio-performance (meronx)
- **Summary**: Minimal Dockerfile for building Portfolio Performance image
- **Utility**: Lightweight deployment approach
- **Integration**: Minimal containerization reference
- **Status**: Basic deployment reference

## Priority 4 - Specialized Parsers

### StegSchreck/PP-Auxmoney-Parser
- **Summary**: Auxmoney interest parser for P2P lending platform
- **Utility**: Specialized P2P platform support pattern
- **Integration**: Template for additional P2P platform support
- **Status**: P2P platform reference

### pat-s/ppcryptoparser
- **Summary**: R package for crypto staking rewards (Polkadot, Kusama, Solana)
- **Utility**: Cryptocurrency asset class handling patterns
- **Integration**: Reference for crypto/staking support in extractor/
- **Status**: Cryptocurrency reference

### ghostfolio/ghostfolio
- **Summary**: Modern web-based wealth management (Angular + NestJS + TypeScript)
- **Utility**: Modern web architecture patterns for portfolio management
- **Integration**: Reference for web-based interface development
- **Status**: Web architecture reference

### portfolio-performance-xml-parser (d-a-n)
- **Summary**: JavaScript/Node parser converting PP XML to JSON
- **Utility**: Cross-language parsing reference
- **Integration**: Alternative parsing approach for web interfaces
- **Status**: Cross-platform reference

### convert-csv-schwab2pp (rlan)
- **Summary**: Converts Charles Schwab CSV to PP-importable CSV format
- **Utility**: Template for additional broker support
- **Integration**: Pattern for extractor/ module expansion
- **Status**: Broker expansion template

### trade-republic-portfolio (Thukyd)
- **Summary**: Parses Trade Republic PDFs and converts to CSV for PP import
- **Utility**: PDF parsing patterns for broker statements
- **Integration**: Reference for PDF extraction in extractor/
- **Status**: PDF parsing reference

### pytrpp (MartinScharrer)
- **Summary**: Accesses Trade Republic private API; exports data for PP imports
- **Utility**: API integration patterns
- **Integration**: Reference for broker API connections
- **Status**: API integration reference

### alpaca-portfolio-performance-importer (Newtoniano)
- **Summary**: Converts Alpaca executions JSON to PP CSV format
- **Utility**: JSON processing patterns for broker data
- **Integration**: Template for JSON-based broker support
- **Status**: JSON processing reference

### onvista_portfolio_performance_tools (Bazs)
- **Summary**: Converts Onvista statements to PP CSV with templates
- **Utility**: Template-based conversion approach
- **Integration**: Pattern for template-driven parsing
- **Status**: Template processing reference

### PP-P2P-Parser (ChrisRBe)
- **Summary**: Parses Mintos and other P2P statements to PP CSV format
- **Utility**: Specialized asset class handling (P2P lending)
- **Integration**: Reference for alternative investment types
- **Status**: Alternative asset reference

### mintopp (HerrBertling)
- **Summary**: JavaScript tool converting Mintos statements to PP CSV
- **Utility**: Cross-language P2P parsing implementation
- **Integration**: Alternative P2P processing approach
- **Status**: Cross-platform P2P reference

### Convert2PortofolioPerformance (TimoKoole)
- **Summary**: Converts Degiro/ING exports to PP CSV format
- **Utility**: Multi-broker conversion patterns
- **Integration**: Reference for European broker support
- **Status**: Multi-broker reference

### TR-PDF-Parser (MarcBuch)
- **Summary**: Scans folders for Trade Republic invoices/dividends; outputs PP CSV
- **Utility**: Batch processing and file monitoring patterns
- **Integration**: Reference for automated file processing
- **Status**: Batch processing reference

### julian-west/python_portfolio_tracker
- **Summary**: Python portfolio performance tracker with analysis capabilities
- **Utility**: Python-based portfolio analysis patterns
- **Integration**: Reference for analysis module enhancements
- **Status**: Analysis reference

### icheered/StockPortfolioTracker
- **Summary**: DeGiro CSV-based portfolio visualization
- **Utility**: Visualization patterns for portfolio data
- **Integration**: Reference for data visualization in web interface
- **Status**: Visualization reference

## Priority 5 - Development Tools & Analysis

### lequant40/portfolio_allocation_js
- **Summary**: Comprehensive JavaScript library for portfolio allocation and optimization
- **Utility**: Portfolio optimization algorithms for web interfaces
- **Integration**: Reference for optimization features in web UI
- **Status**: Optimization reference

### mayest/Portfolio-Performance
- **Summary**: C# Excel add-in with risk-adjusted portfolio performance functions
- **Utility**: Risk metrics calculation patterns (Sharpe, Treynor, Alpha, Beta)
- **Integration**: Reference for advanced analytics in classifier/ module
- **Status**: Analytics reference

### lorenzbr/PortfolioTracker
- **Summary**: R package with Shiny app for portfolio performance tracking
- **Utility**: Interactive dashboard patterns and R integration
- **Integration**: Reference for dashboard development
- **Status**: Dashboard reference

### pyscripter/XLRisk
- **Summary**: Free Excel add-in for Monte Carlo simulation (open source @RISK alternative)
- **Utility**: Risk analysis and Monte Carlo simulation patterns
- **Integration**: Reference for advanced risk analytics
- **Status**: Risk analysis reference

### Grademark/grademark
- **Summary**: JavaScript/TypeScript backtesting API for trading strategies
- **Utility**: Backtesting patterns and performance analysis
- **Integration**: Reference for strategy analysis features
- **Status**: Backtesting reference

## Official Repositories (Reference Only)

### portfolio-performance/portfolio
- **Summary**: Main desktop application written in Java
- **Utility**: Core application reference and API patterns
- **Integration**: Understanding of core data structures and workflows
- **Status**: Core reference

### portfolio-performance/portfolio-help
- **Summary**: Official manual and documentation
- **Utility**: Understanding of standard workflows and data formats
- **Integration**: Reference for feature compatibility and user expectations
- **Status**: Documentation reference

## Integration Roadmap

### Phase 1 (Immediate)
- Integrate **pp-portfolio-classifier** into classifier/ module
- Evaluate **ppxml2db** for patch/ module replacement
- Review **pytr-org/pytr** for API integration patterns

### Phase 2 (Short-term)
- Replace custom XML parsing with **Portfolio-Performance-Export**
- Assess **pp-data** as supplementary data source
- Implement CSV generation using **PortfolioPerformance-TableHelper** patterns

### Phase 3 (Medium-term)
- Implement Docker deployment using **ich777/docker-portfolio-performance**
- Add cryptocurrency support inspired by **pat-s/ppcryptoparser**
- Add specialized broker parsers based on user demand

### Phase 4 (Long-term)
- Expand broker support using parser templates
- Implement web interface inspired by **ghostfolio** architecture
- Add advanced analytics using **lequant40/portfolio_allocation_js** patterns
- Consider Monte Carlo risk analysis using **pyscripter/XLRisk** approaches

---

*Last updated: 2025-01-22*
*Maintained for Security-Master Service integration planning*
*Total repositories catalogued: 40+*

## Repository Categories Summary

- **Priority 1**: 2 repositories - Core classification and XML handling
- **Priority 2**: 5 repositories - High-value components and tools
- **Priority 3**: 5 repositories - Deployment and infrastructure
- **Priority 4**: 12 repositories - Specialized parsers and converters
- **Priority 5**: 5 repositories - Development tools and advanced analytics
- **Official**: 2 repositories - Reference documentation and core application

## Key Technology Stacks Represented

- **Python**: Core data processing, classification, and analysis
- **JavaScript/TypeScript**: Web interfaces and portfolio optimization
- **C#**: Excel integration and risk analytics
- **R/Shiny**: Interactive dashboards and statistical analysis
- **Docker**: Deployment and containerization
- **Java**: Core Portfolio Performance application reference