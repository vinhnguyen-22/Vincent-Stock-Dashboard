import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st
from plotly.subplots import make_subplots
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from vnstock import Vnstock

# Set page configuration
st.set_page_config(layout="wide", page_title="Stock Market ML Prediction")

# Title and description
st.title("Stock Market Machine Learning Prediction")
st.markdown(
    """
This application analyzes HOSE stock market data and builds a machine learning model to predict whether a stock 
will have positive or negative net value based on trading patterns. The model analyzes relationships between 
trader behaviors and stock performance.
"""
)


# Data loading function
@st.cache_data
def load_data():
    # In a real scenario, we'd load from CSV
    # For demonstration purposes, we'll use the data provided
    try:
        df = pd.DataFrame()
        exchange = st.selectbox(
            "Chọn sàn giao dịch",
            options=[
                # "HOSE",
                # "HNX",
                # "UPCOM",
                "VN30",
                "VN100",
                "HNX30",
                "VNMidCap",
                "VNSmallCap",
                "VNAllShare",
                "HNXCon",
                "HNXFin",
                "HNXLCap",
                "HNXMSCap",
                "HNXMan",
            ],
            index=0,
        )
        stock_by_exchange = (
            Vnstock().stock("ACB", source="VCI").listing.symbols_by_group(exchange).tolist()
        )
        df = pd.DataFrame()
        for ticker in stock_by_exchange:
            df_cf = fetch_cashflow_market(ticker)
            if not df_cf.empty:
                df = pd.concat([df, df_cf], ignore_index=True)
        return df
    except:
        st.error("Error loading data. Please make sure the file is available.")
        # Generate sample data for demonstration if file not found
        return pd.DataFrame(
            {
                "code": ["STB", "MBB", "VIC", "VPB", "HPG", "TCB", "VCB", "SSI", "FPT", "VHM"],
                "totalVal": [
                    1551535570,
                    1554414860,
                    796649250,
                    942031005,
                    1454881785,
                    994374945,
                    388871950,
                    1258278565,
                    1956246640,
                    714540880,
                ],
                "topActiveBuyVal": [
                    932547245,
                    820197130,
                    397965620,
                    417479290,
                    580030640,
                    433357255,
                    159940340,
                    599671720,
                    767535990,
                    318705540,
                ],
                "midActiveBuyVal": [
                    105253625,
                    135841465,
                    103425470,
                    56953770,
                    74452770,
                    72754225,
                    41372890,
                    117723120,
                    167993030,
                    83071240,
                ],
                "botActiveBuyVal": [
                    8939035,
                    12508320,
                    9281200,
                    3505275,
                    6539830,
                    6333210,
                    6422600,
                    8782270,
                    29418650,
                    8157980,
                ],
                "topActiveSellVal": [
                    429463360,
                    495625050,
                    227022970,
                    412817330,
                    684224010,
                    395673430,
                    138455920,
                    442261305,
                    800793960,
                    247107790,
                ],
                "midActiveSellVal": [
                    70316415,
                    82591500,
                    53872040,
                    47805555,
                    100110580,
                    79871715,
                    36923480,
                    82917060,
                    163616200,
                    52367360,
                ],
                "botActiveSellVal": [
                    5015890,
                    7651395,
                    5081950,
                    3469785,
                    9523955,
                    6385110,
                    5756720,
                    6923090,
                    26888810,
                    5130970,
                ],
                "netTopVal": [
                    503083885,
                    324572080,
                    170942650,
                    4661960,
                    -104193370,
                    37683825,
                    21484420,
                    157410415,
                    -33257970,
                    71597750,
                ],
                "netMidVal": [
                    34937210,
                    53249965,
                    49553430,
                    9148215,
                    -25657810,
                    -7117490,
                    4449410,
                    34806060,
                    4376830,
                    30703880,
                ],
                "netBotVal": [
                    3923145,
                    4856925,
                    4199250,
                    35490,
                    -2984125,
                    -51900,
                    665880,
                    1859180,
                    2529840,
                    3027010,
                ],
            }
        )


