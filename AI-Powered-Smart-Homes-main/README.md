# 🏠 AI-Powered Smart Homes

A Machine Learning-based system that analyzes smart home energy consumption and provides insights through data analysis and an interactive dashboard.

---

## 🏆 Project Overview

- 🎯 Problem: Inefficient energy usage in homes leads to higher electricity bills and wastage.
- 💡 Solution: A data-driven system that predicts energy consumption and provides insights.
- ⚙️ Approach: Machine Learning + Data Analysis + Interactive Dashboard

---

## ⚡ Key Features

- ✅ Energy Consumption Prediction  
- ✅ Data Analysis of Smart Home Patterns  
- ✅ Threshold-based Usage Monitoring  
- ✅ Interactive Dashboard (Gradio UI)  
- ✅ Real-world Dataset Integration  

---

## 🛠 Tech Stack

### Machine Learning
- LightGBM

### Programming
- Python

### Libraries
- Pandas  
- NumPy  

### Visualization / UI
- Gradio  
- Jupyter Notebook  

---

## 📁 Project Structure
```
AI-Powered-Smart-Homes/
│
├── AI_Powered_Smart_Homes_v2.ipynb # Main notebook (model building & analysis)
├── gradio_dashboard_cell.py # Dashboard UI using Gradio
├── smart_home_india_corrected.csv # Dataset
├── requirements.txt # Dependencies
│
├── model/
│ ├── lgbm_model.pkl # Trained ML model
│ ├── feature_cols.pkl # Feature columns
│ ├── appliance_avg.pkl # Average usage data
│ └── consumption_thresholds.pkl # Threshold values
│
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```
https://github.com/Navya032006/AI-Powered-Smart-Homes.git
cd AI-Powered-Smart-Homes
```

### 2. Install Dependencies
```
pip install -r requirements.txt
```

---

## ▶️ How to Run

#### Run Jupyter Notebook
#### Run Dashboard

---

## 📊 Dataset

- File: `smart_home_india_corrected.csv`  
- Contains smart home energy consumption data  
- Includes appliance usage patterns and metrics  

---

## 🤖 How It Works

1. Dataset is loaded and preprocessed.  
2. Features are prepared for training.  
3. LightGBM model predicts energy consumption.  
4. Threshold values are used to flag unusual usage.  
5. Results are displayed in a Gradio dashboard.  

---

## 🎯 Use Cases

- Smart home energy analysis  
- Reducing electricity bills  
- Identifying unusual energy usage  
- Supporting sustainable energy practices  

---

## 🌟 Innovation & Impact

- Data-driven energy insights  
- Simple threshold-based monitoring  
- Scalable for smart home datasets  
- Promotes efficient energy usage  

---

## 🚀 Future Enhancements

- Real-time IoT integration  
- Advanced ML/DL models  
- Mobile application  
- Smart recommendation system  

---

## 👩‍💻 Author

Navya Sai  
B.Tech – Computer Science Engineering  

---

## 📄 License

This project is open-source and free to use for educational purposes.
