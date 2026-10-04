"""
Download the hourly price history that the real-path runs and calibration read (Yahoo Finance, via yfinance).

The CSV files are not in the repository: Yahoo's terms do not allow republishing the data. Yahoo serves at most
about 730 days of hourly bars, so a download made later covers a later window and the real-path results move a
little. Synthetic-path results do not need these files (the hourly sigmas they use are stored in sigma_v32.json).

    pip install yfinance pandas
    python3 fetch_data.py              # writes *_1h.csv next to this script
"""
import os
import yfinance as yf

FILES = {
    "eurusd_1h.csv": "EURUSD=X",
    "gbpusd_1h.csv": "GBPUSD=X",
    "usdjpy_1h.csv": "USDJPY=X",
    "gold_1h.csv":   "GC=F",
    "nq_1h.csv":     "NQ=F",
    "es_1h.csv":     "ES=F",
    "btc_1h.csv":    "BTC-USD",
    "eth_1h.csv":    "ETH-USD",
    "dax_1h.csv":    "^GDAXI",
}

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for fn, ticker in FILES.items():
        # the default column layout (Price / Ticker header rows) is what calibrate.load reads
        d = yf.download(ticker, period="730d", interval="1h", progress=False)
        if d is None or d.empty:
            print(f"{ticker}: no data returned")
            continue
        d.to_csv(os.path.join(here, fn))
        print(f"{fn}: {len(d)} bars, {d.index[0]} .. {d.index[-1]}")

if __name__ == "__main__":
    main()
