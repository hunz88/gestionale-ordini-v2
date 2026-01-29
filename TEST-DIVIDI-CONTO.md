# 🧪 Test Completo - Dividi Conto

## ⚠️ IMPORTANTE
Questo test DEVE essere fatto con un ordine NUOVO, non con ordini vecchi che hanno già pagamenti registrati!

---

## 📋 Test Plan - Step by Step

### FASE 1: Preparazione (5 minuti)

1. **Apri il terminale e monitora i log in tempo reale:**
```bash
cd /home/user/gestionale-ordini-v2
tail -f logs/test.log
```
Lascia questa finestra aperta per vedere cosa succede.

2. **Apri il browser in modalità incognito:**
   - Vai su: `http://192.168.1.XXX:44321`
   - Login: user / sunset2024

---

### FASE 2: Crea un Ordine Nuovo Pulito (Tavolo 99)

3. **Crea nuovo ordine SEMPLICISSIMO:**
   - Tavolo: **99** (usa un tavolo che non hai mai usato)
   - Aggiungi:
     - 3× Caffè (€1.50 cad) = €4.50 totale
   - Invia l'ordine

4. **Aspetta che l'ordine appaia in "Ordini Attivi"**

---

### FASE 3: Test Dividi Conto - PRIMA Parte

5. **Apri "Dividi Conto" sul Tavolo 99**

6. **Controlla i LOG** (nella finestra del terminale):
   - Dovresti vedere:
   ```
   📋 Dettagli ordine X: Totale rimanente €4.50, Già pagato €0.00
   ```
   - ✅ Se vedi questo: OK!
   - ❌ Se NON lo vedi: PROBLEMA!

7. **Controlla la MODALE** (nel browser):
   - Colonna SINISTRA dovrebbe mostrare:
     ```
     Caffè ×3 - €4.50
     ```
   - Colonna DESTRA dovrebbe essere VUOTA
   - Totale in basso: €4.50

8. **Fai un pagamento PARZIALE:**
   - Clicca su "Caffè" nella colonna sinistra
   - 1× Caffè dovrebbe spostarsi a destra
   - Totale a destra: €1.50
   - Clicca "Conferma Pagamento Parziale"
   - Seleziona metodo: "Contanti"
   - Conferma

---

### FASE 4: Test Dividi Conto - SECONDA Parte

9. **Riapri "Dividi Conto" sul Tavolo 99**

10. **Controlla i LOG** (nella finestra del terminale):
    - Dovresti vedere:
    ```
    📋 Dettagli ordine X: Totale rimanente €3.00, Già pagato €1.50
    ```
    - ✅ Se vedi questo: OTTIMO!
    - ❌ Se vedi ancora €4.50: PROBLEMA!

11. **Controlla la MODALE** (nel browser):
    - Colonna SINISTRA dovrebbe mostrare:
      ```
      Caffè ×2 - €3.00   ← IMPORTANTE: Solo 2, non 3!
      ```
    - Se vedi ancora "×3": IL BUG È ANCORA PRESENTE!
    - Se vedi "×2": IL FIX FUNZIONA!

---

### FASE 5: Test Aggiungi Articoli Dopo Pagamento Parziale

12. **Chiudi la modale Dividi Conto**

13. **Aggiungi nuovi articoli al Tavolo 99:**
    - Clicca "Aggiungi Articoli"
    - Aggiungi: 1× Brioche (€1.50)
    - Conferma

14. **Riapri "Dividi Conto" sul Tavolo 99**

15. **Controlla i LOG** (nella finestra del terminale):
    - Dovresti vedere:
    ```
    📋 Dettagli ordine X: Totale rimanente €4.50, Già pagato €1.50
    ```
    - ✅ Se vedi €4.50 rimanente: OK!

16. **Controlla la MODALE** (nel browser):
    - Colonna SINISTRA dovrebbe mostrare:
      ```
      Caffè ×2 - €3.00
      Brioche ×1 - €1.50
      ```
    - Totale: €4.50
    - ✅ Se vedi questo: PERFETTO!
    - ❌ Se vedi anche il Caffè già pagato: PROBLEMA!

---

## 📊 Risultati Attesi

### ✅ Test SUPERATO se:
1. I log mostrano i totali corretti (rimanente e già pagato)
2. Dopo il primo pagamento parziale, la modale mostra solo 2× Caffè (non 3)
3. Dopo aver aggiunto Brioche, la modale mostra 2× Caffè + 1× Brioche
4. I totali sono sempre coerenti

### ❌ Test FALLITO se:
1. I log NON mostrano la riga "📋 Dettagli ordine..."
2. Dopo il pagamento parziale, la modale mostra ancora 3× Caffè
3. Dopo aver aggiunto Brioche, la modale mostra anche il Caffè già pagato
4. I totali non tornano

---

## 🔍 Debug

Se il test FALLISCE, raccogli queste informazioni:

1. **Screenshot della modale Dividi Conto**
2. **Copia i log dal terminale** (ultime 50 righe)
3. **Query database:**
```bash
sqlite3 backend/ordini.db "SELECT * FROM pagamenti_parziali WHERE comanda_id = (SELECT id FROM comanda WHERE tavolo = 99 AND stato = 'attivo');"
```

---

## 📝 Note

- Usa SEMPRE il Tavolo 99 per questi test
- NON usare ordini vecchi con pagamenti già registrati
- Tieni sempre aperto il terminale con i log
- Se il test fallisce, NON fare altri pagamenti, chiama subito per debug

---

Ultimo aggiornamento: 29 Gennaio 2026
