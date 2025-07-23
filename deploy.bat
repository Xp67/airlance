@echo off
echo Avvio del deploy su Google App Engine...
gcloud app deploy app.yaml --quiet

IF %ERRORLEVEL% NEQ 0 (
    echo Errore durante il deploy.
    pause
) ELSE (
    echo Deploy completato con successo.
    pause
)

