# Computer science-lingo för hissövervakningsprojektet

Det här dokumentet är en praktisk ordlista och crash course med vårt hissprojekt som exempel. Målet är att kunna beskriva systemet begripligt för exempelvis en frontend-, backend- eller DevOps-utvecklare.

## Projektet på två minuter

Vi har byggt en webbaserad dashboard för att jämföra mätningar från hissar. Rådata från telefonens sensorer analyseras lokalt med Python. Analysen identifierar hissresan och beräknar bland annat acceleration, jerk, hastighet, vibrationer, spektrum och cykler per meter. Resultatet exporteras till JSON-filer.

Webbgränssnittet är skrivet i React och TypeScript. Det läser JSON-filerna och visar interaktiva grafer, hissval, tooltips och slutsatser. Webbplatsen byggs till statiska filer som publiceras på Loopia under elevator.signalprofessor.com.

Källkoden ligger i GitHub-repot signalprofessor/elevator. När kod skickas till GitHub startar GitHub Actions automatiskt ett arbetsflöde som installerar beroenden, bygger och validerar webbplatsen och därefter laddar upp den till Loopia med FTPS. Det är vår CI/CD-pipeline.

Viktigt: själva omvandlingen från rå CSV- eller loggdata till analyserad JSON sker i nuläget lokalt på Fredriks dator. GitHub bygger webbplatsen men gör inte sensoranalysen.

## Systemet i en bild

    Telefonens sensorer
            |
            v
    rå mätfil, till exempel CSV
            |
            v
    lokal Python-analys
            |
            v
    bearbetade JSON-filer
            |
            v
    React-frontend
            |
            v
    statisk webbplats
            |
            v
    GitHub Actions bygger och distribuerar
            |
            v
    Loopia webbhotell
            |
            v
    elevator.signalprofessor.com

Detta är en data pipeline: data passerar genom flera steg där den samlas in, bearbetas, paketeras och presenteras.

## Frontend, backend och statisk webbplats

### Frontend

Frontend är den del användaren ser och interagerar med i webbläsaren. I vårt fall omfattar den:

- graferna
- hissarnas kryssrutor
- tooltips
- datum- och mätserieval
- texter, status och slutsatser

Frontendkoden ligger huvudsakligen i app/page.tsx och är byggd med React och TypeScript. Recharts används för graferna.

### Backend

En backend är programvara som körs på en server och arbetar bakom användargränssnittet. Den kan exempelvis:

- ta emot uppladdade mätfiler
- kontrollera användarens identitet och behörighet
- lagra filer och metadata
- starta analysjobb
- spara resultat i en databas
- skicka notifikationer vid avvikelser
- leverera data till frontend genom ett API

Vår nuvarande webbplats har ingen egentlig driftbackend. Analysen görs lokalt och de färdiga JSON-filerna följer med den statiska webbplatsen.

### Statisk webbplats

En statisk webbplats består efter byggsteget av färdiga HTML-, CSS-, JavaScript- och datafiler. Servern behöver inte köra Python eller skapa varje sida på begäran.

Fördelar:

- enkel och billig drift
- liten attackyta
- snabb laddning
- få komponenter som kan gå sönder

Begränsningar:

- webbläsaren kan inte själv köra vår befintliga Python-pipeline
- uppladdning, användarkonton och central lagring kräver normalt en backend
- ny data måste analyseras och publiceras på något sätt

## Dataflödet

### Rådata

Rådata är informationen så nära sensorn som möjligt, innan vår analys förändrat eller sammanfattat den. Exempel är tidsstämplade värden från accelerometer, gyroskop och barometer.

Rådata bör bevaras. Då går det att göra om analysen senare när algoritmer, filter eller antaganden förbättras.

### Bearbetade data

Bearbetade data är resultatet efter exempelvis:

- filtrering
- identifiering av start och stopp
- integration från acceleration till hastighet
- frekvensanalys
- omräkning från hertz till cykler per meter
- skattning av vibrationsenergi
- beräkning av nyckeltal

### Metadata

