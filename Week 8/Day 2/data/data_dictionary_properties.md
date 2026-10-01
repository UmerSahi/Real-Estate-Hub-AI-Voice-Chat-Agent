# Data Dictionary — Dataset A: Property Listings (Regression)

**Domain:** Pakistani Real Estate Valuation Engine  
**Target Variable:** `price` (Normalized to numeric PKR in cleaned phase)  
**Total Raw Rows:** 6,300 listings  
**Coverage:** Lahore, Islamabad, Rawalpindi, Karachi  
**Source Baseline:** Public Zameen.com / Graana marketplace transactions, cross-referenced with Week 7 realestate-hub catalog.

---

## Field Specifications

| Column Name | Raw Data Type | Cleaned Data Type | Description | Unit | Source | Known Issues & Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `property_id` | String | String | Unique identifier assigned to each listing | Identifier | Portal Scraper / CRM | May have duplicate entities with altered IDs due to multi-agent postings |
| `city` | String | Categorical | Metropolitan city where the property is located (Lahore, Islamabad, Karachi, Rawalpindi) | N/A | Portal metadata | Clean, but categorical distributions differ across tier groups |
| `area_society` | String | Categorical (Standardized) | Residential scheme or sub-locality | N/A | Listing title/body | High cardinality with phonetic/spelling variations (e.g. `DHA Ph 5` vs `DHA Phase 5`, `Gulberg 3` vs `Gulberg III`) |
| `property_type` | String | Categorical | Architectural structure type (House, Flat, Upper Portion, Lower Portion, Farm House, Penthouse) | N/A | Listing spec | Minor missingness; strong non-linear impact on covered area ratio |
| `plot_size` | String | Float (`area_marla`) | Total land plot area | Mixed (Marla, Kanal, Sq Ft, Sq Yds) | Listing spec | Inconsistent units (`1 Kanal`, `10 Marla`, `1800 sq ft`, `250 sq yds`) requiring universal standardization to Marla and Sq Ft |
| `covered_area` | Float | Float | Enclosed built-up covered space | Square Feet (`sq ft`) | Property inspection / seller claim | ~3% missing values; seller misreporting on farm houses or multi-unit portions |
| `bedrooms` | Float | Integer | Number of dedicated bedrooms | Count | Listing spec | ~4% missing; occasional typographical errors (e.g. 48 bedrooms on small plots) |
| `bathrooms` | Float | Integer | Number of attached/guest bathrooms | Count | Listing spec | ~4% missing; must be validated against bedroom counts |
| `age_years` | Float | Integer | Age of property construction in years (0 = brand new) | Years | Seller / municipal record | ~5% missing values; skewed towards newer properties with heavy depreciation curve |
| `floors` | Integer | Integer | Number of operational above-ground storeys | Count | Listing spec | Standard 1-3 storeys; occasionally unrecorded in flat units |
| `is_corner` | String | Binary (`0` / `1`) | Indicates if property occupies a corner plot | Flag (`yes` / `no`) | Listing feature | ~2% missing; carries 8-10% market price premium |
| `is_park_facing` | String | Binary (`0` / `1`) | Indicates if property faces a community park or green belt | Flag (`yes` / `no`) | Listing feature | Seller premium attribute; positively correlated with Tier 1 societies |
| `amenities` | String | Set / Count (`amenity_score`) | Semicolon-separated amenities (24/7 security, backup generator, underground electricity, mosque, etc.) | Feature list | Portal amenities tag | ~3% unlisted; raw text needing extraction into structured count and weightings |
| `dist_main_road_km` | Float | Float | Straight-line road network distance to primary arterial road | Kilometers (`km`) | GIS / Geo-coordinates | Continuous measure; non-linear penalty for remote developments |
| `dist_school_km` | Float | Float | Distance to the nearest accredited school | Kilometers (`km`) | Spatial KB | ~5% uncalculated due to rural/peripheral developments |
| `dist_hospital_km` | Float | Float | Distance to tertiary medical healthcare center | Kilometers (`km`) | Spatial KB | Continuous measure; critical accessibility factor |
| `listing_date` | String | Datetime (`YYYY-MM-DD`) | Date when property listing was published | Date | Portal timestamp | Spans 2023-2025; temporal drift consideration |
| `price` | String | Float (`price_pkr`) | Asking price of the property | Mixed (Crore, Lac, PKR numeric) | Asking price | **Severe messiness:** Written as `1.5 Crore`, `85 Lac`, `1.25 cr`, `90 lakh`, commas, prefix `Rs`/`PKR`; extreme outliers (< PKR 50k or > PKR 100 Crore) |

---

## Cleaning & Quality Assessment Strategy

1. **Price Standardization:** Extract numeric multiplier using regex pattern matching (`Crore` -> $\times 10^7$, `Lac`/`Lakh` -> $\times 10^5$, raw numbers stripped of formatting).
2. **Area Conversion Matrix:**
   - 1 Kanal = 20 Marlas = 4,500 sq ft (assuming standard residential 225 sq ft/marla baseline).
   - 1 Marla = 225 sq ft.
   - 1 Sq Yard = 9 sq ft = 0.04 Marla.
3. **Outlier Filtering Thresholds:**
   - Removal of properties with price < PKR 500,000 (unrealistic for houses/flats).
   - Removal of listings with price > PKR 500,000,000 (50 Crore) unless validated by plot size $\ge 40$ Marlas.
   - Bedroom caps ($1 \le \text{beds} \le 12$) based on plot area.
