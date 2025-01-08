from pathlib import Path
import os
import sys
import yaml
import os
import uuid
import datetime

MODEL_PATH = Path(__file__).resolve().parent.parent
BASE_PATH = MODEL_PATH.parent

sys.path.append(str(BASE_PATH))

CONFIG_PATH = MODEL_PATH.joinpath("configs").joinpath("configs.yaml")
with open(CONFIG_PATH, encoding="utf-8") as config_file:
    configs = yaml.load(config_file, Loader=yaml.SafeLoader)