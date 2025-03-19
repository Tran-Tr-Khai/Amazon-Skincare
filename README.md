# Automated Analysis of Skin Care Product Usage Trends on Amazon Ecommerce

## Table of Contents
- [Project Overview](#project-overview)
- [Data Pipeline](#data-pipeline)
- [Web Scraping](#web-scraping)
- [Transform](#transform)
- [Clustering with K-Means](#clustering-with-k-means)
- [Data Warehouse](#data-warehouse)
- [Visualization with Power BI](#visualization-with-power-bi)
- [Automation with Docker and Airflow](#automation-with-docker-and-airflow)
- [Usage](#usage)
---

## Project Overview
This project, title **"Automated Analyzing Skin-Care Product Usage Trends on the Amazon E-commerce Platform"**, explores skincare product trends on Amazon by collecting, processing, and analyzing data from Amazon's bestseller lists. The main focus is to uncover insights into **customer purchasing behavior** and **product performance** through a robust data pipeline that integrates:
- Web scraping https://www.amazon.com/Best-Sellers-Beauty-Personal-Care-Skin-Care-Products/zgbs/beauty
- ETL (Extract, Transform, Load) processes
- Data warehousing
- K-Means clustering
- Visualization with Power BI

### Goals
The primary objective is to identify key trends in skincare product sales, such as:
- Sustainable practices (e.g., eco-friendly packaging)
- Emerging market trends (e.g., rise of natural ingredients)
- Potential business opportunities (e.g., underserved product categories)

These insights are derived from analyzing critical metrics:
- **`bought_info`**: Number of purchases
- **`rating_count`**: Total number of ratings
- **`top`**: Ranking position on the bestseller list

---

## Data Pipeline
![Data Pipeline Diagram](image/elt.jpg)

*Note*: Update the image path to a valid URL or relative path (e.g., `./image/elt.jpg`) when hosting this project online.

The data pipeline automates the flow from raw data collection to actionable insights, ensuring efficiency and scalability.

---

## Web Scraping
This section leverages web scraping techniques to gather data from Amazon's skincare product listings, including product names, prices, ratings, and purchase statistics.

### Tools Used
- **`Requests`**:
  - **Purpose**: Sends HTTP requests to fetch raw HTML data from Amazon product pages.
  - **Why**: It’s lightweight, fast, and ideal for static web content, reducing the need for heavy browser automation when possible.
- **`BeautifulSoup`**:
  - **Purpose**: Parses HTML content to extract structured data like product titles, ratings, and purchase counts.
  - **Why**: It provides a simple, Pythonic way to navigate and search HTML tags, making data extraction efficient and reliable.
- **`Selenium`**:
  - **Purpose**: Automates browser interactions to scrape dynamic content (e.g., JavaScript-loaded elements like "Load More" buttons).
  - **Why**: Essential for handling Amazon’s dynamic pages where content isn’t fully loaded in the initial HTML response.

### Implementation Notes
- The scraping process starts with `Requests` to fetch initial page data, followed by `BeautifulSoup` for parsing. If dynamic content is detected, `Selenium` takes over to simulate user interactions.
- Anti-scraping measures (e.g., CAPTCHAs) are mitigated by adding delays and rotating user agents.

---

## Transform
The **Transform** step processes raw data collected from web scraping into a clean, structured format suitable for analysis. It includes data cleaning, feature engineering, and predictive modeling to impute missing values, followed by clustering preparation.

### Data Preprocessing
- **Libraries Used**:
  - **`pandas`**: For data manipulation and cleaning.
  - **`numpy`**: For numerical operations.
- **Steps**:
  - Clean and convert columns:
    - `top`: Remove `#` and convert to integer.
    - `rating_count`: Remove commas and convert to integer.
    - `price`: Remove `$` and convert to float.
    - `bought_info`: Extract numeric value from "X K+" format (e.g., "10K+" → 10000), handle missing values later.
  - Fill missing `brand` values with `"unknown"`.

### Predictive Modeling for Missing Values
- **Libraries Used**:
  - **`sklearn`**: For `LabelEncoder`, `StandardScaler`, `RandomForestRegressor`, and model evaluation.
  - **`xgboost`**: For `XGBRegressor`.
- **Process**:
  1. **Encoding**: Convert categorical columns (`category`, `brand`, `skin_type`) to numeric using `LabelEncoder`.
  2. **Split Data**: Separate rows with known `bought_info` (training) and missing `bought_info` (prediction).
  3. **Scaling**: Apply `StandardScaler` to normalize features.
  4. **Model Training**:
     - **Random Forest**: Tune hyperparameters (`n_estimators`, `max_depth`, etc.) using `RandomizedSearchCV`.
     - **XGBoost**: Tune hyperparameters (`learning_rate`, `subsample`, etc.) similarly.
  5. **Evaluation**: Compare models using Mean Squared Error (MSE) and R² on validation data.
  6. **Prediction**: Use the best model (lowest MSE) to predict missing `bought_info` values.
- **Output**: A complete dataset with imputed `bought_info` saved as `processed.csv`.

### Why This Approach?
- Imputing missing `bought_info` with machine learning ensures more accurate trends compared to simple statistical methods (e.g., mean imputation).
- Random Forest and XGBoost handle non-linear relationships in the data effectively.

---

## Clustering with K-Means
This section applies K-Means clustering to group skincare products based on purchase behavior and performance metrics, with feature engineering to enhance the process.

### Feature Engineering
- **Libraries Used**:
  - **`pandas`**: For data manipulation.
  - **`numpy`**: For numerical operations.
  - **`sklearn.preprocessing`**: For `StandardScaler`.
  - **`sklearn.decomposition`**: For `PCA`.
- **Steps**:
  1. **Select Features**: Use `bought_info`, `rating_count`, and `top` for clustering; drop irrelevant columns (`link`, `id`, `skin_type`, `brand`, `price`, `category`).
  2. **Scaling**: Normalize the data using `StandardScaler` to ensure equal feature weighting.
  3. **Dimensionality Reduction**: Apply `PCA` (2 components) to reduce the feature space while retaining variance.

### Clustering Process
- **Libraries Used**:
  - **`sklearn.cluster`**: For `KMeans`.
  - **`yellowbrick.cluster`**: For `KElbowVisualizer`.
  - **`matplotlib` & `seaborn`**: For visualization.
- **Steps**:
  1. **Optimal K Selection**: Use the elbow method (`KElbowVisualizer`) to determine the optimal number of clusters (`k`) within the range 2–10.
  2. **K-Means Clustering**: Apply `KMeans` with the selected `k` to assign cluster labels.
  3. **Visualization**: Plot clusters using a scatter plot of PCA components, colored by cluster labels.
- **Cluster Labeling**:
  - Compute mean `bought_info`, `rating_count`, and `top` for each cluster.
  - Define thresholds based on average `top` and `rating_count`.
  - Assign labels:
    - `Potential Growth`: High `top`, low `rating_count`, highest `bought_info` among potential clusters.
    - `Steady Seller`: High `top`, low `rating_count`, lower `bought_info`.
    - `Sustainable Trend`: Low `top`, high `rating_count`.
    - `Trending`: Low `top`, low `rating_count`.
    - `Trending Again`: High `top`, high `rating_count`.
- **Output**: Updated DataFrame with `cluster` and `cluster_label` columns, saved as `gold.csv`.

### Why This Approach?
- PCA reduces noise and dimensionality, improving clustering performance.
- The elbow method ensures an optimal number of clusters, balancing complexity and interpretability.
- Custom labeling provides actionable insights into product trends.

---

## Data Warehouse
The transformed data is loaded into a **PostgreSQL data warehouse** for structured storage, efficient querying, and downstream analysis.

### Setup
- **Tool**: PostgreSQL
- **Libraries Used**:
  - **`pandas`**: For reading and manipulating the CSV input.
  - **`psycopg2`**: For connecting to PostgreSQL and executing SQL commands.
  - **`dotenv`**: For securely loading environment variables (e.g., database credentials).
  - **`logging`**: For tracking the loading process and errors.
- **Schema**:
  - `id` (TEXT): Product identifier.
  - `top` (INTEGER): Ranking position.
  - `link` (TEXT): Product URL.
  - `rating_count` (INTEGER): Number of ratings.
  - `price` (DECIMAL): Product price.
  - `skin_type` (TEXT): Targeted skin type.
  - `category` (TEXT): Product category.
  - `brand` (TEXT): Product brand.
  - `bought_info` (INTEGER): Number of purchases.
  - `cluster_label` (TEXT): Assigned cluster label from K-Means.

### Loading Process
- **Steps**:
  1. Load database credentials from a `.env` file (e.g., `PG_NAME`, `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_PORT`).
  2. Connect to PostgreSQL using `psycopg2`.
  3. Drop the existing table (if any) to avoid duplication.
  4. Create a new table with the defined schema.
  5. Insert data from the DataFrame using bulk insertion (`executemany`).
  6. Commit the transaction and log success or rollback on error.
- **Logging**: Success or failure is recorded in `load_to_postgresql.log` for debugging.
- **Input**: `gold.csv` (output from the Transform step).
- **Why PostgreSQL**: It’s open-source, supports large datasets, and provides robust SQL capabilities for analysis.

---

## Visualization with Power BI
Power BI is used to create interactive dashboards for visualizing trends and clusters.
![Overview](image/overview.jpg)

![trending](image/trending.jpg)

--- 

## Automation with Docker and Airflow
To enable automated, time-scheduled analysis, the project leverages **Docker** for containerization and **Apache Airflow** for workflow orchestration.  
### Using Docker and Airflow
1. Build Docker images: `docker-compose build`
2. Start containers: `docker-compose up -d`
3. Access Airflow UI (default: `localhost:8080`) to monitor and trigger the DAG.
4. View updated results in Power BI or query the PostgreSQL database.