Metadata betyder data om mätningen, inte själva sensorsignalen. Relevanta fält är exempelvis:

- BRF eller anläggning
- hissens namn
- telefon eller sensorenhet
- datum och tid
- riktning
- start- och slutvåning
- last eller antal passagerare, om känt
- program- och algoritmversion
- kommentarer om avvikande mätförhållanden

Bra metadata är avgörande för att mätningar ska kunna jämföras rättvist.

### JSON

JSON står för JavaScript Object Notation. Det är ett textformat för strukturerade data och fungerar bra som gränssnitt mellan Pythonanalysen och webbappen.

Ett förenklat exempel:

    {
      "elevator": "10A",
      "date": "2026-09-17",
      "direction": "down",
      "startFloor": 10,
      "endFloor": 0,
      "metrics": {
        "maxAcceleration": 0.82,
        "dominantFrequencyHz": 8.3,
        "cyclesPerMeter": 9.1
      }
    }

JSON är maskinläsbart men fortfarande möjligt för en människa att inspektera.

### Schema och validering

Ett schema beskriver vilka fält som ska finnas, vilka datatyper de har och vilka värden som är tillåtna. Validering kontrollerar att data följer schemat.

Exempel: date ska vara ett datum, startFloor ska vara ett heltal och samples ska vara en lista. Ett schema minskar risken för att frontend går sönder när exporteraren ändras.

## Analyskoden

Analyskoden finns i Python och består konceptuellt av flera steg:

1. läsa in mätfilen
2. kontrollera tidsstämplar och samplingsfrekvens
3. filtrera signalerna
4. hitta den faktiska hissresans start och stopp robust
5. dela upp resan i start, konstant fart och inbromsning
6. beräkna profiler och nyckeltal
7. göra spektralanalys
8. skapa automatiska observationer
9. exportera resultatet till JSON

En algoritm är en preciserad metod för att lösa en uppgift. Vår start- och stoppdetektion, lågpassfiltrering och spektralskattning är algoritmer.

En parameter är ett inställningsvärde i en algoritm, exempelvis filtrets gränsfrekvens eller tröskeln för att identifiera rörelse.

En heuristik är en praktisk tumregel som ofta fungerar men inte är matematiskt garanterad. Automatisk klassificering av en ryckig start kan exempelvis börja som en heuristik.

## Automatiska slutsatser och intelligens

Det är viktigt att skilja på olika kunskapsnivåer:

1. Datapunkt: 10A har en spektraltopp vid 8,3 Hz.
2. Mönster: toppen är starkare än hos övriga hissar.
3. Tolkning: beteendet är förenligt med ett återkommande mekaniskt fenomen.
4. Extern information: servicebolaget uppger att ett hjul behöver bytas.
5. Hypotes: den uppmätta toppen orsakas av just detta hjul.

De första två nivåerna kan systemet ofta generera direkt från data. Tolkningar kräver regler, domänkunskap eller en statistisk modell. En orsakshypotes bör redovisas som hypotes om den inte är verifierad.

En regelbaserad analys använder tydliga villkor, exempelvis att markera en hiss om vibrationsenergin ligger långt över gruppens median.

En statistisk analys skattar vad som är normalt utifrån flera mätningar och markerar avvikelser.

En ML-modell, machine learning-modell, lär sig mönster från träningsdata. Den blir relevant först när det finns tillräckligt många väl märkta mätningar och kända felutfall. För detta projekt är transparenta regler och relativa jämförelser sannolikt en bättre start.

## Git och GitHub

### Git

Git är ett versionshanteringssystem. Det håller reda på hur filer förändras över tid och gör det möjligt att:

- se historik
- jämföra versioner
- återgå till en tidigare version
- utveckla parallellt i branches
- granska exakt vad som ändrats

### Repository eller repo

Ett repository är projektmappen tillsammans med dess Git-historik. Vårt repo finns på GitHub som signalprofessor/elevator.

### Commit

En commit är en namngiven ögonblicksbild av en grupp förändringar. Ett bra commit-meddelande beskriver syftet, till exempel:

    Add historical measurement comparison

