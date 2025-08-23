import pandas as pd
from pathlib import Path

TOL = 0

INPUT = Path("bank.csv")
MY_NAMES = {"박수호", "suho", "수호"}

def _fmt_money(x: float, sign: bool = False) -> str:
    s = f"{abs(int(round(x))):,}"
    if sign:
        return ("+" if x > 0 else "-" if x < 0 else "") + s
    return s



def load_and_process(csv_path: Path = INPUT, my_names=None):

    if my_names is None:
        my_names = MY_NAMES
    df = pd.read_csv(csv_path, encoding="utf-8-sig", header=None)
    df.columns = [
        "datetime", "type", "amount", "balance", "category", "counterparty", "memo"
    ]

    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y.%m.%d %H:%M:%S", errors="coerce")
    df["date"] = df["datetime"].dt.date

    for col in ("amount", "balance"):
        s = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        s = pd.to_numeric(s.replace({"": "0", "nan": "0"}), errors="coerce").fillna(0.0)
        df[col] = s

    df = df.sort_values("datetime").reset_index(drop=True)

    df["is_internal"] = df["counterparty"].astype(str).apply(
        lambda s: any(name in s for name in my_names)
    )


    df["deposit"] = df["amount"].where(df["amount"] > 0, 0.0)
    df["withdraw"] = (-df["amount"]).where(df["amount"] < 0, 0.0)


    all_days = df["date"].dropna().sort_values().unique()
    df_excl = df[~df["is_internal"]]
    daily = df_excl.groupby("date").agg(
        deposit=("deposit", "sum"),
        withdraw=("withdraw", "sum"),
        net=("amount", "sum"),
    ).reindex(all_days, fill_value=0).sort_index()


    last_bal = df_excl.groupby("date")["balance"].last()
    if last_bal.empty:
        last_bal = df.groupby("date")["balance"].last()
    last_bal = last_bal.reindex(all_days)
    daily["last_balance"] = last_bal.ffill().fillna(0)


    daily["cum_deposit"] = daily["deposit"].cumsum()
    daily["cum_withdraw"] = daily["withdraw"].cumsum()


    lines = []
    for day, day_df in df.groupby("date", sort=True):
        stats = daily.loc[day] if day in daily.index else pd.Series(
            {"deposit": 0, "withdraw": 0, "net": 0,
             "last_balance": 0, "cum_deposit": 0, "cum_withdraw": 0}
        )
        lines.append("------------------------")
        lines.append(f"{day}")
        lines.append("---오늘의거래내역---")

        for _, row in day_df.iterrows():
            title = (str(row.get("counterparty") or "").strip()) or (str(row.get("category") or "").strip())
            amt = _fmt_money(row["amount"], sign=True)
            tag = " [SELF]" if bool(row.get("is_internal")) else ""
            lines.append(f"\t{title} {row['type']} {amt}{tag}")

        lines.append(" ---오늘의입출금내역(CSV 기준)---")
        lines.append(f"입금: {_fmt_money(stats['deposit'])}")
        lines.append(f"출금: {_fmt_money(stats['withdraw'])}")
        lines.append(f"순이익: {_fmt_money(stats['net'], sign=True)}")
        lines.append("---현재까지의 거래내역--")

        lines.append(f"현재까지 출금: {_fmt_money(stats['cum_withdraw'])}")
        lines.append(f"현재까지 재산: {_fmt_money(stats['last_balance'])}")
        lines.append("")

    return df, daily, lines