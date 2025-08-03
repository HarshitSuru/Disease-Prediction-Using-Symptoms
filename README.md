# 🩺 MediCURE: Disease Prediction Based on Symptoms

MediCURE is a Machine Learning-powered web application that helps users identify possible diseases based on symptoms they experience. It also suggests **home remedies** as supportive treatment. The system is designed for early guidance and **not** as a substitute for professional medical advice.

---

## 🔍 About the Project

Healthcare begins with awareness. MediCURE is built to empower users with a quick, informative, and AI-driven way to assess potential illnesses from symptoms. It provides:

- Disease predictions using multiple machine learning models.
- Probability-based diagnosis.
- Treatment suggestions via home remedies.
- A user-friendly, responsive interface.

---

## 🎯 Objectives

- ✅ Predict possible diseases using symptom input and ML models.
- ✅ Build a Flask-based interactive web application.
- ✅ Provide treatment suggestions from a curated remedy dataset.
- ✅ Evaluate and compare different ML algorithms:
  - Logistic Regression
  - SVM
  - Multilayer Perceptron
  - Naive Bayes
  - Decision Tree
  - XGBoost

> ⚠️ **Note:** This tool is not a replacement for medical consultation. Always consult a licensed doctor for accurate diagnosis and treatment.

---

## 📁 Dataset Details

- ✅ Source: [Kaggle](https://www.kaggle.com/)
- 📊 **Size:** 8836 rows × 489 columns
- 🧬 **Content:** 261 diseases mapped to multiple symptoms
- ➕ Augmented data by symptom combinations
- 🧾 Home remedy data stored in `cure_minor.xlsx`

---

## 🛠️ Tech Stack

| Category       | Tech Used                     |
|----------------|-------------------------------|
| Backend        | Python, Flask, Flask-Mail     |
| ML Libraries   | scikit-learn, pandas, numpy   |
| Frontend       | HTML, CSS, JS, Bootstrap      |
| Database       | SQLite (via SQLAlchemy)       |
| Others         | openpyxl, Wikipedia API       |



## ⚙️ Installation & Setup

### 🔁 Step 1: Clone the Repository
```bash
git clone https://github.com/HarshitSuru/Disease-Prediction-Using-Symptoms.git
cd MediCURE-Disease-Prediction-based-on-Symptoms
```

### 🧪 Step 2: Create a Virtual Environment
```bash
python -m venv venv
# Activate it:
source venv/bin/activate         # For Linux/macOS
venv\Scripts\activate            # For Windows
```
### 📦 Step 3: Install Required Packages
```bash
pip install -r requirements.txt
```


### 🔐 Step 4: Setup Environment Variables
Create a .env file in the root directory:
```bash
# Flask Configuration
SECRET_KEY=your_flask_secret_key

# Database URI
SQLALCHEMY_DATABASE_URI=sqlite:///users.db

# Mail Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

### ▶️ Step 5: Run the Flask App
```bash
python app.py
```
Then visit http://127.0.0.1:5000/ in your browser.