### Push och pull

Push skickar lokala commits till GitHub. Pull hämtar ändringar från GitHub till den lokala kopian.

### Branch

En branch är ett separat utvecklingsspår. Man kan prova en funktion utan att direkt påverka den publicerade versionen. Main är vanligen huvudgrenen.

### Pull request

En pull request, ofta PR, är en begäran om att granska och föra in ändringar från en branch till en annan. Där kan teamet diskutera kod, köra automatiska kontroller och godkänna ändringen.

## Build, dependencies och package manager

### Source code

Source code eller källkod är filerna människor arbetar i, till exempel TypeScript, React och Python.

### Build

Ett buildsteg omvandlar källkoden till filer som kan publiceras. För vår webbapp innebär det bland annat att:

- TypeScript och React bearbetas
- kod och stilmallar paketeras
- filer optimeras
- den statiska katalogen loopia-dist skapas

### Dependency

Ett dependency eller beroende är ett externt kodpaket som projektet använder. React och Recharts är exempel.

### Package manager

En package manager installerar och håller reda på JavaScriptberoenden. Projektet använder pnpm. Filen package.json beskriver bland annat beroenden och tillgängliga kommandon.

### Lockfile

En lockfile låser exakta paketversioner. Det gör bygget reproducerbart: datorn och GitHub Actions ska installera samma versioner.

## CI och CD

### CI: Continuous Integration

Continuous Integration betyder att ändringar integreras ofta och kontrolleras automatiskt. När vi pushar kod till GitHub kör systemet bland annat installation, build och validering.

Syftet är att upptäcka fel tidigt och säkerställa att projektet fortfarande går att bygga.

### CD: Continuous Delivery eller Continuous Deployment

CD kan betyda två närliggande saker:

- Continuous Delivery: en publicerbar version skapas automatiskt, men en människa godkänner publiceringen.
- Continuous Deployment: en godkänd ändring publiceras automatiskt hela vägen till produktion.

Vårt flöde ligger nära Continuous Deployment: efter en lyckad körning laddas de byggda filerna upp till Loopia.

### Pipeline

En pipeline är den ordnade kedjan av automatiska steg:

    push
      -> installera beroenden
      -> bygga
      -> validera
      -> distribuera

### GitHub Actions

GitHub Actions är GitHubs tjänst för att köra automatiserade arbetsflöden. Instruktionerna ligger i:

    .github/workflows/deploy-loopia.yml

Filen ligger alltså i repot och versionshanteras tillsammans med resten av koden.

### YAML och filändelsen YML

YAML är ett textformat för konfiguration. Namnet uttalas ofta ungefär jäm-el och är en rekursiv förkortning av YAML Ain't Markup Language.

Filändelserna .yml och .yaml betyder samma sak. .yml uppstod delvis eftersom äldre system föredrog tre tecken i filändelser. GitHub Actions accepterar båda.

YAML använder indrag för att visa struktur, så mellanslag är betydelsefulla.

Ett förenklat arbetsflöde:

    name: Deploy

    on:
      push:
        branches:
          - main

    jobs:
      build-and-deploy:
        runs-on: ubuntu-latest
        steps:
          - checkout
          - install
          - build
          - validate
          - upload

Den riktiga YAML-filen innehåller mer exakta kommandon och inställningar.

### Runner och job

En runner är den tillfälliga virtuella dator som GitHub använder för att köra arbetsflödet. Ett job är en grupp steg som körs på en runner.

### Secret

Ett secret är ett känsligt värde, exempelvis FTP-användarnamn eller lösenord. Secrets sparas krypterat i GitHub och ska inte skrivas direkt i repot eller YAML-filen.

## Deployment och hosting

Deployment eller driftsättning är processen att flytta en färdig version till den miljö där användarna når den.

Hosting eller webbhotell är infrastrukturen som serverar webbplatsens filer. Loopia är vår hostingleverantör.

FTPS är FTP över en krypterad TLS-anslutning. GitHub Actions använder det för att överföra webbplatsens byggda filer till Loopias public_html-katalog.

