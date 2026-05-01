# ADR-004: Data Quality and Validation Framework

**Date**: 2025-08-22  
**Status**: Accepted  
**Deciders**: Byron, Development Team  
**Consulted**: Portfolio Performance Data Analysis, Asset Allocation Requirements  
**Informed**: Performance Reporting Team, Classification Engine Team  

## Context

The Security Master Service's primary objective is enabling superior **performance reporting and asset allocation analysis** that commercial tools fail to provide adequately. The quality of taxonomy classification and security master data directly impacts the accuracy and utility of these analytical capabilities.

Current commercial tools have limitations in asset allocation views and performance reporting granularity. To achieve the desired analytical depth, we need a comprehensive data quality framework that ensures:

1. **Taxonomy Accuracy**: Reliable GICS/TRBC classifications for meaningful sector analysis
2. **Security Master Integrity**: Complete and accurate reference data for all holdings
3. **Cross-Institution Validation**: Consistent data across multiple data sources
4. **Performance Attribution**: Clean data enabling accurate performance decomposition
5. **Asset Allocation Precision**: Granular classification supporting custom allocation views

## Decision

We will implement a **comprehensive data quality and validation framework** with four validation layers aligned to our data sourcing hierarchy, specifically designed to support advanced performance reporting and asset allocation analysis.

### Layer 1: Source Data Validation (Tier Alignment)

**Purpose**: Validate data quality at ingestion based on source reliability  
**Scope**: All incoming data from four-tier hierarchy (ADR-003)  

#### **Tier 1 (PP Native) - Validation Level: High Confidence**

- **ISIN Validation**: Check digit verification, format compliance
- **Symbol Consistency**: Cross-reference with PP community database
- **Price Data Integrity**: OHLC validation, outlier detection
- **Taxonomy Completeness**: Verify PP community classifications exist

#### **Tier 2 (pp-portfolio-classifier) - Validation Level: Specialized**

- **Fund Holdings Validation**: Verify underlying asset classifications sum to 100%
- **Sector Mapping Accuracy**: Validate GICS assignments against holdings composition
- **Classification Confidence**: Score based on holdings data quality and recency
- **ETF Tracking Validation**: Verify index tracking accuracy for classification purposes

#### **Tier 3 (External APIs) - Validation Level: Cross-Reference**

- **OpenFIGI Response Validation**: Verify FIGI-to-ISIN mappings, check for stale data
- **API Data Freshness**: Timestamp validation, maximum age thresholds
- **Classification Consistency**: Cross-validate GICS codes between API sources
- **Rate Limit Compliance**: Ensure API usage stays within limits to maintain data quality

#### **Tier 4 (Manual Entry) - Validation Level: Expert Review**

- **Documentation Requirements**: Mandatory rationale for manual classifications
- **Expert Review Process**: Subject matter expert validation for high-value holdings
- **Audit Trail**: Complete history of manual decisions with reversal capability
- **Quality Metrics**: Track manual classification accuracy over time

### Layer 2: Cross-Institution Data Validation

**Purpose**: Ensure consistency across multiple data sources for holdings validation  
**Scope**: Wells Fargo, Interactive Brokers, AltoIRA, Kubera, Portfolio Performance  

#### **Holdings Reconciliation**

```sql
-- Example validation query for holdings consistency
SELECT 
    sm.isin,
    sm.symbol,
    sm.security_name,
    pp_holdings.shares AS pp_shares,
    kubera_holdings.shares AS kubera_shares,
    ABS(pp_holdings.shares - kubera_holdings.shares) AS variance,
    CASE 
        WHEN ABS(pp_holdings.shares - kubera_holdings.shares) / pp_holdings.shares > 0.05 
        THEN 'HIGH_VARIANCE' 
        ELSE 'ACCEPTABLE' 
    END AS validation_status
FROM securities_master sm
JOIN portfolio_performance_holdings pp_holdings ON sm.id = pp_holdings.security_id
JOIN kubera_holdings ON sm.isin = kubera_holdings.isin
WHERE pp_holdings.as_of_date = kubera_holdings.as_of_date;
```

