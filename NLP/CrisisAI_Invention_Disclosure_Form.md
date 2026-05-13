# Annexure3b- Complete filing INVENTION DISCLOSURE FORM
Details of Invention for better understanding:

### 1. TITLE:
CrisisAI Sentinel: Real-Time Social Media Sentiment and Crisis Detection System for Disaster Management using Transformer-Based Deep Learning

### 2. INTERNAL INVENTOR(S)/ STUDENT(S): 
All fields in this column are mandatory to be filled

**A. Full name:** [Inventor Name 1]
**Mobile Number:** [Mobile Number]
**Email (personal):** [Email]
**UID/Registration number:** [UID]
**Address of Internal Inventors:** [Address]
**Signature (Mandatory):** _________________

**B. Full name:** [Inventor Name 2]
**Mobile Number:** [Mobile Number]
**Email (personal):** [Email]
**UID/Registration number:** [UID]
**Address of Internal Inventors:** [Address]
**Signature (Mandatory):** _________________

*(FOR ADDITIONAL INVENTORS, PLEASE ADD ROWS)*

**EXTERNAL INVENTOR(S):** (INVENTORS NOT WORKING IN LPU)
**A. Full name:** [External Name]
**Mobile Number:** [Mobile Number]
**Email:** [Email]
**Address of External Affiliations:** [Address]
**Signature (Mandatory):** _________________

*For External Inventors, NOC (No Objection Certificate) from the affiliated institute/university/Industry/lab etc. is mandatory for each individual inventor and their respective topic.*

---

### 3. DESCRIPTION OF THE INVENTION:
Natural and man-made disasters represent one of humanity's most severe societal challenges. Traditional disaster detection and response systems relying on official governmental channels suffer from critical latency of 30 minutes to several hours before actionable intelligence reaches first responders. While social media provides immediate situational awareness data, the sheer volume, noise, and semantic complexity of this data make manual monitoring infeasible.

The **CrisisAI Sentinel** is a novel, fully-automated, real-time social media sentiment analysis and crisis detection system engineered for disaster management applications. The system integrates a multi-modal deep learning pipeline comprising HuggingFace Transformers for sentiment classification, Sentence-Transformers for generating deep semantic embeddings, Zero-Shot classification for dynamic topic modeling, alongside DBSCAN geographic density clustering, and Isolation Forest anomaly detection. These deep learning algorithms replace traditional statistical and rule-based systems, offering profound contextual understanding. 

The system produces a real-time Crisis Index Score (CIS) — a weighted composite metric computed from six orthogonal signals: sentiment distress, anomaly intensity, cluster crisis ratio, disaster keyword density, volume spike detection, and social engagement. 

#### PROBLEM ADDRESSED BY THE INVENTION:
* **High Latency in Official Channels:** Traditional response systems suffer from a latency of 30 minutes to hours before actionable intelligence reaches first responders.
* **Limitations of Traditional NLP:** Prior art systems rely on rule-based sentiment (e.g., VADER) which fails to understand deep context, irony, or complex crisis semantics, or statistical bag-of-words (TF-IDF) which loses word order and semantic relationships.
* **Geographical Disconnect:** Lack of geographic contextualization in analyzing disaster reports, making it hard to identify specific hotspots.
* **Data Overload:** The sheer volume and noise of live social media data makes manual monitoring impossible.

#### OBJECTIVE OF THE INVENTION
* **Context-Aware Sentiment Analysis:** To utilize Transformer-based language models that understand context dynamically to classify distress probabilities without relying on manual rule creation.
* **Real-time Crisis Index Scoring:** To compute a comprehensive multi-signal Crisis Index Score (CIS) combining sentiment, anomalies, clusters, keywords, volume, and engagement.
* **Dynamic Topic Inference:** To dynamically categorize disaster topics (e.g., floods, wildfires) without explicit prior training using Zero-Shot classification.
* **Interactive Geographic Clustering:** To group geographic coordinates using DBSCAN for immediate detection of localized disaster hotspots and visualizing them via a Socket.IO-powered real-time dashboard.

---

### C. STATE OF THE ART/ RESEARCH GAP/NOVELTY:

