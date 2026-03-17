# quant-qmt

这是一个用于研究 `xtquant`（MiniQMT 本地 Python 模式）行情获取与交易下单的实验项目。

## 前置条件

- Windows
- 已安装 MiniQMT，并已启动客户端
- 本项目使用 `.venv`，且 venv 使用 `--system-site-packages` 复用系统 Python 里的 `xtquant`

## 环境准备

在项目根目录执行：

```powershell
C:\Users\jack\AppData\Local\Programs\Python\Python312\python.exe -m venv .venv --system-site-packages
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

## scripts 目录脚本说明

### 1) 行情：下载历史 + 订阅全推（xtdata）

脚本：`scripts/xtdata_subscribe_and_download.py`

仅查看帮助：

```powershell
& .\.venv\Scripts\python.exe .\scripts\xtdata_subscribe_and_download.py --help
```

下载历史（示例）：

```powershell
& .\.venv\Scripts\python.exe .\scripts\xtdata_subscribe_and_download.py --download-history --codes "000001.SZ" --period 1d --no-subscribe
```

订阅并轮询输出（示例）：

```powershell
& .\.venv\Scripts\python.exe .\scripts\xtdata_subscribe_and_download.py --codes "000001.SZ" --period 1d --loop 10 --sleep 3
```

订阅回调模式（会阻塞在 `xtdata.run()`，用于观察实时推送）：

```powershell
& .\.venv\Scripts\python.exe .\scripts\xtdata_subscribe_and_download.py --codes "000001.SZ" --period 1d --use-callback
```

### 2) 交易：查询资产/持仓 + 买一笔 + 卖一笔 + 回调（xttrader）

脚本：`scripts/xttrader_simple_buy_sell.py`

仅查看帮助：

```powershell
& .\.venv\Scripts\python.exe .\scripts\xttrader_simple_buy_sell.py --help
```

只查询（默认不发单，安全）：

```powershell
& .\.venv\Scripts\python.exe .\scripts\xttrader_simple_buy_sell.py --account-id 你的资金账号
```

如果你的 `userdata_mini` 路径不是默认值，手动指定：

```powershell
& .\.venv\Scripts\python.exe .\scripts\xttrader_simple_buy_sell.py --account-id 你的资金账号 --qmt-path "D:\xxx\userdata_mini"
```

真下单（需要显式加 `--confirm`；`FIX_PRICE` 还需要 `--price`）：

```powershell
& .\.venv\Scripts\python.exe .\scripts\xttrader_simple_buy_sell.py `
  --account-id 你的资金账号 `
  --code 600000.SH `
  --price-type FIX_PRICE `
  --price 10.5 `
  --buy-volume 100 `
  --sell-volume 100 `
  --confirm `
  --wait 10
```

打印 raw 对象属性（用于对照字段/排查返回结构）：

```powershell
& .\.venv\Scripts\python.exe .\scripts\xttrader_simple_buy_sell.py --account-id 你的资金账号 --dump-raw
```