#### **Transaction Consistency Checks**

- **Date Range Validation**: Ensure transaction dates fall within account active periods
- **Amount Reconciliation**: Validate transaction amounts against position changes
- **Corporate Actions**: Cross-reference splits, dividends, mergers across institutions
- **Currency Consistency**: Validate multi-currency transactions and conversions

### Layer 3: Performance Reporting Data Quality

**Purpose**: Ensure data quality specifically supports accurate performance attribution  
**Scope**: All data used in performance calculations and attribution analysis  

#### **Performance Attribution Requirements**

- **Security Return Calculation**: Clean price data with dividend adjustments
- **Benchmark Mapping**: Accurate sector/industry classifications for benchmark construction
- **Asset Allocation Precision**: Granular sub-sector classifications for custom allocation views
- **Time-Weighted Returns**: Validated transaction timing for accurate return calculations

#### **Data Quality Metrics for Performance Analysis**

```python
class PerformanceDataQuality:
    """Data quality metrics specifically for performance reporting"""
    
    def calculate_classification_completeness(self) -> float:
        """Percentage of holdings with complete GICS Level 4 classification"""
        pass
    
    def validate_price_data_continuity(self) -> Dict[str, float]:
        """Check for gaps in price data that would impact return calculations"""
        pass
    
    def assess_benchmark_mapping_accuracy(self) -> float:
        """Validate sector assignments against recognized benchmark compositions"""
        pass
    
    def calculate_asset_allocation_precision(self) -> Dict[str, float]:
        """Measure granularity available for custom asset allocation views"""
        pass
```

#### **Asset Allocation Analysis Support**

- **Multi-Level Classification**: Support for custom allocation hierarchies beyond standard GICS
- **Geographic Exposure**: Country and region classifications for geographic allocation analysis
- **Market Cap Segmentation**: Size-based classifications (large/mid/small cap) for style analysis
- **ESG Classifications**: Environmental, Social, Governance scores for sustainable allocation views

### Layer 4: Continuous Data Quality Monitoring

**Purpose**: Ongoing validation and quality improvement  
**Scope**: All data in the system with automated monitoring and alerting  

#### **Real-Time Quality Monitoring**

- **Data Freshness Alerts**: Automated alerts for stale price data or missing classifications
- **Classification Drift Detection**: Monitor for unexpected changes in security classifications
- **Holdings Variance Monitoring**: Alert on significant discrepancies between institutions
- **Performance Attribution Validation**: Automated checks for return calculation accuracy

#### **Quality Improvement Workflows**

- **Data Quality Dashboard**: Real-time visibility into quality metrics across all tiers
- **Exception Management**: Workflow for investigating and resolving data quality issues
- **Quality Trend Analysis**: Track data quality improvements over time
- **User Feedback Integration**: Incorporate user-reported quality issues into improvement process

## Implementation Strategy

### Phase 1: Foundation (MVP Timeframe)

- **Basic Validation**: ISIN check digits, symbol format validation, date range checks
- **Holdings Reconciliation**: Basic PP vs Kubera holdings comparison
- **Manual Review Workflow**: Simple CLI-based review process for exceptions
- **Quality Scoring**: Basic confidence scores based on data source tier

### Phase 2: Enhanced Validation (Release 2.0)

- **Cross-Source Validation**: Full implementation of Tier 1-4 validation rules
- **Performance Data Quality**: Specialized validation for performance attribution
- **Automated Monitoring**: Real-time quality alerts and dashboard
- **Advanced Classification**: Multi-level taxonomy validation

### Phase 3: Advanced Analytics (Release 3.0)

- **Predictive Quality**: Machine learning models to predict data quality issues
- **Custom Allocation Support**: Framework for user-defined allocation hierarchies
- **Benchmark Validation**: Automated benchmark composition verification
- **Quality Optimization**: Continuous improvement based on usage patterns

## Data Quality Standards for Performance Reporting

