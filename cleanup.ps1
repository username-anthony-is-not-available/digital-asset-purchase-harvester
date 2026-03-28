# Cleanup script for Digital Asset Purchase Harvester
# This script helps remove the virtual environment and clean up

Write-Host "🧹 Digital Asset Purchase Harvester - Cleanup Script" -ForegroundColor Yellow
Write-Host "=" * 60

$choice = Read-Host "What would you like to do?
[1] Deactivate virtual environment only
[2] Remove virtual environment completely
[3] Clean pip cache
[4] Full cleanup (remove venv + clean cache)
[q] Quit

Enter your choice"

switch ($choice.ToLower()) {
    "1" {
        Write-Host "Deactivating virtual environment..." -ForegroundColor Cyan
        if ($env:VIRTUAL_ENV) {
            deactivate
            Write-Host "✅ Virtual environment deactivated" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️ No virtual environment is currently active" -ForegroundColor Yellow
        }
    }
    "2" {
        Write-Host "Removing virtual environment..." -ForegroundColor Cyan
        if (Test-Path "venv") {
            Remove-Item -Recurse -Force "venv"
            Write-Host "✅ Virtual environment removed" -ForegroundColor Green
            Write-Host "💡 Run setup.ps1 to recreate it" -ForegroundColor Blue
        }
        else {
            Write-Host "⚠️ No 'venv' directory found" -ForegroundColor Yellow
        }
    }
    "3" {
        Write-Host "Cleaning pip cache..." -ForegroundColor Cyan
        pip cache purge
        Write-Host "✅ Pip cache cleaned" -ForegroundColor Green
    }
    "4" {
        Write-Host "Performing full cleanup..." -ForegroundColor Cyan

        # Remove venv
        if (Test-Path "venv") {
            Remove-Item -Recurse -Force "venv"
            Write-Host "✅ Virtual environment removed" -ForegroundColor Green
        }

        # Clean pip cache
        pip cache purge 2>$null
        Write-Host "✅ Pip cache cleaned" -ForegroundColor Green

        # Remove temporary artifacts
        Write-Host "Removing temporary artifacts..." -ForegroundColor Cyan
        Remove-Item -Path "*.mbox", ".llm_cache.json", ".processed_hashes.json", ".sync_state.json", "tasks_db.json" -ErrorAction SilentlyContinue
        Remove-Item -Path "output" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Temporary artifacts removed" -ForegroundColor Green

        Write-Host "✅ Full cleanup complete!" -ForegroundColor Green
        Write-Host "💡 Run setup.ps1 to start fresh" -ForegroundColor Blue
    }
    "q" {
        Write-Host "Goodbye! 👋" -ForegroundColor Green
        exit
    }
    default {
        Write-Host "❌ Invalid choice. Please run the script again." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Done! 🎉" -ForegroundColor Green
