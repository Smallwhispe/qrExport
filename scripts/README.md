# QR Export - Windows 打包 & 部署指南

本项目通过 **PyInstaller** 将 Python 解释器、所有依赖和源码打包成单个 `QrExport.exe`，目标机器**无需安装 Python**即可运行；再通过 **NSSM** 将其注册为 Windows 服务，实现开机自启、崩溃自动重启。

---

## 一、目录结构

```
qrExport/
├── app.py                       # 入口文件（Flask + Manager 线程）
├── requirements.txt             # Python 依赖
├── .env                         # 运行时配置（Oracle/调度参数等）
├── .gitignore
├── config/
├── routes/
├── services/
├── vo/
├── log/                         # 运行日志（运行时自动创建）
├── export/                      # 二维码图片（运行时自动创建）
└── scripts/
    ├── build_windows.bat        # 打包脚本（开发机运行）
    ├── install_service.bat      # 注册为 Windows 服务（目标机运行，管理员）
    ├── uninstall_service.bat    # 停止并卸载服务（目标机运行，管理员）
    ├── prepare_deploy_package.bat # 整理绿色部署包（可选）
    └── README.md                # 本文档
```

---

## 二、核心思路

> 「把 venv 拷到别的机器上跑」是**行不通**的——venv 记录的是**本机 Python 的绝对路径**。
> 正确做法：在开发机用 PyInstaller 一次性打包 Python 解释器 + 所有依赖 + 源码 → 产出 `QrExport.exe` → 拷到任何 Windows 机器上直接运行。

**打包仅需在开发机执行一次**；部署到目标机器时仅需复制 `dist/` 目录。

---

## 三、开发机：打包流程（Step 1）

### 3.1 准备

- 开发机需安装 **Python 3.10+**
- 项目根目录下要有 `.env`（至少配置 Oracle 账号）

### 3.2 一键打包

在项目根目录下（PowerShell 或 cmd，**无需管理员权限**）执行：

```bat
scripts\build_windows.bat
```

脚本会自动：

1. 在项目根目录创建/更新虚拟环境 `.venv\`
2. `pip install -r requirements.txt` 装好全部依赖（包括 PyInstaller）
3. 清理旧产物 `build/`、`dist/`
4. 调用 PyInstaller 打包：
   ```bat
   pyinstaller --onefile --noconsole --name QrExport ^
               --collect-submodules config --collect-submodules routes ^
               --collect-submodules services --collect-submodules vo ^
               --collect-all oracledb app.py
   ```
5. 把 `.env` 复制到 `dist\` 与 `QrExport.exe` 同级

> **首次打包会比较慢**（1-3 分钟），因为 PyInstaller 需要把整个 Python 运行时和依赖压缩进一个 exe。

### 3.3 产物

```
dist/
├── QrExport.exe     ← 主程序（25~40 MB，自带 Python 解释器与所有依赖）
└── .env             ← 运行时配置
```

### 3.4 本地测试（可选）

双击 `dist\QrExport.exe`，然后浏览器打开：

```
http://127.0.0.1:5001/health
```

应返回：

```json
{
    "status": "ok",
    "manager_running": true,
    "qr_interval_seconds": 864000
}
```

确认正常后，**把 exe 进程杀掉**（任务管理器 → `QrExport.exe` → 结束任务），再进行下一步注册为服务。

---

## 四、目标机：注册为 Windows 服务（Step 2）

### 4.1 拷贝部署包

把开发机上的 `dist\` 整个目录拷到目标机器的**固定路径**，例如：

```
D:\apps\QrExport\
├── QrExport.exe
├── .env
└── scripts\               ← 后面会补进去
    ├── install_service.bat
    └── uninstall_service.bat
```

> 也可以在开发机先执行 `scripts\prepare_deploy_package.bat`，它会自动把 `install_service.bat`、`uninstall_service.bat` 复制到 `dist\scripts\` 并生成一份 `README.txt`，方便直接打包拷走。

### 4.2 安装 NSSM

**NSSM（Non-Sucking Service Manager）** 是一个轻量级工具（~400KB），用于把任意 exe 包装成标准 Windows 服务。

- 下载地址：https://nssm.cc/download
- 解压后，将 `nssm-2.24\win64\nssm.exe`（或 `win32\nssm.exe`）放到以下位置之一：
  - `C:\Windows\System32\`（最省事，全局可用）
  - `D:\apps\QrExport\scripts\`
  - 其他已加入 PATH 的目录

> 注意：
> - 64 位 Windows 请用 `win64` 版本的 `nssm.exe`，否则服务会注册失败。
> - 部分杀毒软件可能将 `nssm.exe` 误报为木马（因为它能把任意程序注册为服务），请手动加入白名单。

### 4.3 以管理员身份执行安装脚本

在目标机器上，**右键** `scripts\install_service.bat` → **以管理员身份运行**。

脚本会：

1. 检测 `dist\QrExport.exe` 是否存在（不存在则尝试找 `python.exe` 跑源码）
2. 检测 `nssm.exe` 是否存在
3. 如果服务 `QR Export Service` 已存在则先停止并删除（方便重装）
4. 用 `nssm install` 注册为服务，配置：
   - 工作目录 = exe 所在目录
   - 标准输出 = `log\service-stdout.log`
   - 标准错误 = `log\service-stderr.log`
   - 启动类型 = **自动**（开机自启）
   - 崩溃策略 = **3 秒后自动重启**
5. 用 `net start` 启动服务

成功后控制台输出会提示：

```
[5/5] 完成。
常用命令:
  启动    : net start "QR Export Service"
  停止    : net stop  "QR Export Service"
  ...
