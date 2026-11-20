# 0001 - REsources for language pack Go

Date: 2026-14-11
State: in corso

## Context
The Golang language pack needs some offline resources for documentations and best practice.
These resources are cloned in 'sources/go/' (not versioned) and converted in 'corpus/' using 'ingest.py'.

The collected resources for now are:

- Effective Go
- Go Code Review Comments


## Effective Go

| Field | Value |
| ----- | ----- |
| **Fonte** | sources/go/website/_content/doc/effective_go.html |
| **Format** | HTML with some initial metadata (16 **h2** tags with id and 6 **{{code ...}}** directives that include **doc/progs/eff_*.go** files) |
| **Go version** | No version (static documentation) |
| **Text license** | CC BY 4.0 (CC-BY-4.0) |
| **Code license (eff_*.go)** | BSD-3-Clause |
| **Commit** | git -C ../../website rev-parse HEAD > 9d2e951dbfa18c495ec14086916e413e3554dea8 |

## Code Review Comments

| Field | Value |
|---|---|
| **Fonte** | Go Code Review Comments |
| **Percorso locale** | `sources/go/go.googlesource-wiki/CodeReviewComments.md` |
| **Origine** | `https://go.googlesource.com/wiki` (il repo `golang/go.wiki` su GitHub contiene solo un avviso di spostamento) |
| **URL pubblico** | `https://go.dev/wiki/CodeReviewComments` |
| **Commit** | `fe2268bb04c953cd65bcae752e978912f5cbddaa` |
| **Formato** | Markdown con front matter YAML (`title`) |
| **Struttura** | 31 sezioni `##`; ogni titolo genera un'ancora per l'URL |
| **Da pulire in `ingest.py`** | 1 link HTML (riga 186, goimports) da convertire in markdown; link relativi (es. `/wiki/TestComments`) da trasformare in URL assoluti `https://go.dev/...` |
| **Versione di Go** | non legata a una versione |
| **Licenza** | CC BY 4.0 (SPDX: `CC-BY-4.0`) |
| **Dove letta** | `sources/go/website/_content/copyright.md`, dichiarazione generale del sito. Nel repo della wiki non c'è un `LICENSE`, quindi la licenza è dedotta dal sito e non specifica per questa pagina. Il testo dice "Except as noted", eccezioni non verificate |
| **Note** | Il documento si presenta come un elenco di problemi comuni, non una style guide completa. Rimanda a Go Test Comments e alla Google Go Style Guide (da valutare in seguito) |

## Output di `go doc`

| Campo | Valore |
|---|---|
| **Fonte** | `go doc` (comando del toolchain Go) |
| **Come si ottiene** | `go doc -all <pacchetto>` stampa la documentazione completa del pacchetto; `go doc <pacchetto>.<simbolo>` un singolo simbolo |
| **Formato** | Testo semplice, quasi markdown: titoli `# ...` per le sezioni del pacchetto, blocchi di codice indentati, sezioni `VARIABLES` e `FUNCTIONS` con `-all`. Conversione minima |
| **Ripetibilità** | Verificata: `go doc -all errors > file` produce un file completo (158 righe) |
| **Versione di Go** | Legata al toolchain installato: go1.26.3 (esempio: `errors.AsType` compare solo nelle versioni recenti). Cartella del corpus: `corpus/go/1.26/` |
| **Licenza** | BSD-3-Clause, dal `LICENSE` in `$(go env GOROOT)` |
| **Note** | Pacchetti grandi come `fmt` producono testi molto lunghi: valutare in seguito lo spezzettamento per sezione `#` o per simbolo |

## Sorgenti della stdlib

| Campo | Valore |
|---|---|
| **Fonte** | `$(go env GOROOT)/src` |
| **Formato** | File `.go`; in ogni pacchetto anche `*_test.go` ed `example_test.go` (esempi di uso scritti dai maintainer) |
| **Versione di Go** | Legata al toolchain: go1.26.3 |
| **Licenza** | BSD-3-Clause (`LICENSE` in `$(go env GOROOT)`, letto parzialmente: stesso testo di apertura del repo del sito) |
| **Note** | Da decidere quali pacchetti includere: i sorgenti completi sono molti |

## golangci-lint e fonti per `lint/`

| Campo | Valore |
|---|---|
| **Versione golangci-lint** | 2.15.0 (compilato con go1.27.0; toolchain installato go1.26.3: possibili segnalazioni dipendenti dalla versione) |
| **Elenco linter** | `golangci-lint help linters --json`: nome, descrizione, `since`, `originalURL`. Non contiene spiegazioni per regola |
| **Linter attivi di default** | errcheck, govet, ineffassign, staticcheck, unused |
| **Chiave per risalire alla regola** | `govet`: nome dell'analizzatore prima dei due punti (es. `printf:`). `staticcheck`: codice a inizio messaggio (es. `SA1019`). `errcheck`: nessuno |
| **govet** | `go tool vet help [<nome>]`, versione go1.26.3, BSD-3-Clause (LICENSE di GOROOT). Alcuni analizzatori non registrati (es. `inline`) |
| **staticcheck** | `staticcheck -explain <CODICE>` (binario autonomo v0.8.2, installato con `go install`); licenza MIT (`LICENSE` del modulo). Spiegazione di lunghezza variabile |
| **errcheck** | Nessuna documentazione offline individuata. Pagina da scrivere a mano; licenza da leggere nel suo repo |

