# TheBench

Simple overview of use/purpose:

## Description

An in-depth paragraph about your project and overview of use.

## Getting Started

### Dependencies

* prerequisites, libraries, OS version, etc., before installing program.
* ex. Windows 10

### Installing

* How/where to download program
* modifications needed to be made to files/folders

### Executing program

* How to run the program
* Step-by-step bullets
```
code blocks for commands
```

# Basketball Minutes Prediction - Complete EDA Summary & Modeling Strategy

## **Project Overview**

**Objective**: Build a predictive model to forecast basketball minutes for college basketball players in their **next game** using only pre-game available information (no data leakage).

**Final Dataset**: `basketball_minutes_features_FINAL.csv`
- **Shape**: 13,519 rows × 18 columns
- **Time Period**: 2022-09-30 to 2024-03-09 (2.5 college basketball seasons)
- **Players**: 311 unique college basketball players across 46 teams
- **Target**: `Target_Next_Mins` (6-55 minutes, mean=23.7, std=8.6)

---

## **Feature Engineering & Data Preprocessing**

### **Core Data Structure**
- **PlayerName**: Player identifier for grouping operations
- **Date**: Game date (datetime64, chronologically sorted)
- **Abbr**: Team abbreviation (46 unique teams)
- **Target_Next_Mins**: Minutes player will play in next game (created via shift(1))

### **Game Context Features**
- **Is_Home/Is_Away/Is_Neutral**: Location indicators (mutually exclusive, sum=1)
- **Rest_Days**: Days since last game, **capped at 7** (prevents 288-day outliers from season breaks)
- **Team_Avg_Minutes_Season**: Expanding team average minutes (captures coaching philosophy)

### **Historical Performance Features (No Data Leakage)**
All features use **shift(1)** before calculation, ensuring only past games inform predictions:

#### **Selected Features After Redundancy Analysis:**
- **Mins_ewm_02**: EWM of minutes played (α=0.2) - **Best predictor (r=0.653)**
- **uPER_ewm_01**: EWM of Player Efficiency Rating (α=0.1) - **(r=0.534)**
- **Usage_Rate_ewm_01**: EWM of possession usage rate (α=0.1) - **(r=0.318)**
- **StarterFlag_ewm_02**: EWM of starter status (α=0.2) - **(r=0.525)**

#### **Feature Selection Rationale:**
- **Eliminated 25+ redundant features** (rolling windows highly correlated 0.95-0.99 with EWM)
- **EWM consistently outperformed rolling averages** across all metrics
- **Reduced from 40 to 13 total features** while preserving predictive power

### **Data Leakage Prevention**
- **Critical**: All historical features calculated using `shift(1)` before aggregation
- **Validation**: First game per player shows NaN in historical features (expected)
- **Target Creation**: `Target_Next_Mins` shifts current minutes forward by 1 game

---

## **Comprehensive EDA Findings**

### **1. Target Variable Distribution Analysis**

#### **Multi-Modal Distribution Confirmed:**
- **Bench Players**: 17.5 ± 7.0 minutes (IQR: 12-22 min) - 3,338 games (24.7%)
- **Role Players**: 20.6 ± 7.7 minutes (IQR: 15-26 min) - 1,936 games (14.3%)  
- **Starters**: 27.1 ± 7.5 minutes (IQR: 22-33 min) - 8,245 games (61.0%)

#### **Player Classification Logic:**
```python
StarterFlag_ewm_02 thresholds:
- Bench: <0.2 (avg StarterFlag = 0.037)
- Role Player: 0.2-0.6 (avg StarterFlag = 0.386)
- Starter: ≥0.6 (avg StarterFlag = 0.934)
```

#### **Outlier Analysis (Predictable, Not Random):**
- **High-minute bench players (4.5%)**: Better performance (5.06 vs 3.93 uPER)
- **Low-minute starters (6.1%)**: Declining starter status (0.881 vs 0.934 StarterFlag)
- **Conclusion**: Outliers are performance-driven and predictable

### **2. Feature Correlation & Redundancy Analysis**

