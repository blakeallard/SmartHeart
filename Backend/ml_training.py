import pandas as pd
import joblib
from   sklearn.model_selection import train_test_split
from   sklearn.linear_model import LogisticRegression  # use this for classification
from   sklearn.metrics import accuracy_score, confusion_matrix
import matplotlib.pyplot as plt


# Load your CSV
df = pd.read_csv('bpm_log.csv')

# Debugging: show structure
print("\n[INFO] Column data types:")
print(df.dtypes)

print("\n[INFO] First 5 rows:")
print(df.head())

print("\n[INFO] is_healthy value counts:")
print(df['is_healthy'].value_counts())


# Example: Suppose 'bpm' is your feature and you want to predict 'some_label' (you need a target!)
X = df[['BPM', 'SpO2']].astype(int)
y = df['is_healthy'].astype(int)

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Choose model
model = LogisticRegression()

# Train
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

print("\n[INFO] Predictions:")
print(y_pred)

print("\n[INFO] Accuracy Score:")
print(accuracy_score(y_test, y_pred))

print("\n[INFO] Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))


# Save the model to a file
joblib.dump(model, "model.pkl")
print("[INFO] Model saved to model.pkl")