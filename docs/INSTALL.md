# AYU-trade-AI Installation & Usage Guide

AYU-trade-AI is a high-performance trading engine. Follow the instructions below for your specific Operating System.

## 🛠 Prerequisites
- **Python 3.11+**
- **TA-Lib C Library**: Required for technical indicators.

---

## 🐧 Linux (Ubuntu/Debian)
1. **Install TA-Lib C Library**:
   ```bash
   wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
   tar -xzf ta-lib-0.4.0-src.tar.gz
   cd ta-lib/
   ./configure --prefix=/usr
   make
   sudo make install
   ```
2. **Setup Project**:
   ```bash
   git clone https://github.com/teamhecked-Ayu/AYU-trade-AI.git
   cd AYU-trade-AI
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

## 🍎 macOS (Intel/Apple Silicon)
1. **Install TA-Lib via Homebrew**:
   ```bash
   brew install ta-lib
   ```
2. **Setup Project**:
   ```bash
   git clone https://github.com/teamhecked-Ayu/AYU-trade-AI.git
   cd AYU-trade-AI
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

## 🪟 Windows
1. **Install TA-Lib**:
   - Download the pre-compiled `ta-lib` wheel for your Python version from [here](https://github.com/cgohlke/talib-build/releases).
   - Install it using: `pip install TA_Lib-0.4.24-cp311-cp311-win_amd64.whl`
2. **Setup Project**:
   ```powershell
   git clone https://github.com/teamhecked-Ayu/AYU-trade-AI.git
   cd AYU-trade-AI
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

## 🚀 How to Use

### 1. Configuration
Copy the example environment file and add your keys:
```bash
cp .env.example .env
```

### 2. Running the Oracle
- **Interactive Mode (Stylish Dashboard)**:
  ```bash
  python cli.py --mode interactive
  ```
- **Daemon Mode (Background)**:
  ```bash
  python cli.py --mode daemon
  ```

### 3. Customizing Strategies
- Add new indicators in `indicators/custom.py`.
- Refine AI sentiment logic in `models/sentiment_fusion.py`.
- Adjust risk parameters in `config/config.yaml`.
