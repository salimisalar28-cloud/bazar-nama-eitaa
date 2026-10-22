
import os
import requests
import jdatetime
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal, InvalidOperation

SERVIX_URL = "https://servix.cc/api/v1/assets"
EITAA_URL = "https://eitaayar.ir/api/{}/sendMessage"

ASSET_CODES = {
    "usd": "USD_RLS",
    "eur": "EUR_RLS",
    "gold18": "GOLD_18_RLS",
    "gold24": "GOLD_24_RLS",
    "gold_ounce": "GOLD_OUNCE_USD",
    "emami": "SEKKEH_RLS",
    "half": "NIM_SEKKEH_RLS",
    "quarter": "ROB_SEKKEH_RLS",
    "bahar": "BAHAR_RLS",
    "gerami": "GERAMI_SEKKEH_RLS",
    "silver_ounce": "SILVER_OUNCE_USD",
    "bitcoin": "BTC_USD",
}

DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def persian_number(value):
    return f"{value:,}".translate(DIGITS).replace(",", "٬")


def get_prices():
    response = requests.get(
        SERVIX_URL,
        headers={"X-API-Key": os.environ["SERVIX_API_KEY"]},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list):
        raise ValueError("ساختار پاسخ API قیمت‌ها غیرمنتظره است.")

    return {
        item.get("code"): item.get("value")
        for item in data
        if isinstance(item, dict) and item.get("code")
    }


def format_price(raw, code):
    if raw is None:
        return "ناموجود"

    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return "ناموجود"

    if not value.is_finite():
        return "ناموجود"

    if code.endswith("_RLS"):
        value /= Decimal("10")
        return f"{persian_number(int(value))} تومان"

    return f"${persian_number(int(value))}"


def make_report(prices):
    now = datetime.now(ZoneInfo("Asia/Tehran"))
    jalali_now = jdatetime.datetime.fromgregorian(
        datetime=now.replace(tzinfo=None)
    )

    lines = [
        "📊 بازارنما | Bazar Nama",
        f"📅 {jalali_now.strftime('%Y/%m/%d').translate(DIGITS)} | "
        f"⏰ {jalali_now.strftime('%H:%M').translate(DIGITS)}",
        "",
        "💵 ارز",
        f"💵 دلار آزاد: {format_price(prices.get(ASSET_CODES['usd']), ASSET_CODES['usd'])}",
        f"💶 یورو: {format_price(prices.get(ASSET_CODES['eur']), ASSET_CODES['eur'])}",
        "",
        "🥇 طلا",
        f"🟡 طلای ۱۸ عیار: {format_price(prices.get(ASSET_CODES['gold18']), ASSET_CODES['gold18'])}",
        f"🟡 طلای ۲۴ عیار: {format_price(prices.get(ASSET_CODES['gold24']), ASSET_CODES['gold24'])}",
        f"🌎 اونس طلا: {format_price(prices.get(ASSET_CODES['gold_ounce']), ASSET_CODES['gold_ounce'])}",
        "",
        "🪙 سکه",
        f"🔴 سکه امامی: {format_price(prices.get(ASSET_CODES['emami']), ASSET_CODES['emami'])}",
        f"🟠 نیم‌سکه: {format_price(prices.get(ASSET_CODES['half']), ASSET_CODES['half'])}",
        f"🟠 ربع‌سکه: {format_price(prices.get(ASSET_CODES['quarter']), ASSET_CODES['quarter'])}",
        f"🟡 بهار آزادی: {format_price(prices.get(ASSET_CODES['bahar']), ASSET_CODES['bahar'])}",
        f"🟡 سکه گرمی: {format_price(prices.get(ASSET_CODES['gerami']), ASSET_CODES['gerami'])}",
        "",
        "🥈 نقره",
        f"🥈 اونس نقره: {format_price(prices.get(ASSET_CODES['silver_ounce']), ASSET_CODES['silver_ounce'])}",
        "",
        "₿ ارز دیجیتال",
        f"₿ بیت‌کوین: {format_price(prices.get(ASSET_CODES['bitcoin']), ASSET_CODES['bitcoin'])}",
        "",
        "🔗 @BazarNamaOfficial",
    ]

    return "\n".join(lines)


def send_to_eitaa(message):
    token = os.environ["EITAAYAR_TOKEN"]
    chat_id = os.environ["EITAAYAR_CHAT_ID"]

    response = requests.post(
        EITAA_URL.format(token),
        data={"chat_id": chat_id, "text": message},
        timeout=30,
    )
    response.raise_for_status()

    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"ارسال ایتا ناموفق بود: {result}")

    print("گزارش با موفقیت به ایتا ارسال شد.")


def main():
    print("دریافت قیمت‌ها از Servix...")
    prices = get_prices()

    missing = [
        code for code in ASSET_CODES.values()
        if prices.get(code) is None
    ]
    if missing:
        raise ValueError(
            "قیمت برخی دارایی‌ها موجود نیست: " + ", ".join(missing)
        )

    report = make_report(prices)
    print(report)
    send_to_eitaa(report)


if __name__ == "__main__":
    main()
