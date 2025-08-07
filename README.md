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

## Plan for EDA analysis:
# Comprehensive Context Summary for Basketball Minutes Prediction EDA

## **Project Overview & Objective**
We are building a **basketball minutes prediction model** for college basketball players. The goal is to predict how many minutes a player will play in their **next game** based on their historical performance, recent form, and game context - all using only information available **before the game starts** (no data leakage).

## **Target Variable**
- **`Target_Next_Mins`**: Minutes a player will play in their next game (created by shifting current `Mins` forward by 1 game per player)
- **Range**: 0-45+ minutes (typical college basketball game length)
- **Distribution**: Likely bimodal (starters ~25-35 mins, bench players ~5-15 mins)

## **Dataset Current State**
- **Shape**: 13,524 rows × 40 columns
- **Players**: Multiple college basketball players across teams
- **Time Period**: 2022-2024 seasons
- **Data Quality**: No missing values after preprocessing, proper chronological sorting

## **Feature Engineering Completed**

### **Core Data**
- **`PlayerName`**: Player identifier for grouping
- **`Date`**: Game date (chronological sorting maintained)
- **`Abbr`**: Team abbreviation
- **`Mins`**: Current game minutes (used to create target, will be excluded from model features)

### **Game Context Features (Pre-game Known)**
- **`Is_Home`**: Home game indicator (0/1)
- **`Is_Away`**: Away game indicator (0/1) 
- **`Is_Neutral`**: Neutral site game indicator (0/1)
- **`Rest_Days`**: Days since last game (captures back-to-back effects, rest impact)

### **Historical Performance Features (No Data Leakage)**
All features use **shift(1)** before calculation, ensuring only past games inform predictions:

#### **Minutes History (Rolling)**
- `Mins_last3_mean/median`, `Mins_last5_mean/median`, `Mins_last10_mean/median`
- Captures recent playing time trends, coach trust levels

#### **Efficiency Metrics (Rolling)**  
- `uPER_last3/5/10_median`: Player Efficiency Rating (comprehensive performance metric)
- `Usage_Rate_last3/5/10_median`: Percentage of team possessions used while on court

#### **Role Indicators (Rolling)**
- `StarterFlag_last3/5/10_mean`: Recent starter rate (e.g., 0.67 = started 2 of last 3 games)

#### **Exponentially Weighted Moving Averages**
- **Alpha values**: 0.1, 0.2, 0.3, 0.5 (slow to fast adaptation)
- **Variables**: Mins, uPER, Usage_Rate, StarterFlag
- **Purpose**: Captures different trend timescales (season-long vs recent form)

## **Data Leakage Prevention**
- **Critical Fix**: All rolling/EWM features use `shift(1)` before calculation
- **Validation**: First game for each player has NaN in historical features (expected)
- **Target Creation**: `Target_Next_Mins` shifts current minutes forward, so we predict "tomorrow's" minutes using "yesterday's" performance

## **Feature Selection Philosophy**
- **Median over Mean**: For performance metrics (robust to outlier games like injuries, blowouts)
- **Mean for Binary**: For StarterFlag (represents starter rate percentage)
- **Excluded Current Game Data**: No current game performance stats in features (uPER, Usage_Rate, StarterFlag)

## **Upcoming EDA Analysis Objectives**

### **1. Target Distribution Analysis**
```python
# Expected analyses based on reference script:
- Histogram of Target_Next_Mins (likely bimodal: starters vs bench)
- Distribution by position/role (StarterFlag patterns)
- Minutes variance by team, rest days, home/away
```

### **2. Feature Correlation Analysis**
```python
# High-value correlations expected:
- Mins_last3_median vs Target_Next_Mins (strong positive)
- StarterFlag_last3_mean vs Target_Next_Mins (strong positive) 
- Rest_Days vs Target_Next_Mins (negative for back-to-backs?)
- Team-specific effects via Abbr
```

### **3. Time Series Patterns**
- Seasonal trends (conference play vs non-conference)
- Player development arcs throughout season
- Impact of rest days on minutes allocation

### **4. Outlier Investigation**
- Injury games (sudden minute drops)
- Blowout games (garbage time effects)
- Tournament games (different rotation patterns)

## **Planned Modeling Approach**

### **Train-Test Split Strategy**
- **Temporal Split**: Train on earlier games, test on later games (respects time structure)
- **Alternative**: Random split by player-game combinations (80/20 as in reference)
- **Validation**: Time-series cross-validation for hyperparameter tuning

### **Model Considerations**
- **Separate Models**: Starters vs bench players (different minute distributions)
- **Team Effects**: Account for coach preferences, system differences
- **Player Clustering**: Similar roles/positions may have similar patterns

### **Success Metrics**
- **MAE**: Mean Absolute Error in minutes
- **RMSE**: Root Mean Square Error
- **Classification Accuracy**: High/medium/low minutes buckets
- **Business Metric**: Prediction accuracy within ±5 minutes

## **Key Challenges to Explore in EDA**
1. **Starter vs Bench Separation**: How well do features distinguish these roles?
2. **Team Variability**: Do some teams have more predictable rotations?
3. **Rest Impact**: Quantify back-to-back game effects
4. **Feature Redundancy**: Which EWM alphas and rolling windows add unique value?
5. **Missing Context**: What external factors (injuries, matchups) aren't captured?

## **Next Steps Post-EDA**
1. Feature selection based on correlation analysis
2. Handle any remaining data quality issues
3. Final feature engineering (interaction terms, binning)
4. Model selection and hyperparameter tuning
5. Evaluation on held-out test set

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
