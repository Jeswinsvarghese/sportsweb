# 🏆 SportsWeb

A Flask-based sports website that provides live sports information, match data, and the latest sports news from around the world.

## 📌 Features

- 🏏 Live and ongoing match information
- 📊 Sports and team data
- 🌍 Sports news from around the world
- 📰 Latest news updates
- 🔎 Search and browse sports information
- 🏆 Cricket league and team information
- 👩 Women's sports information
- 🌐 International and domestic sports data
- 💾 MongoDB integration for storing application data

## 🛠️ Technologies Used

- **Python**
- **Flask**
- **MongoDB**
- **PyMongo**
- **HTML**
- **CSS**
- **JavaScript**
- **REST APIs**
- **JSON**

## 📂 Project Structure

```text
SportsWeb/
│
├── app.py
├── domestic.json
├── international.json
├── league.json
├── women.json
├── ipl_data_analysis.py
│
├── templates/
│   └── HTML files
│
├── static/
│   ├── CSS
│   ├── JavaScript
│   └── Images
│
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
⚙️ Installation
1. Clone the repository
git clone https://github.com/YOUR-USERNAME/sportsweb.git
cd sportsweb
2. Install the required packages
pip install flask requests pymongo
3. Configure MongoDB

Create your own MongoDB database and add the connection string through an environment variable.

Create a .env file:

MONGO_URI=your_mongodb_connection_string

Do not upload the .env file to GitHub.

4. Run the application
python app.py

Open the website in your browser:

http://127.0.0.1:5000
