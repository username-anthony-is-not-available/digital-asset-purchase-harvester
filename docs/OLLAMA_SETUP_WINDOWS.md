# Ollama Setup Guide for Windows

This guide provides step-by-step instructions for setting up Ollama on Windows to work with the Digital Asset Purchase Harvester. It covers both the native Windows installation and the WSL2-based installation.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Option 1: Native Windows Installation (Recommended)](#option-1-native-windows-installation-recommended)
3. [Option 2: WSL2 Installation](#option-2-wsl2-installation)
4. [GPU Acceleration](#gpu-acceleration)
5. [Environment Configuration](#environment-configuration)
6. [Verifying the Setup](#verifying-the-setup)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites
- Windows 10 (version 1903 or higher) or Windows 11.
- At least 8GB of RAM (16GB recommended).
- An NVIDIA or AMD GPU (optional but highly recommended for performance).

---

## Option 1: Native Windows Installation (Recommended)

Ollama now offers a native Windows application which is the easiest way to get started.

1. **Download the Installer**: Visit [ollama.com/download/windows](https://ollama.com/download/windows) and download the `OllamaSetup.exe`.
2. **Run the Installer**: Follow the on-screen instructions.
3. **Verify Installation**: Open PowerShell or Command Prompt and run:
   ```powershell
   ollama --version
   ```

---

## Option 2: WSL2 Installation

If you prefer a Linux-like environment or have specific compatibility needs, you can run Ollama within Windows Subsystem for Linux (WSL2).

1. **Install WSL2**:
   Open PowerShell as Administrator and run:
   ```powershell
   wsl --install
   ```
   Restart your computer if prompted.
2. **Install a Linux Distribution**:
   By default, Ubuntu is installed. You can set it up by following the on-screen instructions after the restart.
3. **Install Ollama in WSL2**:
   Open your WSL terminal (e.g., Ubuntu) and run:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
4. **Start the Ollama Service**:
   ```bash
   ollama serve
   ```

---

## GPU Acceleration

Using a GPU significantly speeds up the email parsing process.

### NVIDIA GPUs
Ollama supports NVIDIA GPUs via CUDA.
- **Native Windows**: The native installer should automatically detect and use your NVIDIA GPU if the latest drivers are installed.
- **WSL2**: Ensure you have the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed within WSL2 to pass through GPU access.

### AMD GPUs
Ollama has preview support for AMD GPUs on Windows. Ensure you have the latest Adrenalin drivers installed.

---

## Environment Configuration

To ensure the Harvester can communicate with Ollama, you may need to configure environment variables.

### Setting `OLLAMA_HOST`
If Ollama is running on a different machine or under WSL2 (and the harvester is on native Windows), you might need to set the `OLLAMA_HOST` environment variable.

**PowerShell:**
```powershell
$env:OLLAMA_HOST = "http://localhost:11434"
```

**Command Prompt:**
```cmd
set OLLAMA_HOST=http://localhost:11434
```

### Pulling the Required Model
The Harvester defaults to `llama3.2:3b`. You must pull this model before running the tool:

```bash
ollama pull llama3.2:3b
```

---

## Verifying the Setup

1. **Check if Ollama is responsive**:
   ```powershell
   curl http://localhost:11434/api/tags
   ```
2. **Run a test generation**:
   ```bash
   ollama run llama3.2:3b "Hello, can you help me parse some emails?"
   ```
3. **Test with the Harvester**:
   Follow the instructions in the [README.md](../README.md#quick-start) to process a sample file.

---

## Troubleshooting

- **Port Conflict**: If you get an error that port `11434` is already in use, check if another instance of Ollama is running.
- **WSL2 Connectivity**: If the Harvester (running on Windows) cannot reach Ollama (running in WSL2), you might need to use the WSL2 IP address instead of `localhost` or configure Ollama to listen on `0.0.0.0`.
  - Set `OLLAMA_HOST=0.0.0.0` inside WSL2 and restart the service.
- **Slow Performance**: Ensure GPU acceleration is active. Check `ollama ps` to see if the model is running on the GPU.
