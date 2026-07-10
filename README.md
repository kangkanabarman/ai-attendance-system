# 🎓 AI Attendance System

An AI-powered Smart Attendance System that automates student attendance using **Face Recognition** and **Voice Recognition**. The application provides separate interfaces for teachers and students and securely stores data using **Supabase**.


---

# ✨ Features

## 👨‍🏫 Teacher Module
- Teacher Registration
- Secure Login with Password Authentication
- Password Hashing using bcrypt
- Supabase Database Integration

## 👨‍🎓 Student Module
- Face Recognition Login
- Automatic Student Registration
- Optional Voice Enrollment
- Attendance Prediction using AI

## 🤖 AI Features
- Face Detection using dlib
- 128-D Face Embeddings
- SVM Classifier for Face Recognition
- Voice Embedding Support
- Automatic Model Retraining

---

# 🛠️ Tech Stack

- Python
- Streamlit
- OpenCV
- dlib
- scikit-learn
- NumPy
- Pillow
- bcrypt
- Supabase

---

# 📂 Project Structure

```
ai-attendance-system/
│
├── src/
│   ├── components/
│   ├── database/
│   ├── pipelines/
│   ├── screens/
│   └── ui/
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 🚀 Installation

### Clone the repository
```bash
git clone https://github.com/kangkanabarman/ai-attendance-system.git
```

### Move into the project
```bash
cd ai-attendance-system
```

### Create a virtual environment
```bash
python -m venv venv
```

### Activate the virtual environment

#### Windows
```bash
venv\Scripts\activate
```

#### macOS/Linux
```bash
source venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the application
```bash
streamlit run app.py
```
---
# 🔒 Database

This project uses **Supabase** as the backend database.

Create a `.streamlit/secrets.toml` file and add your own credentials:

```toml
SUPABASE_URL="YOUR_SUPABASE_URL"
SUPABASE_KEY="YOUR_SUPABASE_ANON_KEY"
```
> **Note:** API keys are excluded from this repository using `.gitignore`.
---
# 📸 Workflow
1. Teacher registers and logs in.
2. Student opens the Student Portal.
3. Camera captures the student's face.
4. AI extracts face embeddings.
5. Face is matched with registered students.
6. Attendance is automatically recorded.
7. New students can register with face and optional voice enrollment.

---
# 📌 Upcoming Features

- 📊 Attendance Dashboard
- 📅 Attendance History
- 📈 Analytics & Reports
- 🏫 Multiple Classroom Support
- 🔐 Enhanced Voice Authentication
- 📥 Export Attendance to Excel/PDF