public_html är webbserverns dokumentrot: filer där kan serveras till besökarnas webbläsare.

## Domän, DNS och HTTPS

Domännamnet elevator.signalprofessor.com är människovänligt. DNS översätter det till den server som ska svara.

En subdomän är delen framför huvuddomänen. Här är elevator subdomänen och signalprofessor.com huvuddomänen.

HTTPS är HTTP med kryptering och identitetskontroll via TLS. Ett TLS-certifikat knyter domännamnet till den krypterade anslutningen.

DNS-ändringar och certifikat kan ta en stund att slå igenom. Detta kallas propagation, även om fördröjningen i praktiken kan bero på flera cache- och konfigurationssteg.

## Miljöer

En environment eller miljö är en plats där systemet körs.

- Lokal utvecklingsmiljö: Fredriks Mac.
- Preview: en förhandsversion för snabb granskning.
- CI-miljö: GitHub Actions tillfälliga runner.
- Produktion: den publika webbplatsen på Loopia.

En vanlig princip är att utveckla lokalt, testa i preview eller staging och därefter publicera till production.

## Test, validering och observability

Ett unit test provar en liten funktion isolerat. Ett integration test provar att flera delar fungerar tillsammans. Ett end-to-end-test provar ett helt användarflöde, exempelvis att sidan laddas, att en hiss kan väljas och att rätt graf visas.

Validation kontrollerar att resultatet är rimligt eller har rätt struktur. Vårt deployflöde validerar den byggda webbplatsen innan uppladdning.

Logging betyder att systemet sparar händelser och felmeddelanden. Monitoring betyder att man följer systemets hälsa över tid. Observability är ett bredare begrepp för hur väl man kan förstå ett systems interna tillstånd genom loggar, mätvärden och spårning.

I vår framtida lösning finns två sorters övervakning:

- teknisk övervakning av att mjukvaran och datainsamlingen fungerar
- domänövervakning av hissarnas rörelse och mekaniska tillstånd

## Om vi bygger en riktig backend

En möjlig framtida arkitektur kan se ut så här:

    sensortelefon i hissen
            |
            v
    API för uppladdning
            |
            +----> objektlagring för råfiler
            |
            +----> databas för metadata
            |
            v
    job queue
            |
            v
    Python worker analyserar resan
            |
            +----> resultatdatabas
            |
            +----> avvikelsemotor och notifikationer
            |
            v
    API levererar resultat till webbappen

### API

API står för Application Programming Interface. Det är ett definierat sätt för program att kommunicera. Telefonen kan exempelvis skicka en mätning till en endpoint, och frontend kan hämta analyserade resor från en annan.

### Endpoint

En endpoint är en specifik adress och operation i ett API, exempelvis:

    POST /api/v1/measurements
    GET /api/v1/elevators/10A/trips

POST används typiskt för att skapa eller skicka data. GET används typiskt för att läsa data.

### Databas

En databas lagrar strukturerad information som användare, byggnader, hissar, resor, nyckeltal och analysstatus.

Råa sensorfiler passar ofta bättre i object storage eller objektlagring än direkt i en relationsdatabas. Databasen kan då lagra filens adress och metadata.

### Job queue och worker

Sensoranalys kan ta tid. API:t bör därför kunna ta emot filen snabbt och lägga ett analysjobb i en job queue, alltså en arbetskö.

En worker är en separat process som hämtar jobb ur kön, kör Pythonanalysen och sparar resultatet. Detta kallas asynkron bearbetning eftersom användaren inte behöver hålla samma webbförfrågan öppen tills allt är klart.

### Statusflöde

Ett analysjobb kan ha tillstånd som:

    uploaded -> queued -> processing -> completed
                                  \-> failed

Frontend kan visa status och hämta resultatet när jobbet är färdigt.

### Authentication och authorization

Authentication eller autentisering svarar på frågan: Vem är du?

Authorization eller behörighetskontroll svarar på frågan: Vad får du göra?

En användare kan exempelvis vara autentiserad men bara ha behörighet till sin egen BRF.

