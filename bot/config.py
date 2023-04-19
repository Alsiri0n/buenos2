from typing import TYPE_CHECKING
import os
from dataclasses import dataclass
from dotenv import load_dotenv
if TYPE_CHECKING:
    from bot.app import Application


@dataclass
class TgBotConfig:
    token: str
    openweather: str
    exchange: str
    pexels: str


@dataclass
class Config:
    tg_bot: TgBotConfig = None


def setup_config(app: "Application", config_path: str):
    load_dotenv(config_path)
    app.config = Config(
        tg_bot=TgBotConfig(
            token=os.getenv("TG_BOT_TOKEN"),
            openweather=os.getenv("OPENWEATHER_API_KEY"),
            exchange=os.getenv("EXCHANGE_RATES_API_KEY"),
            pexels=os.getenv("PEXELS_API_KEY"),
        ),
    )
