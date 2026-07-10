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

1. Teacher registers and securely logs into the system.
2. Student selects the Student Portal.
3. Student captures a live photo using the webcam.
4. AI detects the face and generates a 128-dimensional face embedding.
5. The embedding is matched against registered student embeddings using an SVM classifier.
6. If a match is found, the student is authenticated and attendance is marked automatically.
7. If no match is found, the student registers by providing their name, face image, and optionally a voice sample.
8. The new student's embeddings are stored in Supabase, and the recognition model is retrained for future logins.

