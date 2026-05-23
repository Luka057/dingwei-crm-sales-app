# Manifest CSV 格式规范

## 文件位置

`samples.csv` 放在 `vision-service/` 目录下（与 `index_samples.py` 同级）。

---

## 列定义

| 列名          | 类型   | 必填 | 说明                                                      |
|-------------|------|------|-----------------------------------------------------------|
| `image_file`  | str  | 是   | 图片文件名，**相对于 `--images` 目录**（如 `sample_001.png`）      |
| `sample_no`   | str  | 是   | 样本编号，业务主键（如 `HY-20-BK-soft`）                        |
| `external_id` | str  | 否   | ERP 系统外部 ID（对接用，可为空）                               |
| `width`       | str  | 否   | 织带宽度（如 `20mm`、`25mm`、`38mm`）                         |
| `tension`     | str  | 否   | 弹力/开力度等级（见枚举）                                      |
| `ribbon_type` | str  | 否   | 织带类型（如 `提花织带`、`平纹织带`、`罗纹织带`、`锦纶织带`）         |
| `color`       | str  | 否   | 颜色（如 `黑色`、`白色`、`红色`）                               |
| `status`      | str  | 否   | 样本状态（拼音枚举，见下表）                                    |

---

## 示例行

```csv
image_file,sample_no,external_id,width,tension,ribbon_type,color,status
sample_001.png,HY-20-BK-soft,ERP-10001,20mm,soft,提花织带,黑色,queren
sample_002.png,HY-25-WH-medium,ERP-10002,25mm,medium,提花织带,白色,yizhuandingdan
```

---

## `status` 拼音枚举

| 拼音值             | 中文含义   |
|-----------------|--------|
| `qiyang`        | 起样     |
| `zhongban`      | 中版     |
| `queren`        | 确认     |
| `yizhuandingdan` | 已转订单  |
| `yifangqi`      | 已放弃   |

---

## `image_file` 路径规则

- **相对路径**：相对于 `index_samples.py --images` 参数指定的目录。
- 支持子目录，例如 `2024/sample_001.png`（前提是 `--images` 目录下有该子目录）。
- 图片格式支持 PNG、JPEG、WebP（PIL 支持的格式均可）。

---

## 注意事项

1. 文件编码必须为 **UTF-8**（含中文字符）。
2. 若某行 `image_file` 文件不存在，`index_samples.py` 会跳过该行并打印警告。
3. `external_id` 为空时，检索结果中该字段返回 `null`。
4. `tension` 字段目前为自由字符串（`soft`/`medium`/`hard` 仅为约定），
   `process_similarity()` 使用宽松包含匹配，不要求精确值。
