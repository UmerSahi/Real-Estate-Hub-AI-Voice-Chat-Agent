@echo off
title Push RealEstate Hub to GitHub
echo ======================================================================
echo Pushing RealEstate Hub to GitHub (UmerSahi)...
echo A GitHub sign-in browser window will appear. Please click "Authorize".
echo ======================================================================

git remote set-url origin https://github.com/UmerSahi/Real-Estate-Hub-AI-Voice-Chat-Agent.git
git branch -M main
git push -u origin main --force

echo ======================================================================
echo If push succeeded, go to https://vercel.com/new to deploy!
echo ======================================================================
pause