#### **Feature Performance by Player Type:**
```
Category        Mins_ewm_02  uPER_ewm_01  StarterFlag_ewm_02  Usage_Rate_ewm_01
Bench           0.447        0.336        0.039               0.162
Role Player     0.418        0.307        0.106               0.155  
Starter         0.514        0.384        0.215               0.256
```

**Key Insight**: Different feature importance across player types → **separate models recommended**

#### **Team Effects Analysis:**
- **Significant team differences**: 20.7 to 29.4 minutes average (8.7-minute range)
- **Short rotation teams**: YOR (20.7), SAS (20.8), NIP (20.7)
- **Deep rotation teams**: CON (29.4), LAU (28.8), MCG (27.6)
- **Home/Away effect**: Small but measurable (±2.5 minutes for some teams)

### **3. Temporal Patterns Analysis**

#### **Seasonal Minute Allocation:**
- **Early Season** (Sep-Oct): 23.1 minutes (coaches experimenting)
- **Non-Conference** (Nov-Dec): 23.6 minutes  
- **Conference Play** (Jan-Feb): 24.0 minutes (established rotations)
- **Tournament** (Mar): 25.5 minutes (shorter rotations, starters play more)

#### **Year-over-Year Consistency:**
- **2022**: 23.1 minutes (3,445 games)
- **2023**: 23.7 minutes (7,060 games) 
- **2024**: 24.3 minutes (3,019 games)

#### **Player Continuity:**
- **265 players** appear across all 3 years
- **46 players** appear across 2 years
- **Strong temporal structure** for time-series validation

### **4. Data Quality Validation**

#### **Critical Issues Resolved:**
- **✅ Fixed**: 5 duplicate player-date combinations (data corruption)
- **✅ Fixed**: 1,680 missing Starter_Category values (filled with 'Bench')
- **✅ Verified**: No missing values, no infinite values
- **✅ Verified**: All logical consistency checks passed

#### **Final Validation Results:**
- **Feature ranges**: All within expected basketball parameters
- **Location flags**: All games sum to exactly 1
- **StarterFlag alignment**: Perfect correlation with player categories
- **Sample sizes**: All categories >1,900 games (sufficient for modeling)

---

## **Recommended Modeling Strategy**

### **1. Train/Test Split Strategy**

#### **Chosen Approach: Year-Based Split**
- **Training Data**: 2022-2023 seasons (10,505 games, 77.7%)
- **Testing Data**: 2024 season (3,019 games, 22.3%) 
- **Rationale**: Clean temporal separation, realistic evaluation, no data leakage

#### **Split Implementation:**
```python
train_data = df_cleaned[df_cleaned['Year'].isin([2022, 2023])].copy()
test_data = df_cleaned[df_cleaned['Year'] == 2024].copy()
```

#### **Alternative Considered:**
- **80/20 Chronological** (rejected due to less clean separation)

### **2. Modeling Approach Recommendation**

#### **Separate Models by Player Type** (Strongly Recommended)
**Rationale:**
- **Different feature importance** across player types
- **Well-separated distributions** with minimal overlap
- **Sufficient sample sizes** for each category
- **Different prediction ranges** and variances

#### **Model Architecture Options:**
1. **Three separate models**: Bench, Role Player, Starter
2. **Two-tier approach**: Binary classification (starter/non-starter) → Regression
3. **Single ensemble model** with player type as feature (fallback option)

### **3. Feature Set for Modeling**

#### **Final Feature List** (13 features):
```python
model_features = [
    # Identifiers & Context
    'PlayerName', 'Date', 'Abbr',
    
    # Game Context
    'Is_Home', 'Is_Away', 'Is_Neutral', 'Rest_Days', 'Team_Avg_Minutes_Season',
    
    # Historical Performance (reduced from 25+ to 4)
    'Mins_ewm_02',           # Best overall predictor (r=0.653)
    'uPER_ewm_01',           # Performance metric (r=0.534)
    'Usage_Rate_ewm_01',     # Role indicator (r=0.318)
    'StarterFlag_ewm_02',    # Starter status (r=0.525)
    
    # Target
    'Target_Next_Mins'
]
```

### **4. Model Selection Considerations**

