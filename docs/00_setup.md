# 0. Setup

## Get the code

```bash
git clone https://github.com/Csum99/ORANGE_SAR.git
cd UAS_SAR_2026_student
```

## Python environment

Python 3.9+ recommended. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
```

Install the packages for the module you're working in (start with backprojection):

```bash
cd backprojection
pip install -r pip_requirements.txt
```

(`mocap/` and `pulson440/` have their own `pip_requirements.txt` — install those when
you reach guides 3–5.)

## Check it worked

```bash
python check_backprojection.py
```

You should see the simulator run, then three yellow **"NOT IMPLEMENTED YET"** results.
That's correct — implementing them is the assignment. If you instead get an
`ImportError`, see [Troubleshooting](06_troubleshooting.md).

## Repo tour

```
backprojection/   <- YOUR ASSIGNMENT lives here (+ simulator, checker, params, images)
pulson440/        <- radar control & unpacking (small TODOs for you; rest given)
mocap/            <- motion-capture preprocessing (small TODOs in utils.py; rest given)
common/           <- shared helpers (given, don't modify)
docs/             <- you are here
```
