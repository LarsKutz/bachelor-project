# Evaluation
Erklärungen von: 
- [Evidently AI](https://www.evidentlyai.com/ranking-metrics)
- [ranx](https://amenra.github.io/ranx/metrics/)

</br>
</br>

## Erklärung der Metriken

Information-Retrieval-Systeme (IR-Systeme) werden oft anhand von Metriken evaluiert, um ihre Effektivität zu beurteilen, insbesondere wie gut sie relevante Dokumente für eine gegebene Suchanfrage zurückgeben. Die Metriken, die du erwähnt hast (nDCG@k, MRR@k, MAP@k, Recall@k, Precision@k), sind gängige Methoden zur Messung der Qualität von Ergebnissen in IR-Systemen, wobei das `@k` bedeutet, dass man nur die Top-`k`-Ergebnisse betrachtet. Hier ist eine detaillierte Erklärung der einzelnen Metriken:

### 1. **nDCG@k (normalized Discounted Cumulative Gain)**
Diese Metrik bewertet die Relevanz von Dokumenten, wobei sie die Position der relevanten Dokumente in den Ergebnissen berücksichtigt. Das Grundprinzip basiert auf der Annahme, dass relevantere Dokumente höher in der Ergebnisliste erscheinen sollten, und dass die Relevanz eines Dokuments umso geringer gewichtet wird, je weiter unten es in der Liste steht. 

- **Cumulative Gain (CG)**: Die Relevanz der gefundenen Dokumente wird addiert.
- **Discounted Cumulative Gain (DCG)**: Die Relevanzwerte werden nach ihrer Position (Rang) in der Ergebnisliste diskontiert. Ein Dokument auf Rang 1 ist wertvoller als ein Dokument auf Rang 10.
  
  Die Formel für DCG lautet:
  $$
  DCG@k = \sum_{i=1}^{k} \frac{rel_i}{\log_2(i+1)}
  $$
  wobei \(rel_i\) die Relevanz des Dokuments an Position \(i\) ist.

- **nDCG@k** normalisiert den DCG-Wert durch den maximal möglichen DCG-Wert (ideal DCG oder iDCG), damit die Ergebnisse zwischen 0 und 1 liegen:
  $$
  nDCG@k = \frac{DCG@k}{iDCG@k}
  $$
  Ein Wert von 1 bedeutet perfekte Platzierung relevanter Dokumente in den Top-`k`.

### 2. **MRR@k (Mean Reciprocal Rank)**
Der Mean Reciprocal Rank bewertet die Position des ersten relevanten Dokuments in den Ergebnissen. Der Rang des ersten relevanten Dokuments wird invers bewertet, d. h. je früher es erscheint, desto höher ist der Wert. Diese Metrik ist besonders nützlich, wenn es wichtig ist, dass relevante Ergebnisse sehr früh in der Liste erscheinen.

- Die Reciprocal Rank für eine einzelne Suchanfrage ist:
  $$
  RR = \frac{1}{\text{Rang des ersten relevanten Dokuments}}
  $$
- **MRR@k** ist der Durchschnitt dieser Reciprocal Ranks über alle Suchanfragen hinweg:
  $$
  MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} RR_i
  $$
  wobei \(Q\) die Menge der Suchanfragen ist. Ein Wert nahe bei 1 bedeutet, dass das relevante Dokument fast immer an einer der ersten Positionen erscheint.

### 3. **MAP@k (Mean Average Precision)**
Die Average Precision (AP) misst, wie gut die relevanten Dokumente über die gesamte Ergebnisliste verteilt sind. MAP berücksichtigt sowohl Präzision als auch die Reihenfolge der Ergebnisse.

- **Precision@k** misst die Genauigkeit der Ergebnisse bis zu Position \(k\) (mehr dazu unten).
- **AP** berechnet den Durchschnitt der Precision-Werte an den Positionen, an denen relevante Dokumente erscheinen:
  $$
  AP = \frac{1}{\text{Anzahl relevanter Dokumente}} \sum_{i \text{ (relevant)}} \text{Precision@i}
  $$
- **MAP@k** ist der Durchschnitt der AP-Werte über alle Suchanfragen:
  $$
  MAP@k = \frac{1}{|Q|} \sum_{q \in Q} AP@k(q)
  $$
  MAP berücksichtigt also sowohl Präzision als auch die Reihenfolge der relevanten Dokumente, was es zu einer robusten Metrik macht.

### 4. **Recall@k**
Recall misst, wie viele der insgesamt relevanten Dokumente in den Top-`k` Ergebnissen enthalten sind. Es beantwortet die Frage: „Wie viel Prozent der relevanten Dokumente habe ich gefunden?“

- **Recall** ist definiert als:
  $$
  Recall@k = \frac{\text{Anzahl relevanter Dokumente in den Top } k}{\text{Anzahl aller relevanter Dokumente}}
  $$
  Recall@k variiert zwischen 0 und 1, wobei 1 bedeutet, dass alle relevanten Dokumente in den Top-`k` enthalten sind. Recall ignoriert die Reihenfolge der Ergebnisse, weshalb es oft zusammen mit Precision verwendet wird, um eine vollständige Bewertung zu geben.

### 5. **Precision@k**
Precision misst, wie viele der Dokumente in den Top-`k` Ergebnissen tatsächlich relevant sind. Es beantwortet die Frage: „Wie genau sind die Ergebnisse?“

- **Precision** ist definiert als:
  $$
  Precision@k = \frac{\text{Anzahl relevanter Dokumente in den Top } k}{k}
  $$
  Precision@k gibt an, wie viele der Top-`k` zurückgegebenen Dokumente relevant sind. Ein Wert von 1 bedeutet, dass alle zurückgegebenen Dokumente relevant sind.

### Zusammenfassung
- **nDCG@k**: Berücksichtigt Relevanz und die Position von Dokumenten in der Ergebnisliste. Fokus auf die Rangfolge.
- **MRR@k**: Misst die Position des ersten relevanten Dokuments. Wichtig, wenn frühe relevante Ergebnisse erwartet werden.
- **MAP@k**: Durchschnitt der Präzision an den Positionen relevanter Dokumente. Berücksichtigt sowohl Präzision als auch Reihenfolge.
- **Recall@k**: Misst den Anteil der relevanten Dokumente in den Top-`k` Ergebnissen. Wichtig, um festzustellen, ob alle relevanten Dokumente erfasst wurden.
- **Precision@k**: Misst die Genauigkeit der Ergebnisse, also den Anteil relevanter Dokumente unter den zurückgegebenen Top-`k`.

Jede dieser Metriken hat ihre Stärken und Schwächen, je nachdem, ob man sich auf die Reihenfolge (nDCG, MRR), auf Vollständigkeit (Recall), auf Präzision (Precision), oder auf einen ausgeglichenen Mix dieser Aspekte (MAP) konzentrieren möchte.

</br>
</br>

## Beispiel für die Berechnung

Wir werden Schritt für Schritt jede Metrik für die angegebenen Werte von \( k \) (also 3 und 5) berechnen.

### **Gegebener Datensatz**

#### **Qrels (Relevanzbewertungen)**
```python
qrels_dict = {
    "q1": {
        "doc1": 7,
        "doc2": 5,
        "doc4": 3,
    }
}
```

#### **Run (Systemrückgabe mit Scores)**
```python
run_dict = {
    "q1": {
        "doc1": 1,
        "doc2": 0.95,
        "doc3": 0.9,
        "doc4": 0.85,
        "doc5": 0.8,
        "doc6": 0.75,
        "doc7": 0.7,
        "doc8": 0.65,
        "doc9": 0.6,
        "doc10": 0.55,
    }
}
```

#### **Metriken**
```python
metrics = ["ndcg@3", "ndcg@5", "mrr@3", "mrr@5", "map@3", "map@5"]
```

### **Vorbereitung**

1. **Sortiere die Dokumente nach den Scores in absteigender Reihenfolge.**
   
   Für **q1** ergibt sich folgende Rangliste:
   
   | Rang | Dokument | Score |
   |------|----------|-------|
   | 1    | doc1     | 1     |
   | 2    | doc2     | 0.95  |
   | 3    | doc3     | 0.9   |
   | 4    | doc4     | 0.85  |
   | 5    | doc5     | 0.8   |
   | 6    | doc6     | 0.75  |
   | 7    | doc7     | 0.7   |
   | 8    | doc8     | 0.65  |
   | 9    | doc9     | 0.6   |
   | 10   | doc10    | 0.55  |

2. **Identifiziere die relevanten Dokumente und ihre Positionen in den Top-\( k \) Listen.**
   
   Relevante Dokumente: **doc1**, **doc2**, **doc4**

### **1. nDCG@k (normalized Discounted Cumulative Gain)**

#### **Formel:**
$$
nDCG@k = \frac{DCG@k}{iDCG@k}
$$

#### **Berechnung von DCG@k:**
$$
DCG@k = \sum_{i=1}^{k} \frac{rel_i}{\log_2(i+1)}
$$
wobei \( rel_i \) die Relevanz des Dokuments an Position \( i \) ist.

#### **Berechnung von iDCG@k (ideales DCG):**
Sortiere die relevanten Dokumente in der idealen Reihenfolge (höchste Relevanz zuerst).

**Ideale Rangliste für q1:**

| Rang | Dokument | Relevanz |
|------|----------|----------|
| 1    | doc1     | 7        |
| 2    | doc2     | 5        |
| 3    | doc4     | 3        |
| ...  | ...      | ...      |

#### **nDCG@3:**

**Berechnung von DCG@3:**

- Position 1: doc1 (Relevanz 7)
  $$
  \frac{7}{\log_2(1+1)} = \frac{7}{1} = 7
  $$
- Position 2: doc2 (Relevanz 5)
  $$
  \frac{5}{\log_2(2+1)} = \frac{5}{1.58496} \approx 3.155
  $$
- Position 3: doc3 (nicht relevant, Relevanz 0)
  $$
  \frac{0}{\log_2(3+1)} = 0
  $$

$$
DCG@3 = 7 + 3.155 + 0 \approx 10.155
$$

**Berechnung von iDCG@3:**

- Position 1: doc1 (Relevanz 7)
  $$
  \frac{7}{\log_2(1+1)} = 7
  $$
- Position 2: doc2 (Relevanz 5)
  $$
  \frac{5}{\log_2(2+1)} \approx 3.155
  $$
- Position 3: doc4 (Relevanz 3)
  $$
  \frac{3}{\log_2(3+1)} = \frac{3}{2} = 1.5
  $$

$$
iDCG@3 = 7 + 3.155 + 1.5 \approx 11.655
$$

$$
nDCG@3 = \frac{10.155}{11.655} \approx 0.871
$$

#### **nDCG@5:**

**Berechnung von DCG@5:**

- Position 1: doc1 (7)
  $$
  7
  $$
- Position 2: doc2 (5)
  $$
  \frac{5}{1.58496} \approx 3.155
  $$
- Position 3: doc3 (0)
  $$
  0
  $$
- Position 4: doc4 (3)
  $$
  \frac{3}{\log_2(4+1)} \approx \frac{3}{2.32193} \approx 1.293
  $$
- Position 5: doc5 (0)
  $$
  0
  $$

$$
DCG@5 = 7 + 3.155 + 0 + 1.293 + 0 \approx 11.448
$$

**Berechnung von iDCG@5:**

- Position 1: doc1 (7)
  $$
  7
  $$
- Position 2: doc2 (5)
  $$
  \frac{5}{1.58496} \approx 3.155
  $$
- Position 3: doc4 (3)
  $$
  \frac{3}{2} = 1.5
  $$
- Position 4: keine weiteren relevanten Dokumente
  $$
  0
  $$
- Position 5: keine weiteren relevanten Dokumente
  $$
  0
  $$

$$
iDCG@5 = 7 + 3.155 + 1.5 + 0 + 0 \approx 11.655
$$

$$
nDCG@5 = \frac{11.448}{11.655} \approx 0.983
$$

### **2. MRR@k (Mean Reciprocal Rank)**

Da wir nur eine Query haben, ist der MRR einfach der Reciprocal Rank dieser Query.

#### **Formel:**
$$
MRR@k = \frac{1}{\text{Rang des ersten relevanten Dokuments innerhalb der Top } k}
$$

#### **Berechnung von MRR@3:**

- Top 3 Dokumente: doc1, doc2, doc3
- Erster relevantes Dokument: doc1 an Rang 1

$$
RR = \frac{1}{1} = 1
$$

$$
MRR@3 = 1
$$

#### **Berechnung von MRR@5:**

- Top 5 Dokumente: doc1, doc2, doc3, doc4, doc5
- Erster relevantes Dokument: doc1 an Rang 1

$$
RR = 1
$$

$$
MRR@5 = 1
$$

### **3. MAP@k (Mean Average Precision)**

Da wir nur eine Query haben, ist der MAP einfach die Average Precision dieser Query.

#### **Formel:**
$$
AP@k = \frac{1}{\text{Anzahl relevanter Dokumente}} \sum_{i \text{ (relevant)}} \text{Precision@i}
$$

#### **Berechnung von MAP@3:**

- Top 3 Dokumente: doc1, doc2, doc3
- Relevante Dokumente in Top 3: doc1, doc2

**Precision@i:**

- **doc1 (Rang 1):** 
  $$
  \text{Precision@1} = \frac{1}{1} = 1
  $$
- **doc2 (Rang 2):** 
  $$
  \text{Precision@2} = \frac{2}{2} = 1
  $$
- **doc3 (Rang 3):** Nicht relevant

**AP@3:**
$$
AP@3 = \frac{1 + 1}{3} \approx 0.6667
$$

Da die Anzahl relevanter Dokumente insgesamt 3 ist (doc1, doc2, doc4), aber nur 2 in den Top 3 gefunden wurden, korrigieren wir:

$$
AP@3 = \frac{1 + 1}{3} = \frac{2}{3} \approx 0.6667
$$
$$
MAP@3 = 0.6667
$$

#### **Berechnung von MAP@5:**

- Top 5 Dokumente: doc1, doc2, doc3, doc4, doc5
- Relevante Dokumente in Top 5: doc1, doc2, doc4

**Precision@i:**

- **doc1 (Rang 1):** 
  $$
  \text{Precision@1} = 1
  $$
- **doc2 (Rang 2):** 
  $$
  \text{Precision@2} = 2/2 = 1
  $$
- **doc4 (Rang 4):** 
  $$
  \text{Precision@4} = 3/4 = 0.75
  $$
- **doc3 und doc5:** Nicht relevant

**AP@5:**
$$
AP@5 = \frac{1 + 1 + 0.75}{3} \approx \frac{2.75}{3} \approx 0.9167
$$

$$
MAP@5 = 0.9167
$$

### **Zusammenfassung der Berechnungen**

| Metrik   | \( k \) | Wert      |
|----------|---------|-----------|
| nDCG     | @3      | 0.871     |
| nDCG     | @5      | 0.983     |
| MRR      | @3      | 1.0       |
| MRR      | @5      | 1.0       |
| MAP      | @3      | 0.6667    |
| MAP      | @5      | 0.9167    |

### **Erläuterungen und Interpretationen**

- **nDCG@3 (0.871):** Ein hoher Wert zeigt, dass die relevanten Dokumente in den Top 3 gut platziert sind, wobei die Relevanz berücksichtigt wird.
  
- **nDCG@5 (0.983):** Noch näher an der idealen Platzierung, da mehr relevante Dokumente innerhalb der Top 5 gefunden werden.
  
- **MRR@3 und MRR@5 (1.0):** Das erste relevante Dokument befindet sich immer an Rang 1, was den höchsten möglichen Wert für den Reciprocal Rank ergibt.
  
- **MAP@3 (0.6667):** Durchschnittliche Präzision der relevanten Dokumente innerhalb der Top 3 ist moderat.
  
- **MAP@5 (0.9167):** Deutlich höhere durchschnittliche Präzision innerhalb der Top 5, da ein weiteres relevantes Dokument gefunden wurde.

### **Schlussfolgerung**

Diese detaillierten manuellen Berechnungen zeigen, wie jede Metrik die Qualität eines Information-Retrieval-Systems aus verschiedenen Perspektiven bewertet:

- **nDCG** bewertet die Position und die Relevanz der Dokumente.
- **MRR** fokussiert sich auf die Position des ersten relevanten Dokuments.
- **MAP** kombiniert Präzision und die Verteilung der relevanten Dokumente über die Rangliste.

Je nach Anwendung und Prioritäten deines IR-Systems kann die Wahl der geeigneten Metrik variieren. Die Verwendung von Bibliotheken wie **ranx** kann diese Berechnungen automatisieren und für größere Datensätze effizient durchführen.