# OceanSense / ROV Digital Twin Intelligence Stack

This repository now separates the two team responsibilities described in the build plan:

- `src/oceansense/`, `scripts/train_classifier.py`, `scripts/train_detector.py`, `dataset/`, and the
  `/api/*` endpoints are Kerem's image-intelligence deliverable.
- `unity/` and `ros2/` remain integration references for Burak's digital-twin/control work.

Kerem's implemented pipeline is:

```text
licensed underwater image dataset -> validation/split -> EfficientNet-B0 classification
  -> documented anomaly score -> optional YOLOv8n concern boxes
  -> rule-based safety decision -> grounded cautious explanation -> JSON/FastAPI
```

The repository does **not** claim a trained underwater image model yet: no license-reviewed image
snapshot is committed. Training code, evaluation reporting, schemas, API contracts, safety rules, and
tests are complete; add an approved 100-300+ image prototype dataset before reporting accuracy.

## OceanSense quick start

```powershell
python -m pip install -e ".[api]"
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python scripts/run_api.py
```

Train after dataset approval:

```powershell
python -m pip install -e ".[vision]"
python scripts/validate_image_dataset.py dataset/processed/labels.csv --boxes dataset/annotations/bboxes.json
python scripts/train_classifier.py --data dataset/imagefolder
```

See `docs/data_sources.md`, `docs/dataset_card.md`, `docs/model_card.md`, `docs/agent_card.md`, and
`docs/integration_guide.md` before integrating or making performance claims.

Bu depo; Unity tabanli bir su alti robotu dijital ikizi icin veri uretimi, zayif-nokta (weak point) siniflandirmasi, alan-uzman LLM hazirligi ve emniyet-kapili karar ajanini tek bir referans mimaride birlestirir.

## Neler calisiyor?

- Deterministik sentetik telemetri veri uretimi (normal + 4 ariza sinifi)
- Saf Python softmax siniflandirici egitimi, model serilestirme ve metrik raporu
- Tek kayit veya CSV uzerinden weak-point tahmini
- Risk, kural ve alan bilgisi birlestiren karar ajani
- LLM instruction veri seti uretimi ve opsiyonel LoRA fine-tuning giris noktasi
- Unity C# hidrodinamik, duty ve ML-Agents ornekleri
- ROS 2 telemetri/komut koprusu icin referans node
- Unit ve uctan uca testler
- Turkce proje outline dokumani (`docs/ROV_Digital_Twin_Project_Outline.docx`)

## Hizli baslangic

Kurulum gerektirmeyen demo (Python 3.10+):

```powershell
$env:PYTHONPATH = "src"
python -m rov_dt.cli demo --output-dir artifacts/demo
```

Adim adim:

```powershell
$env:PYTHONPATH = "src"
python -m rov_dt.cli generate --rows 4000 --output data/telemetry.csv
python -m rov_dt.cli train --input data/telemetry.csv --model models/weakpoint.json --report artifacts/metrics.json
python -m rov_dt.cli decide --model models/weakpoint.json --input data/telemetry.csv --row 12
python -m rov_dt.cli build-llm-data --input data/telemetry.csv --output data/llm_instructions.jsonl
```

Testler:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## Mimari

```text
Unity / ROS 2 telemetry
        |
        v
schema validation -> feature vector -> weak-point classifier
                                           |
                                           v
domain advisor (LLM/RAG-ready) -> safety decision agent -> action + rationale
                                           |
                                           v
                              operator / ROS command gateway
```

Karar ajani dogrudan motor komutu vermek yerine varsayilan olarak `operator_review`, `degraded_mode` veya `abort_and_surface` gibi emniyetli niyetler uretir. Gercek araca komut gonderimi, ayrica yetkilendirilmis bir ROS gateway ve donanim-in-the-loop test kapisi gerektirir.

## Dizinler

- `src/rov_dt/`: veri, model, LLM verisi ve karar mantigi
- `unity/Assets/ROVDigitalTwin/Scripts/`: Unity/ML-Agents referans kodu
- `ros2/rov_dt_bridge/`: ROS 2 kopru node'u
- `configs/`: ML-Agents ve LoRA konfigürasyonlari
- `knowledge/`: alan-uzman LLM bilgi tabani
- `docs/`: proje outline ve mimari dokumani
- `tests/`: deterministik testler

## Uretime gecis kapilari

Bu depo bir referans/MVP'dir; sentetik veri gercek ariza verisinin yerine gecmez. Uretimden once sensör zaman senkronizasyonu, gercek ROV kalibrasyonu, HIL/SIL testleri, fail-safe durum makinesi, model drift izleme ve operator onayi zorunlu tutulmalidir.