| Sr. No. | Patent Id | Abstract | Research Gap | Novelty |
| :--- | :--- | :--- | :--- | :--- |
| 1 | [Example ID] | Prior systems utilizing rule-based sentiment analysis for social media data (e.g., VADER). | Reliance on rule-based sentiment fails to understand deep context, irony, or complex crisis semantics. They cannot adapt to varying sentence structures. | The invention uses a fine-tuned Transformer-based sequence classification model to map hidden states to a soft probability distribution, offering profound contextual understanding. |
| 2 | [Example ID] | Disaster topic modeling using traditional statistical methods such as TF-IDF and LDA. | Statistical bag-of-words methods lose word order and semantic relationships. They cannot classify emerging disaster topics without explicit retraining. | Utilizes Zero-Shot Topic Classification via Natural Language Inference (NLI), allowing dynamic categorization of unprecedented disaster topics without explicit training. |
| 3 | [Example ID] | Systems using basic thresholding for volume spikes on social media without semantic embeddings. | Lack of semantic text clustering combined with geographic data, leading to false positives and broad alerts. | Integrates 384-dimensional dense semantic embeddings with DBSCAN geographic clustering to accurately pinpoint highly localized and semantically correlated disaster hotspots. |

---

### D. DETAILED DESCRIPTION:

#### 1. System Architecture
The CrisisAI Sentinel implements a highly scalable, distributed five-layer software architecture designed for real-time processing of high-velocity crisis data streams:
*   **Layer 1: Data Ingestion Module:** Continuously polls REST APIs (GDACS, ReliefWeb) and subscribes to social media streaming endpoints (Twitter/X API, Reddit Streams). Data is pushed into a high-throughput message broker to handle volume spikes during major events.
*   **Layer 2: Deep NLP Pipeline:** Text streams undergo asynchronous preprocessing (noise reduction, URL stripping, tokenization) and are mapped into high-dimensional dense vector embeddings using Sentence-Transformers (e.g., all-MiniLM-L6-v2) for semantic matching.
*   **Layer 3: Deep Learning Inference Engine:** Text is classified for sentiment (distress probability) using fine-tuned RoBERTa/DistilBERT models. Concurrently, Zero-Shot Classification via Natural Language Inference (NLI) dynamically infers emerging disaster topics without needing explicit retraining.
*   **Layer 4: Spatial & Anomaly Engine:** Geographic coordinates are clustered using Density-Based Spatial Clustering of Applications with Noise (DBSCAN) to group reports into localized hotspots (ε = 0.5 km). Isolation Forests identify statistical anomalies in reporting volume over rolling time windows.
*   **Layer 5: Real-Time Dashboard & Crisis Scoring:** Computes the 6-signal Crisis Index Score (CIS). The output is pushed to connected client dashboards via WebSocket (Socket.IO) for sub-second latency visualization on interactive Leaflet.js maps and Chart.js timelines.

#### 2. Dataset and Input/Output Specifications
The system relies on a continuous ingestion of multimodal data streams. The dataset characteristics include:
*   **Input Features (Raw Data):** Unstructured text (social media posts, news headlines), precise GPS coordinates, timestamps, and user engagement metrics (retweets, shares, likes) which serve as an amplifier for urgency.
*   **Ground Truth/Training Data:** Historical disaster datasets (e.g., CrisisLex, HumAID) containing millions of annotated tweets related to various natural disasters (floods, earthquakes, hurricanes) are used to fine-tune the sentiment and embedding models.
*   **Output Features (Processed Data):** Each ingested record is augmented with a 384-dimensional dense semantic vector, a categorical topic probability distribution (e.g., 92% Flood, 8% Rain), a clustered hotspot identifier, and an anomalous volume flag. These combined form the final dataset rendered on the dashboard.

#### 3. Mathematical Formulation & Deep Learning Models
*   **Transformer-based Sentiment Analysis:** Self-attention mechanisms weigh surrounding words. The sequence output is pooled and passed through a Softmax layer to predict distress probabilities.
*   **Dense Semantic Embeddings:** A Sentence-Transformer generates 384-dimensional dense vectors to calculate semantic textual similarity.
*   **Zero-Shot Topic Classification:** Utilizes an NLI approach where the premise is the text and hypothesis is 'This text is about {label}'.
*   **DBSCAN Geographic Clustering:** Coordinates are clustered to group reports within city blocks (ε = 0.5 km).
*   **Crisis Index Score (CIS):** Computed as a dynamic weighted sum of 6 normalized orthogonal signals.
    `CIS = (0.25 × S_sent) + (0.25 × S_anom) + (0.20 × S_clust) + (0.15 × S_kw) + (0.10 × S_vol) + (0.05 × S_eng)`

---

### E. RESULTS AND ADVANTAGES:

**RESULTS**
The system evaluated using real-world disaster feeds demonstrated a massive performance leap compared to statistical baselines:
*   **Sentiment Accuracy:** 93.4% (vs 76.2% VADER baseline) -> +17.2pp improvement.
*   **F1 Score:** 90.7% (vs 85.7% baseline) -> +5.0pp improvement.
*   **Embedding Quality:** 0.512 Silhouette score (vs 0.413 TF-IDF) -> +23.9% better semantic separation.
*   **Detection Latency:** Processed in 2.5 seconds per batch with negligible DL overhead.

