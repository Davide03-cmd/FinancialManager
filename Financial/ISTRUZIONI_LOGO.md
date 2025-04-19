# Istruzioni per il Logo dell'Applicazione

Il logo dell'applicazione è un elemento importante dell'identità visiva di My $av€ DC. Ecco come includerlo correttamente nel deployment:

## Posizionamento del Logo

1. **Crea una cartella `assets`** nella root del tuo repository GitHub

2. **Salva il file `MySaveDCLogo.png`** all'interno della cartella `assets`

3. **Assicurati che il percorso sia corretto**: il logo deve essere accessibile tramite il percorso `assets/MySaveDCLogo.png`

## Verificare che il Logo sia Correttamente Visualizzato

Dopo il deployment su Streamlit Community Cloud, controlla che il logo appaia correttamente nell'interfaccia dell'applicazione. Se il logo non viene visualizzato:

1. Verifica che il file sia stato caricato su GitHub nella posizione corretta
2. Controlla che il nome del file corrisponda esattamente a quello usato nel codice (maiuscole/minuscole sono importanti)
3. Riavvia l'applicazione su Streamlit Cloud se necessario

## Note sulla Personalizzazione del Logo

Se desideri modificare il logo in futuro:

1. Mantieni lo stesso nome file (`MySaveDCLogo.png`) per evitare di dover aggiornare il codice
2. Usa preferibilmente un'immagine con sfondo trasparente (formato PNG)
3. Mantieni dimensioni simili per preservare il layout dell'interfaccia