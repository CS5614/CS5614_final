# CS5614_final
Estimating Housing-Centric Quality of Life Assessment in Urban Areas With Social Sentiment and Objective Data

## Getting Started

### Installing uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

or

```bash
pip install uv
```

## Running db import Scripts

To execute the `import.py` script, follow these steps:

```bash
cd scripts

uv run import.py
```



## Run the server and client


### Use docker(recommended)
```bash

docker build \
  --build-arg GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY \
  --build-arg DB_NAME=YOUR_POSTGRESQL_DB_NAME \
  --build-arg DB_USER=YOUR_DB_USER_NAME \
  --build-arg DB_PASSWORD=YOUR_DB_PASSWORD \
  --build-arg DB_HOST=YOUR_DB_HOST \
  -t cs5614_final .

docker run -p 8000:8000 cs5614_final
```

### Use cmd

#### frontend
```bash
cd client
mv ./src/config/index.ts.example ./src/config/index.ts
## replace with your google map api

pnpm install

pnpm run dev
```

#### backend

```bash
cd server

uv sync

uv run fastapi dev
```

## Run Jupyter Notebooks
```bash
cd data_analysis
source .venv/bin/activate
```
Then run the jupyter notebook