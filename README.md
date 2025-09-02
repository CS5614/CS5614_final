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
docker build --secret id=openai_api_key,src=.env -t qolscope-app . 
docker run -p 8000:8000 qolscope
```

### Use cmd

#### frontend
```bash
cd client
pnpm run dev
```

#### backend

```bash
uv run uvicorn server.app:app --reload
```

## Run Jupyter Notebooks
```bash
cd data_analysis
source .venv/bin/activate
```
Then run the jupyter notebook