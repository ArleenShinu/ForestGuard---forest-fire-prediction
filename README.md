Forest Fire Prediction Web App
This project is a web application built with Flask that predicts the occurrence and severity of forest fires based on meteorological data. It also features a user login system and a dashboard that displays relevant news articles.

✨ Key Features
User Authentication: Secure login and registration system (username, email, password).

Fire Prediction: Uses a machine learning model to predict whether a fire will occur based on user input.

Severity Analysis: If a fire is predicted, a second model estimates its severity (Low, Moderate, High, Extreme).

Dashboard: After logging in, users can access a dashboard to input data and view live forest fire news from a News API.

Machine Learning Backend:

Classification: Uses an XGBoost Classifier (fire_classification.pkl) to predict if a fire will happen (Yes/No).

Regression: Uses a Random Forest Regressor (fire_severity.pkl) to predict how severe the fire will be.