### Aperte
- Come enumerare i codici di staticcheck in modo affidabile (le cartelle non sono consecutive: manca `sa1009`).
- Documentazione e licenza di `errcheck`.
- Analizzatori di `govet` mancanti in `go tool vet`.
- Licenza di `golangci-lint`, non letta.

## govet

| Campo | Valore |
|---|---|
| **Fonte** | `go tool vet help` e `go tool vet help <analizzatore>` |
| **Linter in golangci-lint** | `govet`, attivo di default |
| **Chiave per risalire alla regola** | Nome dell'analizzatore a inizio messaggio, prima dei due punti (es. `printf: non-constant format string...` → `printf`) |
| **Formato** | Testo semplice: titolo `<nome>: <descrizione>`, spiegazione, esempio di codice indentato. Per alcuni analizzatori (es. `printf`) compare anche una sezione `Analyzer flags` con elenchi molto lunghi, da tagliare in fase di ingestione |
| **Ripetibilità** | Verificata: l'elenco si ottiene con `go tool vet help`, la spiegazione con `go tool vet help <nome>` |
| **Numero di analizzatori** | Circa 86 (stima dal conteggio delle righe indentate in `go tool vet help`, non verificata) |
| **Versione di Go** | Legata al toolchain installato: go1.26.3 |
| **Licenza** | BSD-3-Clause, dal `LICENSE` in `$(go env GOROOT)` |
| **Limiti** | Alcuni analizzatori usati dal `govet` di golangci-lint non sono registrati in `go tool vet` (es. `inline`: `vet: Analyzer "inline" not registered`). La discrepanza è probabilmente legata alla versione con cui golangci-lint è compilato (go1.27.0 contro go1.26.3 installato), ma non è verificata |
| **Aperte** | Verificare quanti analizzatori ci sono davvero; capire come ottenere la documentazione di quelli che `go tool vet` non conosce |

## Problemi noti per `ingest.py`

### Comuni a tutte le fonti
1. Generare il front matter di ogni file (`source`, `kind`, `language`, `version`, `url`, `license`) dai dati di `pack.toml`.
2. Costruire `url` con l'ancora della sezione: dall'`id` degli `<h2>` per Effective Go, dallo slug del titolo per Code Review Comments.
3. Trasformare i link relativi in URL assoluti (`/pkg/os/` → `https://go.dev/pkg/os/`, `/wiki/TestComments` → `https://go.dev/wiki/TestComments`).
4. Una sezione per file, con file piccoli (soglia da decidere).
5. Scrivere `MANIFEST.json` con commit, versione di Go, data di build e licenze.
6. La rigenerazione da zero deve essere ripetibile e produrre lo stesso risultato.

### `go doc`
1. Eliminare la riga `package <nome> // import "<nome>"`.
2. Togliere l'indentazione di 4 spazi dalle descrizioni dei simboli.
3. Gli esempi di codice sono indentati: vanno in blocchi con tre backtick e `go`.
4. I titoli sono in maiuscolo (`VARIABLES`, `FUNCTIONS`): convertirli in `## Variables`, `## Functions`.
5. Le firme (`func Is(err, target error) bool`) vanno in un blocco `go`, con un `###` per simbolo.
6. Il testo introduttivo del pacchetto non ha titoli: serve decidere come strutturarlo. Nel file di esempio ho scelto a mano titoli come "Prefer Is over equality checks": `ingest.py` non può inventarli, quindi o li omette o li chiede a un LLM.
7. Pacchetti molto lunghi (come `fmt`): decidere se spezzare per sezione `#` o per simbolo.
8. Per alcuni analizzatori di `govet` l'output contiene una sezione `Analyzer flags` con elenchi lunghissimi: da tagliare.

#### Stato dopo il passo 3 (go doc)

Implementate in `ingest.py` e verificate su `errors`, `fmt` e `os`: voci 1-5. La voce 7 resta aperta.

Scelte fatte durante l'implementazione:

