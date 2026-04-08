# EDI2Insights

EDI2Insights is a data engineering pipeline project that ingests healthcare EDI files (837P claims and 270 eligibility inquiries) through a custom API, streams them into Apache Kafka, transforms them into structured formats (CSV/JSON), and delivers them to cloud analytics platforms for insights.

# Project Overview

Workflow:

API Layer: FastAPI endpoint receives EDI files.

Kafka Producer: Publishes files to dedicated topics (edi-837p, edi-270).

Kafka Consumer: Reads messages and parses EDI into structured data.

Transformation: Converts EDI into CSV/JSON using Python (pyx12) or cloud ETL tools (AWS Glue / GCP Dataflow).

Analytics: Stores transformed data in Redshift/BigQuery and connects BI tools for dashboards.

# Project Structure

EDI2Insights/
├── api/
│   └── main.py          # FastAPI service to upload EDI files
├── kafka/
│   ├── producer.py      # Kafka producer logic
│   └── consumer.py      # Kafka consumer + transformation
├── transform/
│   └── edi_parser.py    # EDI to JSON/CSV parser
├── analytics/
│   └── warehouse_setup.md # Notes on Redshift/BigQuery integration
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation

# Setup Instructions

1. Prerequisites

Python 3.9+

Apache Kafka installed locally or on server

Zookeeper running

AWS/GCP account for analytics integration

2. Install Dependencies

pip install -r requirements.txt

3. Create Kafka Topics

kafka-topics.sh --create --topic edi-837p --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
kafka-topics.sh --create --topic edi-270 --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

4. Run API

uvicorn api.main:app --reload

5. Upload EDI Files

curl -X POST "http://127.0.0.1:8000/upload-edi/" -F "file=@sample_837p.edi"

6. Consume and Transform

python kafka/consumer.py

# Tools & Technologies

FastAPI – API layer

Apache Kafka – Streaming backbone

pyx12 / custom parser – EDI parsing

AWS Glue / GCP Dataflow – Cloud ETL

Redshift / BigQuery – Analytics warehouse

Tableau / Power BI / Looker – Visualization

# Example Use Cases

Claims volume analysis (837P)

Eligibility inquiry trends (270)

Provider performance dashboards