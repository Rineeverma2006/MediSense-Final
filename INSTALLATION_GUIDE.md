# Windows installation

Requirements: Windows 10/11, Python 3.10–3.12, Node.js 20+, and npm.

1. Extract `MediSense_Final` to a normal writable folder (not inside the ZIP).
2. Run `setup.bat`. It creates `backend/.venv`, installs Python and npm dependencies, seeds synthetic demo accounts, and creates `backend/.env` from the example.
3. Run `start-all.bat` or start the backend and frontend in separate terminals with the supplied scripts.
4. Open `http://localhost:5173`. API docs are at `http://localhost:8000/docs`.

Demo patient: `patient@medisense.demo` / `MediSense@123`.

Use `test-backend.bat` and `build-frontend.bat` for checks. For OCR of scans, install Tesseract on the backend machine and the Python `pytesseract` and Pillow packages; the default requirements do not silently install the system OCR binary.

The assistant runs in labeled demo mode unless a supported provider and backend API key are configured. Email verification, SMS OTP, password reset delivery, cloud health integrations, and live wearable APIs require external services and are not enabled by these local setup steps.