#### **Algorithm Recommendations:**
1. **Random Forest**: Handles categorical features (teams), robust to outliers
2. **XGBoost/LightGBM**: High performance, handles mixed data types
3. **Linear Regression**: Interpretable baseline, separate by player type
4. **Neural Networks**: If non-linear interactions are important

#### **Evaluation Metrics:**
- **Primary**: MAE (Mean Absolute Error in minutes)
- **Secondary**: RMSE, R²
- **Business**: Accuracy within ±5 minutes
- **Category-specific**: Performance by player type

### **5. Cross-Validation Strategy**

#### **Time-Series Cross-Validation** (Recommended):
- **Expanding window approach** to respect temporal structure
- **Multiple train/validation splits** within training period
- **Prevents data leakage** in hyperparameter tuning

#### **Implementation:**
```python
# Example validation splits within training data
val_splits = [
    ('2022-09-30', '2023-01-31', '2023-02-01', '2023-03-31'),
    ('2022-09-30', '2023-06-30', '2023-07-01', '2023-09-30'),
    ('2022-09-30', '2023-09-30', '2023-10-01', '2023-12-30')
]
```

---

## **Key Success Factors & Considerations**

### **1. Model Performance Expectations**
- **Baseline MAE**: ~6-8 minutes (using mean prediction)
- **Target MAE**: <4 minutes for good performance
- **Different accuracy expected** by player type (starters more predictable)

### **2. Feature Engineering Opportunities**
- **Team interaction terms**: Home advantage by team
- **Player progression**: Within-season trends
- **Matchup effects**: Opponent strength (if available)
- **Conference play indicators**: Different rotation patterns

### **3. Potential Challenges**
- **Injury games**: Sudden minute changes (unpredictable)
- **Blowout games**: Garbage time effects
- **Tournament play**: Different coaching strategies
- **Transfer players**: Limited historical data

### **4. Business Application**
- **Fantasy sports**: Daily lineup optimization
- **Coaching analytics**: Rotation planning
- **Sports betting**: Player prop predictions
- **Player development**: Minutes expectation modeling

---

## **Next Steps for Model Development**

### **Immediate Actions:**
1. **Load cleaned dataset**: `basketball_minutes_features_FINAL.csv`
2. **Implement train/test split**: Year-based (2022-2023 train, 2024 test)
3. **Baseline model**: Simple linear regression by player type
4. **Feature importance analysis**: Validate EDA findings

### **Model Development Pipeline:**
1. **Baseline Models**: Linear regression for each player type
2. **Advanced Models**: Random Forest, XGBoost comparisons  
3. **Hyperparameter Tuning**: Time-series CV within training data
4. **Model Selection**: Best performer on validation sets
5. **Final Evaluation**: Single test on 2024 data

### **Validation Checklist:**
- [ ] Confirm no data leakage in features
- [ ] Validate temporal split integrity  
- [ ] Check feature distributions train vs test
- [ ] Monitor for concept drift (2024 vs 2022-2023)
- [ ] Evaluate performance by player type and season phase

---

## **Dataset Ready for Production**

**Status**: ✅ **COMPLETE AND VALIDATED**
- **Data Quality**: All critical issues resolved
- **Feature Engineering**: Optimally reduced feature set
- **EDA Insights**: Comprehensive understanding of patterns
- **Modeling Strategy**: Clear roadmap for implementation
- **Evaluation Framework**: Robust validation approach

The dataset is now ready for immediate model training with high confidence in data quality and modeling approach.

This foundation provides a clean, leakage-free dataset ready for comprehensive exploratory analysis to understand the patterns that drive basketball minute allocation decisions.

advise for common problems or issues.
```
command to run if program contains helper info
```

## Authors

Jerry Chen
[@_jerry.chen](https://www.instagram.com/_jerry.chen/)
[LinkedIn](https://www.linkedin.com/in/jerry-chen-63a248289/)

## Version History

* 0.2
    * Various bug fixes and optimizations
* 0.1
    * Initial Release

## License

This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* [awesome-readme](https://github.com/matiassingers/awesome-readme)
* [PurpleBooth](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
* [dbader](https://github.com/dbader/readme-template)
* [zenorocha](https://gist.github.com/zenorocha/4526327)
* [fvcproductions](https://gist.github.com/fvcproductions/1bfc2d4aecb01a834b46)