### Classification Completeness Requirements

- **Minimum Standard**: 95% of holdings by value have GICS Level 1 classification
- **Target Standard**: 90% of holdings by value have GICS Level 4 classification
- **Premium Standard**: 85% of holdings by value have custom sub-sector classifications

### Price Data Quality Requirements

- **Frequency**: Daily price updates for all active holdings
- **Accuracy**: Price outliers (>20% daily change) flagged for review
- **Completeness**: <2% missing price data for any trailing 12-month period
- **Timeliness**: Price data updated within 24 hours of market close

### Cross-Institution Validation Thresholds

- **Holdings Variance**: <5% variance in total position values between PP and Kubera
- **Transaction Reconciliation**: 99%+ transaction matching across institutions
- **Classification Consistency**: <2% classification discrepancies between sources

## Success Metrics

### Performance Reporting Quality

- **Attribution Accuracy**: Performance attribution matches manual calculations within 0.1%
- **Benchmark Alignment**: Sector allocations match recognized benchmark compositions within 2%
- **Return Calculation Precision**: Time-weighted returns accurate to 4 decimal places
- **Asset Allocation Granularity**: Support for 10+ custom allocation hierarchies

### Data Quality Operational Metrics

- **Data Freshness**: 99%+ of data updated within defined freshness windows
- **Exception Resolution Time**: Average <24 hours for data quality issue resolution
- **User Satisfaction**: >95% user satisfaction with data quality for reporting needs
- **Automation Rate**: 90%+ of quality checks automated without manual intervention

## Rationale

### Performance Reporting Focus

The primary driver for this system is enabling superior performance reporting and asset allocation analysis that commercial tools cannot provide. Data quality is not just a technical requirement; it's the foundation that enables the analytical capabilities that justify the entire system.

### Commercial Tool Limitations

Current tools fail to provide adequate asset allocation analysis due to:

- **Limited Classification Granularity**: Inability to create custom allocation hierarchies
- **Inconsistent Data Sources**: Lack of unified security master across institutions
- **Poor Performance Attribution**: Insufficient data quality for accurate attribution analysis
- **Generic Reporting**: One-size-fits-all reports that don't meet specific analytical needs

### Quality-First Approach

By implementing comprehensive data quality validation aligned with analytical requirements, we ensure that performance reporting and asset allocation analysis are built on a foundation of reliable, accurate, and complete data.

## Consequences

### Positive

- **Analytical Reliability**: High-quality data enables confident decision-making based on performance analysis
- **Custom Allocation Views**: Flexible taxonomy supports user-defined asset allocation hierarchies
- **Performance Attribution Accuracy**: Clean data enables precise performance decomposition and analysis
- **Cross-Institution Consistency**: Unified view across all holdings regardless of custodian
- **Continuous Improvement**: Systematic quality monitoring drives ongoing data quality enhancements

### Negative

- **Implementation Complexity**: Comprehensive validation requires significant development effort
- **Processing Overhead**: Quality checks add computational cost to data ingestion
- **Manual Review Requirements**: Some quality issues require expert human review
- **Maintenance Burden**: Quality rules need ongoing refinement based on edge cases

### Risk Mitigation

- **Phased Implementation**: Start with basic validation, enhance over time
- **Performance Optimization**: Efficient validation algorithms to minimize processing overhead
- **Expert Review Workflows**: Streamlined processes for handling manual review requirements
- **Quality Rule Management**: Version-controlled quality rules with rollback capability

## Related Decisions

- **ADR-001**: Transaction-Centric Architecture (provides data volume and processing requirements)
- **ADR-002**: Portfolio Performance Backup Restoration (defines data completeness requirements)
- **ADR-003**: Securities Master Data Sourcing Hierarchy (provides quality framework alignment)

## References

- Portfolio Performance Performance Attribution Documentation
- GICS Sector Classification Standards
- TRBC (Thomson Reuters Business Classification) Standards
- CFA Institute Performance Presentation Standards
- Asset Allocation Analysis Best Practices