```

### 4.4 验证

在目标机器浏览器访问：

```
http://127.0.0.1:5001/health
```

---

## 五、日常运维

### 5.1 启停

| 操作 | 命令（管理员 cmd） |
|------|-------------------|
| 启动服务 | `net start "QR Export Service"` |
| 停止服务 | `net stop  "QR Export Service"` |
| 重启服务 | `net stop "QR Export Service" && net start "QR Export Service"` |
| 查看状态 | `sc query "QR Export Service"` 或 `services.msc` |
| 图形化配置 | `nssm edit "QR Export Service"` |

也可以按 `Win + R` → 输入 `services.msc` → 找到 `QR Export Service` → 右键操作。

### 5.2 查看日志

所有日志位于目标机器的部署目录下：

```
D:\apps\QrExport\log\
├── service-stdout.log   ← NSSM 捕获的标准输出（含 Flask 启动信息）
├── service-stderr.log   ← NSSM 捕获的标准错误（用于排查启动失败）
└── app-YYYY-MM-DD.log   ← 应用按日写出的业务日志（保留 30 天）
```

启动失败时**最先查看** `log\service-stderr.log`，常见原因：

- `.env` 缺失或 Oracle 账号密码错误
- 5001 端口被其他进程占用
- 部署路径中包含中文或特殊字符（尽量用纯英文路径）

### 5.3 卸载服务

以管理员身份运行：

```bat
scripts\uninstall_service.bat
```

脚本会先停止服务，再删除注册。服务被卸载后，可手动删除部署目录。

### 5.4 更新版本

1. 在开发机重新打包：`scripts\build_windows.bat`
2. 在目标机器上 `net stop "QR Export Service"` 停止服务
3. 覆盖 `QrExport.exe`（以及 `.env` 如果有配置变更）
4. `net start "QR Export Service"` 重启服务

---

## 六、.env 关键配置项

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `CORS_ALLOW_ORIGINS` | 允许的跨域来源（逗号分隔，`*` 代表允许任意来源） | `*` |
| `CORS_SUPPORT_CREDENTIALS` | 是否允许携带 Cookie/Authorization 等凭证 | `true` |
| `CORS_MAX_AGE` | 预检请求缓存秒数 | `86400` |
| `CORS_EXPOSE_HEADERS` | 暴露给前端的响应头（逗号分隔） | `Content-Type,Authorization` |
| `QR_INTERVAL_SECONDS` | QR 导出周期（秒） | `864000`（10 天） |
| `QR_IMAGE_VIEWER` | 自定义图片查看器命令（空=自动选择） | 空 |
| `ORACLE_USER` / `ORACLE_PASSWORD` | Oracle 账号密码 | 空 |
| `ORACLE_DSN` | Oracle 连接串 | 空 |
| `ORACLE_CONFIG_DIR` | Oracle 客户端配置目录 | 空 |
| `ORACLE_WALLET_PASSWORD` | Wallet 密码 | 空 |
| `ORACLE_DEFAULT_SQL` | 取数据的 SQL | 示例 SQL |

---

## 七、常见问题

**Q1：打包后 exe 能跑，但注册为服务就启动失败？**
A：最常见原因是「当前用户目录下能找到 `.env`，但服务以 SYSTEM 用户运行时工作目录不同」。脚本里已显式通过 `nssm set AppDirectory` 指定工作目录为部署目录，`.env` 与 exe 同级即可。

**Q2：NSSM 下载后报毒？**
A：因为 NSSM 的功能是「把任意 exe 注册为服务」，这在行为上与木马类似，所以部分安全软件会误报。可选择 WinMD / NSSM 官方签名版，或改用 `sc.exe` + `pywin32` 的原生方案（需改写入口）。

**Q3：exe 双击能跑，但服务启动后弹窗看不到二维码？**
A：Windows 服务默认运行在 Session 0，与用户桌面隔离，**弹不出窗口**。这是正常的——服务模式下主要用于后台取数据 + 生成二维码文件。如果需要在用户登录时弹出窗口，应改为「登录后启动 exe」而不是注册为服务。

**Q4：二维码弹窗 / 图片查看器在旧的 Windows 上没弹出来？**
A：Windows 下默认用系统自带的 `mspaint.exe` 打开二维码图片。如果要换用其它看图工具，在 `.env` 里配置 `QR_IMAGE_VIEWER` 指向该工具的绝对路径。

**Q5：如何限制只让本机访问，不让其他机器访问 5001？**
A：把 `app.py` 里的 `host='0.0.0.0'` 改成 `host='127.0.0.1'`，然后重新打包即可。或者在 Windows 防火墙上对 5001 端口放行仅本地 IP。

---

## 八、完整操作速查（复制粘贴）

开发机：

```bat
:: 1. 打包（首次稍慢）
scripts\build_windows.bat

:: 2. 本地测试
::    双击 dist\QrExport.exe → 浏览器访问 http://127.0.0.1:5001/health → 结束任务
```

目标机：

```bat
:: 1. 把 dist\ 整个目录拷到 D:\apps\QrExport\
:: 2. 下载 nssm.exe 放到 C:\Windows\System32\
:: 3. 右键 → 以管理员身份运行：
D:\apps\QrExport\scripts\install_service.bat

:: 4. 验证
::    浏览器打开 http://127.0.0.1:5001/health

:: 5. 卸载（需要时）
::    scripts\uninstall_service.bat
```