### Multi-tenancy

Multi-tenancy innebär att samma system betjänar flera organisationer, men håller deras data logiskt åtskilda. Varje BRF kan vara en tenant.

### Notification

En notification service kan skicka e-post, pushnotis eller annan avisering när exempelvis:

- en mätning misslyckas
- en sensor varit tyst för länge
- ett nyckeltal avviker tydligt
- en hiss förändras jämfört med sin egen historik

## Telefon i varje hiss

En permanent telefon eller sensorenhet i hissen är ett edge device: en enhet nära den fysiska processen som samlar in eller bearbetar data.

En robust insamlingsapp behöver hantera:

- automatisk start efter omstart
- lokal buffring när nät saknas
- unik identitet för enheten och hissen
- tidsstämpling och synkroniserad klocka
- detektion av enskilda resor
- säker uppladdning
- batteri, temperatur och lagringsutrymme
- återförsök utan att samma resa lagras flera gånger
- fjärrövervakning av om enheten fortfarande levererar data

Offline first betyder att enheten kan fortsätta samla data utan nät och synkronisera senare.

Idempotency betyder att samma uppladdning kan skickas igen utan att skapa dubbletter. Varje resa kan få ett unikt trip ID.

## Barometer och referenstryck

En barometer mäter lufttryck. Tryckskillnaden kan användas för att uppskatta höjdskillnad, men väder och ventilation gör att absoluttrycket driver över tid.

En stationär referenstelefon i varje BRF kan mäta den gemensamma tryckdriften. Skillnaden mellan hissens sensor och referensen kan ge en stabilare höjdskattning.

Att kombinera accelerometer, barometer och kännedom om våningsplan är sensor fusion. Varje sensor bidrar med olika egenskaper:

- accelerometern reagerar snabbt men driver vid integration
- barometern ger höjdinformation men påverkas av långsam tryckdrift
- kända våningshöjder ger diskreta referenspunkter

Kalibrering innebär att uppskatta och korrigera systematiska skillnader mellan sensorer och enheter.

## Datamodell för framtiden

En möjlig begreppsmodell:

    Tenant, BRF
      -> Building, byggnad
        -> Elevator, hiss
          -> Device, sensorenhet
          -> Trip, resa
            -> RawFile, råfil
            -> AnalysisRun, analyskörning
              -> Metric, nyckeltal
              -> Finding, observation

En resa och en analyskörning bör vara skilda objekt. Samma rådata kan analyseras igen med en ny algoritmversion utan att den ursprungliga resan ändras.

### Provenance och versionshantering av analys

Data provenance betyder att kunna spåra var ett resultat kommer ifrån. För varje analys bör man kunna se:

- vilken råfil som användes
- algoritmversion
- parameteruppsättning
- tidpunkt
- programversion eller Git-commit
- om analysen lyckades

Detta gör resultaten reproducerbara och möjliga att granska.

## Säkerhet och integritet

Principen least privilege innebär att varje konto eller komponent bara får den åtkomst som behövs. GitHub-kontot för deployment bör exempelvis bara kunna skriva till rätt webbkatalog.

Secrets ska hållas utanför källkoden. Kommunikation bör krypteras. Uppladdningar bör valideras innan de bearbetas.

Sensorer i hissar kan indirekt beskriva människors rörelser. Även utan namn bör man fundera på dataminimering, lagringstid och vem som får se rådata.

## Så kan projektet beskrivas för en backend-utvecklare

### Kort version

Vi har en fungerande statisk Reactdashboard och en lokal Pythonpipeline som omvandlar hissens sensordata till JSON. GitHub Actions bygger och distribuerar dashboarden till Loopia. Nästa möjliga steg är ett API-baserat ingestflöde där råfiler och metadata laddas upp, analys körs asynkront av Pythonworkers och resultat lagras och exponeras per BRF och hiss.

### Mer teknisk version

