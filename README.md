# Fiera di Roma – eventi & traffico (aggiornamento automatico)

1. Crea un repository GitHub (pubblico) e carica tutti questi file, mantenendo la cartella `.github/workflows`.
2. **Settings → Pages** → Source: *Deploy from a branch* → `main` / root.
3. **Actions → Aggiorna eventi → Run workflow** (poi gira da solo ogni 6 ore).
4. Apri `https://TUOUTENTE.github.io/NOMEREPO/` e, da Chrome Android, "Aggiungi a schermata Home".

Eventi che vuoi inserire a mano: modifica `manual.json` (stesso formato di `data.json`, campi n, s, e, k, i, h).
Se l'azione fallisce o non trova nulla, apri il log in Actions: i siti possono cambiare struttura.
