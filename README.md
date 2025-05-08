# 🚨 Emergency Voice Chatbot

This project is a Python-based voice-activated chatbot that can assist users in emergency situations. It listens to voice commands and provides appropriate responses or triggers emergency procedures.

## 📁 Project Structure

```
Emergency-Voice-Chatbot/
│
├── __pycache__/           # Cached Python bytecode
├── app.py                 # Main application script
├── utils.py               # Utility functions
├── emergency.jpg          # Image used in the project
├── requirements.txt       # Python dependencies
└── .gitignore             # Files to ignore in Git
```

---

## ⚙️ Installation & Setup

Follow these steps to run the project locally:

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Shaik-Hamzah123/Emergency-Voice-Chatbot.git
cd Emergency-Voice-Chatbot
```

### 2️⃣ Create a Conda Environment

```bash
conda create -p venv python=3.12 -y
```

> `-p venv` creates the environment in a local `./venv` directory

### 3️⃣ Activate the Environment

On **Linux/macOS**:
```bash
conda activate ./venv
```

On **Windows**:
```bash
conda activate .\venv
```

### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the App

Once the environment is ready and dependencies are installed, run the application using:

```bash
python app.py
```

Make sure your microphone is working as the app listens to voice input.

---

## 📦 Requirements

The project dependencies are listed in `requirements.txt`. If you’re curious, they likely include:

- `speechrecognition`
- `pyttsx3`
- `pyaudio`
- `opencv-python` (if webcam is used)
- other supporting libraries

---

## 🖼️ Assets

The file `emergency.jpg` is used within the app, possibly for UI or visual alerts.

---

## ❗ Troubleshooting

- If you face `pyaudio` install issues on Windows, use:
  ```bash
  pip install pipwin
  pipwin install pyaudio
  ```

- Ensure microphone permissions are granted if using on macOS/Linux.

---

## 📄 License

This project is open-source and available under the MIT License.

---

## 👤 Author

Developed by **Shaik Hamzah**  
GitHub: [Shaik-Hamzah123](https://github.com/Shaik-Hamzah123)