Frontend är en statiskt byggd React- och TypeScriptapplikation som läser förgenererade JSON-filer. Nuvarande ETL-liknande pipeline körs lokalt: rå sensordata läses, filtreras, segmenteras och analyseras i Python, och exporteraren skapar frontendens datamodell. GitHub Actions fungerar som CI/CD för frontendbygge, validering och FTPS-deployment till Loopia.

För en produktionsbackend vill vi separera ingest, objektlagring, metadata, jobbkö, analysworker och resultattjänst. Modellen behöver stöd för tenants, byggnader, hissar, enheter, resor och versionsbundna analyskörningar. Systemet bör vara idempotent, kunna buffra offline på edge-enheten och skicka avvikelsenotifikationer.

### Bra frågor till backendutvecklaren

- Vilket API-kontrakt ska gälla mellan sensorenheten, analysen och frontend?
- Hur modellerar vi tenant, byggnad, hiss, enhet, resa och analysversion?
- Var lagrar vi råfiler respektive metadata och resultat?
- Hur gör vi uppladdningar idempotenta?
- Hur startas, övervakas och återkörs analysjobb?
- Hur isoleras olika BRF:ers data?
- Hur versionssätter vi JSON-schema och algoritm?
- Hur hanterar vi offlinebuffring och stora uppladdningar?
- Vilka händelser ska utlösa notifikationer?
- Hur ser retention, backup och borttagning av data ut?

## Vanliga ord och korta förklaringar

| Term | Betydelse i vårt projekt |
|---|---|
| App | Ett program; kan vara webbappen eller sensorns mobilapp |
| Architecture | Hur systemets delar är uppdelade och samverkar |
| Backend | Serverdelen som tar emot, lagrar och bearbetar data |
| Branch | Separat utvecklingsspår i Git |
| Build | Omvandling från källkod till publicerbara filer |
| CI | Automatiska kontroller och bygge vid kodändringar |
| CD | Automatisk eller publiceringsklar driftsättning |
| Commit | Versionsmärkt paket av kodändringar |
| Dashboard | Det interaktiva gränssnittet med grafer och nyckeltal |
| Database | Strukturerad lagring av metadata och resultat |
| Deploy | Publicera en färdig version |
| Dependency | Externt kodpaket som projektet använder |
| DNS | Kopplar domännamn till rätt server |
| Edge device | Telefonen eller sensorenheten i hissen |
| Endpoint | En bestämd operation och adress i ett API |
| ETL | Extract, Transform, Load: hämta, omvandla och lagra data |
| Frontend | Det användaren ser i webbläsaren |
| FTPS | Krypterad filöverföring till webbhotellet |
| Git | Versionshanteringssystemet |
| GitHub | Tjänsten där repot och Actions finns |
| Hosting | Infrastruktur som gör webbplatsen åtkomlig |
| HTTPS | Krypterad webbkommunikation |
| Idempotent | Samma anrop kan upprepas utan dubbletter |
| JSON | Textformatet som bär analysresultaten till frontend |
| Logging | Registrering av händelser och fel |
| Metadata | Beskrivning av mätningen och dess sammanhang |
| Pipeline | Kedja av automatiska bearbetningssteg |
| Production | Den version verkliga användare möter |
| Pull request | Granskning innan en branch förs in i huvudgrenen |
| Repo | Projektets filer och versionshistorik |
| Schema | Regler för datas struktur |
| Secret | Skyddat lösenord eller annan känslig uppgift |
| Static site | Färdigbyggda filer utan serverkörd applikationslogik |
| Tenant | En kundorganisation, exempelvis en BRF |
| TypeScript | JavaScript med typer, använt i frontend |
| Validation | Kontroll att data eller bygge uppfyller regler |
| Worker | Process som utför bakgrundsjobb |
| YAML | Konfigurationsformatet för GitHub Actions |

## En mening att komma ihåg

Vi har byggt en statisk, interaktiv frontend ovanpå en lokal signalbehandlingspipeline, versionshanterat allt i Git och automatiserat bygge och deployment med GitHub Actions; nästa arkitektursteg skulle vara en multi-tenant backend för ingest, lagring, asynkron analys och avvikelsenotifiering.