# Load data
df = load_data()

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(
    ["Data Exploration", "Feature Engineering", "Model Training", "Prediction"]
)

with tab1:
    st.header("Data Exploration")

    # Show data sample
    st.subheader("Data Sample")
    st.dataframe(df.head())

    # Basic statistics
    st.subheader("Basic Statistics")
    st.dataframe(df.describe())

    # Calculate correlation matrix
    st.subheader("Correlation Matrix")

    # Create derived features
    df["netVal"] = df["netTopVal"] + df["netMidVal"] + df["netBotVal"]
    df["totalBuyVal"] = df["topActiveBuyVal"] + df["midActiveBuyVal"] + df["botActiveBuyVal"]
    df["totalSellVal"] = df["topActiveSellVal"] + df["midActiveSellVal"] + df["botActiveSellVal"]
    df["buyProportion"] = df["totalBuyVal"] / (df["totalBuyVal"] + df["totalSellVal"])
    df["topBuySellRatio"] = df["topActiveBuyVal"] / df["topActiveSellVal"]
    df["midBuySellRatio"] = df["midActiveBuyVal"] / df["midActiveSellVal"]
    df["botBuySellRatio"] = df["botActiveBuyVal"] / df["botActiveSellVal"]
    df["topActiveBuyPct"] = df["topActiveBuyVal"] / df["totalVal"]
    df["topActiveSellPct"] = df["topActiveSellVal"] / df["totalVal"]

    # Select numerical features for correlation
    numerical_features = [
        "totalVal",
        "topActiveBuyVal",
        "midActiveBuyVal",
        "botActiveBuyVal",
        "topActiveSellVal",
        "midActiveSellVal",
        "botActiveSellVal",
        "buyProportion",
        "topBuySellRatio",
        "midBuySellRatio",
        "botBuySellRatio",
        "topActiveBuyPct",
        "topActiveSellPct",
        "netVal",
    ]

    corr_matrix = df[numerical_features].corr()

    # Plot correlation heatmap
    fig = px.imshow(
        corr_matrix,
        text_auto=".2f",
        title="Feature Correlation Heatmap",
        color_continuous_scale="RdBu_r",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Visualize the relationship between key features and target
    st.subheader("Feature Relationships with Net Value")

    # Create scatterplots
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Buy Proportion vs Net Value",
            "Top Trader Buy/Sell Ratio vs Net Value",
            "Top Trader Buy % vs Net Value",
            "Trading Volume vs Net Value",
        ),
    )

    # Buy Proportion vs Net Value
    fig.add_trace(
        go.Scatter(
            x=df["buyProportion"],
            y=df["netVal"],
            mode="markers+text",
            text=df["code"],
            textposition="top center",
            name="Buy Proportion",
        ),
        row=1,
        col=1,
    )

    # Top Trader Buy/Sell Ratio vs Net Value
    fig.add_trace(
        go.Scatter(
            x=df["topBuySellRatio"],
            y=df["netVal"],
            mode="markers+text",
            text=df["code"],
            textposition="top center",
            name="Top Buy/Sell Ratio",
        ),
        row=1,
        col=2,
    )

    # Top Trader Buy % vs Net Value
    fig.add_trace(
        go.Scatter(
            x=df["topActiveBuyPct"],
            y=df["netVal"],
            mode="markers+text",
            text=df["code"],
            textposition="top center",
            name="Top Buy %",
        ),
        row=2,
        col=1,
    )

    # Trading Volume vs Net Value
    fig.add_trace(
        go.Scatter(
            x=df["totalVal"],
            y=df["netVal"],
            mode="markers+text",
            text=df["code"],
            textposition="top center",
            name="Trading Volume",
        ),
        row=2,
        col=2,
    )

    fig.update_layout(height=700, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Feature Engineering")

    # Create target variable
    st.subheader("Target Variable Creation")

    # Add net value target
    df["target"] = np.where(df["netVal"] > 0, 1, 0)

    # Show class distribution
    positive_count = df["target"].sum()
    negative_count = len(df) - positive_count

    fig = px.pie(
        values=[positive_count, negative_count],
        names=["Positive Net Value", "Negative Net Value"],
        title="Target Class Distribution",
        color_discrete_sequence=["green", "red"],
    )
    st.plotly_chart(fig, use_container_width=True)

    # Feature engineering
    st.subheader("Feature Creation")

    # Show the features we'll use for modeling
    st.write("The following features will be used for modeling:")

    # Create more features
    df["topBuyPct"] = df["topActiveBuyVal"] / df["totalBuyVal"]
    df["midBuyPct"] = df["midActiveBuyVal"] / df["totalBuyVal"]
    df["botBuyPct"] = df["botActiveBuyVal"] / df["totalBuyVal"]

    df["topSellPct"] = df["topActiveSellVal"] / df["totalSellVal"]
    df["midSellPct"] = df["midActiveSellVal"] / df["totalSellVal"]
    df["botSellPct"] = df["botActiveSellVal"] / df["totalSellVal"]

    df["topBuySellDiff"] = df["topBuyPct"] - df["topSellPct"]
    df["midBuySellDiff"] = df["midBuyPct"] - df["midSellPct"]
    df["botBuySellDiff"] = df["botBuyPct"] - df["botSellPct"]

    features = [
        "totalVal",
        "buyProportion",
        "topBuySellRatio",
        "midBuySellRatio",
        "botBuySellRatio",
        "topActiveBuyPct",
        "topActiveSellPct",
        "topBuyPct",
        "midBuyPct",
        "botBuyPct",
        "topSellPct",
        "midSellPct",
        "botSellPct",
        "topBuySellDiff",
        "midBuySellDiff",
        "botBuySellDiff",
    ]

    # Show feature table
    feature_df = pd.DataFrame(
        {
            "Feature": features,
            "Description": [
                "Total trading value",
                "Proportion of buy volume to total volume",
                "Ratio of top trader buy to sell values",
                "Ratio of mid trader buy to sell values",
                "Ratio of bot trader buy to sell values",
                "Top trader buy as % of total volume",
                "Top trader sell as % of total volume",
                "Top trader buy as % of total buy volume",
                "Mid trader buy as % of total buy volume",
                "Bot trader buy as % of total buy volume",
                "Top trader sell as % of total sell volume",
                "Mid trader sell as % of total sell volume",
                "Bot trader sell as % of total sell volume",
                "Difference between top buy % and top sell %",
                "Difference between mid buy % and mid sell %",
                "Difference between bot buy % and bot sell %",
            ],
        }
    )

    st.dataframe(feature_df)

    # Show the feature values
    st.subheader("Feature Values")
    st.dataframe(df[features + ["code", "target"]])

    # Feature importance using statistical test
    st.subheader("Feature Importance (Statistical Test)")

    # Calculate feature importance using ANOVA F-test
    X = df[features]
    y = df["target"]

    # Apply feature selection
    selector = SelectKBest(score_func=f_classif, k="all")
    selector.fit(X, y)

    # Get scores and p-values
    importance_df = pd.DataFrame(
        {"Feature": features, "F-Score": selector.scores_, "P-Value": selector.pvalues_}
    )

    importance_df = importance_df.sort_values("F-Score", ascending=False)

    # Plot feature importance
    fig = px.bar(
        importance_df,
        x="Feature",
        y="F-Score",
        title="Feature Importance (F-Score)",
        color="F-Score",
        labels={"F-Score": "F-Score (Higher is Better)"},
    )
    st.plotly_chart(fig, use_container_width=True)

    # Show feature importance table
    st.dataframe(importance_df)

with tab3:
    st.header("Model Training")

    # Setup train-test split
    X = df[features]
    y = df["target"]

    # Add a button to train the model
    if st.button("Train Model"):
        with st.spinner("Training model... This may take a moment."):
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42
            )

            # Create pipeline
            pipeline = Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("classifier", RandomForestClassifier(random_state=42)),
                ]
            )

            # Define parameters for grid search
            param_grid = {
                "classifier__n_estimators": [50, 100],
                "classifier__max_depth": [None, 5, 10],
                "classifier__min_samples_split": [2, 5],
            }

            # Perform grid search
            grid_search = GridSearchCV(
                pipeline, param_grid=param_grid, cv=5, scoring="accuracy", n_jobs=-1, verbose=1
            )

            # Fit the model
            grid_search.fit(X_train, y_train)

            # Get best model
            best_model = grid_search.best_estimator_

            # Make predictions
            y_pred = best_model.predict(X_test)

            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            conf_matrix = confusion_matrix(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True)

            # Display metrics
            st.subheader("Model Performance")
            st.metric("Accuracy", f"{accuracy:.4f}")

            # Plot confusion matrix
            conf_df = pd.DataFrame(
                conf_matrix,
                index=["Actual Negative", "Actual Positive"],
                columns=["Predicted Negative", "Predicted Positive"],
            )

            fig = px.imshow(
                conf_df,
                text_auto=True,
                title="Confusion Matrix",
                labels=dict(x="Predicted", y="Actual", color="Count"),
                x=["Predicted Negative", "Predicted Positive"],
                y=["Actual Negative", "Actual Positive"],
                color_continuous_scale="Blues",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Classification report
            report_df = pd.DataFrame(report).transpose()
            st.dataframe(report_df)

            # Feature importance
            if hasattr(best_model.named_steps["classifier"], "feature_importances_"):
                importances = best_model.named_steps["classifier"].feature_importances_
                indices = np.argsort(importances)[::-1]

                importance_df = pd.DataFrame(
                    {"Feature": [features[i] for i in indices], "Importance": importances[indices]}
                )

                fig = px.bar(
                    importance_df,
                    x="Feature",
                    y="Importance",
                    title="Feature Importance (Random Forest)",
                    color="Importance",
                    labels={"Importance": "Importance Score"},
                )
                st.plotly_chart(fig, use_container_width=True)

            # Store the model in the session state
            st.session_state["model"] = best_model
            st.session_state["features"] = features

            st.success("Model trained successfully!")
    else:
        st.info("Click the button above to train the machine learning model.")

with tab4:
    st.header("Stock Market Prediction")

    # Create a form for user to input stock data
    st.subheader("Predict Stock Net Value Direction")

    # Check if model exists
    if "model" in st.session_state:
        model = st.session_state["model"]

        # Create columns for inputs
        col1, col2 = st.columns(2)

        with col1:
            total_val = st.number_input(
                "Total Trading Value", min_value=0.0, value=500000000.0, step=10000000.0
            )
            buy_proportion = st.slider(
                "Buy Proportion", min_value=0.0, max_value=1.0, value=0.5, step=0.01
            )
            top_buy_sell_ratio = st.slider(
                "Top Trader Buy/Sell Ratio", min_value=0.1, max_value=3.0, value=1.0, step=0.1
            )
            mid_buy_sell_ratio = st.slider(
                "Mid Trader Buy/Sell Ratio", min_value=0.1, max_value=3.0, value=1.0, step=0.1
            )
            bot_buy_sell_ratio = st.slider(
                "Bot Trader Buy/Sell Ratio", min_value=0.1, max_value=3.0, value=1.0, step=0.1
            )
            top_active_buy_pct = st.slider(
                "Top Trader Buy % of Total Vol", min_value=0.0, max_value=1.0, value=0.4, step=0.01
            )
            top_active_sell_pct = st.slider(
                "Top Trader Sell % of Total Vol",
                min_value=0.0,
                max_value=1.0,
                value=0.4,
                step=0.01,
            )
            top_buy_pct = st.slider(
                "Top Trader % of Total Buy", min_value=0.0, max_value=1.0, value=0.6, step=0.01
            )

        with col2:
            mid_buy_pct = st.slider(
                "Mid Trader % of Total Buy", min_value=0.0, max_value=1.0, value=0.3, step=0.01
            )
            bot_buy_pct = st.slider(
                "Bot Trader % of Total Buy", min_value=0.0, max_value=1.0, value=0.1, step=0.01
            )
            top_sell_pct = st.slider(
                "Top Trader % of Total Sell", min_value=0.0, max_value=1.0, value=0.6, step=0.01
            )
            mid_sell_pct = st.slider(
                "Mid Trader % of Total Sell", min_value=0.0, max_value=1.0, value=0.3, step=0.01
            )
            bot_sell_pct = st.slider(
                "Bot Trader % of Total Sell", min_value=0.0, max_value=1.0, value=0.1, step=0.01
            )
            top_buy_sell_diff = st.slider(
                "Top Buy-Sell % Difference", min_value=-1.0, max_value=1.0, value=0.0, step=0.01
            )
            mid_buy_sell_diff = st.slider(
                "Mid Buy-Sell % Difference", min_value=-1.0, max_value=1.0, value=0.0, step=0.01
            )
            bot_buy_sell_diff = st.slider(
                "Bot Buy-Sell % Difference", min_value=-1.0, max_value=1.0, value=0.0, step=0.01
            )

        # Create input data
        input_data = pd.DataFrame(
            {
                "totalVal": [total_val],
                "buyProportion": [buy_proportion],
                "topBuySellRatio": [top_buy_sell_ratio],
                "midBuySellRatio": [mid_buy_sell_ratio],
                "botBuySellRatio": [bot_buy_sell_ratio],
                "topActiveBuyPct": [top_active_buy_pct],
                "topActiveSellPct": [top_active_sell_pct],
                "topBuyPct": [top_buy_pct],
                "midBuyPct": [mid_buy_pct],
                "botBuyPct": [bot_buy_pct],
                "topSellPct": [top_sell_pct],
                "midSellPct": [mid_sell_pct],
                "botSellPct": [bot_sell_pct],
                "topBuySellDiff": [top_buy_sell_diff],
                "midBuySellDiff": [mid_buy_sell_diff],
                "botBuySellDiff": [bot_buy_sell_diff],
            }
        )

        # Make prediction
        if st.button("Predict"):
            prediction = model.predict(input_data)
            probability = model.predict_proba(input_data)

            # Display prediction
            st.subheader("Prediction Result")

            if prediction[0] == 1:
                st.success("Prediction: Positive Net Value (Buy Pressure)")
                st.metric("Confidence", f"{probability[0][1]:.2%}")
            else:
                st.error("Prediction: Negative Net Value (Sell Pressure)")
                st.metric("Confidence", f"{probability[0][0]:.2%}")

            # Show explanation
            st.subheader("Explanation")

            # Determine key factors
            if prediction[0] == 1:
                st.write(
                    """
                This prediction of positive net value could be driven by:
                
                1. High buy proportion (> 0.5) indicating more buying than selling activity
                2. Top trader buy/sell ratio > 1 indicating strong institutional buying
                3. Positive difference between top trader buy and sell percentages
                
                These factors suggest net buying pressure may continue, potentially leading to price appreciation.
                """
                )
            else:
                st.write(
                    """
                This prediction of negative net value could be driven by:
                
                1. Low buy proportion (< 0.5) indicating more selling than buying activity
                2. Top trader buy/sell ratio < 1 indicating institutional selling
                3. Negative difference between top trader buy and sell percentages
                
                These factors suggest net selling pressure may continue, potentially leading to price depreciation.
                """
                )
    else:
        st.warning("Please train the model first in the 'Model Training' tab.")

# Example with preset values for top stocks
st.header("Stock Examples")
if "model" in st.session_state:
    model = st.session_state["model"]
    st.subheader("Quick Prediction for Common Stocks")

    # Create stock examples
    stock_examples = {
        "High Buy Pressure Stock": {
            "totalVal": 1551535570,
            "buyProportion": 0.60,
            "topBuySellRatio": 2.17,
            "midBuySellRatio": 1.50,
            "botBuySellRatio": 1.78,
            "topActiveBuyPct": 0.60,
            "topActiveSellPct": 0.28,
            "topBuyPct": 0.89,
            "midBuyPct": 0.10,
            "botBuyPct": 0.01,
            "topSellPct": 0.85,
            "midSellPct": 0.14,
            "botSellPct": 0.01,
            "topBuySellDiff": 0.04,
            "midBuySellDiff": -0.04,
            "botBuySellDiff": 0.00,
        },
        "High Sell Pressure Stock": {
            "totalVal": 563364440,
            "buyProportion": 0.40,
            "topBuySellRatio": 0.63,
            "midBuySellRatio": 0.78,
            "botBuySellRatio": 0.80,
            "topActiveBuyPct": 0.34,
            "topActiveSellPct": 0.53,
            "topBuyPct": 0.85,
            "midBuyPct": 0.14,
            "botBuyPct": 0.01,
            "topSellPct": 0.87,
            "midSellPct": 0.12,
            "botSellPct": 0.01,
            "topBuySellDiff": -0.02,
            "midBuySellDiff": 0.02,
            "botBuySellDiff": 0.00,
        },
        "Balanced Stock": {
            "totalVal": 290301520,
            "buyProportion": 0.50,
            "topBuySellRatio": 0.99,
            "midBuySellRatio": 1.08,
            "botBuySellRatio": 1.00,
            "topActiveBuyPct": 0.41,
            "topActiveSellPct": 0.41,
            "topBuyPct": 0.82,
            "midBuyPct": 0.17,
            "botBuyPct": 0.01,
            "topSellPct": 0.83,
            "midSellPct": 0.16,
            "botSellPct": 0.01,
            "topBuySellDiff": -0.01,
            "midBuySellDiff": 0.01,
            "botBuySellDiff": 0.00,
        },
    }

    # Create selection for stock examples
    selected_stock = st.selectbox("Select Stock Example", list(stock_examples.keys()))

    if st.button("Make Quick Prediction"):
        # Create input data from selected example
        example_data = pd.DataFrame([stock_examples[selected_stock]])

        # Make prediction
        prediction = model.predict(example_data)
        probability = model.predict_proba(example_data)

        # Display prediction
        if prediction[0] == 1:
            st.success(f"Prediction for {selected_stock}: Positive Net Value (Buy Pressure)")
            st.metric("Confidence", f"{probability[0][1]:.2%}")
        else:
            st.error(f"Prediction for {selected_stock}: Negative Net Value (Sell Pressure)")
            st.metric("Confidence", f"{probability[0][0]:.2%}")
else:
    st.warning("Please train the model first to see stock examples.")

# Add a sidebar with instructions
with st.sidebar:
    st.header("Instructions")
    st.write(
        """
    This application demonstrates a machine learning approach to analyzing stock market trading data:
    
    1. **Data Exploration**: Examine the relationships between trading features and stock performance
    2. **Feature Engineering**: Create meaningful features from raw trading data
    3. **Model Training**: Train a machine learning model to predict stock net value direction
    4. **Prediction**: Make predictions with custom inputs
    
    For best results, train the model first before making predictions.
    """
    )

    st.header("About the Model")
    st.write(
        """
    The model uses Random Forest classification to predict whether a stock will have positive or 
    negative net value based on trading patterns. It analyzes relationships between various 
    trader categories (top/mid/bot) and their buying and selling behaviors.
    
    Key features include:
    - Buy/sell proportions
    - Trader category ratios
    - Volume concentration measurements
    
    The model is trained on historical data from April 11, 2025 from the HOSE exchange.
    """
    )

# Add footer
st.markdown("---")
st.caption("Stock Market Prediction Model | Data as of April 11, 2025")