**ADVANTAGES**
*   **Context-Aware Detection:** Recognizes deep semantic nuances, overcoming the limitations of standard keyword searches.
*   **Immediate Alerting:** Enables emergency management personnel to identify and respond to crisis events within 2–5 seconds.
*   **Dynamic Categorization:** Detects completely novel crisis types using Zero-Shot capabilities.
*   **Actionable Hotspots:** Converts a noisy stream of social media and API data into concrete, geographically actionable clusters.

---

### F. EXPANSION:
To prevent competitors from making minor modifications, the patent covers:
*   **The 6-Signal Composite CIS Formula:** Specifically the weighted integration of distress, anomaly, cluster ratio, keyword density, volume, and engagement.
*   **Hybrid Deep NLP Inference Engine:** The specific sequence of passing streaming data through a Sentence-Transformer embedding generator, Zero-Shot classifier, and DBSCAN geographic clusterer simultaneously.
*   **Dynamic Dashboard Transport:** The real-time Socket.IO WebSocket architecture for streaming Deep Learning outputs directly to front-end visualizations without database polling.

---

### G. WORKING PROTOTYPE/ FORMULATION/ DESIGN/COMPOSITION:
A working prototype of the CrisisAI Sentinel has been successfully developed in Python.
The prototype features:
*   **Flask and Socket.IO Backend:** Handling asynchronous data streams and routing them through the machine learning pipeline.
*   **HuggingFace NLP Models:** Integrated DistilBERT/RoBERTa for sentiment extraction and Sentence-Transformers for embeddings.
*   **Anomaly and Clustering Modules:** Using `scikit-learn` for Isolation Forests and DBSCAN.
*   **Frontend Dashboard:** Responsive web UI with a crisis score timeline, topic distribution charts, and a Leaflet.js interactive map.

---

### G. EXISTING DATA:
The system ingests real-time and historical data from:
*   **GDACS (Global Disaster Alert and Coordination System)**
*   **ReliefWeb APIs**
*   **Social Media Streams (Reddit, Twitter/X)**

---

### 4. USE AND DISCLOSURE (IMPORTANT):
*   Have you described or shown your invention/ design to anyone or in any conference? **NO**
*   Have you made any attempts to commercialize your invention? **NO**
*   Has your invention been described in any printed publication, or any other form of media, such as the Internet? **NO**
*   Do you have any collaboration with any other institute or organization on the same? **NO**
*   Name of Regulatory body or any other approvals if required: **NA**

### 5. Provide links and dates for such actions if the information has been made public before sharing with us.
NA

### 6. Provide the terms and conditions of the MOU also if the work is done in collaboration within or outside university.
NA

### 7. Potential Chances of Commercialization.
**Yes**, the system has substantial commercialization potential for:
*   **Government Agencies:** National Disaster Management Authorities (NDMA) for real-time situational awareness.
*   **NGOs & International Bodies:** Red Cross, FEMA, UN-OCHA relief coordination centers.
*   **Private Infrastructure:** Power grids, water utilities, and transportation sectors needing early warnings of localized crises.

### 8. List of companies which can be contacted for commercialization along with the website link.
1.  **Palantir Technologies:** https://www.palantir.com/
2.  **Esri (ArcGIS):** https://www.esri.com/
3.  **Dataminr:** https://www.dataminr.com/
4.  **Everbridge:** https://www.everbridge.com/

### 9. Any basic patent which has been used and we need to pay royalty to them.
NA (Uses open-source HuggingFace models and scikit-learn libraries).

### 10. FILING OPTIONS:
**Provisional Patent Filing:** I am considering filing a provisional patent to establish an early priority date. The core mathematical models (CIS formula), clustering algorithms, and the deep NLP pipeline are well-defined in the prototype, providing a strong basis for early protection while the front-end features are finalized.

### 11. KEYWORDS:
*   Disaster Management
*   Deep Learning
*   Transformer Models
*   Real-Time Systems
*   Sentence Embeddings
*   Zero-Shot Classification
*   Crisis Index Score
*   DBSCAN Clustering

---

### NO OBJECTION CERTIFICATE
This is to certify that University/Organization Name or its associates shall have no objection if Lovely Professional University files an IPR (Patent/Copyright/Design/any other…….) entitled "CrisisAI Sentinel: Real-Time Social Media Sentiment and Crisis Detection System for Disaster Management using Transformer-Based Deep Learning" including the name(s) of,…as inventors who is(are) student(s)/employee(s) studying/ working in our University/ organization.

Further Name of the University/Organization shall not provide any financial assistance in respect of said IPR nor shall raise any objection later with respect to filing or commercialization of the said IPR or otherwise claim any right to the patent/invention at any stage.

________________________
(Authorised Signatory)