1. **Titoli `#` nel testo di `go doc`.** Vengono abbassati nel parser (`demote_heading`: +2 nell'overview, +3 nelle descrizioni, solo a colonna 0), non in `render_markdown`. Così il renderer riceve già i livelli giusti. Se in futuro serve rendere lo stesso parse in un altro formato, la logica va spostata nel renderer.
2. **Firme multi-riga.** `type X interface {...}` e `const (...)` sono raccolte fino alla chiusura a colonna 0. Il caso di una `func` con firma a capo non è gestito né verificato.
3. **Gruppi `const (` / `var (`.** Il titolo `###` è costruito da `symbol_title`: primo identificatore del gruppo più il suffisso `(group)` (es. `O_RDONLY (group)`, 8 casi in `os.md`). Il titolo nomina solo il primo simbolo, gli altri compaiono solo nel blocco ```go. Alternativa scartata: elencare i primi nomi (`O_RDONLY, O_WRONLY, ... (+4)`). Da rivedere solo se in uso reale l'agente non trova costanti che esistono.Scelta: tenere così. Alternativa scartata: titolo con i primi nomi del gruppo (`O_RDONLY, O_WRONLY, ... (+4)`). Da rivedere solo se in uso reale l'agente non trova costanti che esistono.
4. **Metodi.** I titoli escono come `Tipo.Metodo` (verificato su `os`: `File.Close`, `Root.Open`, ecc.).
5. **Manifest.** `command` riporta il comando reale (`go doc -all <pkg>`). `go_version` è la stringa grezza. La data di build compare solo nel manifest, mai nei file del corpus.

Limiti accettati:

- Nell'overview il codice resta rientrato di 4 spazi, senza ` ```go ` (valido come blocco in markdown).
- I titoli scritti a mano nell'overview del file di esempio non vengono generati: il `diff` con l'esempio differisce per questo.
- Metodi e costruttori restano piatti sotto `Types`, non raggruppati sotto il loro tipo.
- Il corpo delle interfacce è rientrato di 8 spazi, come lo stampa `go doc`.
- Elenco dei pacchetti e metadati sono scritti nel codice, non letti da `pack.toml`.

Verifica su `os`:

- Lettura a mano: 2 simboli su 10 campionati (`CopyFS`, `Getuid`), coincidono con `go doc`. Il criterio "5-10 sezioni" non è raggiunto.
- Controllo automatico: ogni funzione esportata di `go doc -short os` ha un titolo `###` in `os.md`. Non copre tipi, costanti, variabili e metodi.


### Effective Go (HTML)
1. Rimuovere il blocco di metadati `<!--{ ... }-->` in cima al file.
2. Risolvere le 6 direttive `{{code "/doc/progs/eff_*.go" ...}}`: leggono un intervallo di righe da file esterni, indicato con espressioni regolari.
3. Le righe tipo `{{"{{if .}}"}}` non sono direttive: sono testo da riportare come `{{if .}}`.
4. Estrarre una sezione dall'`<h2>` all'`<h2>` successivo, escluso.
5. Spostare i livelli dei titoli: `<h2>` → `#`, `<h3>` → `##`.
6. Decodificare le entità HTML anche dentro i `<pre>` (`&lt;`, `&gt;`, `&amp;`, `&mdash;`).
7. I `<pre>` non dichiarano un linguaggio: assumere `go`, con eccezioni (es. l'output di un errore, `text`) da gestire con una lista scritta a mano.
8. I link interni (`#interface_conversions`) puntano ad altre sezioni: decidere se linkare l'URL pubblico o il file locale.
9. Il testo sorgente è spezzato a righe fisse: decidere se ricompattarlo.
10. Conversione consigliata con una libreria (`markdownify`, `html2text` o BeautifulSoup per tagliare per sezione), non con regex.

### Code Review Comments (markdown)
1. Gestire il front matter già presente nel file (`title`): non duplicarlo.
2. Convertire il link HTML alla riga 186 in markdown.
3. Dividere in 31 file, uno per sezione `##`.
4. Generare lo slug dei titoli per le ancore.

### Linter
1. Elenco dei linter da `golangci-lint help linters --json` (nome, descrizione, `since`, `originalURL`).
2. `govet`: ricavare l'elenco da `go tool vet help` e poi chiamare `go tool vet help <nome>` per ciascuno. Il numero di analizzatori (circa 86) è una stima, da verificare.
3. Alcuni analizzatori usati da `govet` dentro golangci-lint non sono registrati in `go tool vet` (es. `inline`): decidere come segnalarlo.
4. `staticcheck`: ricavare i codici dalle cartelle in `staticcheck/` (non consecutive, manca `sa1009`: verificare), poi `staticcheck -explain <CODICE>`.
5. L'output di `-explain` contiene "Available since" e "Online documentation": estrarli per il front matter.
6. La lunghezza della spiegazione varia (ricca per `SA1002`, scarna per `SA1019`): marcare le regole con testo breve.
7. `errcheck`: nessuna fonte offline, la pagina va scritta a mano.
8. Discrepanza di versioni (golangci-lint compilato con go1.27.0, toolchain go1.26.3): registrarla in `MANIFEST.json`.